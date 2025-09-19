-- P4 Network Monitor Database Schema
-- PostgreSQL initialization script

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS monitoring;
CREATE SCHEMA IF NOT EXISTS configuration;

-- Switch management table
CREATE TABLE IF NOT EXISTS configuration.switches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    switch_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    ip_address INET NOT NULL,
    grpc_port INTEGER DEFAULT 50051,
    device_id INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'inactive',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Flow rules configuration
CREATE TABLE IF NOT EXISTS configuration.flow_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    switch_id VARCHAR(50) REFERENCES configuration.switches(switch_id),
    rule_name VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    match_fields JSONB NOT NULL,
    action_name VARCHAR(100) NOT NULL,
    action_params JSONB DEFAULT '{}',
    priority INTEGER DEFAULT 100,
    timeout INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Monitoring policies
CREATE TABLE IF NOT EXISTS configuration.monitoring_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    sampling_rate FLOAT DEFAULT 1.0,
    export_interval INTEGER DEFAULT 5, -- seconds
    flow_timeout INTEGER DEFAULT 300, -- seconds
    features_enabled JSONB DEFAULT '{}',
    thresholds JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users and authentication
CREATE TABLE IF NOT EXISTS configuration.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Flow metadata for complex queries
CREATE TABLE IF NOT EXISTS monitoring.flow_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(100) NOT NULL,
    switch_id VARCHAR(50) NOT NULL,
    src_ip INET NOT NULL,
    dst_ip INET NOT NULL,
    src_port INTEGER,
    dst_port INTEGER,
    protocol INTEGER NOT NULL,
    flow_start_time TIMESTAMPTZ NOT NULL,
    flow_end_time TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts and notifications
CREATE TABLE IF NOT EXISTS monitoring.alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    switch_id VARCHAR(50),
    flow_id VARCHAR(100),
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    is_acknowledged BOOLEAN DEFAULT false,
    acknowledged_by UUID REFERENCES configuration.users(id),
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- System events log
CREATE TABLE IF NOT EXISTS monitoring.system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    source VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'info',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_switches_switch_id ON configuration.switches(switch_id);
CREATE INDEX IF NOT EXISTS idx_switches_status ON configuration.switches(status);

CREATE INDEX IF NOT EXISTS idx_flow_rules_switch_id ON configuration.flow_rules(switch_id);
CREATE INDEX IF NOT EXISTS idx_flow_rules_active ON configuration.flow_rules(is_active);

CREATE INDEX IF NOT EXISTS idx_policies_active ON configuration.monitoring_policies(is_active);

CREATE INDEX IF NOT EXISTS idx_flow_metadata_flow_id ON monitoring.flow_metadata(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_metadata_switch_id ON monitoring.flow_metadata(switch_id);
CREATE INDEX IF NOT EXISTS idx_flow_metadata_src_ip ON monitoring.flow_metadata(src_ip);
CREATE INDEX IF NOT EXISTS idx_flow_metadata_dst_ip ON monitoring.flow_metadata(dst_ip);
CREATE INDEX IF NOT EXISTS idx_flow_metadata_protocol ON monitoring.flow_metadata(protocol);
CREATE INDEX IF NOT EXISTS idx_flow_metadata_time_range ON monitoring.flow_metadata(flow_start_time, flow_end_time);

CREATE INDEX IF NOT EXISTS idx_alerts_type ON monitoring.alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON monitoring.alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON monitoring.alerts(is_acknowledged);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON monitoring.alerts(created_at);

CREATE INDEX IF NOT EXISTS idx_system_events_type ON monitoring.system_events(event_type);
CREATE INDEX IF NOT EXISTS idx_system_events_source ON monitoring.system_events(source);
CREATE INDEX IF NOT EXISTS idx_system_events_created_at ON monitoring.system_events(created_at);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_switches_updated_at BEFORE UPDATE ON configuration.switches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flow_rules_updated_at BEFORE UPDATE ON configuration.flow_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON configuration.monitoring_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON configuration.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flow_metadata_updated_at BEFORE UPDATE ON monitoring.flow_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default data
INSERT INTO configuration.monitoring_policies (policy_name, description, sampling_rate, export_interval, flow_timeout)
VALUES 
    ('default', 'Default monitoring policy', 1.0, 5, 300),
    ('high_traffic', 'High traffic monitoring with adaptive sampling', 0.1, 1, 60),
    ('security', 'Security-focused monitoring', 1.0, 1, 600)
ON CONFLICT (policy_name) DO NOTHING;

-- Insert default admin user (password: admin123 - change in production!)
INSERT INTO configuration.users (username, email, password_hash, full_name, role)
VALUES (
    'admin',
    'admin@p4monitor.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfAq3/1N/8Uiuhm', -- admin123
    'System Administrator',
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW monitoring.active_flows AS
SELECT 
    fm.*,
    s.name as switch_name,
    s.ip_address as switch_ip
FROM monitoring.flow_metadata fm
JOIN configuration.switches s ON fm.switch_id = s.switch_id
WHERE fm.status = 'active'
    AND fm.flow_end_time IS NULL;

CREATE OR REPLACE VIEW monitoring.recent_alerts AS
SELECT 
    a.*,
    u.username as acknowledged_by_username
FROM monitoring.alerts a
LEFT JOIN configuration.users u ON a.acknowledged_by = u.id
WHERE a.created_at > NOW() - INTERVAL '24 hours'
ORDER BY a.created_at DESC;

-- Grant permissions
GRANT USAGE ON SCHEMA configuration TO PUBLIC;
GRANT USAGE ON SCHEMA monitoring TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA configuration TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA monitoring TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA configuration TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA monitoring TO PUBLIC;