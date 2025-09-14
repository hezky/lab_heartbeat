#!/usr/bin/env node
// sample_apps/nodejs_app/app.js
// Sample Node.js application with heartbeat support
// Does NOT contain any Process Manager logic, only uses the client

const express = require('express');
const http = require('http');

// Create Express app
const app = express();
const port = process.argv[2] || 3000;

// Application state
const appState = {
    status: 'running',
    requestsCount: 0,
    startTime: Date.now(),
    randomValue: 0
};

// Heartbeat client setup
let heartbeatInterval = null;

function setupHeartbeat() {
    const processId = process.env.PM_PROCESS_ID;
    const managerUrl = process.env.PM_MANAGER_URL || 'http://localhost:8080';

    if (processId) {
        console.log(`Setting up heartbeat for process ${processId}`);

        heartbeatInterval = setInterval(() => {
            const data = JSON.stringify({ process_id: processId });

            const options = {
                hostname: 'localhost',
                port: 8080,
                path: '/api/heartbeat',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': data.length
                }
            };

            const req = http.request(options, (res) => {
                if (res.statusCode !== 200) {
                    console.error(`Heartbeat failed: ${res.statusCode}`);
                }
            });

            req.on('error', (e) => {
                console.error(`Heartbeat error: ${e.message}`);
            });

            req.write(data);
            req.end();
        }, 10000); // Send heartbeat every 10 seconds
    }
}

// Background worker
function backgroundWorker() {
    setInterval(() => {
        appState.randomValue = Math.floor(Math.random() * 100) + 1;
        console.log(`Background worker generated: ${appState.randomValue}`);
    }, 5000);
}

// Routes
app.get('/health', (req, res) => {
    const uptime = Math.floor((Date.now() - appState.startTime) / 1000);
    res.json({
        status: 'healthy',
        uptime_seconds: uptime,
        requests_count: appState.requestsCount
    });
});

app.get('/', (req, res) => {
    appState.requestsCount++;
    res.json({
        message: 'Node.js sample app is running',
        value: appState.randomValue,
        requests: appState.requestsCount
    });
});

app.get('/status', (req, res) => {
    const uptime = Math.floor((Date.now() - appState.startTime) / 1000);
    res.json({
        app: 'nodejs_sample',
        status: appState.status,
        uptime_seconds: uptime,
        random_value: appState.randomValue,
        requests_count: appState.requestsCount
    });
});

app.get('/crash', (req, res) => {
    console.error('Crash requested!');
    process.exit(1);
});

// Signal handlers
process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down...');
    appState.status = 'stopping';

    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
    }

    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('SIGINT received, shutting down...');
    appState.status = 'stopping';

    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
    }

    process.exit(0);
});

// Start application
console.log('Node.js sample app starting...');

// Setup heartbeat if available
setupHeartbeat();

// Start background worker
backgroundWorker();

// Start Express server
app.listen(port, '0.0.0.0', () => {
    console.log(`Server running on port ${port}`);
});