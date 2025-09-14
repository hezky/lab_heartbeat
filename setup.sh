#!/bin/bash
# Setup script for Process Manager

echo "🚀 Process Manager Setup"
echo "========================"
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

# Check Python version
print_step "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "Found Python $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    print_step "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        print_success "Virtual environment created"
    else
        print_error "Failed to create virtual environment"
        echo "Please ensure python3-venv is installed:"
        echo "  sudo apt-get install python3-venv"
        exit 1
    fi
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_step "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_step "Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
print_step "Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Make CLI executable
chmod +x pm

# Create wrapper script that uses venv
cat > pm-wrapper << 'EOF'
#!/bin/bash
# Wrapper script to run Process Manager with virtual environment

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment and run pm
source "$DIR/venv/bin/activate"
python "$DIR/pm" "$@"
EOF

chmod +x pm-wrapper

echo ""
print_success "Setup complete!"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo ""
echo "1. Run Process Manager directly (with venv activated):"
echo "   source venv/bin/activate"
echo "   ./pm --help"
echo ""
echo "2. Or use the wrapper script (no activation needed):"
echo "   ./pm-wrapper --help"
echo ""
echo "3. Try the demo:"
echo "   ./demo.sh"
echo ""
echo "📚 Quick Start Commands:"
echo "   ./pm-wrapper register sample_apps/python_app/app.py --name test-app --type python"
echo "   ./pm-wrapper start test-app"
echo "   ./pm-wrapper status"
echo "   ./pm-wrapper stop test-app"
echo ""