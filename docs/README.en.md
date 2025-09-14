# 🚀 Universal Process Manager

A robust, production-ready process management system with automatic restarts, health monitoring, and clean separation from managed applications.

## ✨ Key Features

- **Universal Support** - Manages Python, Node.js, Shell scripts, Docker containers
- **Zero Dependencies** - Managed apps don't need any modifications
- **Smart Monitoring** - CPU, memory, health checks, and heartbeat support
- **Auto-Recovery** - Configurable restart policies (always, on-failure, never)
- **Clean Architecture** - Complete separation between manager and applications
- **Rich CLI** - Beautiful terminal interface with colored output and tables

## 🚀 Quick Start

```bash
# Setup
./setup.sh

# Register a Python app
./pm register app.py --name myapp --type python --port 5000

# Start process
./pm start myapp

# View status
./pm status

# View logs
./pm logs myapp
```

## 📋 Commands

| Command | Description |
|---------|-------------|
| `register` | Register new process |
| `unregister` | Remove process from registry |
| `start` | Start process(es) |
| `stop` | Stop process(es) |
| `restart` | Restart process |
| `status` | Show process status |
| `logs` | View process logs |
| `list` | List all processes |

## 🏗️ Architecture

```
lab_heartbeat/
├── process_manager/      # Main application
│   ├── core/            # Registry, Controller, Monitor, Heartbeat
│   ├── cli/             # CLI interface
│   │   └── commands/    # Modularized commands
│   └── data/            # SQLite database
├── sample_apps/         # Sample applications
├── docs/                # Documentation
└── venv/                # Python virtual environment
```

### Modularized CLI

The CLI is split following SOLID principles:
- `cli.py` - Main entry point (54 lines)
- `utils.py` - Shared utilities and singleton components
- `commands/process_commands.py` - Lifecycle commands
- `commands/info_commands.py` - Information commands

## 🔧 Restart Policies

- `never` - No automatic restart
- `on-failure` - Restart on crash (exit code != 0)
- `always` - Always restart (respects max_retries)
- `unless-stopped` - Restart unless manually stopped

## 📦 Requirements

- Python 3.8+
- SQLite3
- Virtual environment (for Python apps)

## 🔐 Security

- Database stored in `process_manager/data/`
- Sensitive environment variables are filtered
- Processes run in isolated working directories
- No hardcoded paths - fully portable project

## 💡 Usage Tips

### Registration with Health Checks

```bash
./pm register app.py --name myapp \
    --type python \
    --port 5000 \
    --health-check /health \
    --restart-policy on-failure \
    --max-retries 3
```

### Environment Variables

```bash
./pm register app.py --name myapp \
    --env "DEBUG=true" \
    --env "PORT=8080" \
    --env "DATABASE_URL=postgresql://..."
```

### Batch Operations

```bash
# Start all processes
./pm start --all

# Stop all running processes
./pm stop --all

# JSON output for automation
./pm status --json
```

## 🔍 Debugging

```bash
# Detailed logs
./pm logs myapp --tail 100

# Force stop
./pm stop myapp --force

# Status with metrics
./pm status
```

## 📈 Future Improvements

- [ ] Web dashboard for visual management
- [ ] Distributed mode for multiple servers
- [ ] Docker and Kubernetes integration
- [ ] Prometheus metrics export
- [ ] Plugin system for custom runners

## 📝 License

MIT