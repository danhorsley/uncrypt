import React, { useState, useEffect } from 'react';
import './App.css';
import Confetti from 'react-confetti';

function App() {
  const [encrypted, setEncrypted] = useState('');
  const [display, setDisplay] = useState('');
  const [mistakes, setMistakes] = useState(0);
  const [correctlyGuessed, setCorrectlyGuessed] = useState([]);
  const [selectedEncrypted, setSelectedEncrypted] = useState(null);
  const [lastCorrectGuess, setLastCorrectGuess] = useState(null);
  const [letterFrequency, setLetterFrequency] = useState({});
  const [guessedMappings, setGuessedMappings] = useState({});
  const [originalLetters, setOriginalLetters] = useState([]);
  const [showNumbers, setShowNumbers] = useState(false); // Toggle for numbers vs. bars
  const maxMistakes = 5;

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
      })
      .catch(err => console.error('Error starting game:', err));
  };

  useEffect(() => {
    startGame();
  }, []);

  const handleEncryptedClick = (letter) => {
    if (!correctlyGuessed.includes(letter)) {
      setSelectedEncrypted(letter);
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
          setLastCorrectGuess(selectedEncrypted);
          setGuessedMappings(prev => ({
            ...prev,
            [selectedEncrypted]: guessedLetter.toUpperCase()
          }));
          setTimeout(() => setLastCorrectGuess(null), 500);
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
        setDisplay(data.display);
        setMistakes(data.mistakes);
      })
      .catch(err => console.error('Error getting hint:', err));
  };

  // Keyboard input handler
  useEffect(() => {
    const handleKeyPress = (event) => {
      console.log('Key pressed:', event.key); // Debug key detection
      if (selectedEncrypted && /[A-Z]/.test(event.key.toUpperCase())) {
        submitGuess(event.key.toUpperCase());
        event.preventDefault();
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedEncrypted, submitGuess]);

  const uniqueEncryptedLetters = Object.keys(letterFrequency).length;
  console.log('Win check:', { uniqueEncryptedLetters, correctlyGuessedLength: correctlyGuessed.length }); // Debug win
  const hasWon = correctlyGuessed.length === uniqueEncryptedLetters;

  const encryptedLetters = [...new Set(encrypted.match(/[A-Z]/g) || [])];
  const usedGuessLetters = Object.values(guessedMappings);

  return (
    <div className="App">
      <h1>Decrypt the Puzzle</h1>
      {hasWon && <Confetti width={window.innerWidth} height={window.innerHeight} recycle={false} />}
      <p className="encrypted">{encrypted || 'Loading...'}</p>
      <p className="display">{display || 'Loading...'}</p>

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
        <button onClick={() => setShowNumbers(!showNumbers)}>
          {showNumbers ? 'Switch to Bars' : 'Switch to Numbers'}
        </button>
        <p>Mistakes: {mistakes}/{maxMistakes}</p>
        <button onClick={handleHint} disabled={mistakes >= maxMistakes - 1}>
          Hint (Costs 1 Mistake)
        </button>
      </div>

      <div className="sidebar">
        {Array.from('ABCDEFGHIJKLMNOPQRSTUVWXYZ').map(letter => (
          <div key={letter} className="frequency-bar">
            <span className={usedGuessLetters.includes(letter) ? 'guessed' : ''}>{letter}</span>
            {showNumbers ? (
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
        <div>
          <p>You won! All unique letters decrypted.</p>
          <button onClick={startGame}>Play Again</button>
        </div>
      ) : mistakes >= maxMistakes ? (
        <div>
          <p>Game Over! Too many mistakes.</p>
          <button onClick={startGame}>Try Again</button>
        </div>
      ) : null}
    </div>
  );
}

export default App;