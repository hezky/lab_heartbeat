#!/bin/bash
# Demo script for Process Manager

echo "🚀 Process Manager Demo"
echo "======================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_step "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_step "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_step "Installing Python dependencies..."
pip install -q -r requirements.txt
print_success "Dependencies installed"

# Install Node.js dependencies for sample app
print_step "Installing Node.js dependencies for sample app..."
cd sample_apps/nodejs_app
npm install --silent 2>/dev/null || print_warning "npm not found, skipping Node.js app"
cd ../..

# Make CLI executable
chmod +x pm

echo ""
echo "📋 Demo Scenario"
echo "================"
echo ""

# Clean up any existing database
rm -f process_manager.db 2>/dev/null

# Register Python app
print_step "Registering Python sample application..."
./pm register sample_apps/python_app/app.py \
    --name "python-demo" \
    --type python \
    --port 5000 \
    --health-check /health \
    --restart-policy on-failure \
    --max-retries 3
print_success "Python app registered"

# Register Node.js app if npm is available
if command -v npm &> /dev/null; then
    print_step "Registering Node.js sample application..."
    ./pm register sample_apps/nodejs_app/app.js \
        --name "nodejs-demo" \
        --type nodejs \
        --port 3000 \
        --health-check /health \
        --restart-policy always \
        --max-retries 5
    print_success "Node.js app registered"
fi

echo ""
print_step "Listing registered processes..."
./pm list

echo ""
print_step "Starting all registered processes..."
./pm start --all

echo ""
print_step "Waiting for processes to initialize..."
sleep 3

echo ""
print_step "Checking process status..."
./pm status

echo ""
print_step "Testing Python app endpoint..."
response=$(curl -s http://localhost:5000/ 2>/dev/null)
if [ $? -eq 0 ]; then
    print_success "Python app is responding: $response"
else
    print_error "Python app is not responding"
fi

if command -v npm &> /dev/null; then
    echo ""
    print_step "Testing Node.js app endpoint..."
    response=$(curl -s http://localhost:3000/ 2>/dev/null)
    if [ $? -eq 0 ]; then
        print_success "Node.js app is responding: $response"
    else
        print_error "Node.js app is not responding"
    fi
fi

echo ""
echo "📊 Demo Commands to Try"
echo "======================="
echo ""
echo "# Check status of all processes:"
echo "  ./pm status"
echo ""
echo "# View logs of a specific process:"
echo "  ./pm logs python-demo --tail 20"
echo ""
echo "# Restart a process:"
echo "  ./pm restart python-demo"
echo ""
echo "# Test crash recovery (process will auto-restart):"
echo "  curl http://localhost:5000/crash"
echo ""
echo "# Stop all processes:"
echo "  ./pm stop --all"
echo ""
echo "# Start a specific process:"
echo "  ./pm start python-demo"
echo ""

echo "🎉 Demo setup complete! Processes are running in the background."
echo ""
print_warning "To stop all processes when done: ./pm stop --all"