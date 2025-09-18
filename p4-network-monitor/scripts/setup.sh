#!/bin/bash
# P4 Network Monitor Setup Script

set -e

echo "=== P4 Network Monitor Setup ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check for required commands
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    else
        print_status "$1 is available"
        return 0
    fi
}

print_status "Checking system requirements..."

# Check for essential tools
REQUIRED_COMMANDS=("git" "python3" "pip3" "docker" "make" "cmake" "g++")
MISSING_COMMANDS=()

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! check_command $cmd; then
        MISSING_COMMANDS+=($cmd)
    fi
done

if [ ${#MISSING_COMMANDS[@]} -ne 0 ]; then
    print_error "Missing required commands: ${MISSING_COMMANDS[*]}"
    print_status "Please install missing packages and try again"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_PYTHON="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_status "Python version $PYTHON_VERSION is compatible"
else
    print_error "Python 3.8+ required, found $PYTHON_VERSION"
    exit 1
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
if [ -f "control_plane/requirements.txt" ]; then
    pip3 install --user -r control_plane/requirements.txt
    print_status "Python dependencies installed"
else
    print_warning "requirements.txt not found, skipping Python dependencies"
fi

# Check Docker
print_status "Checking Docker setup..."
if docker ps &> /dev/null; then
    print_status "Docker is running"
else
    print_warning "Docker is not running or requires sudo"
    print_status "Starting Docker services..."
    sudo systemctl start docker
fi

# Check Docker Compose
if docker compose version &> /dev/null; then
    print_status "Docker Compose is available"
else
    print_error "Docker Compose not available"
    exit 1
fi

# Create build directories
print_status "Creating build directories..."
mkdir -p p4src/build
mkdir -p logs
mkdir -p data

# Set permissions
chmod +x mininet/topology.py
chmod +x scripts/*.sh

# Install Node.js dependencies for dashboard
if [ -d "dashboard" ] && [ -f "dashboard/package.json" ]; then
    print_status "Installing Node.js dependencies..."
    cd dashboard
    if command -v npm &> /dev/null; then
        npm install
        print_status "Node.js dependencies installed"
    else
        print_warning "npm not found, skipping dashboard dependencies"
    fi
    cd ..
fi

# Check for P4 tools (optional)
print_status "Checking for P4 development tools..."
if command -v p4c &> /dev/null; then
    print_status "P4 compiler (p4c) is available"
    P4C_VERSION=$(p4c --version 2>&1 | head -n1)
    print_status "P4C version: $P4C_VERSION"
else
    print_warning "P4 compiler (p4c) not found"
    print_status "Install P4 tools using one of these scripts:"
    print_status "  ./scripts/install_p4_tools.sh      # Full installation (recommended)"
    print_status "  ./scripts/install_p4_minimal.sh    # Minimal setup for testing"
fi

if command -v simple_switch_grpc &> /dev/null; then
    print_status "BMv2 simple_switch_grpc is available"
else
    print_warning "BMv2 simple_switch_grpc not found"
    print_status "BMv2 will be installed with P4 tools"
fi

# Create environment file
print_status "Creating environment configuration..."
cat > .env << EOF
# P4 Network Monitor Environment Configuration

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=p4monitor
POSTGRES_USER=admin
POSTGRES_PASSWORD=password

# InfluxDB Configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-auth-token
INFLUXDB_ORG=p4monitor
INFLUXDB_BUCKET=network_metrics

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Control Plane Configuration
CONTROLLER_HOST=localhost
CONTROLLER_PORT=8000
GRPC_PORT=50051

# Dashboard Configuration
DASHBOARD_PORT=3000

# Monitoring Configuration
SAMPLING_RATE=1.0
EXPORT_INTERVAL=5
FLOW_TIMEOUT=300

# Development
DEBUG=true
LOG_LEVEL=INFO
EOF

print_status "Environment configuration created"

# Final instructions
print_status "Setup completed successfully!"
echo
print_status "Next steps:"
echo "  1. Install P4 tools (choose one):"
echo "     ./scripts/install_p4_tools.sh      # Full installation"
echo "     ./scripts/install_p4_minimal.sh    # Minimal/testing setup"
echo "  2. Start infrastructure: docker compose up -d"
echo "  3. Compile P4 program: ./scripts/compile_p4.sh"
echo "  4. Start Mininet topology: sudo python3 mininet/topology.py --cli"
echo "  5. Start controller: python3 control_plane/controller.py"
echo "  6. Open dashboard: http://localhost:3000"
echo
print_status "For development:"
echo "  - View logs: docker compose logs -f"
echo "  - Stop services: docker compose down"
echo "  - Run tests: ./scripts/run_tests.sh"
echo
print_status "Installation options:"
echo "  - Full P4 tools: 4-6 hours compilation time, full functionality"
echo "  - Minimal setup: 10-15 minutes, mock tools for testing"
echo
print_status "See README.md for detailed installation instructions"