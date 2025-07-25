// src/components/Layout/Header.js
import React from 'react';
import { useTheme } from '../../context/ThemeContext';
import { Sun, Moon } from 'lucide-react';
import { FileText, Menu, X } from 'lucide-react';
import { useReceipt } from '../../context/ReceiptContext';

const Header = ({ onMenuClick, isMobile }) => {
  const { backendStatus, totalReceipts } = useReceipt();
  const { theme, toggleTheme } = useTheme();

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
            <FileText className="logo-icon" size={isMobile ? 20 : 24} />
            <span className="logo-text">Project Raseed</span>
          </a>
        </div>
        
        <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {!isMobile && (
            <div className="stats">
              <span className="receipt-count">
                {totalReceipts} Receipt{totalReceipts !== 1 ? 's' : ''}
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
          <div className={`status-indicator ${backendStatus}`}>
            <div className={`status-dot ${backendStatus}`}></div>
            <span className="status-text">
              {isMobile 
                ? (backendStatus === 'online' ? 'Online' : 'Offline')
                : (backendStatus === 'online' ? 'Backend Online' : 'Backend Offline')
              }
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;