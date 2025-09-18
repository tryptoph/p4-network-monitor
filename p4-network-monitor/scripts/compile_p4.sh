#!/bin/bash
# P4 Compilation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if P4 compiler is available
if ! command -v p4c &> /dev/null; then
    print_error "P4 compiler (p4c) not found"
    print_error "Please install P4 development tools first"
    exit 1
fi

# Check if source file exists
P4_SOURCE="p4src/monitor.p4"
if [ ! -f "$P4_SOURCE" ]; then
    print_error "P4 source file not found: $P4_SOURCE"
    exit 1
fi

# Create build directory
mkdir -p p4src/build

print_status "Compiling P4 program..."

# Compile P4 program for BMv2 target
p4c --target bmv2 --arch v1model \
    --p4runtime-files p4src/build/monitor.p4info.txt \
    -o p4src/build/monitor.json \
    $P4_SOURCE

if [ $? -eq 0 ]; then
    print_status "P4 compilation successful"
    print_status "Generated files:"
    echo "  - p4src/build/monitor.json (BMv2 configuration)"
    echo "  - p4src/build/monitor.p4info.txt (P4Runtime info)"
else
    print_error "P4 compilation failed"
    exit 1
fi

# Validate generated files
if [ -f "p4src/build/monitor.json" ] && [ -f "p4src/build/monitor.p4info.txt" ]; then
    print_status "All required files generated successfully"
else
    print_error "Some output files are missing"
    exit 1
fi

print_status "P4 program ready for deployment"