// src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import UploadPage from './pages/UploadPage';
import ReceiptsPage from './pages/ReceiptsPage';
import QueryPage from './pages/QueryPage';
import { ReceiptProvider } from './context/ReceiptContext';
import './styles/App.css';

function App() {
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <ReceiptProvider>
      <Router>
        <div className="app">
          <Header onMenuClick={toggleSidebar} isMobile={isMobile} />
          <div className="app-body">
            <Sidebar isOpen={sidebarOpen} isMobile={isMobile} onClose={() => setSidebarOpen(false)} />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<UploadPage />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/receipts" element={<ReceiptsPage />} />
                <Route path="/query" element={<QueryPage />} />
              </Routes>
            </main>
          </div>
          
          {/* Mobile overlay */}
          {isMobile && sidebarOpen && (
            <div 
              className="mobile-overlay" 
              onClick={() => setSidebarOpen(false)}
            />
          )}
        </div>
      </Router>
    </ReceiptProvider>
  );
}

export default App;