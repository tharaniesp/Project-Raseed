// src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import UploadPage from './pages/UploadPage';
import ReceiptsPage from './pages/ReceiptsPage';
import QueryPage from './pages/QueryPage';
import InsightsPage from './pages/InsightsPage';
import { ReceiptProvider } from './context/ReceiptContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import './styles/App.css';
import './pages/InsightsPage.css';

function AppContent() {
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, loading } = useAuth();

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

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <Router>
      {!user ? (
        <Routes>
          <Route path="*" element={<LoginPage />} />
        </Routes>
      ) : (
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
                <Route path="/insights" element={<InsightsPage />} />
                <Route path="*" element={<Navigate to="/upload" replace />} />
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
      )}
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <ReceiptProvider>
        <AppContent />
      </ReceiptProvider>
    </AuthProvider>
  );
}

export default App;