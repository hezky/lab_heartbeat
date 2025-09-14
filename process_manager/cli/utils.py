# process_manager/cli/utils.py
# Shared utilities and component initialization for CLI
# Provides singleton access to core components

from rich.console import Console
from typing import Optional

from process_manager.core import (
    ProcessRegistry,
    ProcessController,
    ProcessMonitor,
    HeartbeatManager
)

# Console for output
console = Console()

# Component instances (initialized lazily)
_registry: Optional[ProcessRegistry] = None
_controller: Optional[ProcessController] = None
_monitor: Optional[ProcessMonitor] = None
_heartbeat_manager: Optional[HeartbeatManager] = None


def init_components(db_path: str = "process_manager/data/process_manager.db"):
    """Initialize all core components"""
    global _registry, _controller, _monitor, _heartbeat_manager

    if _registry is None:
        _registry = ProcessRegistry(db_path)
        _controller = ProcessController(_registry)
        _monitor = ProcessMonitor(_registry)
        _heartbeat_manager = HeartbeatManager(_registry)

        # Start background services
        _monitor.start()
        _heartbeat_manager.start()


def get_registry() -> ProcessRegistry:
    """Get registry instance"""
    if _registry is None:
        raise RuntimeError("Components not initialized. Call init_components() first.")
    return _registry


def get_controller() -> ProcessController:
    """Get controller instance"""
    if _controller is None:
        raise RuntimeError("Components not initialized. Call init_components() first.")
    return _controller


def get_monitor() -> ProcessMonitor:
    """Get monitor instance"""
    if _monitor is None:
        raise RuntimeError("Components not initialized. Call init_components() first.")
    return _monitor


def get_heartbeat_manager() -> HeartbeatManager:
    """Get heartbeat manager instance"""
    if _heartbeat_manager is None:
        raise RuntimeError("Components not initialized. Call init_components() first.")
    return _heartbeat_manager


def cleanup():
    """Cleanup all components"""
    global _monitor, _heartbeat_manager, _controller

    if _monitor:
        _monitor.stop()

    if _heartbeat_manager:
        _heartbeat_manager.stop()

    if _controller:
        _controller.cleanup()