import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ConflictResolution.css';

const ConflictResolutionPage = () => {
  const [mergedResults, setMergedResults] = useState(null); // Stores merged results from backend
  const [resolutions, setResolutions] = useState({}); // Tracks user's resolutions
  const [loading, setLoading] = useState(false);
  const [mergedNotes, setMergedNotes] = useState(''); // Real-time merged notes
  const [confirmation, setConfirmation] = useState(''); // Confirmation message
  
  // Fetch conflicts from backend (runs Python script)
  const fetchConflicts = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5001/run-test-client');
      const results = JSON.parse(response.data.output);
      setMergedResults(results); // Parse the JSON from Python
      setMergedNotes(results.merged_text); // Initialize with base merged text
      setLoading(false);
      setConfirmation('Conflicts fetched successfully!');
    } catch (error) {
      console.error('Error fetching conflicts:', error);
      setLoading(false);
    }
  };

  // Handle resolution choice for headers and bullets
  const handleResolution = (type, headerId, bulletId, resolution, text) => {
    const key = `${headerId}-${bulletId || 'header'}`; // Use both header and bullet id to track resolution

    // Update resolutions state
    setResolutions((prevResolutions) => ({
      ...prevResolutions,
      [key]: { resolution, text },
    }));

    // Update the merged text in real-time
    updateMergedNotes(headerId, bulletId, resolution, text);
    
    setConfirmation(`You resolved conflict for ${type === 'header' ? 'Header' : 'Bullet'} ${headerId} with resolution: ${resolution}`);
  };

  // Function to update the merged text when a resolution is chosen
  const updateMergedNotes = (headerId, bulletId, resolution, resolvedText) => {
    // Create a copy of the current merged text
    let updatedMergedNotes = mergedNotes;

    // If the user selects 'both', we concatenate the conflicting text
    if (resolution === 'both') {
      const conflictText = mergedResults.headers
        .find(header => header.header_id === headerId)
        ?.bullets.find(bullet => bullet.bullet_id === bulletId)?.conflicts[0]?.text || '';

      updatedMergedNotes = updatedMergedNotes.replace(
        new RegExp(`${resolvedText}`),
        `${resolvedText}\n${conflictText}`
      );
    } else if (resolution === 'none') {
      updatedMergedNotes = updatedMergedNotes.replace(
        new RegExp(`${resolvedText}`),
        ''
      );
    } else {
      // Replace original/conflicting bullet text
      updatedMergedNotes = updatedMergedNotes.replace(
        new RegExp(`${resolvedText}`),
        resolvedText
      );
    }

    // Update the mergedNotes state
    setMergedNotes(updatedMergedNotes);
  };

  // Render only sections with conflicts
  const renderConflicts = () => {
    if (!mergedResults) return null;

    return (
      <>
        {mergedResults.headers.map((header) => {
          const hasHeaderConflicts = header.conflicts && header.conflicts.length > 0;
          const hasBulletConflicts = header.bullets.some((bullet) => bullet.conflicts && bullet.conflicts.length > 0);

          // Skip if neither header nor bullet has conflicts
          if (!hasHeaderConflicts && !hasBulletConflicts) return null;

          return (
            <div key={header.header_id} className="conflict-block">
              <h3>{header.header_name}</h3>

              {/* Header conflict resolution */}
              {hasHeaderConflicts && (
                <div className="conflict">
                  <div className="version theirs">
                    <h4>Original Header</h4>
                    <pre>{header.header_name}</pre>
                    <button
                      className={resolutions[`${header.header_id}-header`] === 'theirs' ? 'selected' : ''}
                      onClick={() => handleResolution('header', header.header_id, null, 'theirs', header.header_name)}
                    >
                      Accept Original Header
                    </button>
                  </div>

                  {header.conflicts.map((conflict, index) => (
                    <div className="version incoming" key={index}>
                      <h4>Conflicting Header</h4>
                      <pre>{conflict.header_name}</pre>
                      <button
                        className={resolutions[`${header.header_id}-header`] === 'incoming' ? 'selected' : ''}
                        onClick={() => handleResolution('header', header.header_id, null, 'incoming', conflict.header_name)}
                      >
                        Accept Conflicting Header
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Bullet conflict resolution */}
              {header.bullets.map((bullet) => {
                if (!bullet.conflicts || bullet.conflicts.length === 0) return null;

                return (
                  <div key={bullet.bullet_id} className="bullet-block">
                    <div className="conflict">
                      <div className="version theirs">
                        <h4>Original Bullet</h4>
                        <pre>{bullet.text}</pre>
                        <button
                          className={resolutions[`${header.header_id}-${bullet.bullet_id}`] === 'theirs' ? 'selected' : ''}
                          onClick={() => handleResolution('bullet', header.header_id, bullet.bullet_id, 'theirs', bullet.text)}
                        >
                          Accept Original Bullet
                        </button>
                      </div>

                      {bullet.conflicts.map((conflict, index) => (
                        <div className="version incoming" key={index}>
                          <h4>Conflicting Bullet</h4>
                          <pre>{conflict.text}</pre>
                          <button
                            className={resolutions[`${header.header_id}-${bullet.bullet_id}`] === 'incoming' ? 'selected' : ''}
                            onClick={() => handleResolution('bullet', header.header_id, bullet.bullet_id, 'incoming', conflict.text)}
                          >
                            Accept Conflicting Bullet
                          </button>
                        </div>
                      ))}
                    </div>

                    <div className="resolve-options">
                      <button
                        className={resolutions[`${header.header_id}-${bullet.bullet_id}`] === 'both' ? 'selected' : ''}
                        onClick={() => handleResolution('bullet', header.header_id, bullet.bullet_id, 'both', bullet.text)}
                      >
                        Accept Both
                      </button>
                      <button
                        className={resolutions[`${header.header_id}-${bullet.bullet_id}`] === 'none' ? 'selected' : ''}
                        onClick={() => handleResolution('bullet', header.header_id, bullet.bullet_id, 'none', bullet.text)}
                      >
                        Accept None
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </>
    );
  };

  return (
    <div className="conflict-container">
      <h1>Resolve Merge Conflicts</h1>

      <button className="run-button" onClick={fetchConflicts} disabled={loading}>
        {loading ? 'Fetching conflicts...' : 'Fetch Conflicts'}
      </button>

      {confirmation && <p className="confirmation">{confirmation}</p>}

      {mergedResults && (
        <>
          <h2>Merged Text</h2>
          <pre className="merged-text">{mergedNotes}</pre>

          {renderConflicts()}

          {Object.keys(resolutions).length > 0 && (
            <button className="submit-button" onClick={() => console.log('Final Merged Notes:', mergedNotes)}>
              Resolve and Submit
            </button>
          )}
        </>
      )}

      {!mergedResults && !loading && <p>No conflicts to resolve. Please fetch conflicts.</p>}
    </div>
  );
};

export default ConflictResolutionPage;
