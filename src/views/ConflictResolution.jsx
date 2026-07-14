import React, { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './ConflictResolution.css';

// Build the final merged document from the user's choices.
// resolutions maps a key -> selected option:
//   header key `h:<header_id>`  -> 'accepted' | 'c<idx>'
//   bullet key `b:<header_id>:<bullet_id>` -> 'accepted' | 'c<idx>' | 'both' | 'none'
function buildDocument(result, resolutions) {
  const lines = [];
  for (const header of result.headers) {
    const hKey = `h:${header.header_id}`;
    const hChoice = resolutions[hKey] || 'accepted';
    const headerName =
      hChoice === 'accepted'
        ? header.header_name
        : header.conflicting_headers[Number(hChoice.slice(1))]?.header_name ||
          header.header_name;
    lines.push(`${headerName}:`);

    for (const bullet of header.bullets) {
      const bKey = `b:${header.header_id}:${bullet.bullet_id}`;
      const choice = resolutions[bKey] || 'accepted';
      if (choice === 'none') continue;
      if (choice === 'both') {
        lines.push(`- ${bullet.text}`);
        bullet.conflicting_bullets.forEach((c) => lines.push(`- ${c.text}`));
      } else if (choice === 'accepted') {
        lines.push(`- ${bullet.text}`);
      } else {
        const c = bullet.conflicting_bullets[Number(choice.slice(1))];
        lines.push(`- ${c ? c.text : bullet.text}`);
      }
    }
  }
  return lines.join('\n');
}

const ConflictResolutionPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const result = location.state?.result;

  const [resolutions, setResolutions] = useState({});
  const [copied, setCopied] = useState(false);

  const finalDocument = useMemo(
    () => (result ? buildDocument(result, resolutions) : ''),
    [result, resolutions]
  );

  const choose = (key, value) => {
    setResolutions((prev) => ({ ...prev, [key]: value }));
    setCopied(false);
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(finalDocument);
    setCopied(true);
  };

  const handleDownload = () => {
    const blob = new Blob([finalDocument], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'merged-notes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!result) {
    return (
      <div className="conflict-container">
        <h1>Resolve Merge Conflicts</h1>
        <p>No merge result to show. Upload your notes first.</p>
        <button className="run-button" onClick={() => navigate('/upload')}>
          Go to Upload
        </button>
      </div>
    );
  }

  const conflictHeaders = result.headers.filter(
    (h) =>
      h.conflicting_headers.length > 0 ||
      h.bullets.some((b) => b.conflicting_bullets.length > 0)
  );

  return (
    <div className="conflict-container">
      <h1>Resolve Merge Conflicts</h1>

      {conflictHeaders.length === 0 ? (
        <p className="confirmation">No conflicts found — your notes merged cleanly.</p>
      ) : (
        conflictHeaders.map((header) => (
          <div key={header.header_id} className="conflict-block">
            <h3>{header.header_name}</h3>

            {header.conflicting_headers.length > 0 && (
              <div className="conflict">
                <div className="version theirs">
                  <h4>Header (accepted)</h4>
                  <pre>{header.header_name}</pre>
                  <button
                    className={
                      (resolutions[`h:${header.header_id}`] || 'accepted') === 'accepted'
                        ? 'selected'
                        : ''
                    }
                    onClick={() => choose(`h:${header.header_id}`, 'accepted')}
                  >
                    Keep this
                  </button>
                </div>
                {header.conflicting_headers.map((c, idx) => (
                  <div className="version incoming" key={idx}>
                    <h4>Alternative header</h4>
                    <pre>{c.header_name}</pre>
                    <button
                      className={
                        resolutions[`h:${header.header_id}`] === `c${idx}` ? 'selected' : ''
                      }
                      onClick={() => choose(`h:${header.header_id}`, `c${idx}`)}
                    >
                      Use this
                    </button>
                  </div>
                ))}
              </div>
            )}

            {header.bullets
              .filter((b) => b.conflicting_bullets.length > 0)
              .map((bullet) => {
                const key = `b:${header.header_id}:${bullet.bullet_id}`;
                const current = resolutions[key] || 'accepted';
                return (
                  <div key={bullet.bullet_id} className="bullet-block">
                    <div className="conflict">
                      <div className="version theirs">
                        <h4>Bullet (accepted)</h4>
                        <pre>{bullet.text}</pre>
                        <button
                          className={current === 'accepted' ? 'selected' : ''}
                          onClick={() => choose(key, 'accepted')}
                        >
                          Keep this
                        </button>
                      </div>
                      {bullet.conflicting_bullets.map((c, idx) => (
                        <div className="version incoming" key={idx}>
                          <h4>Alternative bullet</h4>
                          <pre>{c.text}</pre>
                          <button
                            className={current === `c${idx}` ? 'selected' : ''}
                            onClick={() => choose(key, `c${idx}`)}
                          >
                            Use this
                          </button>
                        </div>
                      ))}
                    </div>
                    <div className="resolve-options">
                      <button
                        className={current === 'both' ? 'selected' : ''}
                        onClick={() => choose(key, 'both')}
                      >
                        Keep both
                      </button>
                      <button
                        className={current === 'none' ? 'selected' : ''}
                        onClick={() => choose(key, 'none')}
                      >
                        Drop both
                      </button>
                    </div>
                  </div>
                );
              })}
          </div>
        ))
      )}

      <h2>Merged Notes</h2>
      <pre className="merged-text">{finalDocument}</pre>

      <div className="resolve-options">
        <button className="submit-button" onClick={handleCopy}>
          {copied ? 'Copied!' : 'Copy to clipboard'}
        </button>
        <button className="submit-button" onClick={handleDownload}>
          Download .txt
        </button>
      </div>
    </div>
  );
};

export default ConflictResolutionPage;
