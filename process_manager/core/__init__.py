# process_manager/core/__init__.py
# Core module initialization
# This module contains the fundamental components of the Process Manager

from .registry import ProcessRegistry
from .monitor import ProcessMonitor
from .controller import ProcessController
from .heartbeat import HeartbeatManager

__all__ = [
    'ProcessRegistry',
    'ProcessMonitor',
    'ProcessController',
    'HeartbeatManager'
]

__version__ = '0.1.0'