#!/bin/bash
# P4 Development Tools Installation Script
# This script installs P4 compiler, BMv2, Mininet, and all dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   print_status "Run as regular user with sudo privileges"
   exit 1
fi

# Check for sudo privileges
if ! sudo -n true 2>/dev/null; then
    print_status "This script requires sudo privileges"
    print_status "You may be prompted for your password"
fi

# Configuration
WORKSPACE_DIR="$HOME/p4-workspace"
NUM_CORES=$(nproc)
INSTALL_DIR="/usr/local"

print_header "P4 Development Environment Installation"
print_status "Installing to workspace: $WORKSPACE_DIR"
print_status "Using $NUM_CORES CPU cores for compilation"
print_status "Installation directory: $INSTALL_DIR"

# Create workspace directory
mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install system packages
install_system_packages() {
    print_header "Installing System Dependencies"
    
    # Update package lists
    print_status "Updating package lists..."
    sudo apt update
    
    # Install basic build tools
    print_status "Installing build tools..."
    sudo apt install -y \
        build-essential \
        cmake \
        g++ \
        git \
        autoconf \
        automake \
        libtool \
        pkg-config \
        make \
        unzip \
        wget \
        curl
    
    # Install P4 dependencies
    print_status "Installing P4 dependencies..."
    sudo apt install -y \
        libgmp-dev \
        libboost-dev \
        libboost-iostreams-dev \
        libboost-program-options-dev \
        libboost-system-dev \
        libboost-filesystem-dev \
        libboost-thread-dev \
        libssl-dev \
        libffi-dev \
        zlib1g-dev \
        libevent-dev \
        libjudy-dev \
        libreadline-dev \
        valgrind \
        libtool-bin \
        libboost-test-dev \
        libboost-serialization-dev \
        libthrift-dev \
        bison \
        flex
    
    # Install Python dependencies
    print_status "Installing Python development packages..."
    sudo apt install -y \
        python3 \
        python3-dev \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        python3-cffi \
        python3-ply \
        python3-yaml \
        python3-click \
        python3-six
    
    # Install networking tools
    print_status "Installing networking tools..."
    sudo apt install -y \
        net-tools \
        iproute2 \
        iputils-ping \
        tcpdump \
        wireshark-common \
        iperf3 \
        hping3 \
        nmap \
        openvswitch-switch \
        openvswitch-common
    
    print_status "System packages installed successfully"
}

# Function to install Protobuf
install_protobuf() {
    print_header "Installing Protocol Buffers"
    
    if command_exists protoc; then
        PROTOC_VERSION=$(protoc --version | cut -d' ' -f2)
        print_status "Protocol Buffers already installed (version $PROTOC_VERSION)"
        return
    fi
    
    print_status "Downloading and building Protocol Buffers..."
    cd "$WORKSPACE_DIR"
    
    # Clone protobuf repository
    if [ ! -d "protobuf" ]; then
        git clone https://github.com/protocolbuffers/protobuf.git
    fi
    
    cd protobuf
    git checkout v3.21.12  # Use stable version
    git submodule update --init --recursive
    
    # Configure and build
    ./autogen.sh
    ./configure --prefix="$INSTALL_DIR"
    make -j"$NUM_CORES"
    sudo make install
    sudo ldconfig
    
    print_status "Protocol Buffers installed successfully"
}

# Function to install gRPC
install_grpc() {
    print_header "Installing gRPC"
    
    print_status "Downloading and building gRPC..."
    cd "$WORKSPACE_DIR"
    
    # Clone gRPC repository
    if [ ! -d "grpc" ]; then
        git clone --recurse-submodules -b v1.54.0 --depth 1 --shallow-submodules https://github.com/grpc/grpc
    fi
    
    cd grpc
    mkdir -p cmake/build
    cd cmake/build
    
    # Configure with cmake
    cmake -DgRPC_INSTALL=ON \
          -DgRPC_BUILD_TESTS=OFF \
          -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" \
          ../..
    
    # Build and install
    make -j"$NUM_CORES"
    sudo make install
    sudo ldconfig
    
    print_status "gRPC installed successfully"
}

# Function to install P4 compiler
install_p4c() {
    print_header "Installing P4 Compiler (p4c)"
    
    if command_exists p4c; then
        P4C_VERSION=$(p4c --version 2>&1 | head -n1)
        print_status "P4 compiler already installed: $P4C_VERSION"
        return
    fi
    
    print_status "Downloading and building P4 compiler..."
    cd "$WORKSPACE_DIR"
    
    # Clone p4c repository
    if [ ! -d "p4c" ]; then
        git clone --recursive https://github.com/p4lang/p4c.git
    fi
    
    cd p4c
    git checkout stable  # Use stable branch
    git submodule update --init --recursive
    
    # Create build directory
    mkdir -p build
    cd build
    
    # Configure with cmake
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" \
        -DENABLE_TEST_TOOLS=ON
    
    # Build and install
    make -j"$NUM_CORES"
    sudo make install
    
    # Update library cache
    sudo ldconfig
    
    print_status "P4 compiler installed successfully"
}

# Function to install BMv2
install_bmv2() {
    print_header "Installing BMv2 (Behavioral Model v2)"
    
    if command_exists simple_switch_grpc; then
        print_status "BMv2 already installed"
        return
    fi
    
    print_status "Downloading and building BMv2..."
    cd "$WORKSPACE_DIR"
    
    # Clone BMv2 repository
    if [ ! -d "behavioral-model" ]; then
        git clone https://github.com/p4lang/behavioral-model.git
    fi
    
    cd behavioral-model
    git checkout stable  # Use stable branch
    
    # Install BMv2 dependencies
    print_status "Installing BMv2 specific dependencies..."
    sudo apt install -y \
        libnanomsg-dev \
        libthrift-0.13.0 \
        thrift-compiler
    
    # Install PI (P4Runtime implementation)
    print_status "Installing PI (P4Runtime)..."
    cd "$WORKSPACE_DIR"
    if [ ! -d "PI" ]; then
        git clone https://github.com/p4lang/PI.git
    fi
    
    cd PI
    git checkout stable
    git submodule update --init --recursive
    
    ./autogen.sh
    ./configure --prefix="$INSTALL_DIR" --with-proto --without-internal-rpc --without-cli --without-bmv2
    make -j"$NUM_CORES"
    sudo make install
    sudo ldconfig
    
    # Build BMv2
    print_status "Building BMv2..."
    cd "$WORKSPACE_DIR/behavioral-model"
    
    ./autogen.sh
    ./configure --prefix="$INSTALL_DIR" --enable-debugger --with-pi
    make -j"$NUM_CORES"
    sudo make install
    sudo ldconfig
    
    print_status "BMv2 installed successfully"
}

# Function to install Mininet
install_mininet() {
    print_header "Installing Mininet"
    
    if command_exists mn; then
        MININET_VERSION=$(mn --version 2>&1 | head -n1)
        print_status "Mininet already installed: $MININET_VERSION"
        return
    fi
    
    print_status "Downloading and installing Mininet..."
    cd "$WORKSPACE_DIR"
    
    # Clone Mininet repository
    if [ ! -d "mininet" ]; then
        git clone https://github.com/mininet/mininet.git
    fi
    
    cd mininet
    git checkout master
    
    # Install Mininet
    sudo PYTHON=python3 ./util/install.sh -nwv
    
    print_status "Mininet installed successfully"
}

# Function to install Python packages
install_python_packages() {
    print_header "Installing Python Packages"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    python3 -m pip install --user --upgrade pip setuptools wheel
    
    # Install P4 Python packages
    print_status "Installing P4 Python packages..."
    python3 -m pip install --user \
        p4runtime-sh \
        grpcio \
        grpcio-tools \
        protobuf==3.20.3 \
        scapy \
        psutil \
        ply \
        six \
        ipaddress \
        pypcap \
        bitstring
    
    # Install project dependencies
    if [ -f "../control_plane/requirements.txt" ]; then
        print_status "Installing project dependencies..."
        python3 -m pip install --user -r ../control_plane/requirements.txt
    fi
    
    print_status "Python packages installed successfully"
}

# Function to configure environment
configure_environment() {
    print_header "Configuring Environment"
    
    # Update PATH and library paths
    BASHRC="$HOME/.bashrc"
    
    # Add to PATH if not already there
    if ! grep -q "$INSTALL_DIR/bin" "$BASHRC"; then
        print_status "Adding $INSTALL_DIR/bin to PATH..."
        echo "export PATH=\"$INSTALL_DIR/bin:\$PATH\"" >> "$BASHRC"
    fi
    
    # Add library path
    if ! grep -q "$INSTALL_DIR/lib" "$BASHRC"; then
        print_status "Adding library paths..."
        echo "export LD_LIBRARY_PATH=\"$INSTALL_DIR/lib:\$LD_LIBRARY_PATH\"" >> "$BASHRC"
        echo "export PKG_CONFIG_PATH=\"$INSTALL_DIR/lib/pkgconfig:\$PKG_CONFIG_PATH\"" >> "$BASHRC"
    fi
    
    # Source the updated bashrc
    export PATH="$INSTALL_DIR/bin:$PATH"
    export LD_LIBRARY_PATH="$INSTALL_DIR/lib:$LD_LIBRARY_PATH"
    export PKG_CONFIG_PATH="$INSTALL_DIR/lib/pkgconfig:$PKG_CONFIG_PATH"
    
    # Update library cache
    sudo ldconfig
    
    print_status "Environment configured successfully"
}

# Function to run post-installation tests
run_tests() {
    print_header "Running Post-Installation Tests"
    
    # Test P4 compiler
    if command_exists p4c; then
        print_status "✓ P4 compiler (p4c) is available"
        p4c --version
    else
        print_error "✗ P4 compiler not found in PATH"
    fi
    
    # Test BMv2
    if command_exists simple_switch_grpc; then
        print_status "✓ BMv2 simple_switch_grpc is available"
    else
        print_error "✗ BMv2 simple_switch_grpc not found"
    fi
    
    # Test Mininet
    if command_exists mn; then
        print_status "✓ Mininet is available"
        mn --version
    else
        print_error "✗ Mininet not found"
    fi
    
    # Test Python packages
    print_status "Testing Python packages..."
    python3 -c "import grpc; print('✓ gRPC Python bindings working')" || print_error "✗ gRPC Python bindings failed"
    python3 -c "import scapy; print('✓ Scapy working')" || print_error "✗ Scapy failed"
    
    # Test protobuf
    if command_exists protoc; then
        print_status "✓ Protocol Buffers compiler is available"
        protoc --version
    else
        print_error "✗ Protocol Buffers compiler not found"
    fi
}

# Function to create a test P4 program
create_test_program() {
    print_header "Creating Test P4 Program"
    
    TEST_DIR="$WORKSPACE_DIR/test_p4"
    mkdir -p "$TEST_DIR"
    
    cat > "$TEST_DIR/test.p4" << 'EOF'
#include <core.p4>
#include <v1model.p4>

header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

struct headers {
    ethernet_t ethernet;
}

struct metadata {
}

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    state start {
        packet.extract(hdr.ethernet);
        transition accept;
    }
}

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    apply {
        standard_metadata.egress_spec = 1;
    }
}

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply { }
}

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
    }
}

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
EOF

    print_status "Test P4 program created at $TEST_DIR/test.p4"
    
    # Try to compile it
    cd "$TEST_DIR"
    if p4c --target bmv2 --arch v1model test.p4 --p4runtime-files test.p4info.txt -o test.json; then
        print_status "✓ Test P4 program compiled successfully"
        ls -la test.*
    else
        print_error "✗ Test P4 program compilation failed"
    fi
}

# Function to display final instructions
show_final_instructions() {
    print_header "Installation Complete!"
    
    print_status "P4 development environment has been installed successfully."
    echo
    print_status "Next steps:"
    echo "  1. Restart your terminal or run: source ~/.bashrc"
    echo "  2. Navigate to your P4 project directory"
    echo "  3. Compile your P4 program: p4c --target bmv2 --arch v1model your_program.p4"
    echo "  4. Start a Mininet topology: sudo mn --topo single,3 --controller remote"
    echo "  5. Run BMv2 switch: simple_switch_grpc --log-console program.json"
    echo
    print_status "Useful commands:"
    echo "  - p4c --help                    # P4 compiler help"
    echo "  - simple_switch_grpc --help     # BMv2 switch help" 
    echo "  - mn --help                     # Mininet help"
    echo "  - p4runtime-sh                  # P4Runtime shell"
    echo
    print_status "Test your installation:"
    echo "  - cd $WORKSPACE_DIR/test_p4"
    echo "  - p4c --target bmv2 --arch v1model test.p4"
    echo
    print_warning "Note: Some operations (like Mininet) require root privileges"
    print_status "Documentation: https://github.com/p4lang/tutorials"
}

# Main installation flow
main() {
    print_header "Starting P4 Development Tools Installation"
    
    # Check system compatibility
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_error "This script is designed for Linux systems"
        exit 1
    fi
    
    # Install components
    install_system_packages
    install_protobuf
    install_grpc
    install_p4c
    install_bmv2
    install_mininet
    install_python_packages
    configure_environment
    
    # Test installation
    run_tests
    create_test_program
    
    # Show final instructions
    show_final_instructions
}

# Handle command line arguments
case "${1:-}" in
    "system")
        install_system_packages
        ;;
    "protobuf")
        install_protobuf
        ;;
    "grpc")
        install_grpc
        ;;
    "p4c")
        install_p4c
        ;;
    "bmv2")
        install_bmv2
        ;;
    "mininet")
        install_mininet
        ;;
    "python")
        install_python_packages
        ;;
    "test")
        run_tests
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [component]"
        echo
        echo "Install specific components:"
        echo "  system      Install system packages and dependencies"
        echo "  protobuf    Install Protocol Buffers"
        echo "  grpc        Install gRPC"
        echo "  p4c         Install P4 compiler"
        echo "  bmv2        Install BMv2 behavioral model"
        echo "  mininet     Install Mininet"
        echo "  python      Install Python packages"
        echo "  test        Run installation tests"
        echo
        echo "Run without arguments to install everything"
        ;;
    *)
        main
        ;;
esac