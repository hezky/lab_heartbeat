#!/usr/bin/env python3
# Main entry point for Process Manager CLI

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from process_manager.cli.cli import cli

if __name__ == '__main__':
    cli()