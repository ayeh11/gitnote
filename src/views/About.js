// src/About.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './About.css';

function About() {
  const [name, setName] = useState('');
  const [value, setValue] = useState('');
  const [responseMessage, setResponseMessage] = useState('');
  const [dataList, setDataList] = useState([]); // Initial state set to an empty array

  // Function to handle form submission and post data to the backend
  const postData = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post('http://localhost:5001/api/add', {
        name: name,
        value: value,
      });
      setResponseMessage(response.data.message);
      fetchData(); // Fetch the updated data after adding a new entry
    } catch (error) {
      console.error('Error posting data:', error);
      setResponseMessage('Failed to submit data.');
    }
  };

  // Function to fetch stored data from the backend
  const fetchData = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/data');
      console.log('Fetched data:', response.data); // Log the fetched data to verify it's an array
      setDataList(response.data || []); // Ensure the response is an array
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  // Fetch data when the component mounts
  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="about-container">
      <h1>About Us</h1>
      <p>
        This is the About page of the website. Here you can provide details about your website, team, or mission.
      </p>

      {/* Form to take user input */}
      <form onSubmit={postData}>
        <div>
          <label htmlFor="name">Name:</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)} // Update the name state on input change
            required
          />
        </div>

        <div>
          <label htmlFor="value">Value:</label>
          <input
            type="text"
            id="value"
            value={value}
            onChange={(e) => setValue(e.target.value)} // Update the value state on input change
            required
          />
        </div>

        <button className="submit-button" type="submit">Submit</button>
      </form>

      {/* Display response message from the backend */}
      {responseMessage && (
        <p className={responseMessage.includes('Failed') ? 'error' : ''}>{responseMessage}</p>
      )}

      {/* Display the stored data */}
      <h2>Stored Data</h2>
      <ul>
        {Array.isArray(dataList) && dataList.map((item, index) => (
          <li key={index}>
            Name: {item.name}, Value: {item.value}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default About;
