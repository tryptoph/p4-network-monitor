#!/usr/bin/env python3
"""
Mininet topology for P4 Network Monitoring System
Creates a network topology with P4 switches for testing
"""

import sys
import os
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.node import OVSController
import argparse

# Add P4 utilities to path (when P4 tools are installed)
# try:
#     from p4utils.mininetlib.network_API import NetworkAPI
#     from p4utils.mininetlib.bmv2 import P4Switch
#     P4_AVAILABLE = True
# except ImportError:
#     P4_AVAILABLE = False
#     print("Warning: P4 utilities not available, using standard switches")

class NetworkMonitorTopology(Topo):
    """
    Network topology for testing P4-based network monitoring
    
    Topology:
        h1 --- s1 --- s2 --- h2
               |      |
              h3     h4
    
    Where:
    - s1, s2 are P4 switches (or OVS switches if P4 not available)
    - h1, h2, h3, h4 are hosts for traffic generation
    """
    
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        
        # Add hosts
        h1 = self.addHost('h1', ip='10.0.1.1/24', mac='00:00:00:00:01:01')
        h2 = self.addHost('h2', ip='10.0.2.1/24', mac='00:00:00:00:02:01')
        h3 = self.addHost('h3', ip='10.0.1.2/24', mac='00:00:00:00:01:02')
        h4 = self.addHost('h4', ip='10.0.2.2/24', mac='00:00:00:00:02:02')
        
        # Add P4 switches (or regular switches)
        # if P4_AVAILABLE:
        #     s1 = self.addSwitch('s1', cls=P4Switch,
        #                        json_path='../p4src/build/monitor.json',
        #                        p4info_path='../p4src/build/monitor.p4info.txt',
        #                        device_id=1)
        #     s2 = self.addSwitch('s2', cls=P4Switch,
        #                        json_path='../p4src/build/monitor.json', 
        #                        p4info_path='../p4src/build/monitor.p4info.txt',
        #                        device_id=2)
        # else:
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        
        # Add links with bandwidth limitations for realistic testing
        self.addLink(h1, s1, bw=100)  # 100 Mbps
        self.addLink(h3, s1, bw=100)
        self.addLink(s1, s2, bw=1000)  # 1 Gbps backbone
        self.addLink(s2, h2, bw=100)
        self.addLink(s2, h4, bw=100)

class MonitoringNetwork:
    """
    Network manager for the monitoring topology
    """
    
    def __init__(self, p4_program_path=None):
        self.net = None
        self.p4_program_path = p4_program_path
        
    def create_network(self):
        """Create and configure the network"""
        topo = NetworkMonitorTopology()
        
        # Create network with TC links for bandwidth control
        self.net = Mininet(
            topo=topo,
            link=TCLink,
            controller=OVSController,
            cleanup=True
        )
        
        info("*** Starting network\n")
        self.net.start()
        
        # Configure hosts
        self._configure_hosts()
        
        # Configure switches (flow rules for basic connectivity)
        self._configure_switches()
        
        info("*** Network ready\n")
        
    def _configure_hosts(self):
        """Configure host networking"""
        info("*** Configuring hosts\n")
        
        # Set up routing between subnets
        h1 = self.net.get('h1')
        h2 = self.net.get('h2')
        h3 = self.net.get('h3')
        h4 = self.net.get('h4')
        
        # Add routes for inter-subnet communication
        h1.cmd('ip route add 10.0.2.0/24 via 10.0.1.254')
        h3.cmd('ip route add 10.0.2.0/24 via 10.0.1.254')
        h2.cmd('ip route add 10.0.1.0/24 via 10.0.2.254')
        h4.cmd('ip route add 10.0.1.0/24 via 10.0.2.254')
        
    def _configure_switches(self):
        """Configure switch flow rules for basic connectivity"""
        info("*** Configuring switches\n")
        
        s1 = self.net.get('s1')
        s2 = self.net.get('s2')
        
        # Basic L2 learning switch behavior
        # In production, this would be handled by the P4 program
        s1.cmd('ovs-ofctl add-flow s1 "priority=1,actions=CONTROLLER:65535"')
        s2.cmd('ovs-ofctl add-flow s2 "priority=1,actions=CONTROLLER:65535"')
        
    def start_traffic_generation(self):
        """Start background traffic for testing"""
        info("*** Starting background traffic\n")
        
        h1 = self.net.get('h1')
        h2 = self.net.get('h2')
        h3 = self.net.get('h3')
        h4 = self.net.get('h4')
        
        # Start iperf servers on some hosts
        h2.cmd('iperf3 -s -D')  # UDP server
        h4.cmd('iperf3 -s -D')  # TCP server
        
        # Start background traffic
        info("Starting TCP traffic: h1 -> h2\n")
        h1.cmd('iperf3 -c 10.0.2.1 -t 3600 -i 10 &')  # Long-running TCP
        
        info("Starting UDP traffic: h3 -> h4\n")
        h3.cmd('iperf3 -c 10.0.2.2 -u -b 10M -t 3600 -i 10 &')  # UDP traffic
        
    def generate_test_traffic(self):
        """Generate various types of test traffic"""
        info("*** Generating test traffic patterns\n")
        
        h1 = self.net.get('h1')
        h2 = self.net.get('h2')
        h3 = self.net.get('h3')
        h4 = self.net.get('h4')
        
        # HTTP-like traffic
        info("Generating HTTP traffic\n")
        h1.cmd('curl -s http://10.0.2.1:8000/test > /dev/null &')
        
        # DNS-like traffic
        info("Generating DNS-like UDP traffic\n")
        h3.cmd('dig @10.0.2.2 example.com &')
        
        # Large file transfer
        info("Generating large file transfer\n")
        h1.cmd('dd if=/dev/zero bs=1M count=100 | nc 10.0.2.1 9999 &')
        h2.cmd('nc -l 9999 > /dev/null &')
        
    def run_connectivity_test(self):
        """Test basic connectivity"""
        info("*** Testing connectivity\n")
        
        # Test all-to-all ping
        result = self.net.pingAll()
        
        if result == 0:
            info("*** All hosts can reach each other\n")
        else:
            info(f"*** Connectivity test failed: {result}% packet loss\n")
            
        return result
    
    def start_monitoring_demo(self):
        """Start monitoring demonstration"""
        info("*** Starting monitoring demonstration\n")
        
        # Start background traffic
        self.start_traffic_generation()
        
        # Generate test patterns
        self.generate_test_traffic()
        
        info("*** Traffic generation started\n")
        info("*** You can now start the P4 controller to monitor traffic\n")
        info("*** Run: python3 ../control_plane/controller.py\n")
        
    def stop_network(self):
        """Stop and cleanup the network"""
        if self.net:
            info("*** Stopping network\n")
            self.net.stop()

def main():
    parser = argparse.ArgumentParser(description='P4 Network Monitoring Topology')
    parser.add_argument('--p4-program', default=None,
                       help='Path to compiled P4 program')
    parser.add_argument('--cli', action='store_true',
                       help='Start Mininet CLI after setup')
    parser.add_argument('--traffic', action='store_true',
                       help='Generate test traffic')
    parser.add_argument('--test', action='store_true',
                       help='Run connectivity test and exit')
    
    args = parser.parse_args()
    
    # Set log level
    setLogLevel('info')
    
    # Create network
    monitor_net = MonitoringNetwork(args.p4_program)
    
    try:
        # Create and start network
        monitor_net.create_network()
        
        # Run connectivity test
        if monitor_net.run_connectivity_test() != 0:
            info("*** Connectivity test failed, exiting\n")
            return 1
        
        if args.test:
            # Just test and exit
            return 0
        
        if args.traffic:
            # Start traffic generation
            monitor_net.start_monitoring_demo()
        
        if args.cli:
            # Start CLI for interactive testing
            info("*** Starting Mininet CLI\n")
            info("*** Available commands:\n")
            info("*** - pingall: Test connectivity\n")
            info("*** - iperf h1 h2: Test bandwidth\n")
            info("*** - h1 ping h2: Test specific connectivity\n")
            info("*** - exit: Stop network\n")
            CLI(monitor_net.net)
        else:
            # Keep network running for external monitoring
            info("*** Network is running\n")
            info("*** Press Ctrl+C to stop\n")
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
                
    except Exception as e:
        info(f"*** Error: {e}\n")
        return 1
    finally:
        # Cleanup
        monitor_net.stop_network()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())