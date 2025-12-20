# MD 파일 분석 - PART1~6 및 n8n 워크플로우

**분석 대상**: `ideas/anotheraitradingsystem/PART*.md`  
**분석일**: 2025-12-15

---

## 📊 개요

외부 시스템의 MD 파일들은 **"US Market Backend Blueprint"**로, 데이터 수집부터 AI 분석, 웹 대시보드까지 포괄하는 완전한 시스템입니다.

---

## 1. 🎯 PART1~6 핵심 아이디어

### A. Smart Money Tracker (스마트 머니 추적) ⭐⭐⭐

#### 출처
- `PART1_Data_Collection.md`
- `PART2_Analysis_Screening.md`

#### 핵심 개념
단순 가격/거래량이 아닌, **기관 투자자의 움직임**을 추적

#### 구성 요소

**1. 기관 투자자 추적 (13F Filings)**
```python
# 분석 대상
- 헤지펀드 포지션 변화
- 뮤추얼 펀드 매수/매도
- 대형 기관 보유 비율 변화

# 신호
- 버크셔 해서웨이가 새로 매수 → 강력한 매수 신호
- 대형 펀드 3개 이상 청산 → 경고
```

**2. 내부자 거래 (Insider Trading)**
```python
# 추적 대상
- CEO, CFO 자사주 매매
- 임원진 집단 매수/매도
- 대량 주식 옵션 행사

# 활용
if CEO가 자사주 매수:
    매수 신호 가중치 += 20%
if 임원진 3명 이상 매도:
    리스크 경고
```

**3. ETF 자금 흐름 (ETF Flows)**
```python
# backend/data/collectors/etf_flow_tracker.py (신규 제안)

class ETFFlowTracker:
    """
    섹터별 ETF 자금 유입/유출 추적
    
    예시:
    - QQQ (나스닥): 3일 연속 10억 달러 유출
    - XLF (금융): 1주일 간 5억 달러 유입
    
    → 섹터 로테이션 감지
    """
    
    async def analyze_sector_rotation(self):
        # QQQ, SPY, XLF, XLE 등 주요 ETF 추적
        flows = await self.get_etf_flows()
        
        # 유입 상위 섹터 = HOT
        # 유출 상위 섹터 = COLD
        
        return SectorRotationSignal(
            hot_sectors=["Energy", "Financials"],
            cold_sectors=["Technology"],
            confidence=0.78
        )
```

#### 우리 시스템 적용

**현황**:
- ❌ 기관 추적 없음
- ❌ 내부자 거래 없음
- ❌ ETF 흐름 없음

**구현**:
```python
# backend/data/collectors/smart_money_collector.py (신규)

class SmartMoneyCollector:
    async def get_13f_filings(self, ticker: str):
        # SEC EDGAR API
        # Top 10 기관 보유 변화 추적
        pass
    
    async def get_insider_trades(self, ticker: str):
        # OpenInsider.com 크롤링
        # 최근 30일 내부자 거래
        pass
    
    async def get_etf_flows(self):
        # ETF.com API
        # 섹터별 자금 흐름
        pass
```

**활용**:
```python
# AIDebateEngine에 새 Agent 추가
class InstitutionalAgent:
    """기관 투자자 전담 AI"""
    
    async def analyze(self, ticker):
        smart_money = await smart_money_collector.collect(ticker)
        
        if smart_money.institution_buying_pressure > 0.7:
            return Signal.STRONG_BUY
```

---

### B. Macro Analyzer (거시경제 전담 AI) ⭐⭐⭐

#### 출처
- `PART3_AI_Analysis.md`

#### 핵심 개념
개별 종목이 아닌, **시장 전체 날씨** 판단

#### 역할
```python
# backend/ai/macro/macro_analyzer.py (신규)

class MacroAnalyzer:
    """
    거시경제 전담 분석
    
    입력:
    - 국채 금리 (10Y, 2Y)
    - VIX
    - 달러 지수
    - 원자재 가격
    
    출력:
    - Risk On / Risk Off
    - 주식 비중 권장 (0% ~ 100%)
    """
    
    async def analyze_market_regime(self):
        # 1. 데이터 수집
        treasury_10y = await self.get_treasury_yield("10Y")
        vix = await self.get_vix()
        dxy = await self.get_dollar_index()
        
        # 2. Claude에게 종합 판단 요청
        prompt = f"""
        현재 거시 지표:
        - 10년물 국채: {treasury_10y}%
        - VIX: {vix}
        - 달러 지수: {dxy}
        
        현재 시장 Regime을 판단하세요:
        1. Risk On (주식 강세 국면)
        2. Risk Off (방어 국면)
        3. Transition (전환기)
        """
        
        regime = await claude.generate(prompt)
        
        return MarketRegime(
            regime=regime,
            stock_allocation=self._calculate_allocation(regime)
        )
```

#### 우리 시스템 적용

**현황**:
- ✅ EnhancedFREDCollector 존재
- ✅ MarketRegime 개념 있음
- ❌ 전담 Macro AI 없음

**통합**:
```python
# AIDebateEngine에 추가
class MacroAgent:
    """거시경제 전담 - 매매 안함, 시장 방향만 판단"""
    
    async def get_market_direction(self):
        regime = await macro_analyzer.analyze_market_regime()
        
        if regime == "Risk Off":
            # 다른 Agent들에게 "현금 비중 높여" 지시
            return MarketDirective(
                action="REDUCE_RISK",
                cash_ratio=0.5
            )
```

---

### C. Economic Calendar (경제 캘린더 기반 예측) ⭐⭐

#### 출처
- `PART1_Data_Collection.md` - `economic_calendar.py`

#### 핵심 개념
**사후 대응이 아닌 선제 대응**

#### 워크플로우
```
오늘 (월요일)
    ↓
"수요일 CPI 발표 예정" 감지
    ↓
AI 예측: "CPI 상승 시 시장 반응은?"
    ↓
선제 조치: "변동성 클 때까지 매수 자제"
```

#### 구현
```python
# backend/data/collectors/economic_calendar.py (신규)

class EconomicCalendar:
    """
    향후 경제 이벤트 추적
    
    데이터 소스:
    - Investing.com Economic Calendar
    - Trading Economics
    """
    
    async def get_upcoming_events(self, days=7):
        events = [
            {
                "date": "2025-01-15 09:30",
                "event": "CPI (Consumer Price Index)",
                "importance": "HIGH",
                "forecast": "3.2%",
                "previous": "3.1%"
            },
            {
                "date": "2025-01-17 15:00",
                "event": "FOMC Meeting",
                "importance": "CRITICAL"
            }
        ]
        
        return events
    
    async def predict_impact(self, event):
        """AI가 이벤트 영향 예측"""
        prompt = f"""
        이벤트: {event['event']}
        예상: {event.get('forecast')}
        
        시장 영향 예측:
        1. 상승 시나리오
        2. 하락 시나리오
        3. 변동성 레벨
        """
        
        impact = await claude.generate(prompt)
        return impact
```

#### 활용
```python
# AutoTradingScheduler에 추가
async def check_economic_events(self):
    """매일 아침 경제 이벤트 체크"""
    
    events = await economic_calendar.get_upcoming_events(days=3)
    
    for event in events:
        if event['importance'] == 'CRITICAL':
            # 중요 이벤트 2일 전부터 매수 자제
            if event_in_2days(event):
                await self.set_trading_pause(
                    reason=f"{event['event']} 대기",
                    until=event['date']
                )
```

---

### D. TradingView 차트 시각화 ⭐

#### 출처
- `PART5_Frontend_UI.md`
- `PART6_Frontend_Logic.md`

#### 핵심 개념
전문가 수준의 차트 라이브러리

#### 특징
- **TradingView Lightweight Charts**
- 실시간 캔들스틱
- 거래량 표시
- 기술적 지표 오버레이
- 모바일 반응형

#### 우리 시스템 적용

**현황**:
- ✅ Recharts 사용 중 (기본)
- ❌ TradingView 없음

**고려사항**:
```javascript
// frontend/src/components/TradingViewChart.tsx (신규)

import { createChart } from 'lightweight-charts';

export default function TradingViewChart({ data }) {
    // TradingView 스타일 차트
    // Telegram Mini App에 최적
}
```

**장점**:
- 전문 트레이더 느낌
- 모바일 최적화
- 가볍고 빠름

---

## 2. 🔧 n8n 워크플로우 분석

### 파일: `Gemini File Search.json`

#### 현재 구조
```
On form submission (파일 업로드)
    ↓
Create File Store (벡터 스토어 저장)
    ↓
When chat message received (채팅 메시지)
    ↓
RAG Agent (Gemini + Knowledge Base)
    ↓
답변 생성
```

#### 핵심 노드
- **Knowledge Base**: 벡터 스토어 관리
- **RAG Agent**: Gemini AI + 검색
- **File Store**: 문서 임베딩

---

## 3. 🚀 Google Drive + Telegram RAG 서비스

### 개념
```
Google Drive (뉴스 PDF)
    ↓ (자동 감지)
벡터 DB 저장
    ↓
Telegram 질문
    ↓
RAG 검색 + Gemini 답변
    ↓
Telegram 답변 전송
```

### 구현 가능성: **매우 높음**

---

### 구현 방법 (2가지)

#### Option A: n8n 워크플로우 수정 (No Code)

**장점**: 코드 작성 불필요

**수정 사항**:
```
1. 트리거 변경
   [X] On form submission
   [O] Google Drive Trigger
       - 폴더: "Stock_News"
       - 이벤트: "New File Created"

2. 인터페이스 변경
   [X] When chat message received (n8n)
   [O] Telegram Trigger
       - 이벤트: "On Message"

3. 답변 전송
   [O] Telegram → Send Message
```

**최종 플로우**:
```
Google Drive (새 파일)
    ↓
파일 다운로드
    ↓
벡터 스토어 저장
    ↓
(별도) Telegram 메시지 수신
    ↓
RAG Agent (Gemini)
    ↓
Telegram 답변 전송
```

---

#### Option B: Python 자체 구현 (Full Control)

**장점**: 완전한 커스터마이징

```python
# backend/services/google_drive_rag.py (신규)

from google.oauth2 import service_account
from googleapiclient.discovery import build
from langchain.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class GoogleDriveRAG:
    """
    Google Drive 자동 학습 + Telegram RAG
    """
    
    def __init__(self):
        self.drive = self._init_drive()
        self.vectorstore = self._init_vectorstore()
    
    async def watch_drive_folder(self, folder_id: str):
        """
        Google Drive 폴더 모니터링
        새 파일 생기면 자동으로 벡터 DB에 저장
        """
        # Google Drive API - Changes.watch
        # Webhook으로 파일 변경 감지
        pass
    
    async def process_new_file(self, file_id: str):
        """새 파일 처리"""
        # 1. 다운로드
        content = await self.drive.download(file_id)
        
        # 2. 텍스트 추출 (PDF → Text)
        text = extract_text(content)
        
        # 3. 청크로 나누기
        chunks = split_text(text)
        
        # 4. 벡터 DB 저장
        await self.vectorstore.add_documents(chunks)
    
    async def answer_question(self, question: str):
        """RAG 검색 + Gemini 답변"""
        # 1. 벡터 검색
        docs = await self.vectorstore.similarity_search(question)
        
        # 2. Gemini에게 질문
        from backend.ai.gemini_client import get_gemini_client
        gemini = get_gemini_client()
        
        context = "\n".join([doc.page_content for doc in docs])
        
        prompt = f"""
        문서 내용:
        {context}
        
        질문: {question}
        
        위 문서 내용을 바탕으로 답변하세요.
        """
        
        answer = await gemini.generate(prompt)
        return answer
```

**Telegram Bot 연동**:
```python
# backend/services/telegram_bot_service.py 에 추가

from telegram.ext import MessageHandler

async def handle_rag_question(update, context):
    """RAG 질문 처리"""
    question = update.message.text
    
    # Google Drive RAG 검색
    rag = GoogleDriveRAG()
    answer = await rag.answer_question(question)
    
    # 답변 전송
    await update.message.reply_text(answer)

# 핸들러 등록
app.add_handler(MessageHandler(filters.TEXT, handle_rag_question))
```

---

### 활용 시나리오

**사용자 워크플로우**:
```
1. 아침에 증권사 리포트 PDF 다운로드
2. Google Drive "Stock_News" 폴더에 업로드
3. (자동) AI가 PDF 읽고 학습
4. 출근길에 Telegram으로 질문
   "오늘 삼성전자 리포트 요약해줘"
5. AI가 방금 업로드한 PDF에서 답변
```

---

## 4. 📋 구현 우선순위

### 즉시 구현 (1-2주)
1. **ETF Flow Tracker** - 섹터 로테이션 감지
2. **Economic Calendar** - 선제적 리스크 관리

### 중기 구현 (1개월)
3. **Smart Money Collector** - 기관/내부자 추적
4. **Macro Analyzer Agent** - 시장 Regime 판단

### 장기 구현 (2-3개월)
5. **Google Drive RAG** - 자동 학습 시스템
6. **TradingView Charts** - 시각화 고도화

---

## 5. 🎯 기대 효과

### Smart Money Tracker
- **수익률 개선**: +5-10%
- **신호 정확도**: +15%

### Macro Analyzer
- **손실 방지**: 시장 급락 시 조기 탈출
- **리스크 관리**: 현금 비중 동적 조정

### Economic Calendar
- **변동성 회피**: 중요 이벤트 전 포지션 조정
- **기회 포착**: 이벤트 후 빠른 진입

### Google Drive RAG
- **시간 절약**: 수동 리포트 읽기 불필요
- **즉시 활용**: 최신 정보 즉시 질의응답

---

## 6. 💰 추가 비용

### API 비용
- Google Drive API: **무료**
- Gemini Embeddings: ~$0.00002/1000 tokens
- 월 예상: ~$5-10

### 개발 시간
- ETF Tracker: 3일
- Economic Calendar: 2일
- Macro Analyzer: 5일
- Google Drive RAG: 1주
- **총 예상**: 3주

---

## 7. 🔧 기술 스택 추가

```bash
# Google Drive
pip install google-api-python-client google-auth

# Vector DB
pip install chromadb langchain-google-genai

# n8n (선택)
docker run -p 5678:5678 n8nio/n8n
```

---

**작성일**: 2025-12-15  
**다음 단계**: ETF Flow Tracker 또는 Economic Calendar부터 시작
