import React from 'react';

interface DashboardGridProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Responsive grid layout for dashboard components
 * - Mobile: 1 column
 * - Tablet: 2 columns  
 * - Desktop: 4 columns
 */
export const DashboardGrid: React.FC<DashboardGridProps> = ({ 
  children, 
  className = '' 
}) => {
  return (
    <div className={`
      grid gap-6 
      grid-cols-1 
      md:grid-cols-2 
      xl:grid-cols-4 
      auto-rows-min
      ${className}
    `}>
      {children}
    </div>
  );
};

interface GridAreaProps {
  children: React.ReactNode;
  area: 'portfolio' | 'systemHealth' | 'intelligence' | 'hotBots' | 'allBots' | 'activity';
  className?: string;
}

/**
 * Grid area component with predefined responsive spanning
 */
export const GridArea: React.FC<GridAreaProps> = ({ 
  children, 
  area, 
  className = '' 
}) => {
  const getAreaClasses = () => {
    switch (area) {
      case 'portfolio':
        return 'col-span-1 md:col-span-2 xl:col-span-2 row-span-2';
      case 'systemHealth':
        return 'col-span-1 md:col-span-2 xl:col-span-2 row-span-2';
      case 'intelligence':
        return 'col-span-1 md:col-span-2 xl:col-span-4 row-span-1';
      case 'hotBots':
        return 'col-span-1 md:col-span-2 xl:col-span-4 row-span-2';
      case 'allBots':
        return 'col-span-1 md:col-span-2 xl:col-span-4 row-span-4';
      case 'activity':
        return 'col-span-1 md:col-span-2 xl:col-span-4 row-span-2';
      default:
        return 'col-span-1';
    }
  };

  return (
    <div className={`${getAreaClasses()} ${className}`}>
      {children}
    </div>
  );
};

export default DashboardGrid;
