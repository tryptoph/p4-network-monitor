"""
Database models and connection management for P4 Network Monitor
"""

import os
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, INET
from datetime import datetime
import uuid

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('POSTGRES_USER', 'admin')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'password')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'p4monitor')}"
)

# Create database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class Switch(Base):
    __tablename__ = "switches"
    __table_args__ = {"schema": "configuration"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    switch_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    ip_address = Column(INET, nullable=False)
    grpc_port = Column(Integer, default=50051)
    device_id = Column(Integer, default=0)
    status = Column(String(20), default='inactive')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})
    
    # Relationships
    flow_rules = relationship("FlowRule", back_populates="switch")

class FlowRule(Base):
    __tablename__ = "flow_rules"
    __table_args__ = {"schema": "configuration"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    switch_id = Column(String(50), ForeignKey("configuration.switches.switch_id"))
    rule_name = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    match_fields = Column(JSON, nullable=False)
    action_name = Column(String(100), nullable=False)
    action_params = Column(JSON, default={})
    priority = Column(Integer, default=100)
    timeout = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    switch = relationship("Switch", back_populates="flow_rules")

class MonitoringPolicy(Base):
    __tablename__ = "monitoring_policies"
    __table_args__ = {"schema": "configuration"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_name = Column(String(100), unique=True, nullable=False)
    description = Column(String)
    sampling_rate = Column(Float, default=1.0)
    export_interval = Column(Integer, default=5)  # seconds
    flow_timeout = Column(Integer, default=300)   # seconds
    features_enabled = Column(JSON, default={})
    thresholds = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "configuration"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default='viewer')
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FlowMetadata(Base):
    __tablename__ = "flow_metadata"
    __table_args__ = {"schema": "monitoring"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(String(100), nullable=False)
    switch_id = Column(String(50), nullable=False)
    src_ip = Column(INET, nullable=False)
    dst_ip = Column(INET, nullable=False)
    src_port = Column(Integer)
    dst_port = Column(Integer)
    protocol = Column(Integer, nullable=False)
    flow_start_time = Column(DateTime, nullable=False)
    flow_end_time = Column(DateTime)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"schema": "monitoring"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default='info')
    switch_id = Column(String(50))
    flow_id = Column(String(100))
    message = Column(String, nullable=False)
    details = Column(JSON, default={})
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("configuration.users.id"))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    acknowledger = relationship("User")

class SystemEvent(Base):
    __tablename__ = "system_events"
    __table_args__ = {"schema": "monitoring"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)
    source = Column(String(100), nullable=False)
    message = Column(String, nullable=False)
    details = Column(JSON, default={})
    severity = Column(String(20), default='info')
    created_at = Column(DateTime, default=datetime.utcnow)

# Database session management
def get_db():
    """
    Dependency function for FastAPI to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all database tables
    """
    Base.metadata.create_all(bind=engine)

def init_database():
    """
    Initialize database with default data
    """
    create_tables()
    
    # Add any additional initialization logic here
    db = SessionLocal()
    try:
        # Check if default policy exists
        default_policy = db.query(MonitoringPolicy).filter(
            MonitoringPolicy.policy_name == "default"
        ).first()
        
        if not default_policy:
            # Create default monitoring policy
            default_policy = MonitoringPolicy(
                policy_name="default",
                description="Default monitoring policy",
                sampling_rate=1.0,
                export_interval=5,
                flow_timeout=300,
                features_enabled={
                    "packet_count": True,
                    "byte_count": True,
                    "flow_duration": True,
                    "protocol_analysis": True
                },
                thresholds={
                    "high_bandwidth": 1000000,  # 1MB/s
                    "long_flow": 3600,          # 1 hour
                    "port_scan_threshold": 100   # ports per minute
                }
            )
            db.add(default_policy)
            db.commit()
    
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    print("Database initialized successfully")