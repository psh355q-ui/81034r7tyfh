/**
 * Advanced Charts Component
 * 
 * Features:
 * - Portfolio Performance Chart (Area Chart)
 * - Real-time Price Chart (Line + Bar Composite)
 * - Sector Heatmap (Treemap)
 * - Risk Matrix (Scatter Plot)
 * 
 * Author: AI Trading System
 * Date: 2025-11-21
 * Fixed: Removed unused Card and Legend imports
 */

import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  Treemap,
  ScatterChart,
  Scatter,
  ZAxis,
} from 'recharts';

// --- Mock Data Generators (Replace with API calls later) ---

const generatePerformanceData = (days: number) => {
  const data = [];
  let value = 10000;
  const now = new Date();
  for (let i = days; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const change = (Math.random() - 0.48) * 200; // Slightly upward trend
    value += change;
    data.push({
      date: date.toISOString().split('T')[0],
      value: value,
    });
  }
  return data;
};

const generateIntradayData = () => {
  const data = [];
  let price = 150;
  const startTime = new Date();
  startTime.setHours(9, 30, 0, 0);

  for (let i = 0; i < 60; i++) {
    // 60 data points
    const time = new Date(startTime.getTime() + i * 5 * 60000); // 5 min intervals
    const change = (Math.random() - 0.5) * 2;
    price += change;
    const volume = Math.floor(Math.random() * 10000) + 1000;
    data.push({
      time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      price: price,
      volume: volume,
    });
  }
  return data;
};

const SECTOR_DATA = [
  { name: 'Technology', size: 45, fill: '#3B82F6' }, // Blue-500
  { name: 'Finance', size: 20, fill: '#10B981' }, // Emerald-500
  { name: 'Healthcare', size: 15, fill: '#EF4444' }, // Red-500
  { name: 'Consumer', size: 10, fill: '#F59E0B' }, // Amber-500
  { name: 'Energy', size: 10, fill: '#8B5CF6' }, // Violet-500
];

const RISK_DATA = [
  { name: 'AAPL', x: 15, y: 25, z: 1000 }, // x: Risk (Vol), y: Return, z: Position Size
  { name: 'GOOGL', x: 18, y: 20, z: 800 },
  { name: 'TSLA', x: 45, y: 60, z: 500 },
  { name: 'MSFT', x: 12, y: 15, z: 1200 },
  { name: 'AMZN', x: 25, y: 30, z: 700 },
  { name: 'NVDA', x: 35, y: 55, z: 600 },
];

// --- Components ---

export const PortfolioPerformanceChart: React.FC = () => {
  const data = generatePerformanceData(30);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => value.slice(5)} // MM-DD
          />
          <YAxis
            domain={['auto', 'auto']}
            tick={{ fontSize: 12, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `$${value.toLocaleString()}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              borderRadius: '8px',
              border: '1px solid #E5E7EB',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
            formatter={(value: number) => [`$${value.toLocaleString()}`, 'Portfolio Value']}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#3B82F6"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorValue)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

interface RealTimePriceChartProps {
  ticker?: string;
}

export const RealTimePriceChart: React.FC<RealTimePriceChartProps> = ({ ticker = 'AAPL' }) => {
  const data = generateIntradayData();

  return (
    <div className="h-[300px] w-full">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">{ticker} - Real-time Price</h3>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 10, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
            interval={10}
          />
          <YAxis
            yAxisId="price"
            orientation="left"
            tick={{ fontSize: 10, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <YAxis
            yAxisId="volume"
            orientation="right"
            tick={{ fontSize: 10, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              borderRadius: '8px',
              border: '1px solid #E5E7EB',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
          />
          <Bar yAxisId="volume" dataKey="volume" fill="#D1D5DB" opacity={0.3} />
          <Line
            yAxisId="price"
            type="monotone"
            dataKey="price"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export const SectorHeatmap: React.FC = () => {
  const CustomizedContent = (props: any) => {
    const { x, y, width, height, name, size } = props;

    return (
      <g>
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          style={{
            fill: props.fill,
            stroke: '#fff',
            strokeWidth: 2,
          }}
        />
        {width > 50 && height > 30 && (
          <>
            <text
              x={x + width / 2}
              y={y + height / 2 - 5}
              textAnchor="middle"
              fill="#fff"
              fontSize={14}
              fontWeight="bold"
            >
              {name}
            </text>
            <text x={x + width / 2} y={y + height / 2 + 15} textAnchor="middle" fill="#fff" fontSize={12}>
              {size}%
            </text>
          </>
        )}
      </g>
    );
  };

  return (
    <div className="h-[300px] w-full">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Sector Allocation</h3>
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={SECTOR_DATA}
          dataKey="size"
          stroke="#fff"
          fill="#8884d8"
          content={<CustomizedContent />}
        />
      </ResponsiveContainer>
    </div>
  );
};

export const RiskMatrix: React.FC = () => {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-md border border-gray-200">
          <p className="font-semibold text-gray-800">{data.name}</p>
          <p className="text-sm text-gray-600">Risk: {data.x}%</p>
          <p className="text-sm text-gray-600">Return: {data.y}%</p>
          <p className="text-sm text-gray-600">Size: ${data.z}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-[300px] w-full">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Risk vs Return Matrix</h3>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            type="number"
            dataKey="x"
            name="Risk"
            unit="%"
            tick={{ fontSize: 12, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
            label={{ value: 'Risk (Volatility)', position: 'insideBottom', offset: -10, fontSize: 12 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Return"
            unit="%"
            tick={{ fontSize: 12, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
            label={{ value: 'Return', angle: -90, position: 'insideLeft', fontSize: 12 }}
          />
          <ZAxis type="number" dataKey="z" range={[100, 1000]} name="Position Size" />
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          <Scatter data={RISK_DATA} fill="#3B82F6" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};
