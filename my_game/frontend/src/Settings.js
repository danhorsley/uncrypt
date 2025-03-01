import React, { useState, useEffect } from 'react';
import './Settings.css';

function Settings({ currentSettings, onSave, onCancel }) {
  // Local state to track changes before saving
  const [settings, setSettings] = useState(currentSettings);

  useEffect(() => {
    // Update local state when props change
    setSettings(currentSettings);
  }, [currentSettings]);

  const handleChange = (setting, value) => {
    setSettings(prev => ({
      ...prev,
      [setting]: value
    }));
  };

  return (
    <div className="settings-container">
      <h1 className="settings-title">Game Settings</h1>

    {/* Frequency Display Setting */}
    <div className="settings-section">
        <h2>Frequency Display</h2>
        <div className="settings-options">
          <label className="settings-option">
            <input
              type="radio"
              name="frequencyDisplay"
              checked={settings.frequencyDisplay === 'visual'}
              onChange={() => handleChange('frequencyDisplay', 'visual')}
            />
            <span className="option-label">Visual Bars</span>
          </label>
          <label className="settings-option">
            <input
              type="radio"
              name="frequencyDisplay"
              checked={settings.frequencyDisplay === 'numeric'}
              onChange={() => handleChange('frequencyDisplay', 'numeric')}
            />
            <span className="option-label">Numbers</span>
          </label>
        </div>
        </div>
      
      {/* Hardcore Mode Setting */}
      <div className="settings-section">
        <h2>Gameplay Mode</h2>
        <div className="settings-options">
          <label className="settings-option">
            <input
              type="checkbox"
              checked={settings.hardcoreMode}
              onChange={() => handleChange('hardcoreMode', !settings.hardcoreMode)}
            />
            <span className="option-label">Hardcore Mode</span>
          </label>
          <p className="settings-description">
            When enabled, spaces and punctuation will be removed from the encrypted text,
            making it more challenging to decrypt.
          </p>
        </div>
      </div>
      


      {/* Grid Sorting Setting */}
      <div className="settings-section">
        <h2>Encrypted Grid Sorting</h2>
        <div className="settings-options">
          <label className="settings-option">
            <input
              type="radio"
              name="gridSorting"
              checked={settings.gridSorting === 'default'}
              onChange={() => handleChange('gridSorting', 'default')}
            />
            <span className="option-label">Default Order (as they appear in text)</span>
          </label>
          <label className="settings-option">
            <input
              type="radio"
              name="gridSorting"
              checked={settings.gridSorting === 'alphabetical'}
              onChange={() => handleChange('gridSorting', 'alphabetical')}
            />
            <span className="option-label">Alphabetical Order</span>
          </label>
        </div>
      </div>

      {/* Theme Setting */}
      <div className="settings-section">
        <h2>Theme</h2>
        <div className="settings-options">
          <label className="settings-option">
            <input
              type="radio"
              name="theme"
              checked={settings.theme === 'light'}
              onChange={() => handleChange('theme', 'light')}
            />
            <span className="option-label">Light Mode</span>
          </label>
          <label className="settings-option">
            <input
              type="radio"
              name="theme"
              checked={settings.theme === 'dark'}
              onChange={() => handleChange('theme', 'dark')}
            />
            <span className="option-label">Dark Mode</span>
          </label>
        </div>
      </div>

      {/* Difficulty Setting */}
      <div className="settings-section">
        <h2>Difficulty</h2>
        <div className="settings-options">
          <label className="settings-option">
            <input
              type="radio"
              name="difficulty"
              checked={settings.difficulty === 'easy'}
              onChange={() => handleChange('difficulty', 'easy')}
            />
            <span className="option-label">Easy (8 mistakes)</span>
          </label>
          <label className="settings-option">
            <input
              type="radio"
              name="difficulty"
              checked={settings.difficulty === 'normal'}
              onChange={() => handleChange('difficulty', 'normal')}
            />
            <span className="option-label">Normal (5 mistakes)</span>
          </label>
          <label className="settings-option">
            <input
              type="radio"
              name="difficulty"
              checked={settings.difficulty === 'hard'}
              onChange={() => handleChange('difficulty', 'hard')}
            />
            <span className="option-label">Hard (3 mistakes)</span>
          </label>
        </div>
      </div>

      {/* Text Color Setting */}
      <div className="settings-section">
        <h2>Text Color</h2>
        <div className="settings-options">
          <label className="settings-option">
            <input
              type="radio"
              name="textColor"
              checked={settings.textColor === 'default'}
              onChange={() => handleChange('textColor', 'default')}
            />
            <span className="option-label">Default</span>
            <span className="color-preview default"></span>
          </label>
          <label className="settings-option">
            <input
              type="radio"
              name="textColor"
              checked={settings.textColor === 'scifi-blue'}
              onChange={() => handleChange('textColor', 'scifi-blue')}
            />
            <span className="option-label">Sci-Fi Blue</span>
            <span className="color-preview scifi-blue"></span>
          </label>
          <label className="settings-option">
            <input
              type="radio"
              name="textColor"
              checked={settings.textColor === 'retro-green'}
              onChange={() => handleChange('textColor', 'retro-green')}
            />
            <span className="option-label">Retro Green</span>
            <span className="color-preview retro-green"></span>
          </label>
        </div>
      </div>
      
      {/* Speed Mode */}
      <div className="settings-section">
        <h2>Speed Mode</h2>
        <div className="settings-options">
          <label className="settings-option">
            <input
              type="checkbox"
              checked={settings.speedMode}
              onChange={() => handleChange('speedMode', !settings.speedMode)}
            />
            <span className="option-label">Enable Keyboard Speed Mode</span>
          </label>
          <p className="settings-description">
            When enabled, press a key to select an encrypted letter, then press another key to guess.
            ESC cancels selection. Makes for faster gameplay.
          </p>
        </div>
      </div>

      {/* Mobile Mode Setting */}
      <div className="settings-section">
        <h2>Mobile Mode</h2>
        <div className="settings-options">
          <label className="settings-option">
            <input
              type="radio"
              name="mobileMode"
              checked={settings.mobileMode === 'auto'}
              onChange={() => handleChange('mobileMode', 'auto')}
            />
            <span className="option-label">Auto Detect</span>
          </label>
          <label className="settings-option">
            <input
              type="radio"
              name="mobileMode"
              checked={settings.mobileMode === 'always'}
              onChange={() => handleChange('mobileMode', 'always')}
            />
            <span className="option-label">Always Use Mobile Layout</span>
          </label>
          <label className="settings-option">
            <input
              type="radio"
              name="mobileMode"
              checked={settings.mobileMode === 'never'}
              onChange={() => handleChange('mobileMode', 'never')}
            />
            <span className="option-label">Never Use Mobile Layout</span>
          </label>
          <p className="settings-description">
            Mobile mode provides a thumb-friendly interface with grids positioned at the sides 
            of the screen. Best experienced in landscape orientation.
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="settings-actions">
        <button className="settings-button cancel" onClick={onCancel}>
          Cancel
        </button>
        <button 
          className="settings-button save" 
          onClick={() => onSave(settings)}
        >
          Save & Return to Game
        </button>
      </div>
    </div>
  );
}

export default Settings;