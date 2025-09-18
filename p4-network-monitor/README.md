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

1. Install dependencies (see setup documentation)
2. Start infrastructure services: `docker compose up -d`
3. Compile P4 program: `p4c --target bmv2 --arch v1model p4src/monitor.p4`
4. Run Mininet topology: `sudo python3 mininet/topology.py`
5. Start control plane: `python3 control_plane/controller.py`
6. Access dashboard: http://localhost:3000

## Development Phases

- **Phase 1**: Foundation (Environment setup, basic packet parsing)
- **Phase 2**: Core Features (Flow management, data collection, basic dashboard)
- **Phase 3**: Advanced Features (Multi-switch support, advanced visualizations)
- **Phase 4**: Integration & Documentation (Testing, benchmarking, research output)

## Research Contributions

This project focuses on lightweight feature extraction directly in the P4 data plane with minimal overhead, enabling real-time flow analytics and scalable monitoring architecture for multiple switches.