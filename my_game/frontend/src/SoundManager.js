import { useEffect, useRef, useState } from 'react';

const useSound = () => {
  // References to audio elements
  const soundRefs = useRef({
    correct: null,
    incorrect: null,
    hint: null,
    win: null,
    lose: null,
    keyclick: null
  });
  
  // Track loading state
  const [soundsLoaded, setSoundsLoaded] = useState(false);
  const [loadedCount, setLoadedCount] = useState(0);

  // Sound paths - just using MP3 format
  const soundPaths = {
    correct: '/sounds/correct.mp3',
    incorrect: '/sounds/incorrect.mp3',
    hint: '/sounds/hint.mp3',
    win: '/sounds/win.mp3',
    lose: '/sounds/lose.mp3',
    keyclick: '/sounds/keyclick.mp3'
  };

  // Initialize audio elements on component mount
  useEffect(() => {
    // Create audio elements
    const createAudio = (path, volume = 0.7) => {
      const audio = new Audio(path);
      audio.volume = volume;
      audio.preload = 'auto'; // Force preloading
      return audio;
    };
    
    // Initialize each sound with appropriate volume
    soundRefs.current.correct = createAudio(soundPaths.correct, 0.7);
    soundRefs.current.incorrect = createAudio(soundPaths.incorrect, 0.7);
    soundRefs.current.hint = createAudio(soundPaths.hint, 0.7);
    soundRefs.current.win = createAudio(soundPaths.win, 0.8);
    soundRefs.current.lose = createAudio(soundPaths.lose, 0.8);
    soundRefs.current.keyclick = createAudio(soundPaths.keyclick, 0.5);
    
    // Track loaded sounds
    const totalSounds = Object.keys(soundRefs.current).length;
    let loaded = 0;
    
    // Function to mark a sound as loaded
    const handleSoundLoaded = () => {
      loaded++;
      setLoadedCount(loaded);
      
      if (loaded === totalSounds) {
        setSoundsLoaded(true);
        console.log('All sounds loaded successfully');
      }
    };
    
    // Add load event listeners to all sounds
    Object.values(soundRefs.current).forEach(audio => {
      // canplaythrough event fires when the browser estimates it can play through without buffering
      audio.addEventListener('canplaythrough', handleSoundLoaded, { once: true });
      
      // Also handle errors to avoid getting stuck
      audio.addEventListener('error', (e) => {
        console.warn('Error loading sound:', e);
        handleSoundLoaded(); // Still count as "loaded" to avoid getting stuck
      }, { once: true });
      
      // Start loading the audio
      audio.load();
    });
    
    // Safety timeout - if sounds haven't loaded after 3 seconds, consider them loaded anyway
    const timeout = setTimeout(() => {
      if (!soundsLoaded) {
        console.log('Sound loading timeout - forcing loaded state');
        setSoundsLoaded(true);
      }
    }, 3000);
    
    // Cleanup function
    return () => {
      clearTimeout(timeout);
      
      // Clean up audio elements
      Object.values(soundRefs.current).forEach(audio => {
        if (audio) {
          // Remove event listeners
          audio.removeEventListener('canplaythrough', handleSoundLoaded);
          
          // Release resources
          audio.src = '';
          audio.load();
        }
      });
    };
  }, []);

  // Function to play a sound with reliable error handling
  const playSound = (soundType) => {
    const sound = soundRefs.current[soundType];
    
    if (!sound) {
      console.warn(`Sound ${soundType} not found`);
      return;
    }
    
    try {
      // Reset to beginning if it's already playing
      sound.currentTime = 0;
      
      // Play with proper promise handling for modern browsers
      const playPromise = sound.play();
      
      if (playPromise !== undefined) {
        playPromise.catch(e => {
          // Handle autoplay restrictions or other errors
          console.warn(`Couldn't play sound ${soundType}:`, e);
          
          // If it's an autoplay restriction, we could set up a one-time interaction handler
          // to unlock audio, but this is simplest for now
        });
      }
    } catch (e) {
      console.warn(`Error playing sound ${soundType}:`, e);
    }
  };

  return { 
    playSound,
    soundsLoaded,
    loadProgress: () => Math.round((loadedCount / Object.keys(soundPaths).length) * 100)
  };
};

export default useSound;