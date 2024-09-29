// src/Home.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import './Home.css';


function HomePage() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    // Fetch data from the backend
    axios.get('http://localhost:5001/api/data')
      .then(response => {
        setMessage(response.data.message);
      })
      .catch(error => {
        console.error('Error fetching data:', error);
      });
  }, []);

  return (
    <div className="homepage">
      {/* Main Section */}
      <div className="intro">
        <div className="intro-content">
          <h1>Main Line</h1>
          <p>{message}</p>
          <Link to="/about">
            <button className="cta-button">About</button>
          </Link>
        </div>
      </div>

      {/* Features Section */}
      <div className="features">
        <h2>Features</h2>
        <div className="features-list">
          <div className="feature">
            <img src="https://via.placeholder.com/150" alt="Feature #1" />
            <h3>Feature #1</h3>
            <p>blah blah blah</p>
          </div>
          <div className="feature">
            <img src="https://via.placeholder.com/150" alt="Feature #2" />
            <h3>Feature #2</h3>
            <p>blah blah blah</p>
          </div>
          <div className="feature">
            <img src="https://via.placeholder.com/150" alt="Feature #3" />
            <h3>Feature #3</h3>
            <p>blah blah blah</p>
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div className="cta-section">
        <h2>Call to action</h2>
        <Link to="/login">
            <button className="cta-button">Join Today</button>
        </Link>
      </div>
    </div>
  );
};

export default HomePage;
