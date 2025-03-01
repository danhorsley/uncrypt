import React, { useState, useEffect, useRef } from 'react';
import Confetti from 'react-confetti';
import SaveButton from './SaveButton';

// Enhanced win celebration component
const WinCelebration = ({ 
  startGame, 
  playSound, 
  mistakes, 
  maxMistakes, 
  startTime,
  completionTime,
  theme,
  textColor 
}) => {
  // Animation state
  const [animationStage, setAnimationStage] = useState(0);
  const [showStats, setShowStats] = useState(false);
  const [showConfetti, setShowConfetti] = useState(true);
  const [showFireworks, setShowFireworks] = useState(false);
  const [isConfettiActive, setIsConfettiActive] = useState(true);
  
  // Refs for animation
  const statsRef = useRef(null);
  const messageRef = useRef(null);
  const containerRef = useRef(null);
  
  // Calculate stats
  const gameTimeSeconds = startTime && completionTime 
    ? Math.floor((completionTime - startTime) / 1000) 
    : 0;
  const minutes = Math.floor(gameTimeSeconds / 60);
  const seconds = gameTimeSeconds % 60;
  const timeString = `${minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
  
  // Calculate score based on mistakes and time
  const maxScore = 1000;
  const mistakePenalty = 50;
  const timePenalty = 2; // points per second
  const score = Math.max(0, maxScore - (mistakes * mistakePenalty) - (gameTimeSeconds * timePenalty));
  
  // Performance rating based on score
  let rating = '';
  if (score >= 900) rating = 'Perfect';
  else if (score >= 800) rating = 'Ace of Spies';
  else if (score >= 700) rating = 'Bletchley Park';
  else if (score >= 500) rating = 'Cabinet Noir';
  else rating = 'Cryptanalyst';
  
  // Debug logs for troubleshooting
  console.log("Animation stage:", animationStage);
  console.log("Show stats:", showStats);
  console.log("Game time seconds:", gameTimeSeconds);
  console.log("Score:", score);
  
  // Staged animation sequence
  useEffect(() => {
    console.log("Running animation stage:", animationStage);
    
    // Initial animation
    const timeline = [
      () => {
        // Play win sound and start confetti
        playSound('win');
        console.log("Stage 0: Playing win sound");
      },
      () => {
        // Show message with animation
        if (messageRef.current) {
          messageRef.current.classList.add('animate-scale-in');
          console.log("Stage 1: Message animation added");
        }
        
        // Start fireworks after a short delay
        setTimeout(() => {
          setShowFireworks(true);
          console.log("Setting fireworks to true");
        }, 300);
      },
      () => {
        // Show stats with animation
        setShowStats(true);
        console.log("Stage 2: Setting show stats to true");
        
        if (statsRef.current) {
          statsRef.current.classList.add('animate-slide-in');
          console.log("Stats animation class added");
        } else {
          console.log("Stats ref is null");
        }
      },
      () => {
        // Gradually reduce confetti
        console.log("Stage 3: Reducing confetti");
        setTimeout(() => {
          setIsConfettiActive(false);
        }, 1000);
      }
    ];
    
    // Execute animation stages with delays
    if (animationStage < timeline.length) {
      timeline[animationStage]();
      const nextStage = setTimeout(() => {
        setAnimationStage(animationStage + 1);
      }, animationStage === 0 ? 500 : 800);
      
      return () => clearTimeout(nextStage);
    }
  }, [animationStage, playSound]);
  
  // Force show stats after a delay (backup)
  useEffect(() => {
    const forceShowStats = setTimeout(() => {
      if (!showStats) {
        console.log("Force showing stats after timeout");
        setShowStats(true);
      }
    }, 2000);
    
    return () => clearTimeout(forceShowStats);
  }, [showStats]);
  
  // Clean up animations after some time
  useEffect(() => {
    const cleanupTimer = setTimeout(() => {
      setShowConfetti(false);
      setShowFireworks(false);
    }, 7000); // Stop animations after 7 seconds
    
    return () => clearTimeout(cleanupTimer);
  }, []);
  
  return (
    <div ref={containerRef} className={`win-celebration ${theme === 'dark' ? 'dark-theme' : ''} text-${textColor}`}>
      {/* Confetti effect */}
      {showConfetti && (
        <Confetti
          width={window.innerWidth}
          height={window.innerHeight}
          recycle={isConfettiActive}
          numberOfPieces={isConfettiActive ? 200 : 50}
          gravity={0.2}
          tweenDuration={5000}
        />
      )}
      
      {/* Fireworks effect */}
      {showFireworks && (
        <div className="fireworks-container">
          <div className="firework"></div>
          <div className="firework delayed"></div>
          <div className="firework delayed-2"></div>
        </div>
      )}
      
      {/* Main celebration content */}
      <div className="celebration-content">
        {/* Victory message */}
        <div ref={messageRef} className="victory-message">
            <h2 className="victory-title">Solved! Rating : </h2>
          <h2 className="victory-title">{rating}</h2>
          <p className="victory-subtitle">You've successfully decrypted the message!</p>
        </div>
        
        {/* Stats display - now with inline style fallback */}
        <div 
          ref={statsRef} 
          className={`stats-container ${showStats ? 'animate-slide-in' : ''}`}
          style={{ 
            opacity: showStats ? 1 : 0, 
            transition: 'opacity 0.8s ease-out',
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: '20px',
            margin: '25px 0'
          }}
        >
          <div className="stat-item">
            <span className="stat-label">Time</span>
            <span className="stat-value">{timeString}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Mistakes</span>
            <span className="stat-value">{mistakes} / {maxMistakes}</span>
          </div>
          <div className="stat-item score">
            <span className="stat-label">Score</span>
            <span className="stat-value">{score}</span>
          </div>
        </div>
        
        {/* Action buttons */}
        <div className="celebration-actions">
          <SaveButton hasWon={true} playSound={playSound} />
          <button 
            className="play-again-button"
            onClick={startGame}
            style={{ color: textColor === 'retro-green' ? '#003b00' : 'white' }}
          >
            Play Again
          </button>
        </div>
      </div>
    </div>
  );
};

export default WinCelebration;