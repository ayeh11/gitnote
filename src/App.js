import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import NavBar from './components/NavBar';
import Footer from './components/Footer';
import Login from './components/Login';
import Home from './views/Home';
import About from './views/About';
import Calendar from './views/Calendar';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <NavBar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/calendar" element={<Calendar />} />
        </Routes>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
