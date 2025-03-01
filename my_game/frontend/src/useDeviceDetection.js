import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook to detect device type and orientation
 * @returns {Object} Device information including isMobile and orientation
 */
const useDeviceDetection = () => {
  // State for tracking device info
  const [deviceInfo, setDeviceInfo] = useState({
    isMobile: false,
    isLandscape: false,
    screenWidth: window.innerWidth,
    screenHeight: window.innerHeight
  });

  // Extract the detection logic so it can be called from outside the hook
  const detectMobile = useCallback(() => {
      const userAgent = navigator.userAgent || navigator.vendor || window.opera;
      
      // Regular expressions to check for mobile devices
      const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
      
      // Check if it's a mobile device
      const isMobile = mobileRegex.test(userAgent) || 
                       (window.innerWidth <= 800) || 
                       ('ontouchstart' in window && window.innerWidth <= 1024);
      
      // Check orientation
      const isLandscape = window.innerWidth > window.innerHeight;
      
      setDeviceInfo({
        isMobile,
        isLandscape,
        screenWidth: window.innerWidth,
        screenHeight: window.innerHeight
      });
                                        })

    
  
  useEffect(() => {
    // Initial detection
    detectMobile();

    // Add event listeners to detect orientation changes and window resizing
    window.addEventListener('resize', detectMobile);
    window.addEventListener('orientationchange', detectMobile);

    // Cleanup listeners
    return () => {
      window.removeEventListener('resize', detectMobile);
      window.removeEventListener('orientationchange', detectMobile);
    };
  }, [detectMobile]);

  return {
    ...deviceInfo,
    detectMobile
  };
};

export default useDeviceDetection;