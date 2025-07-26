// src/components/Layout/Header.js
import React from 'react';
import { useTheme } from '../../context/ThemeContext';
import { Sun, Moon, LogOut } from 'lucide-react';
import { FileText, Menu, X } from 'lucide-react';
import { useReceipt } from '../../context/ReceiptContext';
import { useAuth } from '../../context/AuthContext';

const Header = ({ onMenuClick, isMobile }) => {
  const { backendStatus, totalReceipts } = useReceipt();
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          {isMobile && (
            <button 
              className="menu-button"
              onClick={onMenuClick}
              aria-label="Toggle menu"
            >
              <Menu size={20} />
            </button>
          )}
        <a href="/" className="logo">
          <span className="logo-icon" style={{ display: 'flex', alignItems: 'center' }}>
        <svg width={isMobile ? 40 : 35} height={isMobile ? 30 : 35} viewBox="120 45 60 60" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">
          <g stroke="#2e7d32" fill="none" stroke-width="4">
            <path d="M40,40 l0,70 l60,0 l0,-70 l-6,6 l-6,-6 l-6,6 l-6,-6 l-6,6 l-6,-6 l-6,6 l-6,-6 z"/>
            <line x1="48" y1="60" x2="92" y2="60" stroke-width="3"/>
            <line x1="48" y1="70" x2="92" y2="70" stroke-width="3"/>
            <line x1="48" y1="80" x2="92" y2="80" stroke-width="3"/>
          </g>

          <g transform="translate(120, 45)">
            <rect x="0" y="0" width="60" height="60" rx="10" ry="10" fill="none" stroke="#2e7d32" stroke-width="4"/>
            <path d="M15,20 Q10,30 20,40 Q30,50 35,40 Q40,30 30,20 Z" fill="#ea4335"/>
            <path d="M20,25 Q15,35 25,45 Q35,55 40,45 Q45,35 35,25 Z" fill="#fbbc05"/>
            <path d="M25,30 Q20,40 30,50 Q40,60 45,50 Q50,40 40,30 Z" fill="#34a853"/>
            <path d="M30,35 Q25,45 35,55 Q45,65 50,55 Q55,45 45,35 Z" fill="#4285f4"/>
          </g>
        </svg>
          </span>
          <span className="logo-text">Project Raseed</span>
        </a>
        </div>
        
      {!isMobile && (
        <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="stats">
            <span className="receipt-count">
              {totalReceipts} Receipt{totalReceipts !== 1 ? 's' : ''}
            </span>
          </div>
          {user && (
            <div className="user-info">
              <span className="user-name">
                {user.displayName || user.email}
              </span>
            </div>
          )}
          <button
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <button
            className="logout-btn"
            onClick={handleLogout}
            aria-label="Logout"
            style={{ 
              background: 'none', 
              border: 'none', 
              cursor: 'pointer', 
              padding: '0.5rem',
              borderRadius: '4px',
              color: '#666',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
            onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
          >
            <LogOut size={20} />
          </button>
          {/* <div className={`status-indicator ${backendStatus}`}>
            <div className={`status-dot ${backendStatus}`}></div>
            <span className="status-text">
              {backendStatus === 'online' ? 'Backend Online' : 'Backend Offline'}
            </span>
          </div> */}
        </div>
      )}
      </div>
    </header>
  );
};

export default Header;