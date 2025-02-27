import React, { useState, useEffect } from 'react';
import './App.css';
import Confetti from 'react-confetti';
import Settings from './Settings';
import { useAppContext } from './AppContext';
import useSound from './SoundManager';
import useKeyboardInput from './KeyboardController';
import QuoteAttribution from './QuoteAttribution';
import { createStructuralMatch } from './utils';
import SaveButton from './SaveButton';

function App() {
  // ==== CONTEXT AND APP SETTINGS ====
  const { 
    settings, 
    updateSettings, 
    currentView, 
    showSettings, 
    showGame,
    maxMistakes 
  } = useAppContext();

  // ==== STATE DECLARATIONS ====
  const [encrypted, setEncrypted] = useState('');
  const [display, setDisplay] = useState('');
  const [mistakes, setMistakes] = useState(0);
  const [correctlyGuessed, setCorrectlyGuessed] = useState([]);
  const [selectedEncrypted, setSelectedEncrypted] = useState(null);
  const [lastCorrectGuess, setLastCorrectGuess] = useState(null);
  const [letterFrequency, setLetterFrequency] = useState({});
  const [guessedMappings, setGuessedMappings] = useState({});
  const [originalLetters, setOriginalLetters] = useState([]);

  // ==== DERIVED VALUES AND CALCULATIONS ====
  // Get unique encrypted letters that actually appear in the encrypted text
  const encryptedLetters = [...new Set(encrypted.match(/[A-Z]/g) || [])];
  const uniqueEncryptedLetters = encryptedLetters.length;
  
  // Calculate if all encrypted letters have been correctly guessed
  const hasWon = uniqueEncryptedLetters > 0 && correctlyGuessed.length >= uniqueEncryptedLetters;
  
  // Get used letters for display
  const usedGuessLetters = Object.values(guessedMappings);

  // ==== UTILITY FUNCTIONS ====
  // Initialize sound manager
  const { playSound } = useSound();

  // ==== GAME FUNCTIONS ====
  const startGame = () => {
    fetch('/start')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        setEncrypted(data.encrypted_paragraph);
        setDisplay(data.display);
        setMistakes(data.mistakes);
        setCorrectlyGuessed([]);
        setLetterFrequency(data.letter_frequency);
        setSelectedEncrypted(null);
        setLastCorrectGuess(null);
        setGuessedMappings({});
        setOriginalLetters(data.original_letters);
        playSound('keyclick');
      })
      .catch(err => console.error('Error starting game:', err));
  };

  const handleEncryptedClick = (letter) => {
    if (!correctlyGuessed.includes(letter)) {
      setSelectedEncrypted(letter);
      playSound('keyclick');
    }
  };

  const handleGuessClick = (guessedLetter) => {
    if (selectedEncrypted) {
      submitGuess(guessedLetter);
    }
  };

  const submitGuess = (guessedLetter) => {
    fetch('/guess', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        encrypted_letter: selectedEncrypted,
        guessed_letter: guessedLetter.toUpperCase()
      })
    })
      .then(res => res.json())
      .then(data => {
        setDisplay(data.display);
        setMistakes(data.mistakes);
        setCorrectlyGuessed(data.correctly_guessed);
        if (data.correctly_guessed.includes(selectedEncrypted) && 
            !correctlyGuessed.includes(selectedEncrypted)) {
          playSound('correct');
          setLastCorrectGuess(selectedEncrypted);
          setGuessedMappings(prev => ({
            ...prev,
            [selectedEncrypted]: guessedLetter.toUpperCase()
          }));
          setTimeout(() => setLastCorrectGuess(null), 500);
        }
        else if (data.mistakes > mistakes) {
          playSound('incorrect');
        }
        setSelectedEncrypted(null);
      })
      .catch(err => console.error('Error guessing:', err));
  };

  const handleHint = () => {
    fetch('/hint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
      .then(res => res.json())
      .then(data => {
        // Store old state for comparison
        const oldCorrectlyGuessed = [...correctlyGuessed];
        
        // Update state with server response
        setDisplay(data.display);
        setMistakes(data.mistakes);
        
        if (data.correctly_guessed) {
          // Find which letter is newly added (the hint)
          const newGuessedLetters = data.correctly_guessed.filter(
            letter => !oldCorrectlyGuessed.includes(letter)
          );
          
          // For each newly guessed letter, update the mapping
          newGuessedLetters.forEach(encryptedLetter => {
            // Find this letter in the encrypted text and get the corresponding character in display
            for (let i = 0; i < encrypted.length; i++) {
              if (encrypted[i] === encryptedLetter && data.display[i] !== '?') {
                // Add to guessedMappings
                setGuessedMappings(prev => ({
                  ...prev,
                  [encryptedLetter]: data.display[i]
                }));
                break;
              }
            }
          });
          
          // Update correctlyGuessed state
          setCorrectlyGuessed(data.correctly_guessed);
        }
      })
      .catch(err => console.error('Error getting hint:', err));
  };

  // Create a structurally identical display text
  // const createStructuralMatch = () => {
  //   if (!encrypted || !display) return { __html: '' };
    
  //   // Extract only the letters from the display text (removing spaces/punctuation)
  //   const displayLetters = display.replace(/[^A-Z?]/g, '');
  //   let letterIndex = 0;
  //   let structuredDisplay = '';
    
  //   // Iterate through encrypted text and replace only the letters
  //   for (let i = 0; i < encrypted.length; i++) {
  //     const char = encrypted[i];
  //     if (/[A-Z]/.test(char)) {
  //       // If it's a letter, use the corresponding character from display
  //       if (letterIndex < displayLetters.length) {
  //         structuredDisplay += displayLetters[letterIndex];
  //         letterIndex++;
  //       } else {
  //         structuredDisplay += '?';
  //       }
  //     } else {
  //       // For non-letters (spaces, punctuation), keep the original character
  //       structuredDisplay += char;
  //     }
  //   }
    
  //   return { __html: structuredDisplay };
  // };

  // ==== KEYBOARD INPUT HANDLERS ====
  const handleEncryptedSelect = (letter) => {
    setSelectedEncrypted(letter);
    if (letter) {
      playSound('keyclick');
    }
  };
  
  const handleGuessSubmit = (guessedLetter) => {
    if (selectedEncrypted) {
      submitGuess(guessedLetter);
    }
  };

  // ==== EFFECTS ====
  // Initialize game on component mount
  useEffect(() => {
    startGame();
  }, []);

  // Keyboard input handling
  useKeyboardInput({
    enabled: !hasWon && mistakes < maxMistakes, // Disable when game is over
    speedMode: settings.speedMode,
    encryptedLetters: encryptedLetters,
    originalLetters: originalLetters,
    selectedEncrypted: selectedEncrypted,
    onEncryptedSelect: handleEncryptedSelect,
    onGuessSubmit: handleGuessSubmit,
    playSound: playSound
  });

  // Play win sound when game is won
  useEffect(() => {
    if (hasWon) {
      playSound('win');
    } 
    console.log('Win check:', { 
      uniqueLetters: uniqueEncryptedLetters, 
      correctlyGuessedLength: correctlyGuessed.length,
      hasWon: hasWon
    });
  }, [correctlyGuessed, uniqueEncryptedLetters, hasWon]);

  // Apply theme effect - this runs for both game and settings views
  useEffect(() => {
    if (settings.theme === 'dark') {
      document.documentElement.classList.add('dark-theme');
      document.body.classList.add('dark-theme');
    } else {
      document.documentElement.classList.remove('dark-theme');
      document.body.classList.remove('dark-theme');
    }
  }, [settings.theme]);

  // ==== SETTINGS HANDLERS ====
  // Handle settings update
  const handleSaveSettings = (newSettings) => {
    updateSettings(newSettings);
    showGame();
  };

  // ==== CONDITIONAL RENDERING ====
  // When in settings view
  if (currentView === 'settings') {
    return (
      <div className={`App-container ${settings.theme === 'dark' ? 'dark-theme' : ''}`}>
        <Settings 
          currentSettings={settings} 
          onSave={handleSaveSettings} 
          onCancel={showGame} 
        />
      </div>
    );
  }

  // ==== MAIN RENDER ====
  // Game view
  return (
    <div className={`App-container ${settings.theme === 'dark' ? 'dark-theme' : ''}`}>
      <div className={`App ${settings.theme === 'dark' ? 'dark-theme' : ''} text-${settings.textColor}`} >
        <div className="game-header">
          <h1 className="game-title">Decrypto</h1>
          <button className="settings-icon" onClick={showSettings} aria-label="Settings">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
          </button>
        </div>

        {hasWon && <Confetti width={window.innerWidth} height={window.innerHeight} recycle={false} />}
        
        <div className="text-container">
          <pre className="encrypted">{encrypted || 'Loading...'}</pre>
          <pre className="display" dangerouslySetInnerHTML={createStructuralMatch(encrypted, display)}></pre>
        </div>
        <QuoteAttribution 
            hasWon={hasWon} 
            theme={settings.theme} 
            textColor={settings.textColor} 
          />

        <div className="grids">
          <div className="encrypted-grid">
            {encryptedLetters.map(letter => (
              <div
                key={letter}
                className={`letter-cell ${selectedEncrypted === letter ? 'selected' : ''} ${
                  correctlyGuessed.includes(letter) ? 'guessed' : ''
                } ${lastCorrectGuess === letter ? 'flash' : ''}`}
                onClick={() => handleEncryptedClick(letter)}
              >
                {letter}
              </div>
            ))}
          </div>
   

  
          <div className="guess-grid">
            {originalLetters.map(letter => (
              <div
                key={letter}
                className={`letter-cell ${usedGuessLetters.includes(letter) ? 'guessed' : ''}`}
                onClick={() => handleGuessClick(letter)}
              >
                {letter}
              </div>
            ))}
          </div>
        </div>

        <div className="controls">
          <p>Mistakes: {mistakes}/{maxMistakes}</p>
          <button 
            onClick={handleHint} 
            disabled={mistakes >= maxMistakes - 1}
            className="hint-button"
          >
            Hint (Costs 1 Mistake)
          </button>
        </div>

        {settings.speedMode && (
          <div className="keyboard-hint">
            <p>
              Keyboard Speed Mode: 
              {!selectedEncrypted 
                ? "Press a letter key to select from the encrypted grid." 
                : `Selected ${selectedEncrypted} - Press a letter key to make a guess or ESC to cancel.`}
            </p>
          </div>
        )}

        <div className="sidebar">
          {Array.from('ABCDEFGHIJKLMNOPQRSTUVWXYZ').map(letter => (
            <div key={letter} className="frequency-bar">
              <span className={usedGuessLetters.includes(letter) ? 'guessed' : ''}>{letter}</span>
              {settings.frequencyDisplay === 'numeric' ? (
                <span className={usedGuessLetters.includes(letter) ? 'guessed' : ''}>
                  {letterFrequency[letter] || 0}
                </span>
              ) : (
                <div
                  className={`bar ${usedGuessLetters.includes(letter) ? 'guessed' : ''}`}
                  style={{ height: `${(letterFrequency[letter] || 0) * 10}px` }}
                ></div>
              )}
            </div>
          ))}
        </div>

            {hasWon ? (
      <div className="game-message">
        <p>You won! All unique letters decrypted.</p>
        <SaveButton hasWon={hasWon} playSound={playSound} />
        <button onClick={startGame}>Play Again</button>
      </div>
    ) : mistakes >= maxMistakes ? (
      <div className="game-message">
        <p>Game Over! Too many mistakes.</p>
        <button onClick={startGame}>Try Again</button>
      </div>
    ) : null}
      </div>
    </div>
  );
}

export default App;