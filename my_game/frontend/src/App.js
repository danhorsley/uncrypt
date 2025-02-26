import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [encrypted, setEncrypted] = useState('');
  const [display, setDisplay] = useState('');
  const [mistakes, setMistakes] = useState(0);
  const [correctlyGuessed, setCorrectlyGuessed] = useState([]);
  const [encryptedLetter, setEncryptedLetter] = useState('');
  const [guessedLetter, setGuessedLetter] = useState('');
  const [letterFrequency, setLetterFrequency] = useState({});
  const [original, setOriginal] = useState('');  // Store original for win check
  const maxMistakes = 5;

  const startGame = () => {
    console.log('Fetching /start...');
    fetch('/start')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        console.log('Received:', data);
        setEncrypted(data.encrypted_paragraph);
        setDisplay(data.encrypted_paragraph);
        setMistakes(data.mistakes);
        setCorrectlyGuessed([]);
        setLetterFrequency(data.letter_frequency);
        // Temp: Guess all letters to get original (for testing; remove later)
        fetch('/guess', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ encrypted_letter: 'A', guessed_letter: 'A' })  // Dummy guess
        })
          .then(res => res.json())
          .then(data => setOriginal(data.display.replace(/[^A-Z ]/g, '')));  // Hack for now
      })
      .catch(err => console.error('Error starting game:', err));
  };

  useEffect(() => {
    startGame();
  }, []);

  const handleGuess = () => {
    if (encryptedLetter && guessedLetter) {
      fetch('/guess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          encrypted_letter: encryptedLetter.toUpperCase(),
          guessed_letter: guessedLetter.toUpperCase()
        })
      })
        .then(res => res.json())
        .then(data => {
          setDisplay(data.display);
          setMistakes(data.mistakes);
          setCorrectlyGuessed(data.correctly_guessed);
          setEncryptedLetter('');
          setGuessedLetter('');
        })
        .catch(err => console.error('Error guessing:', err));
    }
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

  // Win condition: all unique encrypted letters guessed, and display matches original
  const uniqueEncryptedLetters = Object.keys(letterFrequency).length;
  const hasWon = correctlyGuessed.length === uniqueEncryptedLetters; //&& 
              //   display.replace(/[^A-Z ]/g, '') === original && 
               //  uniqueEncryptedLetters > 0;

  return (
    <div className="App">
      <h1>Decrypt the Puzzle</h1>
      <p className="encrypted">Encrypted: {encrypted || 'Loading...'}</p>
      <p className="display">Decoding: {display || 'Loading...'}</p>
      <p>Mistakes: {mistakes}/{maxMistakes}</p>
      <p>
        Letter Frequency: {Object.entries(letterFrequency)
          .map(([letter, count]) => `${letter}:${count}`)
          .join(', ')}
      </p>
      
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
      ) : (
        <div>
          <input
            type="text"
            maxLength="1"
            value={encryptedLetter}
            onChange={(e) => setEncryptedLetter(e.target.value)}
            placeholder="Encrypted letter"
          />
          <input
            type="text"
            maxLength="1"
            value={guessedLetter}
            onChange={(e) => setGuessedLetter(e.target.value)}
            placeholder="Guessed letter"
          />
          <button onClick={handleGuess}>Guess</button>
          <button onClick={handleHint} disabled={mistakes >= maxMistakes - 1}>
            Hint (Costs 1 Mistake)
          </button>
        </div>
      )}
    </div>
  );
}

export default App;