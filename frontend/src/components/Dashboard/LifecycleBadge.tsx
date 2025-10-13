import React from 'react';

interface LifecycleBadgeProps {
  stage: string;
  archivedAt?: string;
  className?: string;
}

/**
 * LifecycleBadge - Shows bot lifecycle state with icon and label
 * 
 * Lifecycle stages:
 * - ACTIVE: Bot is trading normally ✅
 * - CLOSING: Position being liquidated 🔄
 * - CLOSED: 7-day cooling period ⏸️
 * - ARCHIVED: Available for resurrection 📦
 */
export const LifecycleBadge: React.FC<LifecycleBadgeProps> = ({ 
  stage, 
  archivedAt, 
  className = '' 
}) => {
  const getBadgeStyle = () => {
    switch (stage) {
      case 'ACTIVE':
        return {
          icon: '✅',
          bg: 'bg-green-100',
          text: 'text-green-800',
          border: 'border-green-300',
          label: 'Active'
        };
      case 'CLOSING':
        return {
          icon: '🔄',
          bg: 'bg-yellow-100',
          text: 'text-yellow-800',
          border: 'border-yellow-300',
          label: 'Closing'
        };
      case 'CLOSED':
        // Calculate hours remaining in 6-hour cooling period
        const closedDate = archivedAt ? new Date(archivedAt) : new Date();
        const hoursPassed = Math.floor((Date.now() - closedDate.getTime()) / (1000 * 60 * 60));
        const hoursRemaining = Math.max(0, 6 - hoursPassed);
        return {
          icon: '⏸️',
          bg: 'bg-blue-100',
          text: 'text-blue-800',
          border: 'border-blue-300',
          label: hoursRemaining > 0 ? `Cooling (${hoursRemaining}h)` : 'Cooling'
        };
      case 'ARCHIVED':
        return {
          icon: '📦',
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-300',
          label: 'Archived'
        };
      default:
        // Default to ACTIVE if stage is undefined (backwards compatibility)
        return {
          icon: '✅',
          bg: 'bg-green-100',
          text: 'text-green-800',
          border: 'border-green-300',
          label: 'Active'
        };
    }
  };

  const style = getBadgeStyle();

  return (
    <div 
      className={`inline-flex items-center space-x-1 px-2 py-1 rounded-md border ${style.bg} ${style.text} ${style.border} text-xs font-medium ${className}`}
      title={`Lifecycle: ${stage || 'ACTIVE'}`}
    >
      <span>{style.icon}</span>
      <span>{style.label}</span>
    </div>
  );
};
