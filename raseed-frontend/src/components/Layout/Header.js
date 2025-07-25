// src/components/Layout/Header.js
import React from 'react';
import { FileText, Menu, X } from 'lucide-react';
import { useReceipt } from '../../context/ReceiptContext';

const Header = ({ onMenuClick, isMobile }) => {
  const { backendStatus, totalReceipts } = useReceipt();

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
        <svg width={isMobile ? 40 : 60} height={isMobile ? 30 : 50} viewBox="40 40 140 70" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">
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
        <div className="header-actions">
          <div className="stats">
            <span className="receipt-count">
              {totalReceipts} Receipt{totalReceipts !== 1 ? 's' : ''}
            </span>
          </div>
          <div className={`status-indicator ${backendStatus}`}>
            <div className={`status-dot ${backendStatus}`}></div>
            <span className="status-text">
              {backendStatus === 'online' ? 'Backend Online' : 'Backend Offline'}
            </span>
          </div>
        </div>
      )}
      </div>
    </header>
  );
};

export default Header;