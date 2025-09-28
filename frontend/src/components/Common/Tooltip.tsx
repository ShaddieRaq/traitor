import React, { useState } from 'react';
import { HelpCircle, X } from 'lucide-react';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * Contextual tooltip that explains technical terms in plain language
 */
export const Tooltip: React.FC<TooltipProps> = ({ 
  content, 
  children, 
  className = '' 
}) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={() => setIsVisible(!isVisible)}
        className="cursor-help"
      >
        {children}
      </div>
      
      {isVisible && (
        <div className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2">
          <div className="bg-gray-900 text-white text-sm rounded-lg py-2 px-3 max-w-xs">
            <div className="relative">
              {content}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsVisible(false);
                }}
                className="absolute -top-1 -right-1 w-4 h-4 bg-gray-700 rounded-full flex items-center justify-center hover:bg-gray-600"
              >
                <X className="w-2 h-2" />
              </button>
            </div>
          </div>
          <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900 mx-auto"></div>
        </div>
      )}
    </div>
  );
};

interface HelpTermProps {
  term: string;
  definition: string;
  className?: string;
}

/**
 * Wrapper for technical terms that need explanation
 */
export const HelpTerm: React.FC<HelpTermProps> = ({ 
  term, 
  definition, 
  className = '' 
}) => {
  return (
    <Tooltip content={definition} className={className}>
      <span className="border-b border-dotted border-gray-400 cursor-help">
        {term}
        <HelpCircle className="inline w-3 h-3 ml-1 opacity-60" />
      </span>
    </Tooltip>
  );
};

export default Tooltip;