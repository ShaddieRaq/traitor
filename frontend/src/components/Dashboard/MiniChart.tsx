import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export interface MiniChartProps {
  data: number[];
  labels?: string[];
  type?: 'line' | 'bar';
  color?: string;
  height?: number;
  showGrid?: boolean;
  showAxes?: boolean;
  gradient?: boolean;
  className?: string;
  isSignalChart?: boolean; // New prop for signal-specific formatting
}

export const MiniChart: React.FC<MiniChartProps> = ({
  data,
  labels,
  type = 'line',
  color = '#3B82F6',
  height = 60,
  showGrid = false,
  showAxes = false,
  gradient = true,
  className = '',
  isSignalChart = false
}) => {
  // Generate labels if not provided
  const chartLabels = labels || data.map((_, index) => index.toString());

  // Determine trend color based on overall performance
  const isPositiveTrend = data.length > 1 && data[data.length - 1] >= data[0];
  const trendColor = color === '#3B82F6' 
    ? (isPositiveTrend ? '#10B981' : '#EF4444')  // Green for positive, red for negative
    : color;

  const chartOptions: ChartOptions<'line' | 'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: trendColor,
        borderWidth: 1,
        displayColors: false,
        callbacks: {
          title: () => '',
          label: (context) => {
            const value = context.parsed.y;
            if (typeof value === 'number') {
              if (isSignalChart) {
                // Special formatting for signal chart
                if (value > 0.1) return `BUY Signal: ${value.toFixed(3)}`;
                if (value < -0.1) return `SELL Signal: ${value.toFixed(3)}`;
                return `HOLD Signal: ${value.toFixed(3)}`;
              }
              return value.toFixed(2);
            }
            return String(value);
          }
        }
      },
    },
    scales: {
      x: {
        display: showAxes,
        grid: {
          display: showGrid,
        },
        ticks: {
          display: showAxes,
        }
      },
      y: {
        display: showAxes || isSignalChart,
        grid: {
          display: showGrid || isSignalChart,
        },
        ticks: {
          display: showAxes || isSignalChart,
          color: '#6B7280',
          font: {
            size: 10,
          },
          callback: function(value) {
            if (isSignalChart) {
              // Show key reference levels for signal chart
              if (value === 0.1) return '+0.1 (BUY)';
              if (value === -0.1) return '-0.1 (SELL)';
              if (value === 0) return '0 (HOLD)';
              return '';
            }
            return value;
          }
        },
        min: isSignalChart ? -1 : undefined,
        max: isSignalChart ? 1 : undefined,
      },
    },
    elements: {
      point: {
        radius: type === 'line' ? 2 : 0,
        hoverRadius: 4,
        borderWidth: 1,
        backgroundColor: trendColor,
        borderColor: trendColor,
      },
      line: {
        borderWidth: 2,
        tension: 0.3,
      },
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
    animation: {
      duration: 750,
      easing: 'easeInOutQuart',
    },
  };

  const chartData = {
    labels: chartLabels,
    datasets: [
      {
        data: data,
        borderColor: trendColor,
        backgroundColor: gradient
          ? `${trendColor}20`  // Semi-transparent background
          : trendColor,
        fill: type === 'line' ? gradient : false,
        tension: 0.3,
      },
      // Add reference lines for signal chart
      ...(isSignalChart ? [
        // BUY threshold line
        {
          data: new Array(data.length).fill(0.1) as number[],
          borderColor: '#10B981',
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderDash: [5, 5],
          pointRadius: 0,
          pointHoverRadius: 0,
          fill: false,
          tension: 0,
        },
        // SELL threshold line  
        {
          data: new Array(data.length).fill(-0.1) as number[],
          borderColor: '#EF4444',
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderDash: [5, 5],
          pointRadius: 0,
          pointHoverRadius: 0,
          fill: false,
          tension: 0,
        },
        // HOLD center line
        {
          data: new Array(data.length).fill(0) as number[],
          borderColor: '#6B7280',
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderDash: [2, 2],
          pointRadius: 0,
          pointHoverRadius: 0,
          fill: false,
          tension: 0,
        }
      ] : [])
    ],
  };

  const ChartComponent = type === 'line' ? Line : Bar;

  return (
    <div className={`relative ${className}`} style={{ height: `${height}px` }}>
      <ChartComponent 
        data={chartData} 
        options={chartOptions}
      />
    </div>
  );
};

export default MiniChart;
