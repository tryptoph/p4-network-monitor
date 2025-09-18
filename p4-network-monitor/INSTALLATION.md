# P4 Network Monitor Installation Guide

This guide provides step-by-step instructions for installing the P4 Network Monitor system with all required dependencies.

## Quick Start

```bash
# 1. Navigate to project directory
cd p4-network-monitor

# 2. Run basic setup
./scripts/setup.sh

# 3. Choose installation method:
#    Option A: Full P4 tools (4-6 hours, full functionality)
./scripts/install_p4_tools.sh

#    Option B: Minimal setup (15 minutes, testing only)
./scripts/install_p4_minimal.sh

# 4. Start the system
docker compose up -d
sudo python3 mininet/topology.py --cli
```

## Installation Options

### Option 1: Full P4 Development Environment (Recommended)

For complete functionality with real P4 compilation and BMv2 switches:

```bash
./scripts/install_p4_tools.sh
```

**What it installs:**
- P4 compiler (p4c) from source
- BMv2 behavioral model with P4Runtime
- Protocol Buffers and gRPC
- Mininet network emulator
- All Python dependencies
- Development tools and libraries

**Time required:** 4-6 hours (compilation intensive)
**Disk space:** ~8GB
**Best for:** Production use, research, full P4 development

### Option 2: Minimal Setup (Testing)

For quick setup with mock P4 tools for testing:

```bash
./scripts/install_p4_minimal.sh
```

**What it installs:**
- Basic development tools
- Mininet network emulator
- Docker and Docker Compose
- Python packages
- Mock P4 tools for testing
- Network utilities

**Time required:** 10-15 minutes
**Disk space:** ~2GB
**Best for:** Initial testing, development without P4 compilation

## System Requirements

### Supported Systems
- **Ubuntu 20.04+ LTS** (recommended)
- **Debian 10+**
- **Kali Linux** (tested)
- Other Debian-based distributions

### Hardware Requirements
- **CPU:** 4+ cores (for compilation)
- **RAM:** 8GB+ (16GB recommended for full installation)
- **Disk:** 10GB+ free space
- **Network:** Internet connection for downloads

### Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install git if not present
sudo apt install -y git curl wget
```

## Step-by-Step Installation

### 1. Project Setup

```bash
# Clone or ensure you have the project
cd p4-network-monitor

# Run initial setup
./scripts/setup.sh
```

This script will:
- Check system compatibility
- Install basic development tools
- Set up project structure
- Create environment configuration
- Install Node.js dependencies (if available)

### 2. Choose P4 Installation Method

#### Full Installation (Production)

```bash
# This will take 4-6 hours
./scripts/install_p4_tools.sh

# Or install components individually:
./scripts/install_p4_tools.sh system     # System packages
./scripts/install_p4_tools.sh protobuf  # Protocol Buffers
./scripts/install_p4_tools.sh grpc      # gRPC
./scripts/install_p4_tools.sh p4c       # P4 compiler
./scripts/install_p4_tools.sh bmv2      # BMv2 switch
./scripts/install_p4_tools.sh mininet   # Mininet
./scripts/install_p4_tools.sh python    # Python packages
```

#### Minimal Installation (Testing)

```bash
# This will take 10-15 minutes
./scripts/install_p4_minimal.sh

# Or install components individually:
./scripts/install_p4_minimal.sh basic    # Basic packages
./scripts/install_p4_minimal.sh python   # Python packages
./scripts/install_p4_minimal.sh mininet  # Mininet
./scripts/install_p4_minimal.sh docker   # Docker
./scripts/install_p4_minimal.sh mock     # Mock P4 tools
```

### 3. Verify Installation

```bash
# Test the installation
./scripts/run_tests.sh

# Or test specific components
./scripts/run_tests.sh env        # Environment
./scripts/run_tests.sh p4         # P4 tools
./scripts/run_tests.sh mininet    # Mininet
./scripts/run_tests.sh docker     # Docker
```

### 4. Start the System

```bash
# Start database and infrastructure services
docker compose up -d

# Verify services are running
docker compose ps

# Start Mininet topology (requires sudo)
sudo python3 mininet/topology.py --cli

# In another terminal, start the controller
python3 control_plane/controller.py

# Access the dashboard
open http://localhost:3000
```

## Troubleshooting

### Common Issues

#### 1. Permission Denied for Docker
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

#### 2. Mininet Requires Root
```bash
# Mininet operations need sudo
sudo python3 mininet/topology.py --test
```

#### 3. Compilation Errors (Full Installation)
```bash
# Ensure all dependencies are installed
sudo apt update
sudo apt install -y build-essential cmake git

# Check available disk space
df -h

# Monitor compilation progress
tail -f /var/log/syslog
```

#### 4. Python Package Conflicts
```bash
# Use virtual environment
python3 -m venv p4env
source p4env/bin/activate
pip install -r control_plane/requirements.txt
```

#### 5. Port Conflicts
```bash
# Check what's using ports
sudo netstat -tulpn | grep :5432  # PostgreSQL
sudo netstat -tulpn | grep :6379  # Redis
sudo netstat -tulpn | grep :8086  # InfluxDB

# Change ports in docker-compose.yml if needed
```

### WSL2 Specific Issues

If running on Windows WSL2:

```bash
# Enable systemd (if needed)
echo -e "[boot]\nsystemd=true" | sudo tee -a /etc/wsl.conf

# Restart WSL
# In Windows PowerShell: wsl --shutdown

# Install additional packages for WSL
sudo apt install -y bridge-utils net-tools
```

### Log Files and Debugging

```bash
# View container logs
docker compose logs -f

# View specific service logs
docker compose logs control-plane
docker compose logs influxdb

# Check P4 compilation output
./scripts/compile_p4.sh

# Test network connectivity
sudo python3 mininet/topology.py --test
```

## Manual Installation (Alternative)

If the automated scripts fail, you can install manually:

### Manual P4 Tools Installation

```bash
# 1. Install system dependencies
sudo apt install -y build-essential cmake git python3-dev \
    libgmp-dev libboost-dev libssl-dev pkg-config

# 2. Install Protocol Buffers
cd /tmp
git clone https://github.com/protocolbuffers/protobuf.git
cd protobuf
./autogen.sh && ./configure && make -j$(nproc) && sudo make install

# 3. Install P4 compiler
cd /tmp
git clone --recursive https://github.com/p4lang/p4c.git
cd p4c && mkdir build && cd build
cmake .. && make -j$(nproc) && sudo make install

# 4. Install BMv2
cd /tmp
git clone https://github.com/p4lang/behavioral-model.git
cd behavioral-model
./autogen.sh && ./configure && make -j$(nproc) && sudo make install

# 5. Update library cache
sudo ldconfig
```

## Environment Variables

The system uses these environment variables (set automatically by setup):

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=p4monitor
POSTGRES_USER=admin
POSTGRES_PASSWORD=password

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-auth-token
INFLUXDB_ORG=p4monitor
INFLUXDB_BUCKET=network_metrics

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Next Steps

After successful installation:

1. **Compile P4 Program:** `./scripts/compile_p4.sh`
2. **Start Services:** `docker compose up -d`
3. **Test Connectivity:** `sudo python3 mininet/topology.py --test`
4. **Run Controller:** `python3 control_plane/controller.py`
5. **Open Dashboard:** Visit http://localhost:3000

## Support

- Check logs: `docker compose logs -f`
- Run tests: `./scripts/run_tests.sh`
- View documentation: `README.md`
- Issues: https://github.com/your-repo/issues

## Performance Tips

- Use SSD storage for better compilation performance
- Allocate more RAM to WSL2 if on Windows
- Use `make -j$(nproc)` for parallel compilation
- Monitor system resources during installation