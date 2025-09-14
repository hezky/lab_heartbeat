# process_manager/cli/commands/process_commands.py
# Commands for process lifecycle management
# Handles register, unregister, start, stop, restart

import click
import sys
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils import console, get_registry, get_controller
from process_manager.core.registry import ProcessConfig, ProcessType, ProcessState


@click.command()
@click.argument('path')
@click.option('--name', required=True, help='Unique process name')
@click.option('--type',
              type=click.Choice(['python', 'nodejs', 'shell', 'docker', 'custom']),
              default='shell',
              help='Process type')
@click.option('--command', help='Command to execute (default: uses path)')
@click.option('--port', type=int, help='Port used by the process')
@click.option('--env', multiple=True, help='Environment variables (KEY=VALUE)')
@click.option('--restart-policy',
              type=click.Choice(['on-failure', 'always', 'never', 'unless-stopped']),
              default='on-failure',
              help='Restart policy')
@click.option('--max-retries', default=3, help='Maximum restart attempts')
@click.option('--health-check', help='Health check endpoint path')
def register(path, name, type, command, port, env, restart_policy, max_retries, health_check):
    """Register a new process"""
    registry = get_registry()

    try:
        # Parse environment variables
        env_dict = {}
        for env_var in env:
            if '=' in env_var:
                key, value = env_var.split('=', 1)
                env_dict[key] = value

        # Handle port
        port_list = [port] if port else []

        # Create process config
        # Ensure workdir is absolute path
        if Path(path).is_file():
            workdir = Path(path).parent.absolute()
        else:
            workdir = Path(path).absolute()

        config = ProcessConfig(
            name=name,
            command=command or path,
            type=ProcessType(type),
            workdir=str(workdir),
            env=env_dict if env_dict else {},
            ports=port_list,
            restart_policy=restart_policy,
            max_retries=max_retries,
            health_check_endpoint=health_check if health_check else None,
            dependencies=[]
        )

        # Register process
        process_id = registry.register(config)
        console.print(f"[green]✓[/green] Process registered: {name} (ID: {process_id})")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to register process: {e}")
        sys.exit(1)


@click.command()
@click.argument('name')
def unregister(name):
    """Unregister a process"""
    registry = get_registry()

    try:
        process_info = registry.get_process_by_name(name)
        if not process_info:
            console.print(f"[red]✗[/red] Process '{name}' not found")
            sys.exit(1)

        if registry.unregister(process_info.id):
            console.print(f"[green]✓[/green] Process '{name}' unregistered")
        else:
            console.print(f"[red]✗[/red] Failed to unregister process")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@click.command()
@click.argument('name', required=False)
@click.option('--all', is_flag=True, help='Start all registered processes')
def start(name, all):
    """Start a process or all processes"""
    registry = get_registry()
    controller = get_controller()

    try:
        if all:
            _start_all_processes(registry, controller)
        else:
            if not name:
                console.print("[red]✗[/red] Please specify a process name or use --all")
                sys.exit(1)
            _start_single_process(name, registry, controller)

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@click.command()
@click.argument('name', required=False)
@click.option('--all', is_flag=True, help='Stop all running processes')
@click.option('--force', is_flag=True, help='Force kill process')
def stop(name, all, force):
    """Stop a process or all processes"""
    registry = get_registry()
    controller = get_controller()

    try:
        if all:
            _stop_all_processes(registry, controller, force)
        else:
            if not name:
                console.print("[red]✗[/red] Please specify a process name or use --all")
                sys.exit(1)
            _stop_single_process(name, registry, controller, force)

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@click.command()
@click.argument('name')
def restart(name):
    """Restart a process"""
    registry = get_registry()
    controller = get_controller()

    try:
        process_info = registry.get_process_by_name(name)
        if not process_info:
            console.print(f"[red]✗[/red] Process '{name}' not found")
            sys.exit(1)

        with console.status(f"Restarting {name}..."):
            if controller.restart_process(process_info.id):
                console.print(f"[green]✓[/green] Process '{name}' restarted")
            else:
                console.print(f"[red]✗[/red] Failed to restart process '{name}'")
                sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


# Helper functions
def _start_all_processes(registry, controller):
    """Start all eligible processes"""
    processes = []
    processes.extend(registry.list_processes(ProcessState.REGISTERED))
    processes.extend(registry.list_processes(ProcessState.STOPPED))
    processes.extend(registry.list_processes(ProcessState.FAILED))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for process_info in processes:
            task = progress.add_task(f"Starting {process_info.config.name}...", total=1)
            if controller.start_process(process_info.id):
                progress.update(task, advance=1)
                console.print(f"[green]✓[/green] Started: {process_info.config.name}")
            else:
                console.print(f"[red]✗[/red] Failed to start: {process_info.config.name}")


def _start_single_process(name, registry, controller):
    """Start a single process by name"""
    process_info = registry.get_process_by_name(name)
    if not process_info:
        console.print(f"[red]✗[/red] Process '{name}' not found")
        sys.exit(1)

    with console.status(f"Starting {name}..."):
        if controller.start_process(process_info.id):
            console.print(f"[green]✓[/green] Process '{name}' started")
        else:
            console.print(f"[red]✗[/red] Failed to start process '{name}'")
            sys.exit(1)


def _stop_all_processes(registry, controller, force):
    """Stop all running processes"""
    processes = registry.list_processes(ProcessState.RUNNING)

    for process_info in processes:
        if controller.stop_process(process_info.id, force=force):
            console.print(f"[green]✓[/green] Stopped: {process_info.config.name}")
        else:
            console.print(f"[red]✗[/red] Failed to stop: {process_info.config.name}")


def _stop_single_process(name, registry, controller, force):
    """Stop a single process by name"""
    process_info = registry.get_process_by_name(name)
    if not process_info:
        console.print(f"[red]✗[/red] Process '{name}' not found")
        sys.exit(1)

    with console.status(f"Stopping {name}..."):
        if controller.stop_process(process_info.id, force=force):
            console.print(f"[green]✓[/green] Process '{name}' stopped")
        else:
            console.print(f"[red]✗[/red] Failed to stop process '{name}'")
            sys.exit(1)