# process_manager/cli/commands/info_commands.py
# Commands for process information and monitoring
# Handles status, logs, list

import click
import json
import sys
from rich.table import Table

from ..utils import console, get_registry, get_controller, get_monitor
from process_manager.core.registry import ProcessState


@click.command()
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def status(output_json):
    """Show status of all processes"""
    registry = get_registry()
    monitor = get_monitor()

    try:
        processes = registry.list_processes()

        if output_json:
            _output_status_json(processes, monitor)
        else:
            _output_status_table(processes, monitor)

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@click.command()
@click.argument('name')
@click.option('--tail', default=50, help='Number of lines to show')
def logs(name, tail):
    """Show process logs"""
    registry = get_registry()
    controller = get_controller()

    try:
        process_info = registry.get_process_by_name(name)
        if not process_info:
            console.print(f"[red]✗[/red] Process '{name}' not found")
            sys.exit(1)

        stdout_lines, stderr_lines = controller.get_process_output(process_info.id, lines=tail)

        if stdout_lines:
            console.print("\n[bold cyan]STDOUT:[/bold cyan]")
            for line in stdout_lines:
                console.print(line.decode('utf-8', errors='replace').rstrip())

        if stderr_lines:
            console.print("\n[bold red]STDERR:[/bold red]")
            for line in stderr_lines:
                console.print(line.decode('utf-8', errors='replace').rstrip())

        if not stdout_lines and not stderr_lines:
            console.print("[yellow]No logs available[/yellow]")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@click.command('list')
def list_processes():
    """List all registered processes"""
    registry = get_registry()

    try:
        processes = registry.list_processes()

        if not processes:
            console.print("[yellow]No processes registered[/yellow]")
            return

        table = Table(title="Registered Processes")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("Command")
        table.add_column("Restart Policy")
        table.add_column("Ports")

        for process_info in processes:
            ports = ", ".join(map(str, process_info.config.ports)) \
                    if process_info.config.ports and len(process_info.config.ports) > 0 else "-"

            command_display = process_info.config.command[:50] + "..." \
                            if len(process_info.config.command) > 50 \
                            else process_info.config.command

            table.add_row(
                process_info.config.name,
                process_info.config.type.value,
                command_display,
                process_info.config.restart_policy,
                ports
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


# Helper functions
def _output_status_json(processes, monitor):
    """Output status in JSON format"""
    status_data = []
    for process_info in processes:
        health = monitor.check_process_health(process_info.id)
        status_data.append({
            'name': process_info.config.name,
            'state': process_info.state.value,
            'pid': process_info.pid,
            'restart_count': process_info.restart_count,
            'health': health
        })
    console.print(json.dumps(status_data, indent=2))


def _output_status_table(processes, monitor):
    """Output status in table format"""
    table = Table(title="Process Status")
    table.add_column("Name", style="cyan")
    table.add_column("State", style="green")
    table.add_column("PID")
    table.add_column("Restarts")
    table.add_column("CPU %")
    table.add_column("Memory MB")
    table.add_column("Uptime")
    table.add_column("Health")

    for process_info in processes:
        # Get health and metrics
        health = monitor.check_process_health(process_info.id)
        metrics = health.get('metrics', {})

        # Format state with color
        state = _format_state(process_info.state)

        # Format uptime
        uptime_str = _format_uptime(health.get('uptime', 0))

        # Format health
        health_status = _format_health(health.get('health_check'))

        table.add_row(
            process_info.config.name,
            state,
            str(process_info.pid) if process_info.pid else "-",
            str(process_info.restart_count),
            f"{metrics.get('cpu_percent', 0):.1f}" if metrics else "-",
            f"{metrics.get('memory_mb', 0):.1f}" if metrics else "-",
            uptime_str,
            health_status
        )

    console.print(table)


def _format_state(state):
    """Format process state with color"""
    state_value = state.value
    if state == ProcessState.RUNNING:
        return f"[green]{state_value}[/green]"
    elif state == ProcessState.FAILED:
        return f"[red]{state_value}[/red]"
    elif state == ProcessState.STOPPED:
        return f"[yellow]{state_value}[/yellow]"
    elif state == ProcessState.CRASHED:
        return f"[red]{state_value}[/red]"
    return state_value


def _format_uptime(uptime):
    """Format uptime in human-readable format"""
    if uptime:
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        return f"{hours}h {minutes}m"
    return "-"


def _format_health(health_check):
    """Format health check status"""
    if health_check:
        return "✓" if health_check['is_healthy'] else "✗"
    return "-"