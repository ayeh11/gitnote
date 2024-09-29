// src/Login.js
import React, { useState } from 'react';
import './Login.css';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = (event) => {
    event.preventDefault();

    // Simple validation (you can replace this with real validation logic)
    if (!email || !password) {
      setError('Please enter both email and password.');
    } else {
      setError('');
      // Call your API or login logic here
      console.log('Login submitted:', { email, password });
    }
  };

  return (
    <div className="login-page">
      <form className="login-form" onSubmit={handleLogin}>
        <h2>Login to connect your Google Calendar</h2>

        {/* Error message */}
        {error && <p className="error-message">{error}</p>}

        {/* Email Input */}
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
          />
        </div>

        {/* Password Input */}
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
          />
        </div>

        {/* Submit Button */}
        <button type="submit" className="login-button">Login</button>
      </form>
    </div>
  );
};

export default LoginPage;
