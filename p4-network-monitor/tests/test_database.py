"""
Unit tests for database models and operations
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

try:
    from database import (
        Switch, FlowRule, MonitoringPolicy, User, 
        FlowMetadata, Alert, SystemEvent
    )
except ImportError:
    pytest.skip("Database module not available", allow_module_level=True)

@pytest.mark.unit
class TestDatabaseModels:
    """Test database model functionality"""
    
    def test_switch_creation(self, test_db_session, sample_switch_config):
        """Test creating a switch record"""
        switch = Switch(**sample_switch_config)
        test_db_session.add(switch)
        test_db_session.commit()
        
        # Verify switch was created
        saved_switch = test_db_session.query(Switch).filter(
            Switch.switch_id == sample_switch_config["switch_id"]
        ).first()
        
        assert saved_switch is not None
        assert saved_switch.name == sample_switch_config["name"]
        assert str(saved_switch.ip_address) == sample_switch_config["ip_address"]
        assert saved_switch.grpc_port == sample_switch_config["grpc_port"]
        assert saved_switch.status == "inactive"  # default value
    
    def test_switch_unique_constraint(self, test_db_session, sample_switch_config):
        """Test that switch_id must be unique"""
        # Create first switch
        switch1 = Switch(**sample_switch_config)
        test_db_session.add(switch1)
        test_db_session.commit()
        
        # Try to create another switch with same switch_id
        switch2 = Switch(**sample_switch_config)
        switch2.name = "Different Name"
        test_db_session.add(switch2)
        
        with pytest.raises(IntegrityError):
            test_db_session.commit()
    
    def test_flow_rule_creation(self, test_db_session, sample_switch_config):
        """Test creating flow rules"""
        # First create a switch
        switch = Switch(**sample_switch_config)
        test_db_session.add(switch)
        test_db_session.commit()
        
        # Create flow rule
        flow_rule = FlowRule(
            switch_id=sample_switch_config["switch_id"],
            rule_name="test_rule",
            table_name="flow_table",
            match_fields={"src_ip": "10.0.1.1", "dst_ip": "10.0.2.1"},
            action_name="forward",
            action_params={"port": 1},
            priority=100
        )
        test_db_session.add(flow_rule)
        test_db_session.commit()
        
        # Verify flow rule was created
        saved_rule = test_db_session.query(FlowRule).filter(
            FlowRule.rule_name == "test_rule"
        ).first()
        
        assert saved_rule is not None
        assert saved_rule.switch_id == sample_switch_config["switch_id"]
        assert saved_rule.match_fields["src_ip"] == "10.0.1.1"
        assert saved_rule.action_params["port"] == 1
        assert saved_rule.is_active is True  # default value
    
    def test_monitoring_policy_creation(self, test_db_session, sample_monitoring_policy):
        """Test creating monitoring policies"""
        policy = MonitoringPolicy(**sample_monitoring_policy)
        test_db_session.add(policy)
        test_db_session.commit()
        
        # Verify policy was created
        saved_policy = test_db_session.query(MonitoringPolicy).filter(
            MonitoringPolicy.policy_name == sample_monitoring_policy["policy_name"]
        ).first()
        
        assert saved_policy is not None
        assert saved_policy.sampling_rate == sample_monitoring_policy["sampling_rate"]
        assert saved_policy.export_interval == sample_monitoring_policy["export_interval"]
        assert saved_policy.features_enabled == sample_monitoring_policy["features_enabled"]
        assert saved_policy.is_active is True
    
    def test_flow_metadata_creation(self, test_db_session, sample_flow_data):
        """Test creating flow metadata records"""
        flow_meta = FlowMetadata(
            **sample_flow_data,
            flow_start_time=datetime.utcnow(),
            status="active"
        )
        test_db_session.add(flow_meta)
        test_db_session.commit()
        
        # Verify flow metadata was created
        saved_flow = test_db_session.query(FlowMetadata).filter(
            FlowMetadata.flow_id == sample_flow_data["flow_id"]
        ).first()
        
        assert saved_flow is not None
        assert str(saved_flow.src_ip) == sample_flow_data["src_ip"]
        assert str(saved_flow.dst_ip) == sample_flow_data["dst_ip"]
        assert saved_flow.protocol == sample_flow_data["protocol"]
        assert saved_flow.status == "active"
    
    def test_alert_creation(self, test_db_session):
        """Test creating alert records"""
        alert = Alert(
            alert_type="bandwidth_threshold",
            severity="warning",
            switch_id="test-switch-01",
            message="High bandwidth usage detected",
            details={"threshold": 1000000, "current": 1500000}
        )
        test_db_session.add(alert)
        test_db_session.commit()
        
        # Verify alert was created
        saved_alert = test_db_session.query(Alert).filter(
            Alert.alert_type == "bandwidth_threshold"
        ).first()
        
        assert saved_alert is not None
        assert saved_alert.severity == "warning"
        assert saved_alert.is_acknowledged is False
        assert saved_alert.details["current"] == 1500000
    
    def test_system_event_creation(self, test_db_session):
        """Test creating system event records"""
        event = SystemEvent(
            event_type="switch_connected",
            source="controller",
            message="Switch test-switch-01 connected successfully",
            details={"switch_id": "test-switch-01", "ip": "192.168.1.100"},
            severity="info"
        )
        test_db_session.add(event)
        test_db_session.commit()
        
        # Verify event was created
        saved_event = test_db_session.query(SystemEvent).filter(
            SystemEvent.event_type == "switch_connected"
        ).first()
        
        assert saved_event is not None
        assert saved_event.source == "controller"
        assert saved_event.details["switch_id"] == "test-switch-01"
        assert saved_event.severity == "info"

@pytest.mark.unit
class TestDatabaseQueries:
    """Test database query operations"""
    
    def test_active_switches_query(self, test_db_session, sample_switch_config):
        """Test querying for active switches"""
        # Create multiple switches with different statuses
        switch1 = Switch(**sample_switch_config)
        switch1.status = "active"
        
        switch2_config = sample_switch_config.copy()
        switch2_config["switch_id"] = "test-switch-02"
        switch2_config["name"] = "Test Switch 2"
        switch2 = Switch(**switch2_config)
        switch2.status = "inactive"
        
        test_db_session.add_all([switch1, switch2])
        test_db_session.commit()
        
        # Query for active switches
        active_switches = test_db_session.query(Switch).filter(
            Switch.status == "active"
        ).all()
        
        assert len(active_switches) == 1
        assert active_switches[0].switch_id == sample_switch_config["switch_id"]
    
    def test_recent_alerts_query(self, test_db_session):
        """Test querying for recent alerts"""
        now = datetime.utcnow()
        
        # Create alerts with different timestamps
        old_alert = Alert(
            alert_type="old_alert",
            message="Old alert",
            created_at=now - timedelta(days=2)
        )
        
        recent_alert = Alert(
            alert_type="recent_alert", 
            message="Recent alert",
            created_at=now - timedelta(hours=1)
        )
        
        test_db_session.add_all([old_alert, recent_alert])
        test_db_session.commit()
        
        # Query for alerts from last 24 hours
        recent_alerts = test_db_session.query(Alert).filter(
            Alert.created_at > now - timedelta(hours=24)
        ).all()
        
        assert len(recent_alerts) == 1
        assert recent_alerts[0].alert_type == "recent_alert"
    
    def test_flow_aggregation_query(self, test_db_session, sample_flow_data):
        """Test aggregating flow data"""
        base_time = datetime.utcnow()
        
        # Create multiple flows for the same switch
        for i in range(5):
            flow_data = sample_flow_data.copy()
            flow_data["flow_id"] = f"flow-{i}"
            flow_data["packet_count"] = 100 * (i + 1)
            flow_data["byte_count"] = 64000 * (i + 1)
            
            flow = FlowMetadata(
                **flow_data,
                flow_start_time=base_time - timedelta(minutes=i),
                status="active"
            )
            test_db_session.add(flow)
        
        test_db_session.commit()
        
        # Query for flow count by switch
        from sqlalchemy import func
        switch_flow_count = test_db_session.query(
            FlowMetadata.switch_id,
            func.count(FlowMetadata.id).label('flow_count'),
            func.sum(FlowMetadata.packet_count).label('total_packets')
        ).filter(
            FlowMetadata.status == "active"
        ).group_by(FlowMetadata.switch_id).first()
        
        assert switch_flow_count.flow_count == 5
        assert switch_flow_count.total_packets == 1500  # 100+200+300+400+500