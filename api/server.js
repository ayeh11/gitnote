const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const { spawn } = require('child_process'); // Import child_process to run Python
const fs = require('fs');
const app = express();
const PORT = 5001;

// Middleware to handle CORS and parse JSON bodies
app.use(cors());
app.use(express.json());

// Serve static files from the 'uploads' folder
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Home Route
app.get('/', (req, res) => {
  res.send('Welcome to the API! Use /api/data to fetch stored data or /api/add to add new data.');
});

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

// Set up multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = 'uploads/';
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir); // Ensure 'uploads' directory exists
    }
    cb(null, uploadDir); // Files will be saved in the 'uploads' folder
  },
  filename: (req, file, cb) => {
    cb(null, file.originalname); // Save files with their original name
  },
});

// Multer middleware for file uploads, allowing only .json files
const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    const filetypes = /json/;
    const extname = filetypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = filetypes.test(file.mimetype);

    if (mimetype && extname) {
      cb(null, true);
    } else {
      cb(new Error('Only .json files are allowed!'));
    }
  },
}).single('file'); // Expecting a single file with field name 'file'

// POST route for file upload (only .json files)
app.post('/upload', (req, res) => {
  upload(req, res, function (err) {
    if (err instanceof multer.MulterError) {
      console.error('Multer error during upload:', err);
      return res.status(500).json({ error: 'Multer error occurred during file upload', details: err.message });
    } else if (err) {
      console.error('Non-Multer error during upload:', err);
      return res.status(400).json({ error: err.message });
    }

    if (!req.file) {
      console.error('No file was uploaded');
      return res.status(400).json({ error: 'No file uploaded.' });
    }

    console.log('File uploaded successfully:', req.file);

    // Return success response after the file is uploaded
    return res.status(200).json({
      message: 'File uploaded successfully!',
      fileName: req.file.originalname,
    });
  });
});

// POST route for running the Python script separately
app.post('/run-test-client', (req, res) => {
  const pythonScriptPath = path.join(__dirname, 'merging', 'test_client.py');
  console.log(`Running Python script: ${pythonScriptPath}`);

  const pythonProcess = spawn('python3', [pythonScriptPath]);

  // Capture Python script stdout
  let pythonOutput = '';
  pythonProcess.stdout.on('data', (data) => {
    pythonOutput += data.toString();
  });

  // Capture Python script stderr (for errors)
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python error: ${data.toString()}`);
    return res.status(500).json({ error: `Error executing Python script: ${data.toString()}` });
  });

  // Handle script completion
  pythonProcess.on('close', (code) => {
    if (code === 0) {
      console.log('Python script executed successfully.');

      // Read the merged results from 'merged_results.json'
      const resultsFile = path.join(__dirname, 'merged_results.json');
      fs.readFile(resultsFile, 'utf8', (err, data) => {
        if (err) {
          console.error('Error reading merged results:', err);
          return res.status(500).json({ error: 'Error reading merged results.' });
        }

        console.log('Merged results:', data);
        return res.status(200).json({
          message: 'Python script executed and processed successfully!',
          output: data,
        });
      });
    } else {
      console.error(`Python script exited with code: ${code}`);
      return res.status(500).json({ error: 'Error executing Python script.' });
    }
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
