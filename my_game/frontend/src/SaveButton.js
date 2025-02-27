import React, { useState } from 'react';

/**
 * Component for saving a quote to the curated list
 */
const SaveButton = ({ hasWon, playSound }) => {
  const [saveStatus, setSaveStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Don't render if the game isn't won yet
  if (!hasWon) {
    return null;
  }

  const handleSaveQuote = () => {
    setIsLoading(true);
    setSaveStatus(null);
    
    fetch('/save_quote', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then(res => {
        if (!res.ok) {
          throw new Error('Failed to save quote');
        }
        return res.json();
      })
      .then(data => {
        setSaveStatus({ success: true, message: data.message });
        setIsLoading(false);
        // Play a success sound if available
        if (playSound) {
          playSound('correct');
        }
      })
      .catch(err => {
        console.error('Error saving quote:', err);
        setSaveStatus({ success: false, message: 'Failed to save quote' });
        setIsLoading(false);
      });
  };

  // Status message styling classes
  const statusClass = saveStatus 
    ? (saveStatus.success ? 'save-success' : 'save-error') 
    : '';

  return (
    <div className="save-quote-container">
      <button 
        className="save-button"
        onClick={handleSaveQuote}
        disabled={isLoading}
      >
        {isLoading ? 'Saving...' : 'Save to Curated List'}
      </button>
      
      {saveStatus && (
        <div className={`save-status ${statusClass}`}>
          {saveStatus.message}
        </div>
      )}
    </div>
  );
};

export default SaveButton;