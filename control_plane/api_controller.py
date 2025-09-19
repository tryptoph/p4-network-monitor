#!/usr/bin/env python3
"""
Enhanced P4 Controller with FastAPI server
Combines P4Runtime control with HTTP API for dashboard
Now with real data integration
"""

import asyncio
import logging
import threading
import time
from concurrent import futures
from typing import Dict, List

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect
import uvicorn
import json

# Import the enhanced controller and data collection
from controller import P4Controller
from data_collector import initialize_data_collector, get_collectors, db_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIController:
    def __init__(self):
        self.app = FastAPI(title="P4 Network Monitor API", version="1.0.0")
        self.p4_controller = P4Controller()
        self.startup_time = time.time()
        
        # Initialize data collection system
        initialize_data_collector()
        self.flow_collector, self.stats_aggregator = get_collectors()
        
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
                "uptime": time.time() - self.startup_time
            }
        
        @self.app.get("/api/stats")
        async def get_stats():
            """Get current network statistics from real data"""
            try:
                real_stats = await self.stats_aggregator.get_current_statistics()
                return {
                    "stats": real_stats,
                    "timestamp": time.time()
                }
            except Exception as e:
                logging.error(f"Error getting stats: {e}")
                raise HTTPException(status_code=500, detail="Error retrieving statistics")
        
        @self.app.get("/api/flows")
        async def get_flows():
            """Get current flows from real data"""
            try:
                flows = await self.stats_aggregator.get_top_flows(limit=50)
                
                # Convert database records to API format
                flow_list = []
                for flow in flows:
                    protocol_name = self.stats_aggregator.get_protocol_name(flow.get('protocol', 0))
                    flow_data = {
                        "id": str(flow.get('flow_id', '')),
                        "src_ip": str(flow.get('src_ip', '')),
                        "dst_ip": str(flow.get('dst_ip', '')),
                        "src_port": flow.get('src_port', 0),
                        "dst_port": flow.get('dst_port', 0),
                        "protocol": protocol_name,
                        "packets": flow.get('current_packets', 0),
                        "bytes": flow.get('current_bytes', 0),
                        "duration": self.calculate_duration(flow.get('flow_start_time')),
                        "status": flow.get('status', 'unknown')
                    }
                    flow_list.append(flow_data)
                
                return {"flows": flow_list}
                
            except Exception as e:
                logging.error(f"Error getting flows: {e}")
                # Fallback to basic response
                return {"flows": []}
        
        @self.app.get("/api/switches")
        async def get_switches():
            """Get switch information from database"""
            try:
                # Get switch info from PostgreSQL
                cursor = db_manager.postgres_conn.cursor()
                cursor.execute("""
                    SELECT s.switch_id, s.name, s.status, s.ip_address,
                           COUNT(fm.id) as active_flows
                    FROM configuration.switches s
                    LEFT JOIN monitoring.flow_metadata fm ON s.switch_id = fm.switch_id 
                                                            AND fm.status = 'active'
                    GROUP BY s.switch_id, s.name, s.status, s.ip_address
                """)
                
                results = cursor.fetchall()
                cursor.close()
                
                switches = []
                for row in results:
                    switch_data = {
                        "id": row['switch_id'],
                        "name": row['name'],
                        "status": row['status'] or 'unknown',
                        "ip_address": str(row['ip_address']) if row['ip_address'] else '',
                        "flows": row['active_flows'] or 0,
                        "ports": ["1", "2", "3", "4"]  # Default ports
                    }
                    switches.append(switch_data)
                
                # Add default switches if none in database
                if not switches:
                    switches = [
                        {
                            "id": "switch-1",
                            "name": "Simulated Switch 1",
                            "status": "connected",
                            "ip_address": "127.0.0.1",
                            "flows": 0,
                            "ports": ["1", "2", "3", "4"]
                        }
                    ]
                
                return {"switches": switches}
                
            except Exception as e:
                logging.error(f"Error getting switches: {e}")
                # Fallback response
                return {
                    "switches": [
                        {
                            "id": "switch-1",
                            "name": "Default Switch",
                            "status": "connected",
                            "flows": 0,
                            "ports": ["1", "2", "3"]
                        }
                    ]
                }
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get real-time metrics for dashboard from real data"""
            try:
                stats = await self.stats_aggregator.get_current_statistics()
                protocol_dist = await self.stats_aggregator.calculate_protocol_distribution()
                
                # Calculate bandwidth estimate (simplified)
                bandwidth_mbps = (stats['total_bytes'] * 8) / (1024 * 1024) / max((time.time() - self.startup_time), 1)
                
                return {
                    "bandwidth": {
                        "current": round(bandwidth_mbps, 2),
                        "max": 1000,
                        "unit": "Mbps"
                    },
                    "packets_per_second": stats['total_packets'] // max(int(time.time() - self.startup_time), 1),
                    "active_flows": stats['active_flows'],
                    "switch_count": stats['switches_connected'],
                    "protocol_distribution": protocol_dist
                }
                
            except Exception as e:
                logging.error(f"Error getting metrics: {e}")
                # Fallback response
                return {
                    "bandwidth": {"current": 0, "max": 1000, "unit": "Mbps"},
                    "packets_per_second": 0,
                    "active_flows": 0,
                    "switch_count": 0,
                    "protocol_distribution": {}
                }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            try:
                while True:
                    # Send real-time metrics every 2 seconds
                    try:
                        stats = await self.stats_aggregator.get_current_statistics()
                        protocol_dist = await self.stats_aggregator.calculate_protocol_distribution()
                        
                        # Calculate real-time bandwidth
                        bandwidth_mbps = (stats['total_bytes'] * 8) / (1024 * 1024) / max((time.time() - self.startup_time), 1)
                        
                        real_time_data = {
                            "type": "metrics_update",
                            "data": {
                                "active_flows": stats['active_flows'],
                                "total_packets": stats['total_packets'],
                                "total_bytes": stats['total_bytes'],
                                "bandwidth_mbps": round(bandwidth_mbps, 2),
                                "packets_per_second": stats['total_packets'] // max(int(time.time() - self.startup_time), 1),
                                "switches_connected": stats['switches_connected'],
                                "protocol_distribution": protocol_dist,
                                "timestamp": time.time()
                            }
                        }
                        
                        await websocket.send_text(json.dumps(real_time_data))
                        await asyncio.sleep(2)  # Update every 2 seconds
                        
                    except Exception as e:
                        logging.error(f"Error in WebSocket update: {e}")
                        await asyncio.sleep(2)
                        
            except WebSocketDisconnect:
                logging.info("WebSocket client disconnected")
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
    
    def calculate_duration(self, start_time):
        """Calculate flow duration in seconds"""
        if start_time:
            try:
                import datetime
                if isinstance(start_time, datetime.datetime):
                    return (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()
            except Exception:
                pass
        return 0.0
    
    def start_p4_monitoring(self):
        """Start P4 controller in background thread with real data collection"""
        def run_p4_controller():
            try:
                logger.info("Starting P4 controller with data collection...")
                
                # Connect to P4 switch (simulated)
                if self.p4_controller.connect("127.0.0.1"):
                    # Load P4 program
                    self.p4_controller.load_p4_program()
                    
                    # Install flow rules
                    self.p4_controller.install_flow_rules()
                    
                    # Start monitoring (this will run the simulation)
                    self.p4_controller.start_monitoring()
                else:
                    logger.error("Failed to connect to P4 switch")
                    
            except Exception as e:
                logger.error(f"P4 controller error: {e}")
        
        # Run P4 controller in background thread
        p4_thread = threading.Thread(target=run_p4_controller, daemon=True)
        p4_thread.start()
        logger.info("P4 controller thread started with real data collection")
    
    def run(self, host="0.0.0.0", port=8000):
        """Run the API server with real data collection"""
        logger.info(f"Starting API server with real data integration on {host}:{port}")
        
        # Start P4 monitoring with data collection
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