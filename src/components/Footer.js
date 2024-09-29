import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Footer.css';

const Footer = () => {
  const [isHidden, setIsHidden] = useState(true);
  const [ticking, setTicking] = useState(false);

  const handleScroll = () => {
    const scrollPosition = window.scrollY + window.innerHeight;
    const threshold = document.documentElement.scrollHeight - document.querySelector('.footer').clientHeight + 50;

    if (scrollPosition >= threshold) {
      if (isHidden) {
        setIsHidden(false);
      }
    } else {
      if (!isHidden) {
        setIsHidden(true);
      }
    }
    setTicking(false);
  };

  const onScroll = () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        handleScroll();
      });
      setTicking(true);
    }
  };

  useEffect(() => {
    window.addEventListener('scroll', onScroll);
    handleScroll(); // Initial check to set visibility
    return () => {
      window.removeEventListener('scroll', onScroll);
    };
  }, [isHidden]);

  return (
    <footer className={`footer ${!isHidden ? 'footer-visible' : ''}`}>
      <div className="footer-content">
        <div className="footer-links">
          <div className="footer-column">
            <Link to="/about"><button>About</button></Link>
          </div>
          <div className="footer-column">
            <Link to="/"><button>Home</button></Link>
            <Link to="/login"><button>Login</button></Link>
          </div>
        </div>
        <div className="footer-contact">
          <h3>Contact Us</h3>
          <h4>Email: support@_____.com</h4>
          <h4>Phone: (123) 456-7890</h4>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
