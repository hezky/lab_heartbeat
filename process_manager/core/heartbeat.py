# process_manager/core/heartbeat.py
# Heartbeat system for process health monitoring
# Does NOT control processes, only tracks their heartbeats

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from .registry import ProcessRegistry, ProcessState

logger = logging.getLogger(__name__)

class HeartbeatManager:
    def __init__(self, registry: ProcessRegistry):
        self.registry = registry
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.check_interval = 5  # seconds
        self.timeout_threshold = 30  # seconds - mark as unresponsive
        self.crash_threshold = 60  # seconds - mark as crashed
        self.active_processes: Set[str] = set()

    def start(self):
        """Start the heartbeat monitoring thread"""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            logger.warning("Heartbeat manager already running")
            return

        self.stop_event.clear()
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        logger.info("Heartbeat manager started")

    def stop(self):
        """Stop the heartbeat monitoring thread"""
        self.stop_event.set()
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        logger.info("Heartbeat manager stopped")

    def register_heartbeat(self, process_id: str):
        """Register a heartbeat from a process"""
        process_info = self.registry.get_process(process_id)
        if not process_info:
            logger.warning(f"Heartbeat from unknown process: {process_id}")
            return False

        # Update heartbeat timestamp
        self.registry.update_heartbeat(process_id)
        self.active_processes.add(process_id)

        # Update state to running if it was starting
        if process_info.state == ProcessState.STARTING:
            self.registry.update_state(process_id, ProcessState.RUNNING)

        return True

    def _heartbeat_loop(self):
        """Main heartbeat monitoring loop"""
        while not self.stop_event.is_set():
            try:
                self._check_heartbeats()
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

            self.stop_event.wait(self.check_interval)

    def _check_heartbeats(self):
        """Check all running processes for heartbeat timeouts"""
        running_processes = self.registry.list_processes(ProcessState.RUNNING)
        current_time = datetime.now()

        for process_info in running_processes:
            if process_info.last_heartbeat:
                time_since_heartbeat = (current_time - process_info.last_heartbeat).total_seconds()

                if time_since_heartbeat > self.crash_threshold:
                    # Process hasn't sent heartbeat for too long - mark as crashed
                    logger.error(
                        f"Process {process_info.config.name} heartbeat timeout "
                        f"({time_since_heartbeat:.0f}s), marking as crashed"
                    )
                    self.registry.update_state(
                        process_info.id,
                        ProcessState.CRASHED,
                        error=f"Heartbeat timeout after {time_since_heartbeat:.0f} seconds"
                    )
                    self.active_processes.discard(process_info.id)

                elif time_since_heartbeat > self.timeout_threshold:
                    # Warning threshold
                    logger.warning(
                        f"Process {process_info.config.name} heartbeat delayed "
                        f"({time_since_heartbeat:.0f}s)"
                    )

    def get_heartbeat_status(self) -> Dict:
        """Get heartbeat status for all processes"""
        status = {}
        current_time = datetime.now()

        for process_info in self.registry.list_processes():
            process_status = {
                "name": process_info.config.name,
                "state": process_info.state.value,
                "last_heartbeat": None,
                "seconds_since_heartbeat": None,
                "is_healthy": False
            }

            if process_info.last_heartbeat:
                time_since = (current_time - process_info.last_heartbeat).total_seconds()
                process_status["last_heartbeat"] = process_info.last_heartbeat.isoformat()
                process_status["seconds_since_heartbeat"] = round(time_since, 1)
                process_status["is_healthy"] = (
                    process_info.state == ProcessState.RUNNING and
                    time_since < self.timeout_threshold
                )

            status[process_info.id] = process_status

        return status

    def is_process_healthy(self, process_id: str) -> bool:
        """Check if a specific process is healthy based on heartbeat"""
        process_info = self.registry.get_process(process_id)
        if not process_info:
            return False

        if process_info.state != ProcessState.RUNNING:
            return False

        if not process_info.last_heartbeat:
            return False

        time_since = (datetime.now() - process_info.last_heartbeat).total_seconds()
        return time_since < self.timeout_threshold


class ProcessHeartbeatClient:
    """Client for processes to send heartbeats"""

    def __init__(self, process_id: str, manager_url: str = "http://localhost:8080"):
        self.process_id = process_id
        self.manager_url = manager_url
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.interval = 10  # seconds

    def start(self):
        """Start sending heartbeats"""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            return

        self.stop_event.clear()
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def stop(self):
        """Stop sending heartbeats"""
        self.stop_event.set()
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)

    def _heartbeat_loop(self):
        """Send heartbeats periodically"""
        import requests

        while not self.stop_event.is_set():
            try:
                # Send heartbeat to manager
                response = requests.post(
                    f"{self.manager_url}/api/heartbeat",
                    json={"process_id": self.process_id},
                    timeout=5
                )
                if response.status_code != 200:
                    logger.warning(f"Heartbeat failed: {response.status_code}")
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {e}")

            self.stop_event.wait(self.interval)

    def send_heartbeat(self) -> bool:
        """Manually send a single heartbeat"""
        import requests

        try:
            response = requests.post(
                f"{self.manager_url}/api/heartbeat",
                json={"process_id": self.process_id},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return False