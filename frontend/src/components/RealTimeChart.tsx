/**
 * Real-Time Chart Component
 *
 * 실시간 시장 데이터를 표시하는 차트 컴포넌트
 *
 * 기능:
 * 1. 실시간 주가 표시
 * 2. 변동률 색상 표시 (상승: 초록, 하락: 빨강)
 * 3. 연결 상태 표시
 * 4. 자동 갱신
 *
 * 참고: Phase 4 - Real-time Execution 완성
 */

import React from 'react';
import { Card, Tag, Spin, Alert, Row, Col, Statistic } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { useMarketDataWebSocket, Quote } from '@/hooks/useMarketDataWebSocket';

interface RealTimeChartProps {
  symbols: string[];
  wsUrl?: string;
  title?: string;
}

export const RealTimeChart: React.FC<RealTimeChartProps> = ({
  symbols,
  wsUrl,
  title = '실시간 시장 데이터'
}) => {
  const { quotes, isConnected, error } = useMarketDataWebSocket(symbols, wsUrl);

  if (error) {
    return (
      <Alert
        message="WebSocket 연결 오류"
        description={error.message}
        type="error"
        showIcon
      />
    );
  }

  return (
    <Card
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>{title}</span>
          <Tag color={isConnected ? 'green' : 'red'}>
            {isConnected ? '🟢 연결됨' : '🔴 연결 안됨'}
          </Tag>
        </div>
      }
      loading={!isConnected && Object.keys(quotes).length === 0}
    >
      {Object.keys(quotes).length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" tip="데이터 로드 중..." />
        </div>
      ) : (
        <Row gutter={[16, 16]}>
          {Object.values(quotes).map((quote) => (
            <Col xs={24} sm={12} md={8} lg={6} key={quote.symbol}>
              <QuoteCard quote={quote} />
            </Col>
          ))}
        </Row>
      )}
    </Card>
  );
};

interface QuoteCardProps {
  quote: Quote;
}

const QuoteCard: React.FC<QuoteCardProps> = ({ quote }) => {
  const isPositive = quote.change && quote.change > 0;
  const isNegative = quote.change && quote.change < 0;
  const changeColor = isPositive ? '#52c41a' : isNegative ? '#ff4d4f' : 'inherit';
  const changeIcon = isPositive ? <ArrowUpOutlined /> : isNegative ? <ArrowDownOutlined /> : null;

  return (
    <Card
      size="small"
      hoverable
      style={{
        borderLeft: `4px solid ${changeColor}`,
        backgroundColor: isPositive ? 'rgba(82, 196, 26, 0.05)' : isNegative ? 'rgba(255, 77, 79, 0.05)' : 'inherit'
      }}
    >
      <div style={{ marginBottom: 8 }}>
        <h3 style={{ margin: 0, fontSize: 18, fontWeight: 'bold' }}>
          {quote.symbol}
        </h3>
      </div>

      <Statistic
        value={quote.price ?? 0}
        precision={2}
        prefix="$"
        valueStyle={{ fontSize: 24, fontWeight: 'bold' }}
      />

      <div
        style={{
          marginTop: 8,
          color: changeColor,
          display: 'flex',
          alignItems: 'center',
          gap: 4
        }}
      >
        {changeIcon}
        <span style={{ fontSize: 16, fontWeight: 'bold' }}>
          {quote.change !== null ? `${quote.change > 0 ? '+' : ''}${quote.change.toFixed(2)}%` : 'N/A'}
        </span>
      </div>

      {quote.volume && (
        <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
          거래량: {quote.volume.toLocaleString()}
        </div>
      )}

      <div style={{ marginTop: 4, fontSize: 10, color: '#bfbfbf' }}>
        업데이트: {new Date(quote.timestamp).toLocaleTimeString('ko-KR')}
      </div>
    </Card>
  );
};


/**
 * Conflict Alert Component
 *
 * 실시간 충돌 알림을 표시하는 컴포넌트
 */

import { useConflictWebSocket } from '@/hooks/useMarketDataWebSocket';
import { Alert as AntAlert, List, Badge } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';
import type { ConflictAlert as ConflictAlertType } from '@/hooks/useMarketDataWebSocket';

interface ConflictAlertProps {
  wsUrl?: string;
  maxAlerts?: number;
}

export const ConflictAlert: React.FC<ConflictAlertProps> = ({
  wsUrl,
  maxAlerts = 10
}) => {
  const { conflicts, isConnected } = useConflictWebSocket(wsUrl);

  return (
    <Card
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>충돌 알림</span>
          {conflicts.length > 0 && (
            <Badge count={conflicts.length} overflowCount={99} />
          )}
          <Tag color={isConnected ? 'green' : 'red'}>
            {isConnected ? '🟢' : '🔴'}
          </Tag>
        </div>
      }
      size="small"
    >
      {conflicts.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '20px', color: '#8c8c8c' }}>
          충돌 없음
        </div>
      ) : (
        <List
          dataSource={conflicts.slice(0, maxAlerts)}
          renderItem={(conflict) => (
            <List.Item>
              <ConflictItem conflict={conflict} />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

interface ConflictItemProps {
  conflict: ConflictAlertType;
}

const ConflictItem: React.FC<ConflictItemProps> = ({ conflict }) => {
  return (
    <AntAlert
      message={
        <div>
          <strong>{conflict.ticker}</strong> - {conflict.message}
        </div>
      }
      description={
        <div style={{ marginTop: 8, fontSize: 12 }}>
          <div>
            <strong>충돌 전략:</strong> {conflict.conflicting_strategy}
          </div>
          <div>
            <strong>소유 전략:</strong> {conflict.owning_strategy}
          </div>
          <div>
            <strong>해결 방안:</strong> {conflict.resolution}
          </div>
          <div style={{ marginTop: 4, color: '#8c8c8c' }}>
            {new Date(conflict.timestamp).toLocaleString('ko-KR')}
          </div>
        </div>
      }
      type="warning"
      icon={<ExclamationCircleOutlined />}
      showIcon
    />
  );
};


/**
 * Live Signals Component
 *
 * 실시간 트레이딩 시그널을 표시하는 컴포넌트
 */

interface TradingSignal {
  ticker: string;
  action: 'BUY' | 'SELL';
  confidence: number;
  reasoning: string;
  timestamp: string;
}

export const LiveSignals: React.FC = () => {
  const [signals, setSignals] = React.useState<TradingSignal[]>([]);

  // 실제 구현에서는 WebSocket을 통해 시그널을 수신
  // 여기서는 데모 데이터를 사용
  React.useEffect(() => {
    const demoSignals: TradingSignal[] = [
      {
        ticker: 'NVDA',
        action: 'BUY',
        confidence: 0.85,
        reasoning: 'AI 칩 수요 증가, 강력한 기술적 지지선',
        timestamp: new Date().toISOString()
      },
      {
        ticker: 'AAPL',
        action: 'SELL',
        confidence: 0.72,
        reasoning: '과매도 상태, MACD 교차',
        timestamp: new Date(Date.now() - 60000).toISOString()
      }
    ];

    setSignals(demoSignals);
  }, []);

  return (
    <Card title="실시간 시그널" size="small">
      {signals.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '20px', color: '#8c8c8c' }}>
          시그널 없음
        </div>
      ) : (
        <List
          dataSource={signals}
          renderItem={(signal) => (
            <List.Item>
              <SignalItem signal={signal} />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

interface SignalItemProps {
  signal: TradingSignal;
}

const SignalItem: React.FC<SignalItemProps> = ({ signal }) => {
  const isBuy = signal.action === 'BUY';
  const color = isBuy ? '#52c41a' : '#ff4d4f';

  return (
    <div
      style={{
        padding: 12,
        borderLeft: `4px solid ${color}`,
        backgroundColor: isBuy ? 'rgba(82, 196, 26, 0.05)' : 'rgba(255, 77, 79, 0.05)',
        borderRadius: 4
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, fontSize: 16, fontWeight: 'bold' }}>
          {signal.ticker}
        </h4>
        <Tag color={isBuy ? 'green' : 'red'}>
          {signal.action}
        </Tag>
      </div>

      <div style={{ marginTop: 8 }}>
        <span style={{ fontSize: 12, color: '#8c8c8c' }}>신뢰도: </span>
        <span style={{ fontSize: 14, fontWeight: 'bold', color }}>
          {(signal.confidence * 100).toFixed(0)}%
        </span>
      </div>

      <div style={{ marginTop: 4, fontSize: 12 }}>
        {signal.reasoning}
      </div>

      <div style={{ marginTop: 4, fontSize: 10, color: '#bfbfbf' }}>
        {new Date(signal.timestamp).toLocaleString('ko-KR')}
      </div>
    </div>
  );
};
