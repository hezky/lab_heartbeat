# process_manager/core/monitor.py
# Process monitoring system for tracking health and metrics
# Does NOT control processes, only observes and reports

import psutil
import threading
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Callable, Any
from dataclasses import dataclass
from .registry import ProcessRegistry, ProcessInfo, ProcessState

logger = logging.getLogger(__name__)

@dataclass
class ProcessMetrics:
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    num_threads: int
    num_connections: int
    io_read_bytes: int
    io_write_bytes: int
    uptime_seconds: int
    is_responsive: bool

@dataclass
class HealthCheckResult:
    is_healthy: bool
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    error: Optional[str] = None

class ProcessMonitor:
    def __init__(self, registry: ProcessRegistry):
        self.registry = registry
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.check_interval = 10  # seconds
        self.health_check_timeout = 5  # seconds
        self.metrics_cache: Dict[str, ProcessMetrics] = {}
        self.health_callbacks: Dict[str, Callable] = {}

    def start(self):
        """Start the monitoring thread"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitor already running")
            return

        self.stop_event.clear()
        self.monitoring_thread = threading.Thread(target=self._monitor_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        logger.info("Process monitor started")

    def stop(self):
        """Stop the monitoring thread"""
        self.stop_event.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Process monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while not self.stop_event.is_set():
            try:
                # Get all processes to check
                all_processes = self.registry.list_all_processes()

                for process_info in all_processes:
                    # Only check processes that are supposed to be running
                    if process_info.state == ProcessState.RUNNING:
                        self._check_process(process_info)
                    elif process_info.state in [ProcessState.STOPPING, ProcessState.STOPPED]:
                        # Don't touch processes that are being or have been stopped
                        continue

                # Cleanup stale processes
                self.registry.cleanup_stale_processes()

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")

            # Wait for next check interval
            self.stop_event.wait(self.check_interval)

    def _check_process(self, process_info: ProcessInfo):
        """Check individual process health and metrics"""
        try:
            # Check if process is still running
            if process_info.pid:
                if not self._is_process_running(process_info.pid):
                    # Only mark as crashed if it's not being stopped intentionally
                    current_state = self.registry.get_process(process_info.id).state
                    if current_state not in [ProcessState.STOPPING, ProcessState.STOPPED]:
                        self.registry.update_state(
                            process_info.id,
                            ProcessState.CRASHED,
                            error="Process not found"
                        )
                    return

                # Collect metrics
                metrics = self._collect_metrics(process_info.pid, process_info.started_at)
                if metrics:
                    self.metrics_cache[process_info.id] = metrics

            # Perform health check if configured
            if process_info.config.health_check_endpoint:
                health_result = self._perform_health_check(
                    process_info.config.health_check_endpoint,
                    process_info.config.ports[0] if process_info.config.ports else None
                )

                if not health_result.is_healthy:
                    logger.warning(
                        f"Process {process_info.config.name} health check failed: {health_result.error}"
                    )

                    # Execute callback if registered
                    if process_info.id in self.health_callbacks:
                        self.health_callbacks[process_info.id](process_info, health_result)

        except Exception as e:
            logger.error(f"Error checking process {process_info.id}: {e}")

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running"""
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def _collect_metrics(self, pid: int, started_at: Optional[datetime]) -> Optional[ProcessMetrics]:
        """Collect metrics for a process"""
        try:
            process = psutil.Process(pid)

            # Get process info
            with process.oneshot():
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                num_threads = process.num_threads()

                # Get connections
                try:
                    connections = process.connections()
                    num_connections = len(connections)
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    num_connections = 0

                # Get I/O counters
                try:
                    io_counters = process.io_counters()
                    io_read_bytes = io_counters.read_bytes
                    io_write_bytes = io_counters.write_bytes
                except (psutil.AccessDenied, AttributeError):
                    io_read_bytes = 0
                    io_write_bytes = 0

            # Calculate uptime
            uptime_seconds = 0
            if started_at:
                uptime_seconds = int((datetime.now() - started_at).total_seconds())

            return ProcessMetrics(
                cpu_percent=cpu_percent,
                memory_mb=memory_info.rss / (1024 * 1024),
                memory_percent=memory_percent,
                num_threads=num_threads,
                num_connections=num_connections,
                io_read_bytes=io_read_bytes,
                io_write_bytes=io_write_bytes,
                uptime_seconds=uptime_seconds,
                is_responsive=True
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Cannot collect metrics for PID {pid}: {e}")
            return None

    def _perform_health_check(self, endpoint: str, port: Optional[int]) -> HealthCheckResult:
        """Perform HTTP health check"""
        if not port:
            return HealthCheckResult(is_healthy=True)  # No port specified, assume healthy

        url = f"http://localhost:{port}{endpoint}"

        try:
            start_time = time.time()
            response = requests.get(url, timeout=self.health_check_timeout)
            response_time_ms = (time.time() - start_time) * 1000

            is_healthy = 200 <= response.status_code < 300

            return HealthCheckResult(
                is_healthy=is_healthy,
                response_time_ms=response_time_ms,
                status_code=response.status_code
            )

        except requests.RequestException as e:
            return HealthCheckResult(
                is_healthy=False,
                error=str(e)
            )

    def get_metrics(self, process_id: str) -> Optional[ProcessMetrics]:
        """Get cached metrics for a process"""
        return self.metrics_cache.get(process_id)

    def get_all_metrics(self) -> Dict[str, ProcessMetrics]:
        """Get all cached metrics"""
        return self.metrics_cache.copy()

    def register_health_callback(self, process_id: str, callback: Callable):
        """Register a callback for health check failures"""
        self.health_callbacks[process_id] = callback

    def unregister_health_callback(self, process_id: str):
        """Unregister health callback"""
        self.health_callbacks.pop(process_id, None)

    def check_process_health(self, process_id: str) -> Dict[str, Any]:
        """Manually check process health"""
        process_info = self.registry.get_process(process_id)
        if not process_info:
            return {"status": "not_found"}

        result = {
            "process_id": process_id,
            "name": process_info.config.name,
            "state": process_info.state.value,
            "pid": process_info.pid,
            "uptime": None,
            "metrics": None,
            "health_check": None
        }

        # Check if process is running
        if process_info.pid and process_info.state == ProcessState.RUNNING:
            if not self._is_process_running(process_info.pid):
                result["state"] = "crashed"
                return result

            # Get metrics
            metrics = self._collect_metrics(process_info.pid, process_info.started_at)
            if metrics:
                result["metrics"] = {
                    "cpu_percent": metrics.cpu_percent,
                    "memory_mb": metrics.memory_mb,
                    "memory_percent": metrics.memory_percent,
                    "threads": metrics.num_threads,
                    "connections": metrics.num_connections
                }
                result["uptime"] = metrics.uptime_seconds

            # Perform health check
            if process_info.config.health_check_endpoint and process_info.config.ports:
                health_result = self._perform_health_check(
                    process_info.config.health_check_endpoint,
                    process_info.config.ports[0]
                )
                result["health_check"] = {
                    "is_healthy": health_result.is_healthy,
                    "response_time_ms": health_result.response_time_ms,
                    "status_code": health_result.status_code,
                    "error": health_result.error
                }

        return result