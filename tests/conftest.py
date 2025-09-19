"""
Pytest configuration and fixtures for P4 Network Monitor tests
"""

import pytest
import tempfile
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add control_plane to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'control_plane'))

try:
    from database import Base, get_db
except ImportError:
    pytest.skip("Database module not available", allow_module_level=True)

@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine using SQLite in memory"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def override_get_db(test_db_session):
    """Override the get_db dependency for testing"""
    def _override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    return _override_get_db

@pytest.fixture
def sample_switch_config():
    """Sample switch configuration for testing"""
    return {
        "switch_id": "test-switch-01",
        "name": "Test Switch 1",
        "ip_address": "192.168.1.100",
        "grpc_port": 50051,
        "device_id": 1
    }

@pytest.fixture
def sample_flow_data():
    """Sample flow data for testing"""
    return {
        "flow_id": "test-flow-001",
        "switch_id": "test-switch-01",
        "src_ip": "10.0.1.1",
        "dst_ip": "10.0.2.1",
        "src_port": 12345,
        "dst_port": 80,
        "protocol": 6,  # TCP
        "packet_count": 100,
        "byte_count": 65000
    }

@pytest.fixture
def sample_monitoring_policy():
    """Sample monitoring policy for testing"""
    return {
        "policy_name": "test-policy",
        "description": "Test monitoring policy",
        "sampling_rate": 0.5,
        "export_interval": 10,
        "flow_timeout": 600,
        "features_enabled": {
            "packet_count": True,
            "byte_count": True,
            "flow_duration": True
        },
        "thresholds": {
            "high_bandwidth": 1000000,
            "long_flow": 3600
        }
    }

@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file"""
    config_content = """
# Test configuration
[database]
host = localhost
port = 5432
name = test_p4monitor
user = test_user
password = test_password

[monitoring]
sampling_rate = 1.0
export_interval = 5
flow_timeout = 300

[logging]
level = DEBUG
file = test.log
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(config_content)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    os.unlink(temp_file)

@pytest.fixture
def mock_p4_switch():
    """Mock P4 switch for testing"""
    class MockP4Switch:
        def __init__(self, switch_id="mock-switch"):
            self.switch_id = switch_id
            self.is_connected = False
            self.flow_entries = {}
            
        def connect(self):
            self.is_connected = True
            return True
            
        def disconnect(self):
            self.is_connected = False
            
        def install_flow_rule(self, rule):
            if self.is_connected:
                self.flow_entries[rule.get('rule_id')] = rule
                return True
            return False
            
        def get_counters(self):
            if self.is_connected:
                return {
                    "packet_count": 1000,
                    "byte_count": 64000,
                    "flow_count": 10
                }
            return None
    
    return MockP4Switch()

# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_p4: mark test as requiring P4 tools"
    )
    config.addinivalue_line(
        "markers", "requires_mininet: mark test as requiring Mininet"
    )