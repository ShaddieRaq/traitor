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
      
      // Check if centered tooltip would go off-screen
      const centerLeft = rect.left + rect.width / 2 - tooltipWidth / 2;
      const centerRight = centerLeft + tooltipWidth;
      
      if (centerLeft < 10) {
        setPosition('left');
      } else if (centerRight > screenWidth - 10) {
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
        return `${baseClasses} left-0`;
      case 'right':
        return `${baseClasses} right-0`;
      default:
        return `${baseClasses} left-1/2 transform -translate-x-1/2`;
    }
  };

  const getArrowClasses = () => {
    const baseArrowClasses = "absolute top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-900";
    
    switch (position) {
      case 'left':
        return `${baseArrowClasses} left-6`;
      case 'right':
        return `${baseArrowClasses} right-6`;
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
