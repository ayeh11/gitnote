import React, { useState } from 'react';
import axios from 'axios';
import './Upload.css';
import { useNavigate } from 'react-router-dom';

const UploadPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const navigate = useNavigate();

  // Handle file selection
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  // Handle file upload
  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!selectedFile) {
      alert('Please select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('http://localhost:5001/upload', formData);
      setUploadStatus('File uploaded successfully!');

      // Redirect to conflict resolution page after successful upload
      navigate('/resolve-conflicts'); 
    } catch (error) {
      console.error('Error uploading file:', error);
      setUploadStatus('Error uploading file. Please try again.');
    }
  };

  return (
    <div className="upload-container">
      <h1>Upload Your Files</h1>
      <form onSubmit={handleSubmit}>
        <input type="file" onChange={handleFileChange} />
        <button type="submit" className="upload-button">Upload File</button>
      </form>
      <div>{uploadStatus}</div>
    </div>
  );
};

export default UploadPage;
