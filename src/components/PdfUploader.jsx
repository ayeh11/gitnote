import React, { useState } from "react";
import axios from "axios";

const PdfUploader = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");

  // Handle file selection
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  // Handle file upload
  const handleSubmit = async (event) => {
    event.preventDefault();

    // Ensure that a file is selected
    if (!selectedFile) {
      alert("Please select a PDF file to upload.");
      return;
    }

    // Create FormData object to hold the selected file
    const formData = new FormData();
    formData.append("pdf", selectedFile);

    try {
      // Send the file to the backend using Axios
      const response = await axios.post("http://localhost:5002/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      // Set upload status based on response
      setUploadStatus("File uploaded successfully!");
    } catch (error) {
      console.error("Error uploading file:", error);
      setUploadStatus("Error uploading file. Please try again.");
    }
  };

  return (
    <div>
      <h1>Upload PDF</h1>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="application/pdf" onChange={handleFileChange} />
        <button type="submit">Upload</button>
      </form>
      <div>{uploadStatus}</div>
    </div>
  );
};

export default PdfUploader;
