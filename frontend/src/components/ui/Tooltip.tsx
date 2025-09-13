import React, { useState, useRef, useEffect } from 'react';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  className?: string;
}

const Tooltip: React.FC<TooltipProps> = ({ content, children, className = '' }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState<'center' | 'left' | 'right'>('center');
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isVisible && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const tooltipWidth = 256; // w-64 = 256px
      const screenWidth = window.innerWidth;
      
      // Check if centered tooltip would go off-screen OR past container boundaries
      const centerLeft = rect.left + rect.width / 2 - tooltipWidth / 2;
      const centerRight = centerLeft + tooltipWidth;
      
      // Very aggressive left boundary detection - if element is close to left, use left positioning
      // This accounts for the fact that signal meter is the first element in a flex container
      if (rect.left < 150 || centerLeft < 50) { // Much more aggressive detection
        setPosition('left');
      } else if (centerRight > screenWidth - 20) {
        setPosition('right');
      } else {
        setPosition('center');
      }
    }
  }, [isVisible]);

  const getTooltipClasses = () => {
    const baseClasses = "absolute z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg -top-2 -translate-y-full w-64 max-w-sm";
    
    switch (position) {
      case 'left':
        // Position tooltip to start at the left edge of the trigger element
        return `${baseClasses} left-0`;
      case 'right':
        // Position tooltip to end at the right edge of the trigger element
        return `${baseClasses} right-0`;
      default:
        // Center the tooltip on the trigger element
        return `${baseClasses} left-1/2 transform -translate-x-1/2`;
    }
  };

  const getArrowClasses = () => {
    const baseArrowClasses = "absolute top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-900";
    
    switch (position) {
      case 'left':
        // Position arrow to point to the center of the trigger element
        return `${baseArrowClasses} left-8`; // Adjusted from left-6 to left-8 for better centering
      case 'right':
        return `${baseArrowClasses} right-8`; // Adjusted from right-6 to right-8 for better centering
      default:
        return `${baseArrowClasses} left-1/2 transform -translate-x-1/2`;
    }
  };

  return (
    <div 
      ref={containerRef}
      className={`relative inline-block ${className}`}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className={getTooltipClasses()}>
          <div className="text-xs leading-relaxed whitespace-normal">{content}</div>
          {/* Arrow pointing down */}
          <div className={getArrowClasses()}></div>
        </div>
      )}
    </div>
  );
};

export default Tooltip;
