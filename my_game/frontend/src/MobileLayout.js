import React, { useState, useEffect } from 'react';
import { useAppContext } from './AppContext';
import './Mobile.css';

/**
 * A wrapper component for the mobile layout
 * Handles orientation messaging and applies mobile-specific classes
 */
const MobileLayout = ({ 
  children, 
  isLandscape
}) => {
  // Get theme settings from context
  const { settings } = useAppContext();
  const { theme, textColor } = settings;
  const [dismissedWarning, setDismissedWarning] = useState(false);
  
  // Reset dismissed state when orientation changes to portrait
  useEffect(() => {
    if (!isLandscape) {
      // Wait a moment before showing the warning to avoid flashing during rotation
      const timer = setTimeout(() => {
        setDismissedWarning(false);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isLandscape]);
  
  // Determine if we should show portrait warning
  const showPortraitWarning = !isLandscape && !dismissedWarning;
  
  // Apply appropriate classes
  const mobileClasses = `
    mobile-mode 
    ${theme === 'dark' ? 'dark-theme' : ''} 
    text-${textColor || 'default'} 
    ${!isLandscape ? 'portrait' : 'landscape'}
  `.trim().replace(/\s+/g, ' ');

  const handleDismissWarning = () => {
    setDismissedWarning(true);
  };

  return (
    <div className={mobileClasses}>
      {/* Orientation warning overlay */}
      {showPortraitWarning && (
        <div className="mobile-orientation-warning">
          <div className="orientation-message">
            <h3>For the best experience, please rotate your device to landscape mode</h3>
            <p>This game is designed to be played with your phone in landscape orientation</p>
            <button 
              className="orientation-dismiss"
              onClick={handleDismissWarning}
            >
              Continue Anyway
            </button>
          </div>
        </div>
      )}
      
      {/* Main content with mobile-specific structure */}
      <div className="game-content">
        {children}
      </div>
      
      {/* Optional debug information - can be removed in production */}
      {process.env.NODE_ENV === 'development' && (
        <div className="debug-info" style={{ 
          position: 'fixed', 
          bottom: 0, 
          right: 0, 
          background: 'rgba(0,0,0,0.7)', 
          color: 'white', 
          padding: '5px',
          fontSize: '10px',
          zIndex: 9999
        }}>
          {isLandscape ? 'Landscape' : 'Portrait'} Mode
        </div>
      )}
    </div>
  );
};

export default MobileLayout;