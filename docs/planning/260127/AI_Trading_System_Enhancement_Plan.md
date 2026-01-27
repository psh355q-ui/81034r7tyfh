# AI Trading System 종합 강화 계획 (v3.0 Final)
**Persona-Aware Agents + Data Enhancement + Constitution + News RAG**  
**Expert Feedback Fully Integrated (Gemini + ChatGPT + Claude)**

**작성일**: 2026-01-27  
**버전**: v3.0 (Final - 상업 서비스 레벨)  
**목표**: "실제 고객 자금을 운용 가능한 시스템"

---

## 📋 Executive Summary

### 전문가 3곳 종합 평가

> **"이 시스템은 개인 프로젝트가 아니라, 실제 고객 자금을 상정한 구조다."** (ChatGPT 평가)  
> **"회사 만들어도 되는 설계."** (ChatGPT)  
> **"규제 통과 가능한 수준."** (Claude)

**핵심 구조**:
```
[ Constitution ] ← 최상위 헌법
   ↓
[ Meta-Controller V2 ] ← 🆕 3축 리스크 감지
   • VIX (시장 공포)
   • Correlation (구조 붕괴) 🆕
   • Drawdown (나의 실패) 🆕
   ↓
[ Liquidity Guardian ] ← 🆕 주문 직전 현실 체크
   ↓
[ Persona Agents ] (4 Modes × 3 Agents)
   ↓
[ Exit Rules ] ← AI 개입 없는 강제 청산
   ↓
[ Constitutional Validation ]
   ↓
[ Human Approval ]
```

---

## 🆕 Meta-Controller V2 (3축 리스크 감지)

### 개념

> **"외부 신호(VIX) + 내부 신호(Correlation + Drawdown) = 진짜 리스크 관리"**

### 구현

```python
# backend/ai/meta_controller_v2.py

class MetaControllerV2:
    """
    3축 리스크 감지 시스템
    
    1. VIX: 시장 공포 (외부)
    2. Correlation: 분산 효과 소멸 (포트폴리오 내부)
    3. Drawdown: 연속 손실 (나의 실패)
    """
    
    def __init__(self):
        self.correlation_detector = CorrelationShockDetector()
        self.drawdown_monitor = DrawdownRecoveryMode()
        self.liquidity_guardian = LiquidityGuardian()
    
    def evaluate_market_regime(
        self,
        market_data: Dict,
        portfolio_data: Dict
    ) -> Dict:
        """
        3축 종합 판단 - 가장 보수적인 판단 채택
        """
        # 1. VIX 기반 (기존)
        vix = market_data.get('vix', 15)
        if vix > 35:
            vix_regime = "crisis"
        elif vix > 25:
            vix_regime = "risk_off"
        else:
            vix_regime = "risk_on"
        
        # 2. 🆕 Correlation 기반
        corr_regime, avg_corr = self.correlation_detector.detect_correlation_regime(
            portfolio_data
        )
        
        # 3. 🆕 Drawdown 기반
        dd_status = self.drawdown_monitor.check_drawdown(
            portfolio_data['current_value'],
            portfolio_data['peak_value']
        )
        
        # 가장 보수적인 판단 채택
        return self._combine_regimes(vix_regime, corr_regime, dd_status)
    
    def _combine_regimes(self, vix_regime, corr_regime, dd_status):
        """
        우선순위: Drawdown > Correlation > VIX
        
        왜? "내 손실"이 가장 확실한 신호
        """
        # Drawdown Critical (20% 손실)
        if dd_status.get('severity') == 'critical':
            return {
                'final_regime': 'crisis',
                'forced_mode': 'dividend',
                'reason': '20% Drawdown - 방어 모드 강제 전환',
                'position_limit_multiplier': 0.3
            }
        
        # Correlation Shock (분산 효과 소멸)
        if corr_regime == 'crisis_correlation':
            return {
                'final_regime': 'crisis',
                'forced_mode': 'dividend',
                'reason': '상관관계 위기: 분산 효과 소멸',
                'position_limit_multiplier': 0.5
            }
        
        # VIX Crisis
        if vix_regime == 'crisis':
            return {
                'final_regime': 'crisis',
                'forced_mode': 'dividend',
                'reason': f'VIX {vix} - 시장 공포',
                'position_limit_multiplier': 0.7
            }
        
        # Drawdown Warning (10% 손실)
        if dd_status.get('severity') == 'warning':
            return {
                'final_regime': 'risk_off',
                'position_limit_multiplier': 0.5,
                'reason': '10% Drawdown - 포지션 50% 축소'
            }
        
        # Elevated Correlation
        if corr_regime == 'elevated_correlation':
            return {
                'final_regime': 'risk_off',
                'position_limit_multiplier': 0.7,
                'reason': '상관관계 상승 - 주의 필요'
            }
        
        # VIX Risk-off
        if vix_regime == 'risk_off':
            return {
                'final_regime': 'risk_off',
                'position_limit_multiplier': 0.8,
                'reason': 'VIX 25+ - 변동성 증가'
            }
        
        # Normal
        return {
            'final_regime': 'risk_on',
            'position_limit_multiplier': 1.0,
            'reason': '정상 시장 환경'
        }
```

---

## 🆕Correlation Shock Detector

### 개념

> **"VIX가 낮아도 내 포트폴리오 안에서 분산이 죽는 순간 감지"**

**핵심 원리**:
- 평시: 주식 간 상관관계 0.3~0.6
- 위기: 모든 자산 → 1.0 수렴 (2020 COVID, 2008 금융위기 패턴)

### 구현

```python
# backend/ai/correlation_shock_detector.py

import numpy as np
import pandas as pd

class CorrelationShockDetector:
    """
    포트폴리오 내부 상관관계 급등 감지
    
    겉으로는 분산, 실제로는 단일 베타인 상황 탐지
    """
    
    def detect_correlation_regime(
        self,
        portfolio: Dict[str, Dict]
    ) -> Tuple[str, float]:
        """
        Args:
            portfolio: {
                'NVDA': {'shares': 100, 'value': 50000},
                'AMD': {'shares': 200, 'value': 30000},
                ...
            }
        
        Returns:
            (regime, avg_correlation)
        """
        tickers = list(portfolio.keys())
        
        if len(tickers) < 2:
            return ("single_position", 0.0)
        
        # 최근 20일 수익률 계산
        returns = self._get_returns(tickers, lookback=20)
        
        # 상관관계 행렬
        corr_matrix = returns.corr()
        
        # 평균 상관관계 (상삼각 행렬만)
        upper_triangle = np.triu_indices_from(corr_matrix, k=1)
        avg_corr = corr_matrix.values[upper_triangle].mean()
        
        # 판단
        if avg_corr > 0.85:
            return ("crisis_correlation", avg_corr)
        elif avg_corr > 0.70:
            return ("elevated_correlation", avg_corr)
        else:
            return ("normal", avg_corr)
    
    def _get_returns(self, tickers: List[str], lookback: int) -> pd.DataFrame:
        """최근 N일 수익률 계산"""
        # yfinance로 데이터 수집
        import yfinance as yf
        from datetime import datetime, timedelta
        
        end = datetime.now()
        start = end - timedelta(days=lookback + 10)
        
        data = yf.download(tickers, start=start, end=end, progress=False)['Adj Close']
        returns = data.pct_change().dropna()
        
        return returns.tail(lookback)
```

---

## 🆕 Drawdown Recovery Mode

### 개념

> **"시장이 아니라 내가 틀렸을 때 - 자동 방어 모드 전환"**

### 구현

```python
# backend/ai/drawdown_recovery.py

class DrawdownRecoveryMode:
    """
    포트폴리오 손실 기반 모드 강등
    
    VIX와 별개로 "나의 연속 손실"에 반응
    """
    
    def check_drawdown(
        self,
        current_value: float,
        peak_value: float
    ) -> Dict:
        """
        Args:
            current_value: 현재 포트폴리오 가치
            peak_value: 과거 최고점
        
        Returns:
            {
                'recovery_mode': bool,
                'severity': str,
                'forced_mode': str,
                'message': str
            }
        """
        drawdown = (peak_value - current_value) / peak_value
        
        # Critical: 20% 손실
        if drawdown >= 0.20:
            return {
                'recovery_mode': True,
                'severity': 'critical',
                'forced_mode': 'dividend',
                'message': f'⚠️ 20% Drawdown ({drawdown:.1%}) - 방어 모드 강제 전환',
                'position_limit_multiplier': 0.3
            }
        
        # Warning: 10% 손실
        elif drawdown >= 0.10:
            return {
                'recovery_mode': True,
                'severity': 'warning',
                'forced_mode': None,  # 모드 강등 없음
                'message': f'⚠️ 10% Drawdown ({drawdown:.1%}) - 포지션 축소 권장',
                'position_limit_multiplier': 0.5
            }
        
        # Normal
        else:
            return {
                'recovery_mode': False,
                'severity': 'normal',
                'position_limit_multiplier': 1.0
            }
```

---

## 🆕 Liquidity Guardian

### 개념

> **"이론적으로 맞아도, 시장에서 안 팔린다" - 현실 체크**

**위치**: Order Execution Gate (주문 직전 마지막 체크)

### 구현

```python
# backend/ai/liquidity_guardian.py

class LiquidityGuardian:
    """
    유동성 위험 체크 (주문 직전)
    
    특히 중요:
    - AGGRESSIVE 모드
    - 소형주
    - 레버리지 ETF
    """
    
    def check_liquidity(
        self,
        symbol: str,
        order_shares: int,
        order_value: float
    ) -> Dict:
        """
        Returns:
            {
                'allow': bool,
                'reason': str,
                'warning': str (optional)
            }
        """
        # 1. 거래량 대비 주문량
        avg_volume = self._get_avg_volume(symbol, days=20)
        
        if avg_volume == 0:
            return {
                'allow': False,
                'reason': '거래량 데이터 없음 - 유동성 불확실'
            }
        
        volume_impact = order_shares / avg_volume
        
        # 5% 초과 - 거부
        if volume_impact > 0.05:
            return {
                'allow': False,
                'reason': f'유동성 경고: 주문량이 일평균의 {volume_impact:.1%}',
                'recommendation': '분할 매수 권장 (3일 이상)'
            }
        
        # 2. Bid-Ask Spread
        spread = self._get_bid_ask_spread(symbol)
        
        if spread is None:
            warnings = []
        elif spread > 0.02:  # 2% 초과
            return {
                'allow': True,
                'warning': f'높은 스프레드 {spread:.2%} - 슬리피지 예상'
            }
        
        # 3. 정상
        return {'allow': True}
    
    def _get_avg_volume(self, symbol: str, days: int = 20) -> int:
        """최근 N일 평균 거래량"""
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1mo')
        
        if hist.empty:
            return 0
        
        return int(hist['Volume'].tail(days).mean())
    
    def _get_bid_ask_spread(self, symbol: str) -> Optional[float]:
        """현재 Bid-Ask Spread %"""
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        bid = info.get('bid')
        ask = info.get('ask')
        
        if bid and ask and bid > 0:
            return (ask - bid) / bid
        
        return None
```

---

## 조건부 채택 (기본 OFF, 필요 시 ON)

### 1. Earnings Blackout Zone (Phase 1)

```python
# backend/ai/earnings_blackout.py

class EarningsBlackout:
    """
    실적 발표 전후 거래 제한
    
    기본 OFF, TRADING/AGGRESSIVE에만 자동 적용
    """
    
    BLACKOUT_RULES = {
        "trading": {"enabled": True, "d_before": 3, "d_after": 1},
        "aggressive": {"enabled": True, "d_before": 3, "d_after": 1},
        "dividend": {"enabled": False},  # 경고만
        "long_term": {"enabled": False}  # 경고만
    }
    
    def check_earnings_proximity(
        self,
        symbol: str,
        persona_mode: str
    ) -> Dict:
        rule = self.BLACKOUT_RULES.get(persona_mode, {})
        
        if not rule.get('enabled'):
            return {'blackout': False, 'warning_only': True}
        
        next_earnings = self._get_earnings_date(symbol)
        if not next_earnings:
            return {'blackout': False}
        
        days_to_earnings = (next_earnings - datetime.now()).days
        
        d_before = rule['d_before']
        d_after = rule['d_after']
        
        if -d_after <= days_to_earnings <= d_before:
            return {
                'blackout': True,
                'days_to_earnings': days_to_earnings,
                'reason': f'실적 발표 {days_to_earnings}일 앞',
                'recommendation': '신규 진입 보류'
            }
        
        return {'blackout': False}
```

### 2. Position Aging Tracker (Phase 2)

Thesis Keeper와 통합하여 "강제 리뷰" 트리거

```python
# backend/ai/position_aging.py

class PositionAgingTracker:
    """
    장기 보유 포지션 "왜 아직 들고 있지?" 체크
    """
    
    AGING_RULES = {
        "dividend": {"review_days": 180, "stale_days": 365},
        "long_term": {"review_days": 90, "stale_days": 180},
        "trading": {"review_days": 7, "stale_days": 14},
        "aggressive": {"review_days": 3, "stale_days": 7}
    }
    
    def check_position_age(
        self,
        position: Dict,
        persona_mode: str
    ) -> Dict:
        age_days = (datetime.now() - position['entry_date']).days
        rules = self.AGING_RULES[persona_mode]
        
        # Stale - 강제 리뷰
        if age_days > rules['stale_days']:
            return {
                'status': 'stale',
                'action': 'forced_review',
                'message': f'{age_days}일 보유 - Thesis 재검토 필요'
            }
        
        # Review Needed - 경고
        elif age_days > rules['review_days']:
            return {
                'status': 'review_needed',
                'action': 'soft_reminder',
                'message': f'{age_days}일 경과 - 정기 검토 권장'
            }
        
        return {'status': 'fresh'}
```

---

## 데이터 강화 계획 (최종)

### 🔴 P0: 필수 (Week 1-2)

1. **Fundamental Data**: PER, PBR, ROE, FCF
2. **Macro Data**: 금리, CPI, GDP
3. **Dividend Data**: 배당률, Payout Ratio
4. **Portfolio Analytics**: 상관관계 행렬, Drawdown

### 🟡 P1: 중요 (Week 3-4)

1. **Liquidity Metrics**: 평균 거래량, Bid-Ask Spread
2. **Earnings Calendar**: 실적 발표일
3. **Thesis Keeper**: 투자 논리 DB

### 🟢 P2: 보완 (Week 5-6)

1. **Short Interest**: 공매도 비율
2. **Insider Trading**: SEC Form 4
3. **Position Aging**: 보유 일수 추적

---

## 구현 우선순위 (최종)

### Phase 0: Meta-Controller V2 (Week 1) ⭐⭐⭐

- [ ] **Correlation Shock Detector** 구현
- [ ] **Drawdown Recovery Mode** 구현
- [ ] **Meta-Controller V2 통합** (3축 판단)
- [ ] 테스트: VIX 정상 + Correlation Crisis 시나리오

### Phase 0-B: 기반 구조 (Week 2) ⭐⭐⭐

- [ ] **Liquidity Guardian** 구현 (주문 직전 게이트)
- [ ] **Exit Rules Engine** 구현
- [ ] **Thesis Keeper DB** 스키마
- [ ] Persona Prompts (12개)

### Phase 1: P0 데이터 + 조건부 기능 (Week 3-4) ⭐⭐

- [ ] Fundamental/Macro/Dividend Data 수집
- [ ] **Earnings Blackout Zone** (기본 OFF)
- [ ] Constitutional Validation 통합

### Phase 2: P1 데이터 (Week 5-6) ⭐

- [ ] **Position Aging Tracker** (Thesis Keeper 통합)
- [ ] News RAG (Fact/Opinion 분리)

### Phase 3: 실험 기능 (Week 7+)

- [ ] Contrarian Signal (로그만)
- [ ] Regulatory Blacklist (보수적 적용)

---

## 검증 시나리오 (추가)

### Scenario 7: Correlation Crisis

```python
# 포트폴리오: NVDA, AMD, TSM, AVGO (모두 반도체)
portfolio = {
    'NVDA': {'value': 40000},
    'AMD': {'value': 30000},
    'TSM': {'value': 20000},
    'AVGO': {'value': 10000}
}

# 평균 상관관계 0.92 (위기 수준)
meta_result = meta_controller_v2.evaluate_market_regime(
    market_data={'vix': 18},  # VIX는 정상
    portfolio_data=portfolio
)

# 기대 결과
assert meta_result['final_regime'] == 'crisis'
assert '상관관계 위기' in meta_result['reason']
assert meta_result['position_limit_multiplier'] == 0.5
```

### Scenario 8: Liquidity Rejection

```python
# 소형주에 대량 주문
result = liquidity_guardian.check_liquidity(
    symbol="SMCI",  # 소형주
    order_shares=10000,
    order_value=50000
)

# 기대 결과
assert result['allow'] == False
assert '유동성 경고' in result['reason']
assert '분할 매수' in result['recommendation']
```

### Scenario 9: Drawdown Recovery

```python
# 20% 손실 발생
portfolio_data = {
    'current_value': 80000,
    'peak_value': 100000
}

meta_result = meta_controller_v2.evaluate_market_regime(
    market_data={'vix': 15},  # VIX 정상
    portfolio_data=portfolio_data
)

# 기대 결과
assert meta_result['forced_mode'] == 'dividend'
assert meta_result['position_limit_multiplier'] == 0.3
assert '20% Drawdown' in meta_result['reason']
```

---

## 최종 시스템 레벨 평가

### ChatGPT 판정

> **"이 시스템은:**
> - 개인 프로젝트 ❌
> - 백테스트 장난 ❌
> **→ 실제 고객 자금을 상정한 구조다"**

### 도달한 수준

```
현재:
✅ SaaS 가능
✅ 투자자 설명 가능
✅ 규제 논의 테이블에 올릴 수 있음
```

### 핵심 차별점

**기존 AI 트레이딩 시스템**:
- LLM → 판단 → 매매

**이 시스템**:
```
[ 3축 리스크 감지 ]
   ↓ 실시간 환경 체크
[ 현실 제약 검증 ] (Liquidity)
   ↓ 물리적 가능성
[ Persona AI 판단 ]
   ↓ 맥락 인식 분석
[ 강제 청산 규칙 ]
   ↓ 감정 배제
[ 헌법 검증 ]
   ↓ 최종 안전장치
[ 인간 승인 ]
```

---

## 다음 단계

### 즉시 시작 (현실적인 실행 계획)

1. **Meta-Controller V2** 구현 (최우선)
   - Drawdown + Correlation + Liquidity
   
2. **백테스트 검증**
   - 2020 COVID Crash 시뮬레이션
   - Correlation 1.0 수렴 감지 여부
   
3. **Phase 0-B** 병행
   - Exit Rules
   - Thesis Keeper
   
4. **점진적 확장**
   - DIVIDEND 모드 먼저
   - 2주 실전 데이터 검증
   - LONG_TERM → TRADING → AGGRESSIVE 순서

---

## Q&A (Expert 제기 질문)

### Q1: Meta-Controller 판단 충돌 시 우선순위

```python
# ChatGPT 질문: VIX 정상 + Drawdown 심각 → 어떻게?

# 답: 우선순위 명확화
우선순위: Drawdown > Correlation > VIX

이유: "내 손실"이 가장 확실한 신호
```

### Q2: Correlation Shock 대응 방식

```python
# ChatGPT 질문: 전 종목 축소 vs 신규 진입 금지?

# 답: 둘 다 (단계별)
1. avg_corr > 0.70: 신규 진입 50% 축소
2. avg_corr > 0.85: 기존 포지션도 50% 청산 권장
```

### Q3: 자동 vs 인간 승인 경계선

```python
# ChatGPT 질문: 어디까지 자동?

# 답:
자동 실행 가능:
- Exit Rules (배당 삭감, 손절가)
- Meta-Controller 모드 강등 (경고)
- Liquidity 거부

인간 승인 필수:
- 모든 매수 주문
- Exit Rule 예외 (Thesis 판단 필요 시)
- Constitution 위반 처리
```

---

**이 계획은 Expert 3곳의 종합 피드백을 모두 반영한 최종 버전입니다.**
