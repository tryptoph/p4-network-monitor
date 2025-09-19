import React from 'react';
import { Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  BarChartOutlined,
  NodeIndexOutlined,
  HeartOutlined,
  AlertOutlined,
  SettingOutlined,
} from '@ant-design/icons';

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/traffic',
      icon: <BarChartOutlined />,
      label: 'Traffic Analysis',
    },
    {
      key: '/flows',
      icon: <NodeIndexOutlined />,
      label: 'Flow Analysis',
    },
    {
      key: '/health',
      icon: <HeartOutlined />,
      label: 'Network Health',
    },
    {
      key: '/alerts',
      icon: <AlertOutlined />,
      label: 'Alerts',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
  ];

  const handleMenuClick = (key: string) => {
    navigate(key);
  };

  return (
    <Menu
      theme="dark"
      mode="horizontal"
      selectedKeys={[location.pathname]}
      items={menuItems}
      onClick={({ key }) => handleMenuClick(key)}
      style={{ background: 'transparent', border: 'none' }}
    />
  );
};

export default Navigation;