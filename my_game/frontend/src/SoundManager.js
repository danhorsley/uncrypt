import { useEffect, useRef } from 'react';

const useSound = () => {
  // References to audio elements
  const correctGuessRef = useRef(null);
  const incorrectGuessRef = useRef(null);
  const hintRef = useRef(null);
  const winRef = useRef(null);
  const loseRef = useRef(null);
  const keyClickRef = useRef(null);

  // Initialize audio elements on component mount
  useEffect(() => {
    // Create audio elements
    correctGuessRef.current = new Audio('/sounds/correct.mp3');
    incorrectGuessRef.current = new Audio('/sounds/incorrect.mp3');
    hintRef.current = new Audio('/sounds/hint.mp3');
    winRef.current = new Audio('/sounds/win.mp3');
    loseRef.current = new Audio('/sounds/lose.mp3');
    keyClickRef.current = new Audio('/sounds/keyclick.mp3');
    
    // Set volume
    const setVolume = (audio, volume) => {
      if (audio) audio.volume = volume;
    };
    
    setVolume(correctGuessRef.current, 0.7);
    setVolume(incorrectGuessRef.current, 0.7);
    setVolume(hintRef.current, 0.7);
    setVolume(winRef.current, 0.8);
    setVolume(loseRef.current, 0.8);
    setVolume(keyClickRef.current, 0.5);
    
    // Cleanup function
    return () => {
      // No cleanup needed for Audio objects
    };
  }, []);

  // Function to play a sound
  const playSound = (soundType) => {
    let sound = null;
    
    switch (soundType) {
      case 'correct':
        sound = correctGuessRef.current;
        break;
      case 'incorrect':
        sound = incorrectGuessRef.current;
        break;
      case 'hint':
        sound = hintRef.current;
        break;
      case 'win':
        sound = winRef.current;
        break;
      case 'lose':
        sound = loseRef.current;
        break;
      case 'keyclick':
        sound = keyClickRef.current;
        break;
      default:
        console.error('Unknown sound type:', soundType);
        return;
    }
    
    if (sound) {
      // Reset sound to beginning if it's already playing
      sound.currentTime = 0;
      sound.play().catch(e => {
        // Handle any errors (e.g., if browser requires user interaction first)
        console.warn(`Couldn't play sound ${soundType}:`, e);
      });
    }
  };

  return { playSound };
};

export default useSound;