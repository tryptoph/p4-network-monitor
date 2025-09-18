import React from 'react';
import { Card, Row, Col, Alert, List } from 'antd';

const mockAlerts = [
  {
    id: 1,
    type: 'warning',
    message: 'High bandwidth usage detected on switch-01',
    timestamp: '2024-01-15 10:30:00',
  },
  {
    id: 2,
    type: 'error',
    message: 'Connection lost to switch-03',
    timestamp: '2024-01-15 10:25:00',
  },
  {
    id: 3,
    type: 'info',
    message: 'New flow detected: 192.168.1.100 -> 10.0.0.50',
    timestamp: '2024-01-15 10:20:00',
  },
];

const Alerts: React.FC = () => {
  return (
    <div>
      <h1>System Alerts</h1>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="Recent Alerts">
            <List
              dataSource={mockAlerts}
              renderItem={(alert) => (
                <List.Item>
                  <Alert
                    type={alert.type as any}
                    message={alert.message}
                    description={`Timestamp: ${alert.timestamp}`}
                    style={{ width: '100%' }}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Alerts;