// src/components/Insights/NotificationsCenter.js
import React, { useState, useMemo } from 'react';
import { 
  Bell, BellOff, Filter, CheckCircle, XCircle, 
  AlertTriangle, Wallet, TrendingDown, Settings,
  MoreHorizontal, Trash2, MarkAsRead
} from 'lucide-react';
import './NotificationsCenter.css';

const notificationTypeConfig = {
  insight_alert: {
    icon: AlertTriangle,
    color: '#f97316',
    label: 'Insight Alert'
  },
  wallet_pass_updated: {
    icon: Wallet,
    color: '#6366f1',
    label: 'Wallet Update'
  },
  price_alert: {
    icon: TrendingDown,
    color: '#10b981',
    label: 'Price Alert'
  },
  budget_alert: {
    icon: AlertTriangle,
    color: '#ef4444',
    label: 'Budget Alert'
  },
  default: {
    icon: Bell,
    color: '#6b7280',
    label: 'Notification'
  }
};

const priorityColors = {
  urgent: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6'
};

const NotificationsCenter = ({ 
  notifications = [], 
  onMarkAsRead, 
  onMarkAllAsRead, 
  onDeleteNotification,
  onUpdateSettings 
}) => {
  const [filter, setFilter] = useState('all');
  const [selectedNotifications, setSelectedNotifications] = useState(new Set());
  const [showSettings, setShowSettings] = useState(false);

  // Filter notifications
  const filteredNotifications = useMemo(() => {
    switch (filter) {
      case 'unread':
        return notifications.filter(n => !n.read);
      case 'high':
        return notifications.filter(n => n.priority === 'high' || n.priority === 'urgent');
      case 'medium':
        return notifications.filter(n => n.priority === 'medium');
      case 'low':
        return notifications.filter(n => n.priority === 'low');
      default:
        return notifications;
    }
  }, [notifications, filter]);

  // Statistics
  const stats = useMemo(() => {
    const unreadCount = notifications.filter(n => !n.read).length;
    const highPriorityCount = notifications.filter(n => 
      n.priority === 'high' || n.priority === 'urgent'
    ).length;
    
    return {
      total: notifications.length,
      unread: unreadCount,
      highPriority: highPriorityCount
    };
  }, [notifications]);

  const handleSelectNotification = (notificationId) => {
    const newSelected = new Set(selectedNotifications);
    if (newSelected.has(notificationId)) {
      newSelected.delete(notificationId);
    } else {
      newSelected.add(notificationId);
    }
    setSelectedNotifications(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedNotifications.size === filteredNotifications.length) {
      setSelectedNotifications(new Set());
    } else {
      setSelectedNotifications(new Set(filteredNotifications.map(n => n.id)));
    }
  };

  const handleBulkMarkAsRead = () => {
    selectedNotifications.forEach(id => {
      const notification = notifications.find(n => n.id === id);
      if (notification && !notification.read) {
        onMarkAsRead(id);
      }
    });
    setSelectedNotifications(new Set());
  };

  const handleBulkDelete = () => {
    if (window.confirm(`Delete ${selectedNotifications.size} notifications?`)) {
      selectedNotifications.forEach(id => onDeleteNotification(id));
      setSelectedNotifications(new Set());
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  const getNotificationConfig = (type) => {
    return notificationTypeConfig[type] || notificationTypeConfig.default;
  };

  return (
    <div className="notifications-center">
      {/* Header */}
      <div className="notifications-header">
        <div className="header-title">
          <Bell className="header-icon" />
          <h2>Notifications</h2>
          {stats.unread > 0 && (
            <span className="unread-badge">{stats.unread}</span>
          )}
        </div>
        
        <div className="header-actions">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="btn btn-ghost"
            title="Notification Settings"
          >
            <Settings className="btn-icon" />
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div className="notifications-stats">
        <div className="stat-item">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="stat-item">
          <span className="stat-value unread">{stats.unread}</span>
          <span className="stat-label">Unread</span>
        </div>
        <div className="stat-item">
          <span className="stat-value high-priority">{stats.highPriority}</span>
          <span className="stat-label">High Priority</span>
        </div>
      </div>

      {/* Controls */}
      <div className="notifications-controls">
        <div className="filter-controls">
          <Filter className="filter-icon" />
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Notifications</option>
            <option value="unread">Unread</option>
            <option value="high">High Priority</option>
            <option value="medium">Medium Priority</option>
            <option value="low">Low Priority</option>
          </select>
        </div>

        <div className="action-controls">
          {selectedNotifications.size > 0 ? (
            <>
              <span className="selection-count">
                {selectedNotifications.size} selected
              </span>
              <button onClick={handleBulkMarkAsRead} className="btn btn-sm">
                <CheckCircle className="btn-icon" />
                Mark as Read
              </button>
              <button onClick={handleBulkDelete} className="btn btn-sm btn-danger">
                <Trash2 className="btn-icon" />
                Delete
              </button>
            </>
          ) : (
            <button 
              onClick={onMarkAllAsRead}
              className="btn btn-sm"
              disabled={stats.unread === 0}
            >
              <CheckCircle className="btn-icon" />
              Mark All as Read
            </button>
          )}
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-panel">
          <h3>Notification Preferences</h3>
          <div className="settings-grid">
            <div className="setting-item">
              <label className="setting-label">
                <input type="checkbox" defaultChecked />
                Email notifications
              </label>
            </div>
            <div className="setting-item">
              <label className="setting-label">
                <input type="checkbox" defaultChecked />
                Push notifications
              </label>
            </div>
            <div className="setting-item">
              <label className="setting-label">
                <input type="checkbox" defaultChecked />
                Wallet pass updates
              </label>
            </div>
            <div className="setting-item">
              <label className="setting-label">
                <input type="checkbox" defaultChecked />
                Budget alerts
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Notifications List */}
      <div className="notifications-list">
        {filteredNotifications.length > 0 ? (
          <>
            {/* Bulk Actions Header */}
            {filteredNotifications.length > 1 && (
              <div className="bulk-actions">
                <label className="select-all-label">
                  <input
                    type="checkbox"
                    checked={selectedNotifications.size === filteredNotifications.length}
                    onChange={handleSelectAll}
                  />
                  Select all
                </label>
              </div>
            )}

            {/* Notifications */}
            {filteredNotifications.map((notification) => {
              const config = getNotificationConfig(notification.type);
              const IconComponent = config.icon;
              const isSelected = selectedNotifications.has(notification.id);

              return (
                <div 
                  key={notification.id}
                  className={`notification-item ${!notification.read ? 'unread' : ''} ${isSelected ? 'selected' : ''}`}
                >
                  <div className="notification-selector">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleSelectNotification(notification.id)}
                    />
                  </div>

                  <div className="notification-icon" style={{ color: config.color }}>
                    <IconComponent />
                  </div>

                  <div className="notification-content">
                    <div className="notification-header">
                      <h4 className="notification-title">{notification.title}</h4>
                      <div className="notification-meta">
                        <span className="notification-time">
                          {formatTimestamp(notification.timestamp)}
                        </span>
                        {notification.priority && (
                          <span 
                            className="priority-indicator"
                            style={{ backgroundColor: priorityColors[notification.priority] }}
                          />
                        )}
                      </div>
                    </div>
                    <p className="notification-message">{notification.message}</p>
                    <div className="notification-type">{config.label}</div>
                  </div>

                  <div className="notification-actions">
                    {!notification.read && (
                      <button
                        onClick={() => onMarkAsRead(notification.id)}
                        className="action-btn"
                        title="Mark as read"
                      >
                        <CheckCircle className="action-icon" />
                      </button>
                    )}
                    <button
                      onClick={() => onDeleteNotification(notification.id)}
                      className="action-btn delete-btn"
                      title="Delete notification"
                    >
                      <XCircle className="action-icon" />
                    </button>
                  </div>

                  {!notification.read && <div className="unread-indicator" />}
                </div>
              );
            })}
          </>
        ) : (
          <div className="empty-notifications">
            <BellOff className="empty-icon" />
            <h3>No notifications</h3>
            <p>
              {filter === 'all' 
                ? "You're all caught up! No notifications to show."
                : `No ${filter} notifications found.`
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsCenter;