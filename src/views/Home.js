import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Home.css';

function HomePage() {
  const [displayText, setDisplayText] = useState(''); // Text shown in the terminal
  const [userInput, setUserInput] = useState(''); // The user's current command
  const [isTypingComplete, setIsTypingComplete] = useState(false); // Track if initial text is typed
  const [errorMessage, setErrorMessage] = useState(''); // Error message display
  const navigate = useNavigate(); // React Router's navigate function for redirection

  // Typewriter effect for "Welcome to NoteMerge"
  useEffect(() => {
    const welcomeText = 'Welcome to NoteMerge\n';

    let currentText = '';
    let index = 0;

    const typeText = () => {
      if (index < welcomeText.length) {
        currentText += welcomeText.charAt(index);
        setDisplayText(currentText);
        index++;
        setTimeout(typeText, 100); // Adjust speed here
      } else {
        setIsTypingComplete(true); // Mark typing as complete after the welcome message
      }
    };

    typeText();
  }, []);

  // Handle user input when they type in the terminal
  const handleUserInput = (e) => {
    const { key, keyCode } = e;

    if (isTypingComplete) {
      if (keyCode === 13) {
        // If the user presses "Enter", process the command with a slight delay for consistency
        e.preventDefault();
        processCommand();
      } else if (keyCode === 8) {
        // If the user presses "Backspace"
        setUserInput((prev) => prev.slice(0, -1));
      } else if (key.length === 1) {
        // Append characters to the command
        setUserInput((prev) => prev + key);
      }
    }
  };

  // Process the user command
  const processCommand = () => {
    const trimmedInput = userInput.trim();

    if (trimmedInput === 'git upload') {
      // Add a slight delay to allow input state updates to complete before navigation
      setTimeout(() => {
        console.log('Navigating to /upload...');
        navigate('/upload'); // Perform navigation
      }, 100); // Slight delay ensures the navigation is triggered after all updates
    } else if (trimmedInput === 'git help') {
      // If the user typed "git help", display the help message and reset error
      setDisplayText((prev) => prev + `\nAvailable commands:\n  git upload: upload a file\n> `);
      setUserInput(''); // Clear the input
      setErrorMessage(''); // Clear the error message
    } else {
      // Invalid command, display error message but do not clear it on typing
      setErrorMessage(`error: type in git help for help`); 
      setDisplayText((prev) => prev + `\n> ${userInput}\n`); // Display invalid command in terminal
      setUserInput(''); // Clear the input, but keep the error
    }
  };

  // Enable keyboard input (useEffect to add/remove event listeners)
  useEffect(() => {
    window.addEventListener('keydown', handleUserInput);

    return () => {
      window.removeEventListener('keydown', handleUserInput);
    };
  }, [userInput, isTypingComplete]); // Track the current input and typing completion

  return (
    <div className="terminal-container">
      <div className="terminal-content">
        <pre>{displayText}</pre>
        <div className="prompt-line">
          <span>&gt; {userInput}</span>
          <span className="blinking-cursor"></span>
        </div>
        {errorMessage && <div className="error-line">{errorMessage}</div>} {/* Show the error message */}
      </div>
    </div>
  );
}

export default HomePage;
