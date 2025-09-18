#!/usr/bin/env python3
"""
P4Runtime Controller for Network Monitoring
Main controller for managing P4 switches and collecting data
"""

import argparse
import asyncio
import grpc
import logging
import sys
import time
import random
import threading
from concurrent import futures
from typing import Dict, List

# Import our data collection system
from data_collector import initialize_data_collector, get_collectors, db_manager

class P4Controller:
    def __init__(self, device_id=0, grpc_port=50051, election_id=(0, 1)):
        """
        Initialize P4Runtime controller with data collection
        
        Args:
            device_id: P4 device ID
            grpc_port: gRPC port for P4Runtime
            election_id: Election ID for mastership
        """
        self.device_id = device_id
        self.grpc_port = grpc_port
        self.election_id = election_id
        self.client = None
        self.is_running = False
        self.flow_counter = 0
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize data collection system
        initialize_data_collector()
        self.flow_collector, self.stats_aggregator = get_collectors()
        
        # Simulated network flows for demonstration
        self.simulated_flows = self.generate_simulated_flows()
    
    def connect(self, switch_address="127.0.0.1"):
        """
        Connect to P4 switch via P4Runtime (simulated for demo)
        
        Args:
            switch_address: IP address of the P4 switch
        """
        try:
            # Simulate P4Runtime connection
            self.logger.info(f"Simulating P4Runtime connection to {switch_address}:{self.grpc_port}")
            self.client = f"simulated_client_{switch_address}_{self.grpc_port}"
            
            # Start background digest processing
            self.is_running = True
            digest_thread = threading.Thread(target=self.simulate_digest_processing, daemon=True)
            digest_thread.start()
            
            self.logger.info(f"Connected to switch at {switch_address}:{self.grpc_port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to switch: {e}")
            return False
    
    def load_p4_program(self, p4info_file=None, bmv2_json_file=None):
        """
        Load P4 program to the switch (simulated)
        
        Args:
            p4info_file: Path to P4Info file
            bmv2_json_file: Path to BMv2 JSON file
        """
        try:
            # Simulate P4 program loading
            self.logger.info("Simulating P4 program loading...")
            
            if p4info_file:
                self.logger.info(f"Loading P4Info from {p4info_file}")
            if bmv2_json_file:
                self.logger.info(f"Loading BMv2 JSON from {bmv2_json_file}")
            
            # Simulate program compilation and loading delay
            time.sleep(2)
            
            self.logger.info("P4 program loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load P4 program: {e}")
            return False
    
    def install_flow_rules(self):
        """
        Install flow rules for network monitoring (simulated)
        """
        try:
            self.logger.info("Installing monitoring flow rules...")
            
            # Simulate flow rule installation
            rules = [
                "flow_table: 5-tuple matching rules",
                "monitoring_policy: sampling configuration", 
                "forwarding rules: basic L2/L3 forwarding"
            ]
            
            for rule in rules:
                self.logger.info(f"Installing: {rule}")
                time.sleep(0.5)
            
            self.logger.info("Flow rules installed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to install flow rules: {e}")
            return False
    
    def start_monitoring(self):
        """
        Start monitoring network traffic with real data collection
        """
        self.logger.info("Starting network monitoring with data collection...")
        
        try:
            # Start periodic cleanup
            cleanup_thread = threading.Thread(target=self.periodic_cleanup, daemon=True)
            cleanup_thread.start()
            
            while self.is_running:
                # Simulate counter polling
                self.poll_flow_counters()
                
                # Log current statistics
                asyncio.run(self.log_current_stats())
                
                time.sleep(5)  # Polling interval
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
            self.is_running = False
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
            self.is_running = False
    
    def disconnect(self):
        """
        Disconnect from P4 switch and cleanup
        """
        self.is_running = False
        if self.client:
            self.logger.info("Disconnecting from switch")
            self.client = None
        
        # Close database connections
        if db_manager:
            db_manager.close_connections()
        
        self.logger.info("Disconnected from switch")
    
    def generate_simulated_flows(self) -> List[Dict]:
        """
        Generate simulated network flows for demonstration
        """
        flows = []
        
        # Common source/destination IPs
        ips = [
            (0xC0A80164, 0x0A000032),  # 192.168.1.100 -> 10.0.0.50
            (0xC0A801C8, 0x0A000064),  # 192.168.1.200 -> 10.0.0.100
            (0x0A000001, 0xC0A80196),  # 10.0.0.1 -> 192.168.1.150
            (0xC0A8010A, 0x08080808),  # 192.168.1.10 -> 8.8.8.8
            (0xC0A8010B, 0x08080404),  # 192.168.1.11 -> 8.8.4.4
        ]
        
        # Common port combinations
        ports = [
            (12345, 80),   # Web traffic
            (54321, 443),  # HTTPS traffic
            (53, 53),      # DNS traffic
            (22, 22),      # SSH traffic
            (3306, 3306),  # MySQL traffic
        ]
        
        protocols = [6, 17, 1]  # TCP, UDP, ICMP
        
        for i, (src_ip, dst_ip) in enumerate(ips):
            for j, (src_port, dst_port) in enumerate(ports):
                for protocol in protocols:
                    # Skip ports for ICMP
                    if protocol == 1:
                        src_port = dst_port = 0
                    
                    flow = {
                        'flow_id': (i * 1000) + (j * 100) + protocol,
                        'src_ip': src_ip,
                        'dst_ip': dst_ip,
                        'protocol': protocol,
                        'src_port': src_port if protocol != 1 else 0,
                        'dst_port': dst_port if protocol != 1 else 0,
                        'base_packet_count': random.randint(10, 1000),
                        'base_byte_count': random.randint(1000, 100000),
                        'packet_size': random.randint(64, 1500)
                    }
                    flows.append(flow)
        
        return flows
    
    def simulate_digest_processing(self):
        """
        Simulate P4 digest message processing
        """
        self.logger.info("Starting digest message simulation")
        
        while self.is_running:
            try:
                # Randomly select a flow to update
                if self.simulated_flows:
                    flow = random.choice(self.simulated_flows)
                    
                    # Simulate flow evolution
                    packet_increment = random.randint(1, 50)
                    byte_increment = packet_increment * flow['packet_size']
                    
                    # Create digest message
                    digest_data = {
                        'flow_id': flow['flow_id'],
                        'src_ip': flow['src_ip'],
                        'dst_ip': flow['dst_ip'],
                        'protocol': flow['protocol'],
                        'src_port': flow['src_port'],
                        'dst_port': flow['dst_port'],
                        'packet_count': flow['base_packet_count'] + packet_increment,
                        'byte_count': flow['base_byte_count'] + byte_increment,
                        'timestamp': int(time.time() * 1000000),  # microseconds
                        'flow_duration': random.randint(1000, 300000),  # 1s to 5min
                        'packet_size': flow['packet_size']
                    }
                    
                    # Update base counts
                    flow['base_packet_count'] += packet_increment
                    flow['base_byte_count'] += byte_increment
                    
                    # Process the digest
                    asyncio.run(self.flow_collector.process_flow_digest(digest_data))
                    
                    self.flow_counter += 1
                    if self.flow_counter % 100 == 0:
                        self.logger.info(f"Processed {self.flow_counter} flow digests")
                
                # Random delay between digests (0.1 to 2 seconds)
                time.sleep(random.uniform(0.1, 2.0))
                
            except Exception as e:
                self.logger.error(f"Error in digest simulation: {e}")
                time.sleep(1)
    
    def poll_flow_counters(self):
        """
        Simulate polling flow counters from P4 switch
        """
        try:
            # This would normally read counter values from the switch
            # For simulation, we just log the action
            active_flows = len(self.simulated_flows)
            self.logger.debug(f"Polling counters for {active_flows} flows")
            
        except Exception as e:
            self.logger.error(f"Error polling counters: {e}")
    
    async def log_current_stats(self):
        """
        Log current statistics
        """
        try:
            stats = await self.stats_aggregator.get_current_statistics()
            self.logger.info(
                f"Stats - Active flows: {stats['active_flows']}, "
                f"Total packets: {stats['total_packets']}, "
                f"Total bytes: {stats['total_bytes']}"
            )
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
    
    def periodic_cleanup(self):
        """
        Periodic cleanup of expired flows
        """
        while self.is_running:
            try:
                asyncio.run(self.flow_collector.cleanup_expired_flows())
                time.sleep(60)  # Cleanup every minute
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {e}")
                time.sleep(60)

def main():
    parser = argparse.ArgumentParser(description='P4 Network Monitoring Controller with Data Collection')
    parser.add_argument('--switch', default='127.0.0.1', 
                       help='Switch IP address (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=50051,
                       help='gRPC port (default: 50051)')
    parser.add_argument('--device-id', type=int, default=0,
                       help='P4 device ID (default: 0)')
    parser.add_argument('--p4info', required=False,
                       help='Path to P4Info file')
    parser.add_argument('--bmv2-json', required=False,
                       help='Path to BMv2 JSON file')
    parser.add_argument('--simulate', action='store_true',
                       help='Run in simulation mode with generated data')
    
    args = parser.parse_args()
    
    # Create and configure controller
    controller = P4Controller(
        device_id=args.device_id,
        grpc_port=args.port
    )
    
    # Connect to switch
    if not controller.connect(args.switch):
        sys.exit(1)
    
    # Load P4 program
    if not controller.load_p4_program(args.p4info, args.bmv2_json):
        sys.exit(1)
    
    # Install flow rules
    if not controller.install_flow_rules():
        sys.exit(1)
    
    try:
        # Start monitoring with data collection
        controller.start_monitoring()
    finally:
        # Clean up
        controller.disconnect()

if __name__ == "__main__":
    main()