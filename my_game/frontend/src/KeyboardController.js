import { useEffect } from 'react';

/**
 * Custom hook to handle keyboard inputs for the Decrypto game
 * 
 * @param {Object} props - Configuration and callback functions
 * @param {boolean} props.enabled - Whether keyboard control is enabled
 * @param {boolean} props.speedMode - Whether speed mode is active
 * @param {Array<string>} props.encryptedLetters - Array of encrypted letters in the grid
 * @param {Array<string>} props.originalLetters - Array of original letters for guessing
 * @param {string|null} props.selectedEncrypted - Currently selected encrypted letter
 * @param {Function} props.onEncryptedSelect - Callback when an encrypted letter is selected
 * @param {Function} props.onGuessSubmit - Callback when a guess is submitted
 * @param {Function} props.playSound - Function to play sound effects
 * @returns {Object} - State of the keyboard input
 */
const useKeyboardInput = ({
  enabled = true,
  speedMode = false,
  encryptedLetters = [],
  originalLetters = [],
  selectedEncrypted = null,
  onEncryptedSelect,
  onGuessSubmit,
  playSound
}) => {
  // Handle all keyboard events
  useEffect(() => {
    if (!enabled) return;

    const handleKeyPress = (event) => {
      const key = event.key.toUpperCase();
      
      // Handle ESC key to deselect
      if (event.key === 'Escape') {
        if (selectedEncrypted) {
          onEncryptedSelect(null);
          playSound('keyclick');
          event.preventDefault();
        }
        return;
      }

      // Check if key is a letter A-Z
      if (/^[A-Z]$/.test(key)) {
        // In speed mode, first press selects from encrypted grid, second submits guess
        if (speedMode) {
          // If no letter is selected, try to select from encrypted grid
          if (!selectedEncrypted) {
            const encryptedLetter = encryptedLetters.find(letter => letter === key);
            if (encryptedLetter) {
              onEncryptedSelect(encryptedLetter);
              playSound('keyclick');
              event.preventDefault();
            }
          } 
          // If a letter is already selected, submit the guess
          else {
            // Check if key is in original letters
            if (originalLetters.includes(key)) {
              onGuessSubmit(key);
              event.preventDefault();
            }
          }
        } 
        // In normal mode, just submit guess if a letter is selected
        else if (selectedEncrypted) {
          onGuessSubmit(key);
          event.preventDefault();
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [
    enabled,
    speedMode,
    encryptedLetters,
    originalLetters,
    selectedEncrypted,
    onEncryptedSelect,
    onGuessSubmit,
    playSound
  ]);

  // Return the current state (could be extended with more state if needed)
  return {
    isActive: enabled,
    speedModeActive: speedMode
  };
};

export default useKeyboardInput;