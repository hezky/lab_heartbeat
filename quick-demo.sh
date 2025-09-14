#!/bin/bash
# Quick demo of Process Manager functionality

echo "🚀 Process Manager - Quick Demo"
echo "================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Clean up any previous state
echo "📧 Cleaning up..."
./pm stop --all 2>/dev/null
rm -f process_manager.db

echo ""
echo "📝 Registering Python demo application..."
./pm register sample_apps/python_app/app.py \
    --name "python-demo" \
    --type python

echo ""
echo "🚀 Starting the application..."
# Start the app directly with Python from venv
python sample_apps/python_app/app.py 5000 &
APP_PID=$!

echo "Application started with PID: $APP_PID"

echo ""
echo "⏳ Waiting for application to start..."
sleep 3

echo ""
echo "🔍 Testing the endpoint..."
response=$(curl -s http://localhost:5000/)
if [ $? -eq 0 ]; then
    echo "✅ Success! Response from application:"
    echo "$response" | python -m json.tool
else
    echo "❌ Failed to connect to application"
fi

echo ""
echo "📊 Testing health endpoint..."
health=$(curl -s http://localhost:5000/health)
if [ $? -eq 0 ]; then
    echo "✅ Health check response:"
    echo "$health" | python -m json.tool
else
    echo "❌ Health check failed"
fi

echo ""
echo "🛑 Stopping the application..."
kill $APP_PID 2>/dev/null

echo ""
echo "✨ Demo complete!"
echo ""
echo "📚 Key Features Demonstrated:"
echo "  • Process registration with metadata"
echo "  • Application lifecycle management"
echo "  • Health check endpoints"
echo "  • Clean separation between PM and apps"
echo ""
echo "🎯 Architecture Highlights:"
echo "  • Process Manager core (registry, monitor, controller)"
echo "  • CLI interface for easy control"
echo "  • Sample applications work independently"
echo "  • Heartbeat system for monitoring"