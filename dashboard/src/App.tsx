import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import TrafficAnalysis from './pages/TrafficAnalysis';
import FlowAnalysis from './pages/FlowAnalysis';
import NetworkHealth from './pages/NetworkHealth';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';
import './App.css';

const { Header, Content, Footer } = Layout;

const App: React.FC = () => {
  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <div className="logo">
          <h2 style={{ color: 'white', margin: 0 }}>P4 Network Monitor</h2>
        </div>
        <Navigation />
      </Header>
      
      <Content className="app-content">
        <div className="content-container">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/traffic" element={<TrafficAnalysis />} />
            <Route path="/flows" element={<FlowAnalysis />} />
            <Route path="/health" element={<NetworkHealth />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </Content>
      
      <Footer className="app-footer">
        <div style={{ textAlign: 'center' }}>
          P4 Network Monitor ©2024 - Research Project
        </div>
      </Footer>
    </Layout>
  );
};

export default App;