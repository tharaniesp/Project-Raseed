import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import RegisterPage from './RegisterPage';
import '../styles/LoginPage.css';

const LoginPage = () => {
  const { signInWithGoogle, signInWithEmail } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    
    try {
      setIsLoading(true);
      setError('');
      await signInWithEmail(email, password);
      // Success - user will be automatically redirected by AuthContext
    } catch (error) {
      console.error('Email sign-in error:', error);
      setError(error.message || 'Failed to sign in. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      setError('');
      await signInWithGoogle();
      // Success - user will be automatically redirected by AuthContext
    } catch (error) {
      console.error('Google sign-in error:', error);
      setError('Failed to sign in with Google. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (showRegister) {
    return (
      <RegisterPage onRegister={() => {
        setShowRegister(false);
        setError('');
      }} />
    );
  }
  
  return (
    <div className="login-container">
      {/* Left side - Wallet illustration */}
      <div className="login-illustration">
        <div className="wallet-graphic">
          <svg width="100%" height="100%" viewBox="0 0 400 400" fill="none">
            {/* Wallet base */}
            <rect x="80" y="120" width="240" height="160" rx="20" fill="#4285F4" stroke="#1a73e8" strokeWidth="4"/>
            
            {/* Wallet fold */}
            <rect x="80" y="120" width="240" height="40" rx="20" fill="#34A853"/>
            
            {/* Cards inside wallet */}
            <rect x="100" y="140" width="200" height="120" rx="8" fill="#FBBC05"/>
            <rect x="110" y="150" width="180" height="100" rx="6" fill="#EA4335"/>
            <rect x="120" y="160" width="160" height="80" rx="4" fill="#4285F4"/>
            
            {/* Wallet chain */}
            <circle cx="200" cy="100" r="15" fill="#1a73e8"/>
            <path d="M200 85 Q200 70 200 55" stroke="#1a73e8" strokeWidth="3" fill="none"/>
            
            {/* Floating elements */}
            <circle cx="320" cy="80" r="8" fill="#34A853" opacity="0.8"/>
            <circle cx="80" cy="320" r="12" fill="#FBBC05" opacity="0.7"/>
            <circle cx="350" cy="350" r="10" fill="#EA4335" opacity="0.6"/>
            
            {/* Receipt icon */}
            <rect x="60" y="200" width="40" height="50" rx="4" fill="#34A853" opacity="0.9"/>
            <rect x="65" y="205" width="30" height="2" fill="white"/>
            <rect x="65" y="215" width="25" height="2" fill="white"/>
            <rect x="65" y="225" width="30" height="2" fill="white"/>
            <rect x="65" y="235" width="20" height="2" fill="white"/>
          </svg>
        </div>
        <div className="illustration-text">
          <h2>Smart Receipt Management</h2>
          <p>Organize, track, and analyze your receipts with AI-powered insights</p>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="login-form-section">
        <div className="login-card">
          {/* Header */}
          <div className="login-header">
            <div className="logo-container">
              <div className="app-logo">
                <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                  <rect width="40" height="40" rx="8" fill="#4285F4"/>
                  <path d="M8 12h24v2H8zM8 16h24v2H8zM8 20h24v2H8z" fill="white"/>
                  <circle cx="20" cy="28" r="6" fill="#34A853"/>
                </svg>
              </div>
              <h1 className="app-title">Project Raseed</h1>
            </div>
          </div>

          {/* Form */}
          <div className="login-form-container">
            <h2 className="login-title">Welcome back</h2>
            <p className="login-subtitle">Sign in to your account to continue</p>
            
            {error && (
              <div className="error-message">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                {error}
                {error.includes('No account found') && (
                  <div className="error-help">
                    <p>Don't have an account? <button 
                      type="button" 
                      onClick={() => setShowRegister(true)}
                      className="error-link"
                    >
                      Sign up here
                    </button></p>
                  </div>
                )}
              </div>
            )}

            <form onSubmit={handleSubmit} className="login-form">
              <div className="input-group">
                <label htmlFor="email" className="input-label">Email address</label>
                <input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="input-field"
                  required
                />
              </div>

              <div className="input-group">
                <label htmlFor="password" className="input-label">Password</label>
                <input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="input-field"
                  required
                />
              </div>

              <button type="submit" className="login-button primary" disabled={isLoading}>
                {isLoading ? 'Signing in...' : 'Sign in'}
              </button>
            </form>

            {/* Divider */}
            <div className="divider">
              <span>or</span>
            </div>

            {/* Google Sign-In */}
            <button 
              onClick={handleGoogleLogin} 
              disabled={isLoading}
              className="google-signin-button"
            >
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              {isLoading ? 'Signing in...' : 'Continue with Google'}
            </button>

            {/* Sign up link */}
            <div className="signup-link">
              <span>Don't have an account? </span>
              <button 
                type="button"
                onClick={() => setShowRegister(true)}
                className="signup-button"
              >
                Sign up
              </button>
            </div>
            
            {/* Back to login link (when showing register) */}
            {showRegister && (
              <div className="back-to-login">
                <button 
                  type="button"
                  onClick={() => setShowRegister(false)}
                  className="back-button"
                >
                  ← Back to Sign In
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
