#!/usr/bin/env python3
"""
Initialize database with default data for P4 Network Monitor
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'control_plane'))

from data_collector import initialize_data_collector, db_manager
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_switches():
    """Add default switches to the database"""
    from data_collector import db_manager
    try:
        cursor = db_manager.postgres_conn.cursor()
        
        # Insert default switches
        switches = [
            ('switch-1', 'Simulated P4 Switch 1', '127.0.0.1', 50051, 0, 'active'),
            ('switch-2', 'Simulated P4 Switch 2', '127.0.0.2', 50052, 1, 'active'),
        ]
        
        for switch_id, name, ip, port, device_id, status in switches:
            cursor.execute("""
                INSERT INTO configuration.switches 
                (switch_id, name, ip_address, grpc_port, device_id, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (switch_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    ip_address = EXCLUDED.ip_address,
                    grpc_port = EXCLUDED.grpc_port,
                    device_id = EXCLUDED.device_id,
                    status = EXCLUDED.status,
                    updated_at = NOW()
            """, (switch_id, name, ip, port, device_id, status))
        
        db_manager.postgres_conn.commit()
        cursor.close()
        logger.info("Default switches initialized")
        
    except Exception as e:
        logger.error(f"Error initializing switches: {e}")
        if db_manager.postgres_conn:
            db_manager.postgres_conn.rollback()

def initialize_monitoring_policies():
    """Update monitoring policies"""
    from data_collector import db_manager
    try:
        cursor = db_manager.postgres_conn.cursor()
        
        # Update existing policies or insert new ones
        policies = [
            ('default', 'Default monitoring policy for all traffic', 1.0, 5, 300),
            ('high_performance', 'High performance monitoring with sampling', 0.1, 1, 60),
            ('security_focused', 'Security monitoring with full capture', 1.0, 1, 600),
        ]
        
        for name, desc, sampling, export_int, timeout in policies:
            cursor.execute("""
                INSERT INTO configuration.monitoring_policies 
                (policy_name, description, sampling_rate, export_interval, flow_timeout)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (policy_name) DO UPDATE SET
                    description = EXCLUDED.description,
                    sampling_rate = EXCLUDED.sampling_rate,
                    export_interval = EXCLUDED.export_interval,
                    flow_timeout = EXCLUDED.flow_timeout,
                    updated_at = NOW()
            """, (name, desc, sampling, export_int, timeout))
        
        db_manager.postgres_conn.commit()
        cursor.close()
        logger.info("Monitoring policies initialized")
        
    except Exception as e:
        logger.error(f"Error initializing policies: {e}")
        if db_manager.postgres_conn:
            db_manager.postgres_conn.rollback()

def setup_influxdb_bucket():
    """Setup InfluxDB bucket and organization"""
    try:
        # Skip InfluxDB setup for now - simplified version
        logger.info("InfluxDB setup skipped (using simplified data collection)")
        
    except Exception as e:
        logger.warning(f"InfluxDB setup warning (may need manual configuration): {e}")

def initialize_redis_data():
    """Initialize Redis with default data"""
    from data_collector import db_manager
    try:
        # Clear existing data
        db_manager.redis_client.flushdb()
        
        # Set initial global statistics
        db_manager.redis_client.hset("global_stats", mapping={
            "total_packets": "0",
            "total_bytes": "0", 
            "last_update": "0"
        })
        
        # Initialize active flows set
        db_manager.redis_client.delete("active_flows")
        
        logger.info("Redis initialized with default data")
        
    except Exception as e:
        logger.error(f"Error initializing Redis: {e}")

def main():
    """Initialize all database systems"""
    logger.info("Initializing P4 Network Monitor database...")
    
    # Initialize data collection system
    initialize_data_collector()
    
    from data_collector import db_manager
    if not db_manager:
        logger.error("Failed to initialize database connections")
        return False
    
    try:
        # Initialize all components
        initialize_switches()
        initialize_monitoring_policies()
        setup_influxdb_bucket()
        initialize_redis_data()
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
    
    finally:
        # Close connections
        if db_manager:
            db_manager.close_connections()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)