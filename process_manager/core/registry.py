# process_manager/core/registry.py
# Central process registry for managing all registered processes
# Does NOT handle process execution, only registration and metadata

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

class ProcessType(Enum):
    PYTHON = "python"
    NODEJS = "nodejs"
    SHELL = "shell"
    DOCKER = "docker"
    CUSTOM = "custom"

class ProcessState(Enum):
    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    CRASHED = "crashed"

@dataclass
class ProcessConfig:
    name: str
    command: str
    type: ProcessType
    workdir: str
    env: Dict[str, str] = field(default_factory=dict)
    ports: List[int] = field(default_factory=list)
    restart_policy: str = "on-failure"
    max_retries: int = 3
    health_check_endpoint: Optional[str] = None
    health_check_interval: int = 30
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self):
        data = asdict(self)
        data['type'] = self.type.value
        return data

    @classmethod
    def from_dict(cls, data: dict):
        data = data.copy()
        data['type'] = ProcessType(data['type'])
        # Ensure all fields have proper defaults
        data['env'] = data.get('env') or {}
        data['ports'] = data.get('ports') or []
        data['dependencies'] = data.get('dependencies') or []
        return cls(**data)

@dataclass
class ProcessInfo:
    id: str
    config: ProcessConfig
    state: ProcessState
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    restart_count: int = 0
    last_heartbeat: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self):
        data = asdict(self)
        data['config'] = self.config.to_dict()
        data['state'] = self.state.value
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.stopped_at:
            data['stopped_at'] = self.stopped_at.isoformat()
        if self.last_heartbeat:
            data['last_heartbeat'] = self.last_heartbeat.isoformat()
        return data

class ProcessRegistry:
    def __init__(self, db_path: str = "process_manager/data/process_manager.db"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._init_database()

    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processes (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    config TEXT NOT NULL,
                    state TEXT NOT NULL,
                    pid INTEGER,
                    started_at TEXT,
                    stopped_at TEXT,
                    restart_count INTEGER DEFAULT 0,
                    last_heartbeat TEXT,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_process_state ON processes(state)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_process_name ON processes(name)
            ''')
            conn.commit()

    def register(self, config: ProcessConfig) -> str:
        """Register a new process in the registry"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Check if process with same name exists
                cursor = conn.execute(
                    "SELECT id FROM processes WHERE name = ?",
                    (config.name,)
                )
                if cursor.fetchone():
                    raise ValueError(f"Process with name '{config.name}' already exists")

                # Generate unique ID
                process_id = f"{config.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                # Insert new process
                conn.execute('''
                    INSERT INTO processes (id, name, config, state)
                    VALUES (?, ?, ?, ?)
                ''', (
                    process_id,
                    config.name,
                    json.dumps(config.to_dict()),
                    ProcessState.REGISTERED.value
                ))
                conn.commit()

                return process_id

    def unregister(self, process_id: str) -> bool:
        """Remove a process from the registry"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM processes WHERE id = ?",
                    (process_id,)
                )
                conn.commit()
                return cursor.rowcount > 0

    def get_process(self, process_id: str) -> Optional[ProcessInfo]:
        """Get process information by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM processes WHERE id = ?",
                (process_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_process_info(row)
            return None

    def get_process_by_name(self, name: str) -> Optional[ProcessInfo]:
        """Get process information by name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM processes WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_process_info(row)
            return None

    def list_processes(self, state: Optional[ProcessState] = None) -> List[ProcessInfo]:
        """List all processes, optionally filtered by state"""
        with sqlite3.connect(self.db_path) as conn:
            if state:
                cursor = conn.execute(
                    "SELECT * FROM processes WHERE state = ? ORDER BY created_at",
                    (state.value,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM processes ORDER BY created_at"
                )

            return [self._row_to_process_info(row) for row in cursor.fetchall()]

    def update_state(self, process_id: str, state: ProcessState,
                    pid: Optional[int] = None, error: Optional[str] = None):
        """Update process state"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                updates = ["state = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [state.value]

                if pid is not None:
                    updates.append("pid = ?")
                    params.append(pid)

                if state == ProcessState.RUNNING:
                    updates.append("started_at = CURRENT_TIMESTAMP")
                    updates.append("stopped_at = NULL")
                elif state in [ProcessState.STOPPED, ProcessState.FAILED, ProcessState.CRASHED]:
                    updates.append("stopped_at = CURRENT_TIMESTAMP")
                    updates.append("pid = NULL")

                if error:
                    updates.append("error_message = ?")
                    params.append(error)

                params.append(process_id)

                conn.execute(
                    f"UPDATE processes SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                conn.commit()

    def update_heartbeat(self, process_id: str):
        """Update last heartbeat timestamp"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE processes SET last_heartbeat = CURRENT_TIMESTAMP WHERE id = ?",
                    (process_id,)
                )
                conn.commit()

    def increment_restart_count(self, process_id: str):
        """Increment restart counter"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE processes SET restart_count = restart_count + 1 WHERE id = ?",
                    (process_id,)
                )
                conn.commit()

    def _row_to_process_info(self, row) -> ProcessInfo:
        """Convert database row to ProcessInfo object"""
        # SQLite row columns based on table schema
        (process_id, name, config_json, state, pid, started_at, stopped_at,
         restart_count, last_heartbeat, error_message, created_at, updated_at) = row

        config = ProcessConfig.from_dict(json.loads(config_json))

        return ProcessInfo(
            id=process_id,
            config=config,
            state=ProcessState(state),
            pid=pid,
            started_at=datetime.fromisoformat(started_at) if started_at else None,
            stopped_at=datetime.fromisoformat(stopped_at) if stopped_at else None,
            restart_count=restart_count,
            last_heartbeat=datetime.fromisoformat(last_heartbeat) if last_heartbeat else None,
            error_message=error_message
        )

    def list_all_processes(self) -> List[ProcessInfo]:
        """List all processes regardless of state"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT * FROM processes')
                rows = cursor.fetchall()
                return [self._row_to_process_info(row) for row in rows]

    def cleanup_stale_processes(self, timeout_seconds: int = 180):
        """Mark processes as crashed if no heartbeat for timeout period"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE processes
                    SET state = ?, error_message = ?
                    WHERE state = ?
                    AND last_heartbeat IS NOT NULL
                    AND datetime(last_heartbeat, '+' || ? || ' seconds') < datetime('now')
                ''', (
                    ProcessState.CRASHED.value,
                    "Process heartbeat timeout",
                    ProcessState.RUNNING.value,
                    timeout_seconds
                ))
                conn.commit()