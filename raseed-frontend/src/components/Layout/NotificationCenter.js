import React, { useState, useEffect, useRef } from 'react';
import { Bell, X, CheckCircle, AlertCircle, Info, DollarSign, CreditCard } from 'lucide-react';
import './NotificationCenter.css';

const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const notificationRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current && typeof wsRef.current.close === 'function') {
        wsRef.current.close();
      }
    };
  }, []);

  // Handle clicks outside notification panel and escape key
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscapeKey);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isOpen]);

  const connectWebSocket = () => {
    const userId = 'demo_user'; // In real app, get from auth context
    const wsUrl = `ws://localhost:8000/ws/${userId}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('🔌 WebSocket connected');
        setIsConnected(true);
      };
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      wsRef.current.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setIsConnected(false);
      };
      
    } catch (error) {
      console.error('❌ Failed to connect WebSocket:', error);
      setIsConnected(false);
    }
  };

  const handleWebSocketMessage = (data) => {
    if (data.type === 'notification') {
      addNotification(data);
    } else if (data.type === 'update') {
      handleUpdate(data);
    }
  };

  const addNotification = (notification) => {
    const newNotification = {
      id: notification.id || Date.now(),
      title: notification.title,
      message: notification.message,
      category: notification.category,
      priority: notification.priority,
      timestamp: notification.timestamp,
      data: notification.data,
      read: false
    };
    
    setNotifications(prev => [newNotification, ...prev.slice(0, 9)]); // Keep max 10 notifications
    setUnreadCount(prev => prev + 1);
    
    // Auto-remove notification after 10 seconds
    setTimeout(() => {
      removeNotification(newNotification.id);
    }, 10000);
  };

  const handleUpdate = (update) => {
    if (update.update_type === 'receipt_processed') {
      addNotification({
        id: `update_${Date.now()}`,
        title: 'Receipt Processed! 📄',
        message: `Receipt from ${update.data.merchant_name} processed successfully`,
        category: 'receipt',
        priority: 'normal',
        timestamp: update.timestamp,
        data: update.data
      });
    }
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const markAsRead = (id) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  const getNotificationIcon = (category) => {
    switch (category) {
      case 'receipt':
        return <CreditCard size={16} />;
      case 'budget':
        return <DollarSign size={16} />;
      case 'insight':
        return <Info size={16} />;
      case 'wallet':
        return <CheckCircle size={16} />;
      default:
        return <AlertCircle size={16} />;
    }
  };

  const getNotificationClass = (priority, category) => {
    let classes = ['notification-item'];
    
    if (priority === 'high') classes.push('high-priority');
    if (priority === 'medium') classes.push('medium-priority');
    
    classes.push(`category-${category}`);
    
    return classes.join(' ');
  };

  return (
    <div className="notification-center" ref={notificationRef}>
      {/* Notification Bell */}
      <button 
        className="notification-bell"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="notification-badge">{unreadCount}</span>
        )}
        <span 
          className={`connection-indicator ${isConnected ? 'online' : 'offline'}`} 
          title={isConnected ? 'Connected' : 'Disconnected'}
        >
          ●
        </span>
      </button>

      {/* Notification Panel */}
      {isOpen && (
        <div className="notification-panel">
          <div className="notification-header">
            <h3>Notifications</h3>
            <div className="notification-actions">
              {unreadCount > 0 && (
                <button 
                  className="mark-all-read"
                  onClick={markAllAsRead}
                >
                  Mark all read
                </button>
              )}
              <button 
                className="close-panel"
                onClick={() => setIsOpen(false)}
              >
                <X size={16} />
              </button>
            </div>
          </div>

          <div className="notification-list">
            {notifications.length === 0 ? (
              <div className="no-notifications">
                <Bell size={24} />
                <p>No notifications yet</p>
                <small>Real-time updates will appear here</small>
              </div>
            ) : (
              notifications.map(notification => (
                <div 
                  key={notification.id}
                  className={getNotificationClass(notification.priority, notification.category)}
                >
                  <div className="notification-icon">
                    {getNotificationIcon(notification.category)}
                  </div>
                  
                  <div className="notification-content">
                    <div className="notification-title">
                      {notification.title}
                    </div>
                    <div className="notification-message">
                      {notification.message}
                    </div>
                    <div className="notification-meta">
                      <span className="notification-time">
                        {new Date(notification.timestamp).toLocaleTimeString()}
                      </span>
                      {notification.data.merchant_name && (
                        <span className="notification-merchant">
                          {notification.data.merchant_name}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="notification-actions">
                    {!notification.read && (
                      <button 
                        className="mark-read"
                        onClick={() => markAsRead(notification.id)}
                        title="Mark as read"
                      >
                        <CheckCircle size={14} />
                      </button>
                    )}
                    <button 
                      className="remove-notification"
                      onClick={() => removeNotification(notification.id)}
                      title="Remove"
                    >
                      <X size={14} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {notifications.length > 0 && (
            <div className="notification-footer">
              <small>
                {unreadCount} unread • {notifications.length} total
              </small>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationCenter; 