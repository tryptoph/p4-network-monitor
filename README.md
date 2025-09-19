# P4-Based Network Monitoring Tool

A research-grade network monitoring system that leverages P4 programmable switches for real-time traffic analysis and feature extraction.

## Project Structure

- `p4src/` - P4 programs for data plane packet processing
- `control_plane/` - Python applications for switch management and data collection
- `dashboard/` - Frontend web application for visualization
- `database/` - Database schemas and migration scripts
- `docker/` - Docker configuration files
- `mininet/` - Network topology simulation scripts
- `tests/` - Test suites for all components
- `scripts/` - Utility scripts and tools

## System Requirements

- Ubuntu 20.04+ LTS (or compatible Linux distribution)
- Docker and Docker Compose
- Python 3.8+
- P4 development tools (p4c compiler, BMv2)
- Mininet network emulator

## Quick Start

1. Clone repository: `git clone https://github.com/tryptoph/p4-network-monitor.git`
2. Install dependencies: `bash scripts/setup.sh`
3. Start infrastructure services: `docker compose up -d`
4. Compile P4 program: `bash scripts/compile_p4.sh`
5. Run Mininet topology: `sudo python3 mininet/topology.py`
6. Start control plane: `python3 control_plane/controller.py`
7. Access dashboard: http://localhost:3000

## Development Phases

- **Phase 1**: Foundation (Environment setup, basic packet parsing)
- **Phase 2**: Core Features (Flow management, data collection, basic dashboard)
- **Phase 3**: Advanced Features (Multi-switch support, advanced visualizations)
- **Phase 4**: Integration & Documentation (Testing, benchmarking, research output)

## Research Contributions

This project focuses on lightweight feature extraction directly in the P4 data plane with minimal overhead, enabling real-time flow analytics and scalable monitoring architecture for multiple switches.