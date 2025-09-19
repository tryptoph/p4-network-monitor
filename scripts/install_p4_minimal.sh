#!/bin/bash
# Minimal P4 Installation Script
# This script installs minimal P4 tools using package managers where possible

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

print_header "Minimal P4 Development Environment Setup"

# Install basic packages
install_basic_packages() {
    print_header "Installing Basic Packages"
    
    sudo apt update
    
    # Essential development tools
    sudo apt install -y \
        build-essential \
        cmake \
        git \
        python3 \
        python3-pip \
        python3-dev \
        curl \
        wget \
        net-tools \
        iproute2 \
        tcpdump \
        iperf3
    
    print_status "Basic packages installed"
}

# Install Python packages
install_python_packages() {
    print_header "Installing Python Packages"
    
    # Upgrade pip
    python3 -m pip install --user --upgrade pip setuptools wheel
    
    # Install essential Python packages
    python3 -m pip install --user \
        grpcio \
        grpcio-tools \
        protobuf \
        scapy \
        psutil \
        mininet \
        networkx \
        matplotlib \
        numpy \
        pandas
    
    # Install project requirements if available
    if [ -f "control_plane/requirements.txt" ]; then
        print_status "Installing project requirements..."
        python3 -m pip install --user -r control_plane/requirements.txt
    fi
    
    print_status "Python packages installed"
}

# Install Mininet from packages
install_mininet_package() {
    print_header "Installing Mininet"
    
    if command -v mn >/dev/null 2>&1; then
        print_status "Mininet already installed"
        return
    fi
    
    # Try to install from package manager first
    if sudo apt install -y mininet; then
        print_status "Mininet installed from packages"
    else
        print_warning "Package installation failed, trying alternative method"
        
        # Install Mininet from source (minimal)
        cd /tmp
        git clone https://github.com/mininet/mininet.git
        cd mininet
        sudo ./util/install.sh -n
        
        print_status "Mininet installed from source"
    fi
}

# Install Docker if not present
install_docker() {
    print_header "Installing Docker"
    
    if command -v docker >/dev/null 2>&1; then
        print_status "Docker already installed"
        return
    fi
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Install Docker Compose
    sudo apt install -y docker-compose-plugin
    
    print_status "Docker installed (logout/login required for group membership)"
}

# Setup P4 simulation environment without full P4 tools
setup_simulation_env() {
    print_header "Setting Up Simulation Environment"
    
    # Create workspace
    mkdir -p "$HOME/p4-workspace"
    
    # Install Open vSwitch for basic switching
    sudo apt install -y openvswitch-switch openvswitch-common
    
    # Install additional networking tools
    sudo apt install -y \
        bridge-utils \
        vlan \
        hping3 \
        nmap \
        wireshark-common
    
    print_status "Simulation environment setup complete"
}

# Create mock P4 tools for testing
create_mock_tools() {
    print_header "Creating Mock P4 Tools"
    
    MOCK_DIR="$HOME/.local/bin"
    mkdir -p "$MOCK_DIR"
    
    # Mock P4 compiler
    cat > "$MOCK_DIR/p4c" << 'EOF'
#!/bin/bash
echo "Mock P4 Compiler v1.0.0"
echo "Note: This is a mock compiler for testing purposes"
echo "Arguments: $@"

# Create mock output files
if [[ "$*" == *"--p4runtime-files"* ]]; then
    # Extract output filename
    for arg in "$@"; do
        if [[ "$arg" == *.p4info.txt ]]; then
            echo "# Mock P4Info file" > "$arg"
        elif [[ "$arg" == *.json ]]; then
            echo '{"mock": "bmv2_json"}' > "$arg"
        fi
    done
fi

echo "Mock compilation complete"
EOF
    
    # Mock BMv2 switch
    cat > "$MOCK_DIR/simple_switch_grpc" << 'EOF'
#!/bin/bash
echo "Mock BMv2 Simple Switch gRPC"
echo "Note: This is a mock switch for testing purposes"
echo "Arguments: $@"
echo "Press Ctrl+C to stop"

# Keep running until interrupted
trap 'echo "Mock switch stopped"; exit 0' INT
while true; do
    sleep 1
done
EOF
    
    chmod +x "$MOCK_DIR/p4c"
    chmod +x "$MOCK_DIR/simple_switch_grpc"
    
    # Update PATH
    if ! grep -q "$HOME/.local/bin" "$HOME/.bashrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
    
    print_status "Mock P4 tools created in $MOCK_DIR"
    print_warning "These are mock tools for testing - install real P4 tools for production"
}

# Test the installation
test_installation() {
    print_header "Testing Installation"
    
    # Test Python packages
    python3 -c "import grpc; print('✓ gRPC available')" || print_error "✗ gRPC failed"
    python3 -c "import scapy; print('✓ Scapy available')" || print_error "✗ Scapy failed"
    
    # Test Mininet
    if command -v mn >/dev/null 2>&1; then
        print_status "✓ Mininet available"
    else
        print_error "✗ Mininet not found"
    fi
    
    # Test Docker
    if command -v docker >/dev/null 2>&1; then
        print_status "✓ Docker available"
    else
        print_error "✗ Docker not found"
    fi
    
    # Test mock tools
    export PATH="$HOME/.local/bin:$PATH"
    if command -v p4c >/dev/null 2>&1; then
        print_status "✓ P4 compiler (mock) available"
    else
        print_error "✗ P4 compiler not found"
    fi
}

# Show usage instructions
show_instructions() {
    print_header "Installation Complete - Minimal Setup"
    
    print_status "What was installed:"
    echo "  ✓ Basic development tools"
    echo "  ✓ Python 3 and essential packages"
    echo "  ✓ Mininet network emulator"
    echo "  ✓ Docker and Docker Compose"
    echo "  ✓ Mock P4 tools for testing"
    echo "  ✓ Network utilities"
    echo
    
    print_status "To use the full P4 development environment:"
    echo "  1. Restart your terminal: source ~/.bashrc"
    echo "  2. Start Docker services: sudo systemctl start docker"
    echo "  3. Test Mininet: sudo mn --test pingall"
    echo "  4. Start project services: docker compose up -d"
    echo "  5. Test mock compilation: p4c --help"
    echo
    
    print_warning "For production use, install real P4 tools:"
    echo "  ./scripts/install_p4_tools.sh"
    echo
    
    print_status "Quick start commands:"
    echo "  cd p4-network-monitor"
    echo "  ./scripts/setup.sh              # Setup project"
    echo "  docker compose up -d            # Start services"
    echo "  sudo python3 mininet/topology.py --cli  # Test topology"
}

# Main function
main() {
    print_status "Starting minimal P4 development environment setup..."
    
    install_basic_packages
    install_python_packages
    install_mininet_package
    install_docker
    setup_simulation_env
    create_mock_tools
    test_installation
    show_instructions
    
    print_status "Minimal installation complete!"
}

# Handle command line arguments
case "${1:-}" in
    "basic")
        install_basic_packages
        ;;
    "python")
        install_python_packages
        ;;
    "mininet")
        install_mininet_package
        ;;
    "docker")
        install_docker
        ;;
    "mock")
        create_mock_tools
        ;;
    "test")
        test_installation
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [component]"
        echo
        echo "Available components:"
        echo "  basic       Install basic development packages"
        echo "  python      Install Python packages"
        echo "  mininet     Install Mininet"
        echo "  docker      Install Docker"
        echo "  mock        Create mock P4 tools"
        echo "  test        Test installation"
        echo
        echo "Run without arguments to install everything (minimal setup)"
        ;;
    *)
        main
        ;;
esac