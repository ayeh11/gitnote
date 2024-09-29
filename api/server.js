// server.js
const express = require('express');
const cors = require('cors');
const app = express();
const PORT = 5001;

// Middleware to handle CORS and parse JSON bodies
app.use(cors());
app.use(express.json());

// Array to store data temporarily (in-memory)
let storedData = [];

// POST endpoint to receive and store data
app.post('/api/add', (req, res) => {
  const { name, value } = req.body;

  // Validate input
  if (!name || !value) {
    return res.status(400).json({ error: 'Name and value are required!' });
  }

  // Add the new entry to the storedData array
  const newData = { name, value };
  storedData.push(newData); // Push the new data to the array

  // Respond with a success message
  res.status(201).json({
    message: 'Data received successfully!',
    receivedData: newData,
  });
});

// GET endpoint to fetch all stored data
app.get('/api/data', (req, res) => {
  res.json(storedData); // Send the storedData array as the response
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
