#!/usr/bin/env python3
"""
Enhanced P4 Controller with FastAPI server
Combines P4Runtime control with HTTP API for dashboard
"""

import asyncio
import logging
import threading
import time
from concurrent import futures
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the original controller
from controller import P4Controller

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIController:
    def __init__(self):
        self.app = FastAPI(title="P4 Network Monitor API", version="1.0.0")
        self.p4_controller = P4Controller()
        self.stats = {
            "active_flows": 0,
            "total_packets": 0,
            "total_bytes": 0,
            "switches_connected": 0,
            "uptime": time.time()
        }
        self.setup_routes()
        self.setup_cors()
        
    def setup_cors(self):
        """Setup CORS for dashboard access"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "p4-network-monitor",
                "timestamp": time.time(),
                "uptime": time.time() - self.stats["uptime"]
            }
        
        @self.app.get("/api/stats")
        async def get_stats():
            """Get current network statistics"""
            return {
                "stats": self.stats,
                "timestamp": time.time()
            }
        
        @self.app.get("/api/flows")
        async def get_flows():
            """Get current flows"""
            # Mock data for now
            return {
                "flows": [
                    {
                        "id": "flow-001",
                        "src_ip": "10.0.1.1",
                        "dst_ip": "10.0.2.1",
                        "src_port": 12345,
                        "dst_port": 80,
                        "protocol": "TCP",
                        "packets": 150,
                        "bytes": 96000,
                        "duration": 45.2
                    },
                    {
                        "id": "flow-002", 
                        "src_ip": "10.0.1.2",
                        "dst_ip": "10.0.2.2",
                        "protocol": "UDP",
                        "src_port": 53,
                        "dst_port": 53,
                        "packets": 12,
                        "bytes": 1024,
                        "duration": 1.1
                    }
                ]
            }
        
        @self.app.get("/api/switches")
        async def get_switches():
            """Get switch information"""
            return {
                "switches": [
                    {
                        "id": "s1",
                        "name": "Switch 1",
                        "status": "connected",
                        "flows": 25,
                        "ports": ["1", "2", "3"]
                    },
                    {
                        "id": "s2", 
                        "name": "Switch 2",
                        "status": "connected",
                        "flows": 18,
                        "ports": ["1", "2", "3"]
                    }
                ]
            }
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get real-time metrics for dashboard"""
            return {
                "bandwidth": {
                    "current": 89.5,
                    "max": 1000,
                    "unit": "Mbps"
                },
                "packets_per_second": 15420,
                "active_flows": self.stats["active_flows"],
                "switch_count": 2
            }
    
    def start_p4_monitoring(self):
        """Start P4 controller in background thread"""
        def run_p4_controller():
            try:
                logger.info("Starting P4 controller...")
                self.p4_controller.connect("127.0.0.1")
                self.p4_controller.install_flow_rules()
                
                # Update stats periodically
                while True:
                    # Mock stats update
                    self.stats["active_flows"] = 43
                    self.stats["total_packets"] += 1000
                    self.stats["total_bytes"] += 64000
                    self.stats["switches_connected"] = 2
                    
                    time.sleep(5)  # Update every 5 seconds
                    
            except Exception as e:
                logger.error(f"P4 controller error: {e}")
        
        # Run P4 controller in background thread
        p4_thread = threading.Thread(target=run_p4_controller, daemon=True)
        p4_thread.start()
        logger.info("P4 controller thread started")
    
    def run(self, host="0.0.0.0", port=8000):
        """Run the API server"""
        logger.info(f"Starting API server on {host}:{port}")
        
        # Start P4 monitoring
        self.start_p4_monitoring()
        
        # Start FastAPI server
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )

def main():
    """Main entry point"""
    api_controller = APIController()
    api_controller.run()

if __name__ == "__main__":
    main()