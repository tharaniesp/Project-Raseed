import React from 'react';
import './StatsGrid.css';

/**
 * StatsCard component for displaying individual financial metrics
 */
const StatsCard = ({ 
  title, 
  value, 
  icon,
  iconBgColor = '#ebf5ff', 
  iconColor = '#3b82f6',
  change,
  changeType = 'neutral', // 'positive', 'negative', 'neutral'
  message,
  currencySymbol,
  notifications
}) => {
  return (
    <div className="stats-card">
      {/* Desktop and Tablet Layout */}
      <div className="stats-card-desktop">
        {icon && (
          <div 
            className="stats-card-icon" 
            style={{ 
              backgroundColor: iconBgColor,
              color: iconColor 
            }}
          >
            {icon}
          </div>
        )}
        <div className="stats-card-title">{title}</div>
        
        <div className="stats-card-value">
          {currencySymbol && <span className="currency">{currencySymbol}</span>}
          {value}
        </div>
        
        {change && (
          <div className="stats-card-info">
            <span className={`stats-card-tag ${changeType}`}>
              {change > 0 ? '+' : ''}{change}%
            </span>
          </div>
        )}
        
        {message && <div className="stats-card-message">{message}</div>}
        {notifications && <div className="stats-card-message">{notifications} unread notifications</div>}
      </div>
      
      {/* Mobile Layout */}
      <div className="stats-card-mobile">
        <div className="stats-card-left">
          {icon && (
            <div 
              className="stats-card-icon" 
              style={{ 
                backgroundColor: iconBgColor,
                color: iconColor 
              }}
            >
              {icon}
            </div>
          )}
          <div>
            <div className="stats-card-title">{title}</div>
            <div className="stats-card-value">
              {currencySymbol && <span className="currency">{currencySymbol}</span>}
              {value}
            </div>
          </div>
        </div>
        
        <div className="stats-card-right">
          {change && (
            <div className="stats-card-info">
              <span className={`stats-card-tag ${changeType}`}>
                {change > 0 ? '+' : ''}{change}%
              </span>
            </div>
          )}
          {message && <div className="stats-card-message">{message}</div>}
          {notifications && <div className="stats-card-message">{notifications} notifications</div>}
        </div>
      </div>
    </div>
  );
};

/**
 * StatsGrid component - Responsive grid layout for financial stats cards
 */
const StatsGrid = ({ children }) => {
  return (
    <div className="stats-grid">
      {children}
    </div>
  );
};

export { StatsCard, StatsGrid };
