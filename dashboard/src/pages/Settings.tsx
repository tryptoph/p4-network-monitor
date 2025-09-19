import React from 'react';
import { Card, Row, Col, Form, Input, Switch, Button, Divider } from 'antd';

const Settings: React.FC = () => {
  const [form] = Form.useForm();

  const onFinish = (values: any) => {
    console.log('Settings updated:', values);
  };

  return (
    <div>
      <h1>Settings</h1>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="Monitoring Configuration">
            <Form
              form={form}
              layout="vertical"
              onFinish={onFinish}
              initialValues={{
                samplingRate: 1.0,
                exportInterval: 5,
                flowTimeout: 300,
                enableRealTime: true,
                enableAlerts: true,
              }}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Sampling Rate"
                    name="samplingRate"
                    help="Rate at which packets are sampled (0.1 = 10%, 1.0 = 100%)"
                  >
                    <Input type="number" step="0.1" min="0.1" max="1.0" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Export Interval (seconds)"
                    name="exportInterval"
                    help="How often to export data to database"
                  >
                    <Input type="number" min="1" max="60" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Flow Timeout (seconds)"
                    name="flowTimeout"
                    help="Timeout for inactive flows"
                  >
                    <Input type="number" min="60" max="3600" />
                  </Form.Item>
                </Col>
              </Row>

              <Divider />

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Enable Real-time Updates"
                    name="enableRealTime"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Enable Alerts"
                    name="enableAlerts"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button type="primary" htmlType="submit">
                  Save Settings
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Settings;