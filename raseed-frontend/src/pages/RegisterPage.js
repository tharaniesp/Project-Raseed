import React, { useState } from 'react';
import '../styles/LoginPage.css';
const bgUrl = '/dark-glass-background.svg'; // new dark glass-style background

const RegisterPage = ({ onRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email || !password || !confirmPassword) {
      setError('Please fill all fields.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    // Store user in localStorage (simulate DB)
    const users = JSON.parse(localStorage.getItem('users') || '{}');
    if (users[email]) {
      setError('User already exists.');
      return;
    }
    users[email] = { email, password };
    localStorage.setItem('users', JSON.stringify(users));
    onRegister && onRegister(email);
  };

  return (
    <div className="login-page" style={{
      background: `linear-gradient(rgba(0,0,0,0.45),rgba(0,0,0,0.45)), url(${bgUrl}) center/cover no-repeat`,
    }}>
      <div className="floating-shape circle1"></div>
      <div className="floating-shape circle2"></div>
      <div className="floating-shape hexagon"></div>
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>Create Account</h2>
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
        <input
          type="password"
          placeholder="Confirm Password"
          value={confirmPassword}
          onChange={e => setConfirmPassword(e.target.value)}
        />
        <button type="submit">Register</button>
      </form>
    </div>
  );
};

export default RegisterPage;
