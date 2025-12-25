# AI Trading System - Coding Standards

## 📋 목적
AI 에이전트의 효율적인 코드 분석을 위해 모든 코드 파일에 명확한 메타데이터와 주석을 포함합니다.

## 🔧 Python 파일 표준

### 1. 파일 헤더 주석 (필수)
모든 `.py` 파일 상단에 다음 정보를 포함해야 합니다:

```python
"""
[파일명] - [간단한 설명]

📊 Data Sources:
    - KIS API: 포트폴리오 데이터, 잔고 조회
    - Yahoo Finance: 배당 정보, 섹터 정보
    - PostgreSQL: [테이블명] - [용도]

🔗 External Dependencies:
    - yfinance: 주식 데이터 조회
    - requests: HTTP 통신
    - pandas: 데이터 처리

📤 API Endpoints (if applicable):
    - GET /api/portfolio: 포트폴리오 조회
    - POST /api/rebalance: 리밸런싱 실행

🔄 Called By:
    - frontend/src/pages/Portfolio.tsx
    - backend/services/portfolio_scheduler.py

📝 Notes:
    - 특이사항이나 중요한 비즈니스 로직 설명
"""
```

### 2. 함수/클래스 Docstring
모든 public 함수와 클래스에 다음을 포함:

```python
def get_portfolio_data(account_no: str) -> Dict:
    """
    포트폴리오 데이터 조회
    
    Data Source: KIS API → /account/balance
    Fallback: Yahoo Finance (배당 정보)
    
    Args:
        account_no: 계좌번호 (예: "12345678-01")
        
    Returns:
        Dict: {
            "total_value": float,
            "positions": List[Dict],
            "cash": float
        }
        
    Raises:
        HTTPException: KIS API 인증 실패 시
    """
```

### 3. 중요 변수 주석

```python
# Data Source: KIS API response.body.output1
positions = balance.get("positions", [])

# Calculated from: current_price - avg_price
profit_loss = pos.get("profit_loss", 0)

# External API: Yahoo Finance ticker.info['sector']
sector = yf.get_stock_sector(symbol)
```

## 📁 TypeScript/React 파일 표준

### 1. 컴포넌트 헤더 주석

```typescript
/**
 * Portfolio.tsx - 포트폴리오 대시보드
 * 
 * 📊 API Dependencies:
 *    - GET /api/portfolio: 포트폴리오 데이터
 *    - GET /api/tickers/autocomplete: 티커 자동완성
 * 
 * 🔄 Data Flow:
 *    1. useEffect → fetch('/api/portfolio')
 *    2. setState(portfolio)
 *    3. Render charts & tables
 * 
 * 📦 External Libraries:
 *    - recharts: 차트 렌더링
 *    - lucide-react: 아이콘
 */
```

### 2. 복잡한 로직 주석

```typescript
// Data transformation: API response → Chart format
// Source: portfolio.positions[].sector
const getSector = (symbol: string): string => {
    // Mapping based on S&P 500 GICS classification
    const tech = ['AAPL', 'MSFT', ...];
```

## 🎯 구현 우선순위

### Phase 1: 핵심 데이터 파이프라인
1. **backend/api/** - 모든 router 파일
2. **backend/brokers/** - KIS 브로커 연동
3. **backend/data_sources/** - 외부 API 연동

### Phase 2: 프론트엔드
1. **frontend/src/pages/** - 페이지 컴포넌트
2. **frontend/src/components/** - 재사용 컴포넌트

### Phase 3: 유틸리티 & 테스트
1. **backend/utils/** - 유틸리티 함수
2. **backend/tests/** - 테스트 코드

## 🚀 자동화 도구

### 주석 검증 스크립트
```bash
# 주석이 없는 파일 찾기
python scripts/check_docstrings.py

# 자동 주석 템플릿 생성
python scripts/generate_docstring_template.py <filename>
```

## ✅ 체크리스트

코드 커밋 전:
- [ ] 파일 헤더에 Data Sources 명시
- [ ] External Dependencies 문서화
- [ ] Public 함수에 docstring 작성
- [ ] API 호출하는 곳에 endpoint 주석
- [ ] 복잡한 로직에 설명 주석

## 📌 예시: 좋은 주석 vs 나쁜 주석

### ❌ 나쁜 예
```python
# Get portfolio
def get_portfolio():
    data = api.call()
    return data
```

### ✅ 좋은 예
```python
"""
포트폴리오 조회
Data Source: KIS API /account/balance (TTTS3012R)
"""
def get_portfolio(account_no: str) -> PortfolioResponse:
    # KIS API 호출: 해외주식 잔고 조회
    balance = kis.overseas_stock.get_balance(account_no, "NASD")
    
    # Response format: {positions: [...], cash: float}
    return balance
```

## 🔄 업데이트 이력
- 2025-12-25: 초안 작성 - 데이터 소스 명시 표준 정의
