import React, { useState, useEffect } from 'react';
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
  Cell
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

  for (let i = 0; i < 60; i++) { // 60 data points
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
  { name: 'Finance', size: 20, fill: '#10B981' },    // Emerald-500
  { name: 'Healthcare', size: 15, fill: '#EF4444' }, // Red-500
  { name: 'Consumer', size: 10, fill: '#F59E0B' },   // Amber-500
  { name: 'Energy', size: 10, fill: '#8B5CF6' },     // Violet-500
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
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 실제 포트폴리오 데이터 가져오기
    const fetchPortfolioHistory = async () => {
      try {
        // 현재 포트폴리오 값 가져오기
        const response = await fetch('/api/portfolio');
        const portfolio = await response.json();

        // 히스토리 데이터 생성 (30일)
        const historyData = [];
        const currentValue = portfolio.total_value || 100;
        const days = 30;

        for (let i = days; i >= 0; i--) {
          const date = new Date();
          date.setDate(date.getDate() - i);
          // 현재 값 기준으로 역산 (실제로는 DB에서 가져와야 함)
          const randomFactor = 0.98 + Math.random() * 0.04; // ±2% 변동
          const value = currentValue * Math.pow(randomFactor, i / 10);

          historyData.push({
            date: date.toISOString().split('T')[0],
            value: value,
          });
        }

        // 마지막 날을 실제 현재 값으로 설정
        historyData[historyData.length - 1].value = currentValue;

        setData(historyData);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch portfolio data:', error);
        // 에러 시 mock 데이터 사용
        setData(generatePerformanceData(30));
        setLoading(false);
      }
    };

    fetchPortfolioHistory();
  }, []);

  if (loading) {
    return <div className="h-[300px] flex items-center justify-center">로딩 중...</div>;
  }

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
            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #E5E7EB', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
            formatter={(value: number) => [`$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, '포트폴리오 가치']}
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
  ticker: string;
}

export const RealTimePriceChart: React.FC<RealTimePriceChartProps> = ({ ticker: _ticker }) => {
  const [data, setData] = useState(generateIntradayData());

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setData(prevData => {
        const lastItem = prevData[prevData.length - 1];
        const newTime = new Date();
        const change = (Math.random() - 0.5) * 1;
        const newPrice = lastItem.price + change;
        const newVolume = Math.floor(Math.random() * 5000) + 500;

        const newItem = {
          time: newTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          price: newPrice,
          volume: newVolume
        };

        return [...prevData.slice(1), newItem]; // Keep window size constant
      });
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 10, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            yAxisId="left"
            domain={['auto', 'auto']}
            tick={{ fontSize: 12, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `$${value.toFixed(2)}`}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 10, fill: '#9CA3AF' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #E5E7EB' }}
            labelStyle={{ fontWeight: 'bold', color: '#374151' }}
          />
          <Bar yAxisId="right" dataKey="volume" fill="#E5E7EB" barSize={20} radius={[4, 4, 0, 0]} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="price"
            stroke="#2563EB"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
            animationDuration={500}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

const CustomTreemapContent = (props: any) => {
  const { depth, x, y, width, height, name, fill } = props;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: fill,
          stroke: '#fff',
          strokeWidth: 2 / (depth + 1e-10),
          strokeOpacity: 1 / (depth + 1e-10),
        }}
      />
      {width > 50 && height > 30 && (
        <text
          x={x + width / 2}
          y={y + height / 2}
          textAnchor="middle"
          fill="#fff"
          fontSize={14}
          fontWeight="bold"
        >
          {name}
        </text>
      )}
    </g>
  );
};

export const SectorHeatmap: React.FC = () => {
  const [sectorData, setSectorData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSectorAllocation = async () => {
      try {
        const response = await fetch('/api/portfolio');
        const portfolio = await response.json();

        // 간단한 섹터 매핑 (실제로는 ticker별 섹터 정보 필요)
        const sectorMap: Record<string, { size: number, fill: string }> = {
          'Technology': { size: 0, fill: '#3B82F6' },
          'Finance': { size: 0, fill: '#10B981' },
          'Healthcare': { size: 0, fill: '#EF4444' },
          'Consumer': { size: 0, fill: '#F59E0B' },
          'Energy': { size: 0, fill: '#8B5CF6' },
          'Other': { size: 0, fill: '#6B7280' },
        };

        // 포지션별 섹터 분류 (간단한 ticker 기반 추정)
        if (portfolio.positions && portfolio.positions.length > 0) {
          portfolio.positions.forEach((pos: any) => {
            const ticker = pos.ticker.toUpperCase();
            const value = pos.market_value || 0;

            // 디버깅: ticker 값 확인
            console.log(`Ticker: ${ticker}, Value: ${value}`);

            // 간단한 섹터 분류 (실제로는 API에서 가져와야 함)
            if (['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'META', 'TSLA', 'INTC', 'AMD', 'ORCL', 'CSCO', 'IBM', 'QCOM'].includes(ticker)) {
              sectorMap['Technology'].size += value;
              console.log(`  → Technology (${ticker})`);
            } else if (['JPM', 'BAC', 'GS', 'WFC'].includes(ticker)) {
              sectorMap['Finance'].size += value;
              console.log(`  → Finance (${ticker})`);
            } else if (['JNJ', 'PFE', 'UNH', 'ABBV'].includes(ticker)) {
              sectorMap['Healthcare'].size += value;
              console.log(`  → Healthcare (${ticker})`);
            } else if (['AMZN', 'WMT', 'HD', 'NKE'].includes(ticker)) {
              sectorMap['Consumer'].size += value;
              console.log(`  → Consumer (${ticker})`);
            } else if (['XOM', 'CVX', 'COP'].includes(ticker)) {
              sectorMap['Energy'].size += value;
              console.log(`  → Energy (${ticker})`);
            } else {
              sectorMap['Other'].size += value;
              console.log(`  → Other (${ticker}) ⚠️`);
            }
          });

          // 0이 아닌 섹터만 필터링
          const filteredData = Object.entries(sectorMap)
            .filter(([_, data]) => data.size > 0)
            .map(([name, data]) => ({
              name,
              size: data.size,
              fill: data.fill
            }));

          if (filteredData.length > 0) {
            setSectorData(filteredData);
          }
        }
      } catch (error) {
        console.error('Failed to fetch sector allocation:', error);
      }
    };

    fetchSectorAllocation();
  }, []);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={sectorData}
          dataKey="size"
          aspectRatio={4 / 3}
          stroke="#fff"
          content={<CustomTreemapContent />}
        >
          <Tooltip />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
};

export const RiskMatrix: React.FC = () => {
  const [riskData, setRiskData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRiskData = async () => {
      try {
        const response = await fetch('/api/portfolio');
        const portfolio = await response.json();

        if (portfolio.positions && portfolio.positions.length > 0) {
          const positionsData = portfolio.positions.map((pos: any) => ({
            name: pos.ticker,
            x: Math.abs(pos.unrealized_pnl_pct || 0) * 2, // Risk (변동성 추정)
            y: pos.unrealized_pnl_pct || 0, // Return
            z: pos.market_value || 100 // Position Size
          }));

          setRiskData(positionsData);
        }
      } catch (error) {
        console.error('Failed to fetch risk data:', error);
      }
    };

    fetchRiskData();
  }, []);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            type="number"
            dataKey="x"
            name="Risk (Volatility)"
            unit="%"
            tick={{ fontSize: 12, fill: '#6B7280' }}
            label={{ value: 'Risk (Volatility)', position: 'bottom', offset: 0, fill: '#6B7280', fontSize: 12 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Return"
            unit="%"
            tick={{ fontSize: 12, fill: '#6B7280' }}
            label={{ value: 'Return', angle: -90, position: 'left', offset: 0, fill: '#6B7280', fontSize: 12 }}
          />
          <ZAxis type="number" dataKey="z" range={[100, 1000]} name="Position Size" />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                    <p className="font-bold text-gray-900">{data.name}</p>
                    <p className="text-sm text-gray-600">Risk: {data.x.toFixed(1)}%</p>
                    <p className="text-sm text-gray-600">Return: {data.y.toFixed(2)}%</p>
                    <p className="text-sm text-gray-600">Size: ${data.z.toFixed(2)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter name="Positions" data={riskData} fill="#8884d8">
            {riskData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.y > 0 ? '#10B981' : '#F59E0B'} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};
