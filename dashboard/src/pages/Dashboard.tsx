import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Progress, Table, Tag } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

// Mock data - replace with real API calls
const mockTrafficData = [
  { time: '00:00', bandwidth: 45, packets: 1200 },
  { time: '00:05', bandwidth: 52, packets: 1350 },
  { time: '00:10', bandwidth: 48, packets: 1180 },
  { time: '00:15', bandwidth: 61, packets: 1420 },
  { time: '00:20', bandwidth: 55, packets: 1300 },
  { time: '00:25', bandwidth: 67, packets: 1580 },
];

const mockProtocolData = [
  { name: 'TCP', value: 65, color: '#1890ff' },
  { name: 'UDP', value: 25, color: '#52c41a' },
  { name: 'ICMP', value: 7, color: '#faad14' },
  { name: 'Other', value: 3, color: '#f5222d' },
];

const mockTopFlows = [
  {
    key: '1',
    src: '192.168.1.100',
    dst: '10.0.0.50',
    protocol: 'TCP',
    port: '80',
    bandwidth: '15.2 MB/s',
    packets: '12,450',
    status: 'active',
  },
  {
    key: '2',
    src: '192.168.1.200',
    dst: '10.0.0.100',
    protocol: 'UDP',
    port: '53',
    bandwidth: '2.1 MB/s',
    packets: '8,230',
    status: 'active',
  },
  {
    key: '3',
    src: '10.0.0.1',
    dst: '192.168.1.150',
    protocol: 'TCP',
    port: '443',
    bandwidth: '8.7 MB/s',
    packets: '5,670',
    status: 'active',
  },
];

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    totalBandwidth: 89.5,
    activeFlows: 1247,
    packetsPerSecond: 15420,
    activeSwitches: 3,
  });

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        totalBandwidth: Number((prev.totalBandwidth + (Math.random() - 0.5) * 5).toFixed(1)),
        activeFlows: Math.floor(prev.activeFlows + (Math.random() - 0.5) * 100),
        packetsPerSecond: Math.floor(prev.packetsPerSecond + (Math.random() - 0.5) * 1000),
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const flowColumns = [
    {
      title: 'Source IP',
      dataIndex: 'src',
      key: 'src',
    },
    {
      title: 'Destination IP',
      dataIndex: 'dst',
      key: 'dst',
    },
    {
      title: 'Protocol',
      dataIndex: 'protocol',
      key: 'protocol',
      render: (protocol: string) => (
        <Tag color={protocol === 'TCP' ? 'blue' : protocol === 'UDP' ? 'green' : 'orange'}>
          {protocol}
        </Tag>
      ),
    },
    {
      title: 'Port',
      dataIndex: 'port',
      key: 'port',
    },
    {
      title: 'Bandwidth',
      dataIndex: 'bandwidth',
      key: 'bandwidth',
    },
    {
      title: 'Packets',
      dataIndex: 'packets',
      key: 'packets',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <span>
          <span className={`status-indicator status-${status}`}></span>
          {status}
        </span>
      ),
    },
  ];

  return (
    <div>
      <h1>Network Monitoring Dashboard</h1>
      
      {/* Statistics Cards */}
      <Row gutter={[16, 16]} className="dashboard-grid">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Bandwidth"
              value={stats.totalBandwidth}
              suffix="MB/s"
              valueStyle={{ color: '#3f8600' }}
              prefix={<ArrowUpOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Flows"
              value={stats.activeFlows}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Packets/sec"
              value={stats.packetsPerSecond}
              valueStyle={{ color: '#cf1322' }}
              prefix={<ArrowDownOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Switches"
              value={stats.activeSwitches}
              valueStyle={{ color: '#722ed1' }}
            />
            <Progress percent={100} showInfo={false} strokeColor="#722ed1" />
          </Card>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="Traffic Overview" className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockTrafficData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="bandwidth"
                  stroke="#1890ff"
                  strokeWidth={2}
                  name="Bandwidth (MB/s)"
                />
                <Line
                  type="monotone"
                  dataKey="packets"
                  stroke="#52c41a"
                  strokeWidth={2}
                  name="Packets/sec"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Protocol Distribution" className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={mockProtocolData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {mockProtocolData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Top Flows Table */}
      <Card title="Top Active Flows">
        <Table
          columns={flowColumns}
          dataSource={mockTopFlows}
          pagination={false}
          className="flow-table"
        />
      </Card>
    </div>
  );
};

export default Dashboard;