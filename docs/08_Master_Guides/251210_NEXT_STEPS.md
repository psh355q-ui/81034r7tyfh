# 다음 작업 계획 (Next Steps)

**Updated**: 2025-12-06 (최신 업데이트)  
**문서 버전**: 2.0  
**기반 문서**: [251210_Project_Total_Docs.md](251210_Project_Total_Docs.md)

---

## ✅ 완료된 작업

### Phase E (Defensive Consensus System) - 완료
- ✅ **E1: 3-AI Voting System** - 비대칭 투표 로직
- ✅ **E2: DCA Strategy** - 펀더멘털 기반 물타기
- ✅ **E3: Position Tracking** - 포지션 추적 & 손익 관리

### Option 1 (전체 시스템 통합) - 완료 ✅
- ✅ **Task 1.1**: Deep Reasoning Strategy → Consensus 연동
- ✅ **Task 1.2**: 뉴스 이벤트 → DCA 자동 평가
- ✅ **Task 1.3**: Position Tracker ↔ KIS Broker 동기화
- ✅ **Task 1.4**: 통합 테스트
- 📄 **보고서**: [251210_11_Option1_Integration_Complete.md](../02_Phase_Reports/251210_11_Option1_Integration_Complete.md)

### Option 2 (자동 거래 시스템) - 완료 ✅
- ✅ **Task 2.1**: AutoTrader 클래스 (Consensus 승인 시 자동 주문)
- ✅ **Task 2.2**: Stop-Loss 실시간 모니터링
- ✅ **Task 2.3**: WebSocket 실시간 알림 시스템
- ✅ **Task 2.4**: 통합 테스트
- 📄 **보고서**: [251210_12_Option2_AutoTrading_Complete.md](../02_Phase_Reports/251210_12_Option2_AutoTrading_Complete.md)

**전체 완성도**: Phase 0-16 + A-E + Option 1-2 모두 완료 (100%)

---

## 🎯 다음 단계 옵션

### ~~옵션 1: 전체 시스템 통합~~ ✅ 완료

~~**목표**: Phase A-D와 Phase E 연결하여 완전한 자동화 파이프라인 구축~~

**작업 내용**:

작업 1.1**: Deep Reasoning Strategy → Consensus 연동
```python
# backend/ai/strategies/deep_reasoning_strategy.py
from backend.ai.consensus import get_consensus_engine

class DeepReasoningStrategy:
    async def analyze_news(self, news_text: str):
        # 기존 분석
        signal = self.deep_analyze(news_text)
        
        # Consensus 투표 추가
        consensus = get_consensus_engine()
        result = await consensus.vote_on_signal(
            context=self.build_context(news_text),
            action=signal.action
        )
        
        if not result.approved:
            signal.action = "HOLD"  # 부결 시 보류
            signal.confidence *= 0.5
        
        return signal
```

**Task 1.2**: 뉴스 이벤트 → DCA 자동 평가
```python
# backend/data/news_analyzer.py
async def on_news_event(news):
    # Position 보유 중인 종목만 필터링
    if has_position(news.ticker):
        position = get_position(news.ticker)
        current_price = await get_price(news.ticker)
        
        # DCA 조건 체크
        if should_evaluate_dca(position current_price, news):
            dca_result = await consensus_engine.evaluate_dca(
                context=build_context(news, position),
                current_price=current_price,
                avg_entry_price=position.avg_entry_price
            )
            
            if dca_result.approved:
                await kis_broker.place_dca_order(position, dca_result)
```

**Task 1.3**: Position Tracker ↔ KIS Broker 동기화
```python
# backend/database/models.py
class Position(Base):
    __tablename__ = "positions"
    
    ticker = Column(String, primary_key=True)
    avg_entry_price = Column(Float)
    quantity = Column(Integer)
    dca_count = Column(Integer, default=0)
    last_dca_date = Column(DateTime)
    
    # DCA 내역 추적
    dca_entries = relationship("DCAEntry", back_populates="position")

# backend/brokers/kis_broker.py
async def on_order_filled(order):
    # 체결 시 자동으로 Position 업데이트
    await position_tracker.update_from_order(order)
```

**예상 기간**: 2-3일  
**파일 수정**: 5개 파일 (strategy, news_analyzer, models, kis_broker)  
**예상 코드량**: ~800 lines  

---

### ~~옵션 2: 자동 거래 시스템~~ ✅ 완료

~~**목표**: Consensus 승인 시 자동 주문 실행, Stop-loss 모니터링~~

**작업 내용**:

**Task 2.1**: 자동 주문 실행기 구현
```python
# backend/automation/auto_trader.py (신규 생성)
class AutoTrader:
    async def on_consensus_approved(self, result: ConsensusResult):
        if result.action == "BUY":
            order = await self.broker.buy(
                ticker=result.ticker,
                quantity=self.calculate_position_size(result),
                order_type="MARKET"
            )
            await self.position_tracker.add_position(order)
            
        elif result.action == "DCA":
            position = await self.position_tracker.get(result.ticker)
            dca_quantity = self.calculate_dca_size(position, result)
            
            order = await self.broker.buy(
                ticker=result.ticker,
                quantity=dca_quantity
            )
            await self.position_tracker.add_dca_entry(position, order)
            
        elif result.action == "STOP_LOSS":
            position = await self.position_tracker.get(result.ticker)
            await self.broker.sell(result.ticker, position.quantity)
            await self.position_tracker.close_position(result.ticker)
```

**Task 2.2**: Stop-loss 실시간 모니터링
```python
# background task
async def monitor_stop_loss():
    while True:
        for position in tracker.get_open_positions():
            current_price = await get_price(position.ticker)
            
            # 손실률 체크
            loss_pct = (current_price - position.avg_entry_price) / position.avg_entry_price
            
            if loss_pct < -0.10:  # -10% 손실
                # Consensus 투표 (1/3만 찬성해도 실행)
                result = await consensus_engine.vote_on_signal(
                    context=build_context(position),
                    action="STOP_LOSS"
                )
                
                if result.approved:
                    await auto_trader.execute_stop_loss(position)
                    await notify_user(f"Stop-loss executed for {position.ticker}")
        
        await asyncio.sleep(60)  # 1분마다 체크
```

**Task 2.3**: 실시간 알림 (WebSocket)
```python
# backend/notifications/webhook_notifier.py (신규 생성)
class WebSocketNotifier:
    async def on_consensus_decision(self, result: ConsensusResult):
        message = {
            "type": "consensus_decision",
            "action": result.action,
            "ticker": result.ticker,
            "approved": result.approved,
            "votes": f"{result.approve_count}/3",
            "timestamp": datetime.now().isoformat()
        }
        
        # WebSocket으로 실시간 전송
        await self.broadcast(message)
        
        # Telegram/Slack 알림
        if result.approved and result.action != "HOLD":
            await telegram_notifier.send(message)
```

**예상 기간**: 3-4일  
**파일 생성**: 3개 (auto_trader.py, webhook_notifier.py, monitor_service.py)  
**예상 코드량**: ~1,200 lines  

---

### Option 3: 백테스팅 & 성과 분석 (Backtesting) - 완료 ✅

**목표**: DCA + Consensus 전략 성과 검증

**작업 내용**:
- ✅ **Task 3.1**: 과거 데이터 시뮬레이션 (`ConsensusBacktest`)
- ✅ **Task 3.2**: 성과 지표 분석 (`ConsensusPerformanceAnalyzer`)
- ✅ **Task 3.3**: 최적 파라미터 탐색
- 📄 **보고서**: [251210_13_Option3_Backtesting_Complete.md](../Dummy_Link_Will_Create_Later.md)

**완료된 코드**:
- `backend/backtesting/backtest_engine.py`: 이벤트 기반 백테스트 엔진
- `backend/backtesting/consensus_backtest.py`: Consensus 전략 백테스트 러너
- `backend/backtesting/consensus_performance_analyzer.py`: 성과 분석기
- `scripts/run_consensus_backtest.py`: 실행 스크립트

**테스트 결과**:
- Mock 데이터를 사용하여 전체 파이프라인(데이터→신호→주문→분석) 작동 검증 완료
- 성과 보고서 자동 생성 기능 확인

---

### Option 4: 리스크 관리 강화 (Risk Management) - 완료 ✅

**목표**: 포트폴리오 레벨 리스크 관리

**작업 내용**:
- ✅ **Task 4.1**: 포트폴리오 매니저 (`PortfolioManager`) - 리밸런싱 로직 구현
- ✅ **Task 4.2**: 리스크 분석 통합 - `RiskSkill` (VaR, CVaR) 연동
- ✅ **Task 4.3**: 상관관계/집중도 분석 및 알림
- 📄 **보고서**: [251210_14_Option4_RiskManagement_Complete.md](../Dummy_Link_Will_Create_Later.md)

**완료된 코드**:
- `backend/analytics/portfolio_manager.py`: 리스크 관리 및 리밸런싱 제안
- `scripts/run_risk_analysis.py`: 검증 스크립트 (시나리오 테스트)

**테스트 결과**:
- 고위험 포트폴리오(집중투자) 감지 및 리밸런싱(매도) 제안 생성 확인
- 최대 낙폭(Max Drawdown) 경고 시스템 작동 확인

---

## 💡 추천 순서

### ~~1단계: 옵션 1 (전체 통합)~~ ✅ 완료
~~**이유**: Phase E가 독립적으로 작동 중이므로, 기존 시스템과 연결하는 것이 자연스러운 다음 단계~~

### ~~2단계: 옵션 2 (자동 거래)~~ ✅ 완료
~~**이유**: 통합 후 실전 사용 가능한 완전 자동화 시스템 구축~~

### 1단계: 옵션 3 (백테스팅) - 4-5일 ⭐ (최우선 추천)
**이유**: 자동 거래 시스템이 완성되었으므로, 전략 성과 검증이 필수

### 2단계: 옵션 4 (리스크 관리) - 3-4일
**이유**: 실전 운영 전 리스크 관리 강화 필요

---

## 🚨 Gap Analysis 기반 추가 작업 (옵션 5+)

### 옵션 5: 문서화 보완

**목표**: 사용자/개발자 가이드 강화

**작업 내용**:
- [ ] `docs/Phase16_Incremental_Update_Guide.md` - 증분 업데이트 상세 가이드
- [ ] `docs/251210_Security_Best_Practices.md` - InputGuard, WebhookSecurity 사용법
- [ ] `docs/251210_Performance_Tuning.md` - Redis/TimescaleDB 최적화
- [ ] `docs/251210_Troubleshooting_Guide.md` - 자주 발생하는 오류 해결
- [ ] `docs/251210_Setup_Wizard_Guide.md` - 초보자용 설치 가이드

**예상 기간**: 2일  
**예상 문서량**: 5개 파일, ~5,000 words  

### 옵션 6: Alpaca Broker 통합

**목표**: 미국 주식 거래 지원 (현재 KIS만 있음)

**작업 내용**:
```python
# backend/brokers/alpaca_broker.py (신규 생성)
class AlpacaBroker:
    """Alpaca API 통합 (미국 주식 거래)"""
    
    def __init__(self):
        self.api = alpaca_trade_api.REST(
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_SECRET_KEY"),
            base_url=os.getenv("ALPACA_BASE_URL")
        )
    
    async def buy(self, ticker, quantity):
        order = self.api.submit_order(
            symbol=ticker,
            qty=quantity,
            side='buy',
            type='market',
            time_in_force='day'
        )
        return order
```

**환경 변수 추가**:
```bash
# .env
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # 모의투자
```

**예상 기간**: 2일  
**파일 생성**: 1개 (alpaca_broker.py)  
**예상 코드량**: ~800 lines  

### 옵션 7: CI/CD 파이프라인 구축

**목표**: GitHub Actions로 자동 테스트 + 배포

**작업 내용**:
```yaml
# .github/workflows/ci.yml (신규 생성)
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ --cov=backend --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        run: |
          ssh ${{ secrets.NAS_HOST }} "cd /volume1/ai_trading && git pull && docker-compose up -d --build"
```

**예상 기간**: 1-2일  
**파일 생성**: 2개 (ci.yml, deploy.sh)  

### 옵션 8: 모바일 앱 (React Native)

**목표**: 스마트폰에서 포트폴리오 모니터링

**작업 내용**:
- React Native 프로젝트 초기화
- Dashboard 모바일 버전
- Push Notification (Consensus 결정 알림)
- 주문 승인/거부 UI

**예상 기간**: 7-10일  
**파일 생성**: 30+ files (새 프로젝트)  

### 옵션 9: ELK Stack 로그 중앙화

**목표**: 로그 검색 및 분석 강화

**작업 내용**:
```yaml
# docker-compose.yml에 추가
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
  
  logstash:
    image: docker.elastic.co/logstash/logstash:8.10.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch
  
  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

**예상 기간**: 2-3일  

### 옵션 10: Tax Loss Harvesting

**목표**: 세금 최적화 (미국 주식)

**작업 내용**:
```python
# backend/strategies/tax_harvesting.py (신규 생성)
class TaxLossHarvester:
    async def identify_opportunities(self, positions):
        opportunities = []
        
        for position in positions:
            if position.unrealized_loss > 3000:  # $3,000 이상 손실
                # 유사 종목 찾기 (Wash Sale Rule 회피)
                similar_tickers = await self.find_similar_stocks(position.ticker)
                
                opportunities.append({
                    "sell": position.ticker,
                    "buy": similar_tickers[0],  # 가장 유사한 종목
                    "tax_benefit": position.unrealized_loss * 0.22  # 세율 22% 가정
                })
        
        return opportunities
```

**예상 기간**: 2일  
**파일 생성**: 1개 (tax_harvesting.py)  

---

## 📋 각 옵션별 세부 작업 (기존 유지)

### 옵션 1 상세 계획

**Task 1.1**: Deep Reasoning → Consensus 연동
- [ ] DeepReasoningStrategy에 Consensus 호출 추가
- [ ] InvestmentSignal → ConsensusResult 변환 로직
- [ ] Phase D API에서 Consensus 결과 반환

**Task 1.2**: 뉴스 이벤트 → DCA 자동 평가
- [ ] News aggregator에 이벤트 리스너 추가
- [ ] Position 보유 중인 종목 뉴스 필터링
- [ ] DCA 평가 자동 트리거

**Task 1.3**: Position ↔ KIS 동기화
- [ ] KIS 주문 체결 시 Position 자동 업데이트
- [ ] Position DCA 추가 시 KIS 자동 주문
- [ ] 데이터 일관성 보장 (트랜잭션)

### 옵션 2 상세 계획

**Task 2.1**: 자동 주문 실행기 구현
- [ ] AutoTrader 클래스 생성
- [ ] Consensus 승인 → 주문 파이프라인
- [ ] 실행 로그 및 오류 처리

**Task 2.2**: Stop-loss 모니터링
- [ ] 실시간 가격 모니터링 서비스
- [ ] Stop-loss 조건 체크 (손실률, 기간 등)
- [ ] Consensus 투표 → 자동 청산

**Task 2.3**: 실시간 알림
- [ ] WebSocket 알림 서비스
- [ ] Slack/Discord/Email 통합
- [ ] 알림 템플릿 및 우선순위

### 옵션 3 상세 계획

**Task 3.1**: 백테스트 엔진
- [ ] 과거 데이터 로더 (Yahoo Finance)
- [ ] 시뮬레이션 실행 엔진
- [ ] 포트폴리오 상태 추적

**Task 3.2**: 성과 분석
- [ ] Sharpe Ratio, Sortino Ratio 계산
- [ ] Maximum Drawdown 분석
- [ ] DCA 효과성 분석

**Task 3.3**: 파라미터 최적화
- [ ] Grid Search 구현
- [ ] 베이지안 최적화 (선택)
- [ ] 결과 시각화 (차트)

### 옵션 4 상세 계획

**Task 4.1**: 포트폴리오 분석
- [ ] 섹터/산업별 비중 계산
- [ ] 리밸런싱 로직
- [ ] 자동 리밸런싱 제안

**Task 4.2**: 리스크 측정
- [ ] VaR 계산 (Historical, Monte Carlo)
- [ ] CVaR (Conditional VaR)
- [ ] 베타, 상관관계 분석

**Task 4.3**: 리스크 제한
- [ ] Position size limit
- [ ] 섹터 exposure limit
- [ ] 총 레버리지 제한

---

## 🚀 시작 방법

사용자가 선택한 옵션에 따라:

```bash
# 옵션 1 선택 시
python scripts/integrate_phase_e.py

# 옵션 2 선택 시
python scripts/setup_auto_trading.py

# 옵션 3 선택 시
python scripts/run_consensus_backtest.py

# 옵션 4 선택 시
python scripts/setup_risk_management.py

# 옵션 5 선택 시 (문서화)
# docs/ 폴더에 새 가이드 생성

# 옵션 6 선택 시 (Alpaca)
python scripts/setup_alpaca_broker.py

# 옵션 7 선택 시 (CI/CD)
# GitHub Actions 설정
```

---

## 📞 다음 단계 결정

**질문**: 어떤 옵션으로 진행하시겠습니까?

### 핵심 옵션 (1-4)
1. **옵션 1: 전체 통합** ⭐ (Phase A-D-E 연결) - 가장 우선 추천
2. **옵션 2: 자동 거래** (Consensus → KIS 자동화)
3. **옵션 3: 백테스팅** (전략 성과 검증)
4. **옵션 4: 리스크 관리** (포트폴리오 리스크 컨트롤)

### 추가 옵션 (5-10)
5. **옵션 5: 문서화 보완** (사용자 가이드 강화)
6. **옵션 6: Alpaca 통합** (미국 주식 거래)
7. **옵션 7: CI/CD** (자동 테스트 + 배포)
8. **옵션 8: 모바일 앱** (React Native)
9. **옵션 9: ELK Stack** (로그 중앙화)
10. **옵션 10: Tax Harvesting** (세금 최적화)

### 조합 예시
- **조합 A**: 옵션 1 + 5 (통합 + 문서화)
- **조합 B**: 옵션 1 + 2 (통합 + 자동화)
- **조합 C**: 옵션 1 + 3 (통합 + 백테스팅)
- **조합 D**: 옵션 6 + 7 (Alpaca + CI/CD)

### 다른 아이디어
- 사용자 정의 요구사항을 말씀해주세요!

---

## 📊 우선순위 매트릭스

| 옵션 | 중요도 | 긴급도 | 난이도 | 예상 기간 | 우선순위 |
|------|-------|-------|-------|----------|---------|
| 옵션 1 (통합) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 2-3일 | **1위** |
| 옵션 2 (자동) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 3-4일 | **2위** |
| 옵션 3 (백테스트) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 4-5일 | **3위** |
| 옵션 4 (리스크) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 3-4일 | **4위** |
| 옵션 5 (문서) | ⭐⭐⭐ | ⭐⭐ | ⭐ | 2일 | 5위 |
| 옵션 6 (Alpaca) | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 2일 | 6위 |
| 옵션 7 (CI/CD) | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 1-2일 | 7위 |
| 옵션 8 (모바일) | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | 7-10일 | 8위 |
| 옵션 9 (ELK) | ⭐⭐ | ⭐ | ⭐⭐ | 2-3일 | 9위 |
| 옵션 10 (Tax) | ⭐⭐ | ⭐ | ⭐⭐ | 2일 | 10위 |

---

**사용자 입력을 기다립니다...**

**참고 문서**: [251210_Project_Total_Docs.md](251210_Project_Total_Docs.md) - 전체 프로젝트 종합 문서
