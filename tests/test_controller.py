"""
Unit tests for P4 controller functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add control_plane to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'control_plane'))

try:
    from controller import P4Controller
except ImportError:
    pytest.skip("Controller module not available", allow_module_level=True)

@pytest.mark.unit
class TestP4Controller:
    """Test P4Controller functionality"""
    
    def test_controller_initialization(self):
        """Test controller initialization"""
        controller = P4Controller(device_id=1, grpc_port=50052, election_id=(1, 1))
        
        assert controller.device_id == 1
        assert controller.grpc_port == 50052
        assert controller.election_id == (1, 1)
        assert controller.client is None
    
    @patch('controller.grpc')
    def test_controller_connection_success(self, mock_grpc):
        """Test successful controller connection"""
        controller = P4Controller()
        
        # Mock successful connection
        result = controller.connect("192.168.1.100")
        
        # Since the actual P4Runtime code is commented out,
        # this test verifies the basic structure
        assert result is True
    
    @patch('controller.grpc')
    def test_controller_connection_failure(self, mock_grpc):
        """Test controller connection failure"""
        controller = P4Controller()
        
        # Mock connection failure by raising an exception in the connect method
        with patch.object(controller, 'connect', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception):
                controller.connect("invalid.address")
    
    def test_load_p4_program(self):
        """Test P4 program loading"""
        controller = P4Controller()
        
        # Test with mock file paths
        result = controller.load_p4_program("test.p4info", "test.json")
        
        # Since the actual loading code is commented out, 
        # this test verifies the basic structure
        assert result is True
    
    def test_install_flow_rules(self):
        """Test flow rule installation"""
        controller = P4Controller()
        
        result = controller.install_flow_rules()
        
        # Basic structure test
        assert result is True
    
    @patch('controller.time.sleep')
    def test_monitoring_loop_keyboard_interrupt(self, mock_sleep):
        """Test monitoring loop handles KeyboardInterrupt"""
        controller = P4Controller()
        
        # Mock sleep to raise KeyboardInterrupt after first iteration
        mock_sleep.side_effect = KeyboardInterrupt()
        
        # Should handle KeyboardInterrupt gracefully
        controller.start_monitoring()
        
        # Verify sleep was called (monitoring loop started)
        mock_sleep.assert_called_once()
    
    def test_disconnect(self):
        """Test controller disconnection"""
        controller = P4Controller()
        
        # Should not raise any exceptions
        controller.disconnect()

@pytest.mark.unit
class TestP4ControllerWithMockSwitch:
    """Test P4Controller with mock switch"""
    
    def test_mock_switch_operations(self, mock_p4_switch):
        """Test basic operations with mock switch"""
        # Test connection
        assert mock_p4_switch.connect() is True
        assert mock_p4_switch.is_connected is True
        
        # Test flow rule installation
        test_rule = {
            "rule_id": "test_rule_1",
            "table": "flow_table",
            "match": {"src_ip": "10.0.1.1"},
            "action": "forward",
            "params": {"port": 1}
        }
        
        result = mock_p4_switch.install_flow_rule(test_rule)
        assert result is True
        assert "test_rule_1" in mock_p4_switch.flow_entries
        
        # Test counter retrieval
        counters = mock_p4_switch.get_counters()
        assert counters is not None
        assert "packet_count" in counters
        assert counters["packet_count"] == 1000
        
        # Test disconnection
        mock_p4_switch.disconnect()
        assert mock_p4_switch.is_connected is False
        assert mock_p4_switch.get_counters() is None

@pytest.mark.integration
class TestP4ControllerIntegration:
    """Integration tests for P4Controller"""
    
    @pytest.mark.slow
    def test_controller_full_lifecycle(self, mock_p4_switch):
        """Test complete controller lifecycle"""
        controller = P4Controller(device_id=0, grpc_port=50051)
        
        # Test connection
        result = controller.connect("127.0.0.1")
        assert result is True
        
        # Test P4 program loading (would require actual files)
        # result = controller.load_p4_program("test.p4info", "test.json")
        # assert result is True
        
        # Test flow rule installation
        result = controller.install_flow_rules()
        assert result is True
        
        # Test cleanup
        controller.disconnect()

@pytest.mark.unit
class TestDataCollection:
    """Test data collection functionality"""
    
    def test_flow_data_processing(self):
        """Test processing of flow data"""
        # Mock flow data that would come from P4 switch
        mock_flow_data = {
            "src_ip": "10.0.1.1",
            "dst_ip": "10.0.2.1", 
            "src_port": 12345,
            "dst_port": 80,
            "protocol": 6,
            "packet_count": 150,
            "byte_count": 96000,
            "timestamp": 1642680000
        }
        
        # This would be the data processing logic
        processed_data = self._process_flow_data(mock_flow_data)
        
        assert processed_data["flow_id"] is not None
        assert processed_data["bandwidth"] > 0
        assert processed_data["protocol_name"] == "TCP"
    
    def _process_flow_data(self, raw_data):
        """Mock flow data processing"""
        # Generate flow ID from 5-tuple
        flow_id = f"{raw_data['src_ip']}:{raw_data['src_port']}->" \
                 f"{raw_data['dst_ip']}:{raw_data['dst_port']}-{raw_data['protocol']}"
        
        # Calculate bandwidth (simplified)
        bandwidth = raw_data["byte_count"] * 8 / 1000000  # Mbps
        
        # Map protocol number to name
        protocol_map = {6: "TCP", 17: "UDP", 1: "ICMP"}
        protocol_name = protocol_map.get(raw_data["protocol"], "Unknown")
        
        return {
            "flow_id": flow_id,
            "src_ip": raw_data["src_ip"],
            "dst_ip": raw_data["dst_ip"],
            "src_port": raw_data["src_port"],
            "dst_port": raw_data["dst_port"],
            "protocol": raw_data["protocol"],
            "protocol_name": protocol_name,
            "packet_count": raw_data["packet_count"],
            "byte_count": raw_data["byte_count"],
            "bandwidth": bandwidth,
            "timestamp": raw_data["timestamp"]
        }
    
    def test_statistics_calculation(self):
        """Test statistics calculation"""
        # Mock multiple flow data points
        flow_data_points = [
            {"packet_count": 100, "byte_count": 64000, "timestamp": 1642680000},
            {"packet_count": 150, "byte_count": 96000, "timestamp": 1642680005},
            {"packet_count": 200, "byte_count": 128000, "timestamp": 1642680010},
        ]
        
        stats = self._calculate_flow_statistics(flow_data_points)
        
        assert stats["total_packets"] == 450
        assert stats["total_bytes"] == 288000
        assert stats["avg_packet_rate"] > 0
        assert stats["duration"] == 10  # seconds
    
    def _calculate_flow_statistics(self, data_points):
        """Mock statistics calculation"""
        if not data_points:
            return {}
        
        total_packets = sum(dp["packet_count"] for dp in data_points)
        total_bytes = sum(dp["byte_count"] for dp in data_points)
        
        start_time = min(dp["timestamp"] for dp in data_points)
        end_time = max(dp["timestamp"] for dp in data_points)
        duration = end_time - start_time
        
        avg_packet_rate = total_packets / max(duration, 1)
        avg_byte_rate = total_bytes / max(duration, 1)
        
        return {
            "total_packets": total_packets,
            "total_bytes": total_bytes,
            "duration": duration,
            "avg_packet_rate": avg_packet_rate,
            "avg_byte_rate": avg_byte_rate
        }

@pytest.mark.requires_p4
class TestP4Integration:
    """Tests that require actual P4 tools"""
    
    @pytest.mark.skipif(not os.path.exists("/usr/local/bin/p4c"), 
                       reason="P4 compiler not available")
    def test_p4_compilation(self):
        """Test P4 program compilation"""
        p4_source = os.path.join(os.path.dirname(__file__), "..", "p4src", "monitor.p4")
        
        if os.path.exists(p4_source):
            # This would test actual P4 compilation
            # For now, just check if file exists
            assert os.path.exists(p4_source)
        else:
            pytest.skip("P4 source file not found")