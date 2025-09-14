# process_manager/cli/cli.py
# Main CLI entry point - clean and simple
# Follows SOLID principles by delegating to specialized modules

import click
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from process_manager.cli.utils import init_components, cleanup
from process_manager.cli.commands import (
    register,
    unregister,
    start,
    stop,
    restart,
    status,
    logs,
    list_processes
)


@click.group()
@click.option('--db', default='process_manager/data/process_manager.db', help='Database file path')
def cli(db):
    """Process Manager - Universal process control system"""
    init_components(db)


# Register commands
cli.add_command(register)
cli.add_command(unregister)
cli.add_command(start)
cli.add_command(stop)
cli.add_command(restart)
cli.add_command(status)
cli.add_command(logs)
cli.add_command(list_processes)


def main():
    """Main entry point with cleanup"""
    try:
        cli()
    except KeyboardInterrupt:
        cleanup()
        sys.exit(0)
    except Exception as e:
        cleanup()
        raise
    finally:
        cleanup()


if __name__ == '__main__':
    main()