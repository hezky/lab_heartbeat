#!/usr/bin/env python3
# sample_apps/python_app/app.py
# Sample Python application with heartbeat support
# Does NOT contain any Process Manager logic, only uses the client

import time
import logging
import random
import signal
import sys
import os
from flask import Flask, jsonify
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Application state
app_state = {
    'status': 'running',
    'requests_count': 0,
    'start_time': time.time(),
    'random_value': 0
}

# Heartbeat client (optional integration)
heartbeat_client = None

def setup_heartbeat():
    """Setup heartbeat client if Process Manager is available"""
    try:
        import os
        process_id = os.environ.get('PM_PROCESS_ID')
        manager_url = os.environ.get('PM_MANAGER_URL', 'http://localhost:8080')

        if process_id:
            # Import only if needed - dynamically find project root
            from pathlib import Path
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent  # Go up to lab_heartbeat
            sys.path.insert(0, str(project_root))
            from process_manager.core.heartbeat import ProcessHeartbeatClient

            global heartbeat_client
            heartbeat_client = ProcessHeartbeatClient(process_id, manager_url)
            heartbeat_client.start()
            logger.info(f"Heartbeat client started for process {process_id}")
    except Exception as e:
        logger.warning(f"Heartbeat client not available: {e}")

def background_worker():
    """Simulate background work"""
    while app_state['status'] == 'running':
        app_state['random_value'] = random.randint(1, 100)
        logger.info(f"Background worker generated: {app_state['random_value']}")
        time.sleep(5)

@app.route('/health')
def health():
    """Health check endpoint"""
    uptime = time.time() - app_state['start_time']
    return jsonify({
        'status': 'healthy',
        'uptime_seconds': int(uptime),
        'requests_count': app_state['requests_count']
    })

@app.route('/')
def index():
    """Main endpoint"""
    app_state['requests_count'] += 1
    return jsonify({
        'message': 'Python sample app is running',
        'value': app_state['random_value'],
        'requests': app_state['requests_count']
    })

@app.route('/status')
def status():
    """Status endpoint"""
    uptime = time.time() - app_state['start_time']
    return jsonify({
        'app': 'python_sample',
        'status': app_state['status'],
        'uptime_seconds': int(uptime),
        'random_value': app_state['random_value'],
        'requests_count': app_state['requests_count']
    })

@app.route('/crash')
def crash():
    """Endpoint to simulate crash"""
    logger.error("Crash requested!")
    sys.exit(1)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    app_state['status'] = 'stopping'

    if heartbeat_client:
        heartbeat_client.stop()

    sys.exit(0)

def main():
    """Main application entry point"""
    logger.info("Python sample app starting...")

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Setup heartbeat if available
    setup_heartbeat()

    # Start background worker
    worker_thread = Thread(target=background_worker, daemon=True)
    worker_thread.start()

    # Start Flask app
    port = int(os.environ.get('PORT', sys.argv[1] if len(sys.argv) > 1 else 5000))
    logger.info(f"Starting Flask app on port {port}")

    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()