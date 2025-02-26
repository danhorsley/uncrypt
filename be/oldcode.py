# from flask_cors import CORS
# CORS(app, resources={r"/*": {"origins": "*"}})

# import React, { useState, useEffect } from 'react';
# import './App.css'; // For styling

# function App() {
#   const [encrypted, setEncrypted] = useState('');
#   const [display, setDisplay] = useState('');
#   const [mistakes, setMistakes] = useState(0);
#   const [correctlyGuessed, setCorrectlyGuessed] = useState([]);
#   const [encryptedLetter, setEncryptedLetter] = useState('');
#   const [guessedLetter, setGuessedLetter] = useState('');
#   const maxMistakes = 5;

#   // Start a new game
#   const startGame = () => {

#     fetch('/start')
#     .then(res => {
#       console.log('Response headers:', res.headers.get('content-type'));  // Check response type
#       if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
#       return res.json();
#     })
#       .then(data => {
#         console.log('Received:', data);
#         setEncrypted(data.encrypted_paragraph);
#         setDisplay(data.encrypted_paragraph);
#         setMistakes(data.mistakes);
#         setCorrectlyGuessed([]);
#       })
#       .catch(err => console.error('Error starting game:', err));
#   };

#   // Load initial game on mount
#   useEffect(() => {
#     startGame();
#   }, []);

#   // Handle guess submission
#   const handleGuess = () => {
#     if (encryptedLetter && guessedLetter) {
#       fetch('/guess', {
#         method: 'POST',
#         headers: { 'Content-Type': 'application/json' },
#         body: JSON.stringify({
#           encrypted_letter: encryptedLetter.toUpperCase(),
#           guessed_letter: guessedLetter.toUpperCase()
#         })
#       })
#         .then(res => res.json())
#         .then(data => {
#           setDisplay(data.display);
#           setMistakes(data.mistakes);
#           setCorrectlyGuessed(data.correctly_guessed);
#           setEncryptedLetter('');
#           setGuessedLetter('');
#         })
#         .catch(err => console.error('Error guessing:', err));
#     }
#   };

#   // Handle hint request
#   const handleHint = () => {
#     fetch('/hint', {
#       method: 'POST',
#       headers: { 'Content-Type': 'application/json' }
#     })
#       .then(res => res.json())
#       .then(data => {
#         setDisplay(data.display);
#         setMistakes(data.mistakes);
#       })
#       .catch(err => console.error('Error getting hint:', err));
#   };

#   // Check win condition
#   const hasWon = display === encrypted.replace(/[^A-Z]/g, '') && encrypted.length > 0;

#   return (
#     <div className="App">
#       <h1>Decrypt the Puzzle</h1>
#       <p className="display">{display || 'Loading...'}</p>
#       <p>Mistakes: {mistakes}/{maxMistakes}</p>
      
#       {hasWon ? (
#         <div>
#           <p>You won! All letters decrypted.</p>
#           <button onClick={startGame}>Play Again</button>
#         </div>
#       ) : mistakes >= maxMistakes ? (
#         <div>
#           <p>Game Over! Too many mistakes.</p>
#           <button onClick={startGame}>Try Again</button>
#         </div>
#       ) : (
#         <div>
#           <input
#             type="text"
#             maxLength="1"
#             value={encryptedLetter}
#             onChange={(e) => setEncryptedLetter(e.target.value)}
#             placeholder="Encrypted letter"
#           />
#           <input
#             type="text"
#             maxLength="1"
#             value={guessedLetter}
#             onChange={(e) => setGuessedLetter(e.target.value)}
#             placeholder="Guessed letter"
#           />
#           <button onClick={handleGuess}>Guess</button>
#           <button onClick={handleHint} disabled={mistakes >= maxMistakes - 1}>
#             Hint (Costs 1 Mistake)
#           </button>
#         </div>
#       )}
#     </div>
#   );
# }

# export default App;