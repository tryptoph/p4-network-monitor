#!/usr/bin/env python3
"""
Data Collection Engine for P4 Network Monitor
Handles data storage to PostgreSQL, InfluxDB, and Redis
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
import redis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages connections to PostgreSQL and Redis (InfluxDB simplified for now)"""
    
    def __init__(self):
        self.postgres_conn = None
        self.redis_client = None
        self.setup_connections()
    
    def setup_connections(self):
        """Initialize database connections"""
        try:
            # PostgreSQL connection
            self.postgres_conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="p4monitor",
                user="admin",
                password="password",
                cursor_factory=RealDictCursor
            )
            logger.info("PostgreSQL connected successfully")
            
            # Redis connection
            self.redis_client = redis.Redis(
                host="localhost",
                port=6379,
                decode_responses=True
            )
            logger.info("Redis connected successfully")
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
    
    def close_connections(self):
        """Close all database connections"""
        if self.postgres_conn:
            self.postgres_conn.close()
        if self.redis_client:
            self.redis_client.close()

class FlowDataCollector:
    """Collects and stores network flow data"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.active_flows = {}
        
    async def process_flow_digest(self, digest_data: Dict):
        """Process flow digest message from P4 switch"""
        try:
            flow_id = digest_data.get('flow_id')
            
            # Update active flows tracking
            self.active_flows[flow_id] = {
                'last_seen': time.time(),
                'data': digest_data
            }
            
            # Store in PostgreSQL for metadata
            await self.store_flow_metadata(digest_data)
            
            # Update Redis cache for real-time data
            await self.update_redis_cache(digest_data)
            
            logger.debug(f"Processed flow digest for flow {flow_id}")
            
        except Exception as e:
            logger.error(f"Error processing flow digest: {e}")
    
    async def store_flow_metadata(self, flow_data: Dict):
        """Store flow metadata in PostgreSQL"""
        try:
            cursor = self.db.postgres_conn.cursor()
            
            # Check if flow exists
            cursor.execute(
                "SELECT id FROM monitoring.flow_metadata WHERE flow_id = %s",
                (str(flow_data['flow_id']),)
            )
            
            if cursor.fetchone() is None:
                # Insert new flow
                cursor.execute("""
                    INSERT INTO monitoring.flow_metadata 
                    (flow_id, switch_id, src_ip, dst_ip, src_port, dst_port, 
                     protocol, flow_start_time, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(flow_data['flow_id']),
                    'switch-1',  # Default switch ID
                    self.int_to_ip(flow_data['src_ip']),
                    self.int_to_ip(flow_data['dst_ip']),
                    flow_data.get('src_port', 0),
                    flow_data.get('dst_port', 0),
                    flow_data['protocol'],
                    datetime.fromtimestamp(flow_data['timestamp'] / 1000000, tz=timezone.utc),
                    'active'
                ))
            else:
                # Update existing flow
                cursor.execute("""
                    UPDATE monitoring.flow_metadata 
                    SET updated_at = NOW()
                    WHERE flow_id = %s
                """, (str(flow_data['flow_id']),))
            
            self.db.postgres_conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error storing flow metadata: {e}")
            if self.db.postgres_conn:
                self.db.postgres_conn.rollback()
    
    async def update_redis_cache(self, flow_data: Dict):
        """Update Redis cache with real-time flow data"""
        try:
            flow_key = f"flow:{flow_data['flow_id']}"
            
            # Store individual flow data
            self.db.redis_client.hset(flow_key, mapping={
                'src_ip': self.int_to_ip(flow_data['src_ip']),
                'dst_ip': self.int_to_ip(flow_data['dst_ip']),
                'protocol': flow_data['protocol'],
                'src_port': flow_data.get('src_port', 0),
                'dst_port': flow_data.get('dst_port', 0),
                'packet_count': flow_data['packet_count'],
                'byte_count': flow_data['byte_count'],
                'last_seen': time.time()
            })
            
            # Set expiration (5 minutes)
            self.db.redis_client.expire(flow_key, 300)
            
            # Update active flows set
            self.db.redis_client.sadd("active_flows", str(flow_data['flow_id']))
            
            # Update global statistics
            self.db.redis_client.hincrby("global_stats", "total_packets", 
                                       flow_data['packet_count'])
            self.db.redis_client.hincrby("global_stats", "total_bytes", 
                                       flow_data['byte_count'])
            self.db.redis_client.hset("global_stats", "last_update", time.time())
            
        except Exception as e:
            logger.error(f"Error updating Redis cache: {e}")
    
    @staticmethod
    def int_to_ip(ip_int: int) -> str:
        """Convert integer IP address to string format"""
        return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
    
    async def cleanup_expired_flows(self):
        """Clean up expired flows from tracking"""
        current_time = time.time()
        expired_flows = []
        
        for flow_id, flow_info in self.active_flows.items():
            if current_time - flow_info['last_seen'] > 300:  # 5 minutes
                expired_flows.append(flow_id)
        
        for flow_id in expired_flows:
            del self.active_flows[flow_id]
            # Mark as inactive in PostgreSQL
            try:
                cursor = self.db.postgres_conn.cursor()
                cursor.execute("""
                    UPDATE monitoring.flow_metadata 
                    SET status = 'inactive', flow_end_time = NOW()
                    WHERE flow_id = %s
                """, (str(flow_id),))
                self.db.postgres_conn.commit()
                cursor.close()
            except Exception as e:
                logger.error(f"Error updating expired flow {flow_id}: {e}")
        
        if expired_flows:
            logger.info(f"Cleaned up {len(expired_flows)} expired flows")

class StatisticsAggregator:
    """Aggregates network statistics from collected data"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def calculate_protocol_distribution(self) -> Dict:
        """Calculate protocol distribution from active flows"""
        try:
            cursor = self.db.postgres_conn.cursor()
            cursor.execute("""
                SELECT protocol, COUNT(*) as count 
                FROM monitoring.flow_metadata 
                WHERE status = 'active' 
                GROUP BY protocol
            """)
            
            results = cursor.fetchall()
            cursor.close()
            
            total = sum(row['count'] for row in results)
            if total == 0:
                return {}
            
            distribution = {}
            for row in results:
                protocol_name = self.get_protocol_name(row['protocol'])
                distribution[protocol_name] = {
                    'count': row['count'],
                    'percentage': (row['count'] / total) * 100
                }
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error calculating protocol distribution: {e}")
            return {}
    
    @staticmethod
    def get_protocol_name(protocol_num: int) -> str:
        """Convert protocol number to name"""
        protocol_map = {
            1: 'ICMP',
            6: 'TCP',
            17: 'UDP'
        }
        return protocol_map.get(protocol_num, f'Protocol-{protocol_num}')
    
    async def get_top_flows(self, limit: int = 10) -> List[Dict]:
        """Get top flows by creation order"""
        try:
            cursor = self.db.postgres_conn.cursor()
            cursor.execute("""
                SELECT fm.*
                FROM monitoring.flow_metadata fm
                WHERE fm.status = 'active'
                ORDER BY fm.created_at DESC
                LIMIT %s
            """, (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting top flows: {e}")
            return []
    
    async def get_current_statistics(self) -> Dict:
        """Get current network statistics"""
        try:
            stats = self.db.redis_client.hgetall("global_stats")
            
            # Get active flow count
            active_flow_count = self.db.redis_client.scard("active_flows")
            
            return {
                'active_flows': active_flow_count,
                'total_packets': int(stats.get('total_packets', 0)),
                'total_bytes': int(stats.get('total_bytes', 0)),
                'last_update': float(stats.get('last_update', 0)),
                'switches_connected': 2  # Mock value
            }
            
        except Exception as e:
            logger.error(f"Error getting current statistics: {e}")
            return {
                'active_flows': 0,
                'total_packets': 0,
                'total_bytes': 0,
                'last_update': time.time(),
                'switches_connected': 0
            }

# Global instances
db_manager = None
flow_collector = None
stats_aggregator = None

def initialize_data_collector():
    """Initialize the data collection system"""
    global db_manager, flow_collector, stats_aggregator
    
    db_manager = DatabaseManager()
    flow_collector = FlowDataCollector(db_manager)
    stats_aggregator = StatisticsAggregator(db_manager)
    
    logger.info("Data collection system initialized")

def get_collectors():
    """Get collector instances"""
    return flow_collector, stats_aggregator

if __name__ == "__main__":
    # Test the data collector
    initialize_data_collector()
    
    # Example flow data for testing
    test_flow = {
        'flow_id': 12345,
        'src_ip': 0xC0A80164,  # 192.168.1.100
        'dst_ip': 0x0A000032,  # 10.0.0.50
        'protocol': 6,  # TCP
        'src_port': 12345,
        'dst_port': 80,
        'packet_count': 150,
        'byte_count': 96000,
        'timestamp': int(time.time() * 1000000),  # microseconds
        'flow_duration': 45200,  # milliseconds
        'packet_size': 640
    }
    
    async def test():
        await flow_collector.process_flow_digest(test_flow)
        stats = await stats_aggregator.get_current_statistics()
        print("Current statistics:", stats)
    
    asyncio.run(test())