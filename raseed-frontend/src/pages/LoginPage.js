import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import RegisterPage from './RegisterPage';
import '../styles/LoginPage.css';
const bgUrl = '/dark-glass-background.svg'; // new dark glass-style background

const LoginPage = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    // Validate against localStorage
    const users = JSON.parse(localStorage.getItem('users') || '{}');
    if (!users[email] || users[email].password !== password) {
      setError('Invalid email or password.');
      return;
    }
    login({ email });
  };

  const handleGoogleLogin = () => {
    window.alert('Google Sign-In not implemented.');
  };

  if (showRegister) {
    return (
      <RegisterPage onRegister={(email) => {
        setShowRegister(false);
        setEmail(email);
        setError('Account created! Please login.');
      }} />
    );
  }
  return (
    <div className="login-page" style={{
      background: `linear-gradient(rgba(0,0,0,0.45),rgba(0,0,0,0.45)), url(${bgUrl}) center/cover no-repeat`,
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative'
    }}>
      <div className="floating-shape circle1"></div>
      <div className="floating-shape circle2"></div>
      <div className="floating-shape hexagon"></div>
      <form className="login-form" onSubmit={handleSubmit} style={{ boxShadow: '0 4px 32px rgba(0,0,0,0.13)' }}>
        <h2 style={{ marginBottom: '0.5rem', fontWeight: 700, color: "#1e1e2f" }}>Sign In</h2>
        <p style={{ color: '#6b7280', marginBottom: '1rem', textAlign: 'center' }}>Welcome to your smart wallet</p>
        {error && <div className="error">{error}</div>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />
        <button type="submit">Login</button>
        <button type="button" onClick={handleGoogleLogin} className="google-login-btn" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
          <img src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_2013_Google.png" alt="Google" style={{ width: 20, height: 20, borderRadius: '50%' }} />
          Sign in with Google
        </button>
        <div style={{ textAlign: 'center', marginTop: '1rem', color: '#6b7280' }}>
          Not a member already?{' '}
          <span style={{ color: 'var(--color-link, #3b82f6)', cursor: 'pointer', textDecoration: 'underline' }} onClick={() => setShowRegister(true)}>
            Create an account.
          </span>
        </div>
      </form>
    </div>
  );
};

export default LoginPage;
