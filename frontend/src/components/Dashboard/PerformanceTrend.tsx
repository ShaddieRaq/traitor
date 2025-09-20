import React, { useMemo } from 'react';
import MiniChart from './MiniChart';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface PerformanceTrendProps {
  title: string;
  currentValue: number;
  historicalData?: number[];
  change?: number;
  changePercent?: number;
  format?: 'currency' | 'percentage' | 'number';
  size?: 'sm' | 'md' | 'lg';
  showChart?: boolean;
  className?: string;
}

export const PerformanceTrend: React.FC<PerformanceTrendProps> = ({
  title,
  currentValue,
  historicalData = [],
  change,
  changePercent,
  format = 'number',
  size = 'md',
  showChart = true,
  className = ''
}) => {
  const isPositive = (change ?? 0) >= 0;
  const hasData = historicalData.length > 0;

  const formatValue = (value: number) => {
    switch (format) {
      case 'currency':
        return `$${value.toLocaleString(undefined, { 
          minimumFractionDigits: 2, 
          maximumFractionDigits: 2 
        })}`;
      case 'percentage':
        return `${value.toFixed(2)}%`;
      default:
        return value.toLocaleString(undefined, { 
          minimumFractionDigits: 2, 
          maximumFractionDigits: 2 
        });
    }
  };

  const getTrendIcon = () => {
    if (!change) return <Minus className="h-3 w-3" />;
    return isPositive 
      ? <TrendingUp className="h-3 w-3" />
      : <TrendingDown className="h-3 w-3" />;
  };

  const getTrendColor = () => {
    if (!change) return 'text-gray-500';
    return isPositive ? 'text-green-600' : 'text-red-600';
  };

  const getChartHeight = () => {
    switch (size) {
      case 'sm': return 40;
      case 'lg': return 80;
      default: return 60;
    }
  };

  const mockHistoricalData = useMemo(() => {
    // If no historical data provided, generate some based on current value and change
    if (hasData) return historicalData;
    
    const dataPoints = 10;
    const changeRange = Math.abs(change || currentValue * 0.1);
    
    return Array.from({ length: dataPoints }, (_, i) => {
      const progress = i / (dataPoints - 1);
      const baseValue = currentValue - (change || 0);
      const trendValue = baseValue + (change || 0) * progress;
      const noise = (Math.random() - 0.5) * changeRange * 0.3;
      return Math.max(0, trendValue + noise);
    });
  }, [historicalData, hasData, currentValue, change, isPositive]);

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="mb-2">
        <div className="text-xs text-gray-600 mb-1">{title}</div>
        <div className="flex items-center justify-between">
          <div className={`font-semibold ${
            size === 'sm' ? 'text-sm' : 
            size === 'lg' ? 'text-xl' : 'text-base'
          }`}>
            {formatValue(currentValue)}
          </div>
          
          {(change !== undefined || changePercent !== undefined) && (
            <div className={`flex items-center space-x-1 text-xs ${getTrendColor()}`}>
              {getTrendIcon()}
              <span>
                {change !== undefined && formatValue(Math.abs(change))}
                {changePercent !== undefined && ` (${Math.abs(changePercent).toFixed(1)}%)`}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Mini Chart */}
      {showChart && (
        <MiniChart
          data={mockHistoricalData}
          height={getChartHeight()}
          type="line"
          gradient={true}
          showGrid={false}
          showAxes={false}
          className="rounded"
        />
      )}
    </div>
  );
};

export default PerformanceTrend;
