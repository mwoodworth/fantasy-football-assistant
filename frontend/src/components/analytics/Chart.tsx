import { useState, useEffect, useRef } from 'react';
import { cn } from '../../utils/cn';

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
  metadata?: any;
}

export interface ChartProps {
  data: ChartDataPoint[];
  type: 'line' | 'bar' | 'pie' | 'area';
  title?: string;
  height?: number;
  width?: number;
  showLabels?: boolean;
  showGrid?: boolean;
  showLegend?: boolean;
  colors?: string[];
  className?: string;
  animated?: boolean;
}

// Simple SVG-based chart component
export function Chart({
  data,
  type,
  title,
  height = 300,
  width = 400,
  showLabels = true,
  showGrid = true,
  showLegend = false,
  colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
  className,
  animated = true
}: ChartProps) {
  const [animationProgress, setAnimationProgress] = useState(0);
  const chartRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (animated) {
      setAnimationProgress(0);
      const timer = setTimeout(() => setAnimationProgress(1), 100);
      return () => clearTimeout(timer);
    } else {
      setAnimationProgress(1);
    }
  }, [data, animated]);

  if (!data || data.length === 0) {
    return (
      <div className={cn('flex items-center justify-center bg-gray-50 rounded-lg', className)} style={{ height }}>
        <p className="text-gray-500">No data available</p>
      </div>
    );
  }

  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value), 0);
  const valueRange = maxValue - minValue || 1;

  const chartWidth = width - 80; // Leave space for labels
  const chartHeight = height - 80; // Leave space for title and labels
  const chartX = 40;
  const chartY = 40;

  const renderLineChart = () => {
    const stepX = chartWidth / (data.length - 1 || 1);

    const animatedPoints = data.slice(0, Math.ceil(data.length * animationProgress));
    const animatedPointsStr = animatedPoints.map((d, i) => {
      const x = chartX + i * stepX;
      const y = chartY + chartHeight - ((d.value - minValue) / valueRange) * chartHeight;
      return `${x},${y}`;
    }).join(' ');

    return (
      <>
        {/* Grid lines */}
        {showGrid && (
          <g className="opacity-20">
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
              <line
                key={ratio}
                x1={chartX}
                y1={chartY + chartHeight * ratio}
                x2={chartX + chartWidth}
                y2={chartY + chartHeight * ratio}
                stroke="currentColor"
                strokeWidth="1"
              />
            ))}
          </g>
        )}
        
        {/* Line */}
        <polyline
          points={animatedPointsStr}
          fill="none"
          stroke={colors[0]}
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-all duration-1000"
        />
        
        {/* Points */}
        {animatedPoints.map((d, i) => {
          const x = chartX + i * stepX;
          const y = chartY + chartHeight - ((d.value - minValue) / valueRange) * chartHeight;
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r="4"
              fill={colors[0]}
              className="transition-all duration-1000"
            />
          );
        })}
      </>
    );
  };

  const renderBarChart = () => {
    const barWidth = chartWidth / data.length * 0.7;
    const barSpacing = chartWidth / data.length * 0.3;

    return (
      <>
        {/* Grid lines */}
        {showGrid && (
          <g className="opacity-20">
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
              <line
                key={ratio}
                x1={chartX}
                y1={chartY + chartHeight * ratio}
                x2={chartX + chartWidth}
                y2={chartY + chartHeight * ratio}
                stroke="currentColor"
                strokeWidth="1"
              />
            ))}
          </g>
        )}
        
        {/* Bars */}
        {data.map((d, i) => {
          const barHeight = ((d.value - minValue) / valueRange) * chartHeight * animationProgress;
          const x = chartX + i * (barWidth + barSpacing) + barSpacing / 2;
          const y = chartY + chartHeight - barHeight;
          
          return (
            <rect
              key={i}
              x={x}
              y={y}
              width={barWidth}
              height={barHeight}
              fill={d.color || colors[i % colors.length]}
              className="transition-all duration-1000"
              rx="4"
            />
          );
        })}
      </>
    );
  };

  const renderPieChart = () => {
    const centerX = chartX + chartWidth / 2;
    const centerY = chartY + chartHeight / 2;
    const radius = Math.min(chartWidth, chartHeight) / 2 - 20;
    
    const total = data.reduce((sum, d) => sum + d.value, 0);
    let currentAngle = -90; // Start from top
    
    return (
      <>
        {data.map((d, i) => {
          const sliceAngle = (d.value / total) * 360 * animationProgress;
          const startAngle = currentAngle;
          const endAngle = currentAngle + sliceAngle;
          
          const x1 = centerX + radius * Math.cos((startAngle * Math.PI) / 180);
          const y1 = centerY + radius * Math.sin((startAngle * Math.PI) / 180);
          const x2 = centerX + radius * Math.cos((endAngle * Math.PI) / 180);
          const y2 = centerY + radius * Math.sin((endAngle * Math.PI) / 180);
          
          const largeArcFlag = sliceAngle > 180 ? 1 : 0;
          
          const pathData = [
            `M ${centerX} ${centerY}`,
            `L ${x1} ${y1}`,
            `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
            'Z'
          ].join(' ');
          
          currentAngle += sliceAngle;
          
          return (
            <path
              key={i}
              d={pathData}
              fill={d.color || colors[i % colors.length]}
              className="transition-all duration-1000"
            />
          );
        })}
      </>
    );
  };

  const renderChart = () => {
    switch (type) {
      case 'line':
      case 'area':
        return renderLineChart();
      case 'bar':
        return renderBarChart();
      case 'pie':
        return renderPieChart();
      default:
        return null;
    }
  };

  const renderLabels = () => {
    if (!showLabels) return null;

    if (type === 'pie') {
      return null; // Pie chart labels handled separately
    }

    const stepX = chartWidth / data.length;
    
    return (
      <g className="text-xs fill-gray-600">
        {data.map((d, i) => (
          <text
            key={i}
            x={chartX + i * stepX + stepX / 2}
            y={chartY + chartHeight + 20}
            textAnchor="middle"
            className="text-xs"
          >
            {d.label}
          </text>
        ))}
      </g>
    );
  };

  return (
    <div className={cn('bg-white rounded-lg p-4', className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      )}
      
      <svg
        ref={chartRef}
        width={width}
        height={height}
        className="overflow-visible"
        viewBox={`0 0 ${width} ${height}`}
      >
        {renderChart()}
        {renderLabels()}
        
        {/* Y-axis labels */}
        {showLabels && type !== 'pie' && (
          <g className="text-xs fill-gray-600">
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
              const value = minValue + (maxValue - minValue) * (1 - ratio);
              return (
                <text
                  key={ratio}
                  x={chartX - 10}
                  y={chartY + chartHeight * ratio + 4}
                  textAnchor="end"
                  className="text-xs"
                >
                  {value.toFixed(1)}
                </text>
              );
            })}
          </g>
        )}
      </svg>
      
      {/* Legend */}
      {showLegend && (
        <div className="flex flex-wrap gap-4 mt-4">
          {data.map((d, i) => (
            <div key={i} className="flex items-center space-x-2">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: d.color || colors[i % colors.length] }}
              />
              <span className="text-sm text-gray-600">{d.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}