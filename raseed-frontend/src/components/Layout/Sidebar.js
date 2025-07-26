// src/components/Layout/Sidebar.js
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Upload, 
  Receipt, 
  MessageSquare, 
  BarChart3,
  TrendingUp,
  Bell,
  Target
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const navigationItems = [
    {
      path: '/upload',
      icon: Upload,
      label: 'Upload Receipts',
      description: 'Upload new receipt images',
      badge: null
    },
    {
      path: '/receipts',
      icon: Receipt,
      label: 'My Receipts',
      description: 'View all uploaded receipts',
      badge: null
    },
    {
      path: '/query',
      icon: MessageSquare,
      label: 'AI Assistant',
      description: 'Ask questions about your spending',
      // badge: 'Step 4'
    },
    {
      path: '/insights',
      icon: BarChart3,
      label: 'Smart Insights',
      description: 'AI-powered spending analysis',
      // badge: 'Step 5'
    }
  ];

  const isActivePath = (path) => {
    return location.pathname === path;
  };

  return (
    <aside className="sidebar">
      <nav className="nav-content">
        <ul className="nav-list">
          {navigationItems.map((item) => {
            const IconComponent = item.icon;
            const isActive = isActivePath(item.path);
            
            return (
              <li key={item.path} className="nav-item">
                <Link
                  to={item.path}
                  className={`nav-link ${isActive ? 'active' : ''}`}
                >
                  <div className="nav-icon">
                    <IconComponent className="icon" />
                  </div>
                  <div className="nav-content-text">
                    <div className="nav-label">{item.label}</div>
                    <div className="nav-description">{item.description}</div>
                  </div>
                  {item.badge && (
                    <span className={`nav-badge ${item.badge.startsWith('Step') ? 'badge-blue' : 'badge-gray'}`}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Insights Quick Stats in Sidebar */}
        {/* <div className="sidebar-insights">
          <h3 className="insights-title">
            <TrendingUp className="insights-icon" />
            Quick Insights
          </h3>
          <div className="insight-stats">
            <div className="insight-stat">
              <Target className="stat-icon" />
              <div className="stat-details">
                <span className="stat-value">3</span>
                <span className="stat-label">Active Alerts</span>
              </div>
            </div>
            <div className="insight-stat">
              <Bell className="stat-icon" />
              <div className="stat-details">
                <span className="stat-value">1</span>
                <span className="stat-label">Unread</span>
              </div>
            </div>
          </div>
          <Link to="/insights" className="insights-cta">
            View All Insights
          </Link>
        </div> */}

        {/* Project Status */}
        {/* <div className="project-status">
          <h3 className="status-title">Project Progress</h3>
          <div className="status-steps">
            <div className="status-step completed">
              <div className="step-indicator"></div>
              <span className="step-label">Step 1: Upload & Storage</span>
            </div>
            <div className="status-step completed">
              <div className="step-indicator"></div>
              <span className="step-label">Step 2: AI Extraction</span>
            </div>
            <div className="status-step completed">
              <div className="step-indicator"></div>
              <span className="step-label">Step 3: Wallet Integration</span>
            </div>
            <div className="status-step completed">
              <div className="step-indicator"></div>
              <span className="step-label">Step 4: AI Query System</span>
            </div>
            <div className="status-step active">
              <div className="step-indicator"></div>
              <span className="step-label">Step 5: Smart Insights</span>
            </div>
          </div>
        </div> */}
      </nav>
    </aside>
  );
};

export default Sidebar;