import React, { useState, useEffect } from 'react';
import { Info, CheckCircle, AlertCircle, Clock, Zap } from 'lucide-react';
import './NotificationConditions.css';

const NotificationConditions = () => {
  const [conditions, setConditions] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotificationConditions();
    fetchNotificationStatus();
  }, []);

  const fetchNotificationConditions = async () => {
    try {
      const response = await fetch('http://localhost:8000/notifications/conditions');
      const data = await response.json();
      setConditions(data.notification_conditions || []);
    } catch (error) {
      console.error('Failed to fetch notification conditions:', error);
    }
  };

  const fetchNotificationStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/notifications/status');
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch notification status:', error);
    } finally {
      setLoading(false);
    }
  };

  const testNotification = async (type) => {
    try {
      const response = await fetch(`http://localhost:8000/notifications/test/demo_user?notification_type=${type}`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        alert(`✅ ${data.message}`);
      } else {
        alert(`❌ Failed to send notification: ${data.message}`);
      }
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  const getConditionIcon = (type) => {
    switch (type) {
      case 'receipt_processed':
        return <CheckCircle size={20} />;
      case 'budget_alert':
        return <AlertCircle size={20} />;
      case 'spending_insight':
        return <Info size={20} />;
      case 'real_time_update':
        return <Zap size={20} />;
      default:
        return <Clock size={20} />;
    }
  };

  const getPriorityColor = (priority) => {
    if (priority.includes('high')) return 'high-priority';
    if (priority.includes('medium')) return 'medium-priority';
    return 'normal-priority';
  };

  if (loading) {
    return (
      <div className="notification-conditions">
        <div className="loading">Loading notification conditions...</div>
      </div>
    );
  }

  return (
    <div className="notification-conditions">
      <div className="conditions-header">
        <h2>🔔 Notification Conditions</h2>
        <p>Learn about when and how notifications are triggered</p>
      </div>

      {/* System Status */}
      {status && (
        <div className="system-status">
          <h3>📡 System Status</h3>
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">System:</span>
              <span className={`status-value ${status.system_status === 'active' ? 'active' : 'inactive'}`}>
                {status.system_status}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Connections:</span>
              <span className="status-value">{status.total_connections}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Users:</span>
              <span className="status-value">{status.connected_users.join(', ') || 'None'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Notification Conditions */}
      <div className="conditions-list">
        <h3>📋 Notification Types</h3>
        {conditions.map((condition, index) => (
          <div key={index} className="condition-card">
            <div className="condition-header">
              <div className="condition-icon">
                {getConditionIcon(condition.type)}
              </div>
              <div className="condition-info">
                <h4>{condition.type.replace('_', ' ').toUpperCase()}</h4>
                <p className="condition-trigger">{condition.trigger}</p>
              </div>
              <div className={`condition-priority ${getPriorityColor(condition.priority)}`}>
                {condition.priority}
              </div>
            </div>
            <p className="condition-description">{condition.description}</p>
            <button 
              className="test-button"
              onClick={() => testNotification(condition.type.split('_')[0])}
            >
              🧪 Test This Notification
            </button>
          </div>
        ))}
      </div>

      {/* How to Check */}
      <div className="how-to-section">
        <h3>🎯 How to Check Notifications</h3>
        <div className="how-to-steps">
          <div className="step">
            <span className="step-number">1</span>
            <span className="step-text">Open your frontend at http://localhost:3000</span>
          </div>
          <div className="step">
            <span className="step-number">2</span>
            <span className="step-text">Look for the bell icon in the header</span>
          </div>
          <div className="step">
            <span className="step-number">3</span>
            <span className="step-text">Click the bell to open notification panel</span>
          </div>
          <div className="step">
            <span className="step-number">4</span>
            <span className="step-text">Check the badge number for unread count</span>
          </div>
          <div className="step">
            <span className="step-number">5</span>
            <span className="step-text">Look for connection status indicator</span>
          </div>
        </div>
      </div>

      {/* Quick Test Buttons */}
      <div className="quick-test-section">
        <h3>⚡ Quick Test</h3>
        <div className="test-buttons">
          <button 
            className="test-btn receipt"
            onClick={() => testNotification('receipt')}
          >
            📄 Test Receipt
          </button>
          <button 
            className="test-btn budget"
            onClick={() => testNotification('budget')}
          >
            💰 Test Budget Alert
          </button>
          <button 
            className="test-btn insight"
            onClick={() => testNotification('insight')}
          >
            💡 Test Insight
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotificationConditions; 