import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { mergeNotes } from '../api';
import './Upload.css';

const UploadPage = () => {
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    setFiles(Array.from(event.target.files));
    setStatus('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (files.length < 2) {
      setStatus('Please select at least two note files (.json or .pdf) to merge.');
      return;
    }

    setLoading(true);
    setStatus('Merging notes…');
    try {
      const result = await mergeNotes(files);
      // Hand the merged result to the conflict-resolution page via router state,
      // so no server-side session storage is needed.
      navigate('/resolve-conflicts', { state: { result } });
    } catch (error) {
      const detail = error.response?.data?.detail || error.message;
      console.error('Error merging notes:', error);
      setStatus(`Error: ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <h1>Upload Your Notes</h1>
      <p>Select two or more note files (<code>.json</code> or <code>.pdf</code>) to merge.</p>
      <form onSubmit={handleSubmit}>
        <input type="file" multiple accept=".json,.pdf" onChange={handleFileChange} />
        {files.length > 0 && (
          <ul className="file-list">
            {files.map((file) => (
              <li key={file.name}>{file.name}</li>
            ))}
          </ul>
        )}
        <button type="submit" className="upload-button" disabled={loading}>
          {loading ? 'Merging…' : 'Merge Notes'}
        </button>
      </form>
      {status && <div className="upload-status">{status}</div>}
    </div>
  );
};

export default UploadPage;
