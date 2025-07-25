// src/components/Layout/Sidebar.js - Updated with Step 4 Complete
import React from 'react';
import { NavLink } from 'react-router-dom';
import { Upload, FileText, MessageSquare, BarChart3, Settings, X } from 'lucide-react';

const Sidebar = ({ isOpen, isMobile, onClose }) => {
  const navItems = [
    { 
      path: '/upload', 
      icon: Upload, 
      label: 'Upload',
      fullLabel: 'Upload Receipt',
      description: 'Add new receipts'
    },
    { 
      path: '/receipts', 
      icon: FileText, 
      label: 'Receipts',
      fullLabel: 'My Receipts',
      description: 'View all receipts'
    },
    { 
      path: '/query', 
      icon: MessageSquare, 
      label: 'Query',
      fullLabel: 'AI Assistant',
      description: 'Ask in any language',
      // badge: 'NEW!'
    },
    { 
      path: '/analytics', 
      icon: BarChart3, 
      label: 'Analytics',
      fullLabel: 'Analytics',
      description: 'Spending insights',
      // badge: 'Step 5'
    },
    { 
      path: '/settings', 
      icon: Settings, 
      label: 'Settings',
      fullLabel: 'Settings',
      description: 'App preferences',
      // badge: 'Soon'
    }
  ];

  const handleNavClick = () => {
    if (isMobile && onClose) {
      onClose();
    }
  };

  return (
    <aside className={`sidebar ${isMobile ? 'sidebar-mobile' : ''} ${isMobile && isOpen ? 'sidebar-open' : ''}`}>
      {isMobile && (
        <div className="sidebar-header">
          <h3>Menu</h3>
          <button 
            className="close-button"
            onClick={onClose}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>
      )}
      
      <nav className="sidebar-nav">
        <ul className="nav-list">
          {navItems.map((item) => {
            const IconComponent = item.icon;
            return (
              <li key={item.path} className="nav-item">
                <NavLink 
                  to={item.path} 
                  className={({ isActive }) => 
                    `nav-link ${isActive ? 'active' : ''}`
                  }
                  onClick={handleNavClick}
                >
                  <IconComponent className="nav-icon" size={20} />
                  <div className="nav-content">
                    <span className="nav-label">
                      {isMobile ? item.label : item.fullLabel}
                    </span>
                    {!isMobile && (
                      <span className="nav-description">{item.description}</span>
                    )}
                  </div>
                  {item.badge && !isMobile && (
                    <span className={`nav-badge ${
                      item.badge === 'NEW!' ? 'badge-green' : 
                      item.badge === 'Soon' ? 'badge-gray' : 'badge-blue'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>
      
      {/* {!isMobile && (
        <div className="sidebar-footer">
          <div className="current-step">
            <h4>Current: Step 4 Complete!</h4>
            <p>🎉 Multi-Language AI Queries Active</p>
            <div className="progress-steps">
              <div className="step completed">1</div>
              <div className="step completed">2</div>
              <div className="step completed">3</div>
              <div className="step completed">4</div>
              <div className="step">5</div>
            </div>
            <div className="step-details">
              <small>
                ✅ Upload & Storage<br/>
                ✅ AI Data Extraction<br/>
                ✅ Wallet Pass Generation<br/>
                ✅ Natural Language Queries<br/>
                🔄 Insights & Notifications (Next)
              </small>
            </div>
          </div>
        </div>
      )} */}
    </aside>
  );
};

export default Sidebar;