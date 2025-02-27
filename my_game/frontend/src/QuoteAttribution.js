import React, { useState, useEffect } from 'react';
import { formatMajorAttribution } from './utils'; // Import the formatting function

/**
 * Component to display quote attribution
 */
const QuoteAttribution = ({ hasWon, theme, textColor }) => {
  const [attribution, setAttribution] = useState({
    major: '',
    minor: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch attribution data when the game is won
  useEffect(() => {
    if (hasWon) {
      setIsLoading(true);
      setError(null);
      
      fetch('/get_attribution')
        .then(res => {
          if (!res.ok) {
            throw new Error('Failed to fetch attribution');
          }
          return res.json();
        })
        .then(data => {
          setAttribution({
            major: formatMajorAttribution(data.major_attribution),
            minor: data.minor_attribution
          });
          setIsLoading(false);
        })
        .catch(err => {
          console.error('Error fetching attribution:', err);
          setError('Could not load attribution');
          setIsLoading(false);
        });
    }
  }, [hasWon]);

  // If the game isn't won yet, don't render anything
  if (!hasWon) {
    return null;
  }

  // Show loading state
  if (isLoading) {
    return <div className="attribution-container">Loading attribution...</div>;
  }

  // Show error state
  if (error) {
    return <div className="attribution-container error">{error}</div>;
  }

  // Don't render if we don't have attribution data
  if (!attribution.major && !attribution.minor) {
    return null;
  }

  // Render the attribution
  return (
    <div className={`attribution-container ${theme === 'dark' ? 'dark-theme' : ''} text-${textColor}`}>
      <div className="attribution-content">
        {/* <span className="attribution-label">Attributed to:</span> */}
        <div className="attribution-text">
          <span className="major-attribution">{attribution.major}</span>
          {attribution.minor && (
            <>
              <span className="attribution-separator">—</span>
              <span className="minor-attribution">{attribution.minor}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuoteAttribution;