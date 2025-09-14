# process_manager/core/controller.py
# Process lifecycle controller for starting, stopping, and managing processes
# Does NOT monitor or track heartbeats, only controls execution

import os
import signal
import subprocess
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from .registry import ProcessRegistry, ProcessInfo, ProcessState, ProcessType

logger = logging.getLogger(__name__)

class RestartPolicy:
    ON_FAILURE = "on-failure"
    ALWAYS = "always"
    NEVER = "never"
    UNLESS_STOPPED = "unless-stopped"

class ProcessController:
    def __init__(self, registry: ProcessRegistry):
        self.registry = registry
        self.processes: Dict[str, subprocess.Popen] = {}
        self.restart_threads: Dict[str, threading.Thread] = {}
        self.stop_events: Dict[str, threading.Event] = {}
        self.graceful_timeout = 10  # seconds
        self.restart_backoff = [1, 2, 4, 8, 16, 30, 60]  # exponential backoff

    def start_process(self, process_id: str) -> bool:
        """Start a registered process"""
        process_info = self.registry.get_process(process_id)
        if not process_info:
            logger.error(f"Process {process_id} not found in registry")
            return False

        if process_info.state == ProcessState.RUNNING:
            logger.warning(f"Process {process_id} is already running")
            return False

        try:
            # Update state to starting
            self.registry.update_state(process_id, ProcessState.STARTING)

            # Prepare environment
            env = os.environ.copy()
            if process_info.config.env:
                env.update(process_info.config.env)

            # Add port to environment if specified
            if process_info.config.ports and len(process_info.config.ports) > 0:
                env['PORT'] = str(process_info.config.ports[0])

            # Prepare command based on process type
            cmd = self._prepare_command(process_info.config)

            # Convert relative paths to absolute
            workdir = process_info.config.workdir
            if not os.path.isabs(workdir):
                workdir = os.path.abspath(workdir)

            # Start the process
            # Log the command for debugging
            logger.info(f"Starting process with command: {cmd}")
            logger.info(f"Working directory: {workdir}")
            logger.info(f"Environment PORT: {env.get('PORT', 'not set')}")

            process = subprocess.Popen(
                cmd,
                cwd=workdir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Keep separate for better debugging
                shell=False if isinstance(cmd, list) else True,
                text=True  # Return string instead of bytes
            )

            # Store process reference
            self.processes[process_id] = process

            # Update registry with running state and PID
            self.registry.update_state(process_id, ProcessState.RUNNING, pid=process.pid)

            # Start restart monitor if policy requires it
            if process_info.config.restart_policy != RestartPolicy.NEVER:
                self._start_restart_monitor(process_id)

            logger.info(f"Started process {process_id} with PID {process.pid}")
            return True

        except Exception as e:
            logger.error(f"Failed to start process {process_id}: {e}")
            self.registry.update_state(
                process_id,
                ProcessState.FAILED,
                error=str(e)
            )
            return False

    def stop_process(self, process_id: str, force: bool = False) -> bool:
        """Stop a running process"""
        process_info = self.registry.get_process(process_id)
        if not process_info:
            logger.error(f"Process {process_id} not found")
            return False

        # If process is already stopped or crashed, consider it success
        if process_info.state in [ProcessState.STOPPED, ProcessState.CRASHED, ProcessState.FAILED]:
            logger.info(f"Process {process_id} is already stopped (state: {process_info.state.value})")
            # Clean up any remaining references
            self.processes.pop(process_id, None)
            return True

        if process_info.state != ProcessState.RUNNING:
            logger.warning(f"Process {process_id} is in state {process_info.state.value}, cannot stop")
            return False

        # Stop restart monitor
        self._stop_restart_monitor(process_id)

        # Update state to stopping
        self.registry.update_state(process_id, ProcessState.STOPPING)

        try:
            process = self.processes.get(process_id)
            if process and process.poll() is None:
                if force:
                    # Force kill
                    process.kill()
                    logger.info(f"Force killed process {process_id}")
                else:
                    # Graceful shutdown
                    process.terminate()
                    logger.info(f"Sent SIGTERM to process {process_id}")

                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=self.graceful_timeout)
                        logger.info(f"Process {process_id} terminated gracefully")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Process {process_id} did not terminate gracefully, killing")
                        process.kill()
                        process.wait()

            # Clean up
            self.processes.pop(process_id, None)
            self.registry.update_state(process_id, ProcessState.STOPPED)

            return True

        except Exception as e:
            logger.error(f"Failed to stop process {process_id}: {e}")
            self.registry.update_state(
                process_id,
                ProcessState.FAILED,
                error=str(e)
            )
            return False

    def restart_process(self, process_id: str) -> bool:
        """Restart a process"""
        logger.info(f"Restarting process {process_id}")

        # Stop if running
        if process_id in self.processes:
            self.stop_process(process_id)
            time.sleep(1)  # Brief pause between stop and start

        # Start again
        return self.start_process(process_id)

    def _prepare_command(self, config):
        """Prepare command based on process type"""
        if config.type == ProcessType.PYTHON:
            # Check if venv exists and use it
            # Try to find venv in the project root dynamically
            from pathlib import Path
            current_file = Path(os.path.abspath(__file__))
            project_root = current_file.parent.parent.parent  # Go up to lab_heartbeat
            venv_python = project_root / "venv" / "bin" / "python"

            # Just use the filename, since we'll run from workdir
            script_name = os.path.basename(config.command)

            if venv_python.exists():
                logger.info(f"Using venv Python: {venv_python}")
                return [str(venv_python), "-u", script_name]
            else:
                logger.info("Using system Python")
                return ["python3", "-u", script_name]
        elif config.type == ProcessType.NODEJS:
            # For Node.js, use the command directly as it's the script path
            return ["node", config.command]
        elif config.type == ProcessType.SHELL:
            return config.command  # Keep as string for shell=True
        elif config.type == ProcessType.DOCKER:
            # Docker command preparation
            return ["docker", "run"] + config.command.split()
        else:
            # Custom type - use command as-is
            return config.command.split()

    def _start_restart_monitor(self, process_id: str):
        """Start monitoring thread for automatic restarts"""
        if process_id in self.restart_threads:
            return

        stop_event = threading.Event()
        self.stop_events[process_id] = stop_event

        thread = threading.Thread(
            target=self._restart_monitor_loop,
            args=(process_id, stop_event)
        )
        thread.daemon = True
        thread.start()

        self.restart_threads[process_id] = thread

    def _stop_restart_monitor(self, process_id: str):
        """Stop the restart monitor thread"""
        if process_id in self.stop_events:
            self.stop_events[process_id].set()

        if process_id in self.restart_threads:
            thread = self.restart_threads[process_id]
            thread.join(timeout=5)
            del self.restart_threads[process_id]

        self.stop_events.pop(process_id, None)

    def _restart_monitor_loop(self, process_id: str, stop_event: threading.Event):
        """Monitor process and restart if needed"""
        restart_attempt = 0

        while not stop_event.is_set():
            try:
                process_info = self.registry.get_process(process_id)
                if not process_info:
                    break

                process = self.processes.get(process_id)
                if process:
                    # Check if process has exited
                    exit_code = process.poll()
                    if exit_code is not None:
                        logger.warning(f"Process {process_id} exited with code {exit_code}")

                        # Determine if we should restart
                        should_restart = self._should_restart(
                            process_info.config.restart_policy,
                            exit_code,
                            restart_attempt,
                            process_info.config.max_retries
                        )

                        if should_restart:
                            # Calculate backoff
                            backoff_index = min(restart_attempt, len(self.restart_backoff) - 1)
                            wait_time = self.restart_backoff[backoff_index]

                            logger.info(
                                f"Restarting process {process_id} in {wait_time} seconds "
                                f"(attempt {restart_attempt + 1})"
                            )

                            # Wait with ability to be interrupted
                            if stop_event.wait(wait_time):
                                break

                            # Increment restart count
                            self.registry.increment_restart_count(process_id)
                            restart_attempt += 1

                            # Attempt restart
                            if not self.start_process(process_id):
                                logger.error(f"Failed to restart process {process_id}")
                        else:
                            # No restart, update state and exit
                            # Check if we're being stopped intentionally
                            if stop_event.is_set():
                                # Process was stopped manually, don't change state
                                logger.debug(f"Process {process_id} was manually stopped, keeping current state")
                            else:
                                # Process crashed or exited on its own
                                state = ProcessState.FAILED if exit_code != 0 else ProcessState.STOPPED
                                self.registry.update_state(process_id, state)
                            break

                # Check periodically
                stop_event.wait(2)

            except Exception as e:
                logger.error(f"Error in restart monitor for {process_id}: {e}")
                stop_event.wait(5)

    def _should_restart(self, policy: str, exit_code: int,
                        attempt: int, max_retries: int) -> bool:
        """Determine if process should be restarted"""
        if policy == RestartPolicy.NEVER:
            return False
        elif policy == RestartPolicy.ALWAYS:
            return attempt < max_retries
        elif policy == RestartPolicy.ON_FAILURE:
            return exit_code != 0 and attempt < max_retries
        elif policy == RestartPolicy.UNLESS_STOPPED:
            # Only restart if it crashed (non-zero exit)
            return exit_code != 0 and attempt < max_retries
        return False

    def get_process_output(self, process_id: str, lines: int = 100) -> Tuple[List[str], List[str]]:
        """Get stdout and stderr from a process"""
        process = self.processes.get(process_id)
        if not process:
            return [], []

        stdout_lines = []
        stderr_lines = []

        try:
            # Try to get output, handling both running and terminated processes
            if process.stdout:
                try:
                    # For running process, use communicate with timeout
                    stdout_data, stderr_data = process.communicate(timeout=0.1)
                    if stdout_data:
                        stdout_lines = stdout_data.splitlines()[-lines:]
                    if stderr_data:
                        stderr_lines = stderr_data.splitlines()[-lines:]
                except subprocess.TimeoutExpired:
                    # Process still running, try to read available output
                    if process.stdout and process.stdout.readable():
                        stdout_lines = process.stdout.readlines()[-lines:]
                    if process.stderr and process.stderr.readable():
                        stderr_lines = process.stderr.readlines()[-lines:]
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error reading process output: {e}")

        return stdout_lines, stderr_lines

    def stop_all(self):
        """Stop all running processes"""
        for process_id in list(self.processes.keys()):
            self.stop_process(process_id)

    def cleanup(self):
        """Clean up resources"""
        self.stop_all()
        for thread in self.restart_threads.values():
            if thread.is_alive():
                thread.join(timeout=5)