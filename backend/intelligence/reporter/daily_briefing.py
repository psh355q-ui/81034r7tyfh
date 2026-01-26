"""
Daily Briefing Generator

김현석의 월스트리트나우 스타일 일일 브리핑 자동 생성 (한국어)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import yfinance as yf
import httpx
import json

logger = logging.getLogger(__name__)


@dataclass
class AnalystQuote:
    """전문가 코멘트"""
    source: str  # JP Morgan, Goldman Sachs
    analyst: str
    quote: str
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    topic: str


@dataclass
class MarketBriefing:
    """일일 시황 브리핑"""
    timestamp: datetime
    
    # 시황 요약
    market_summary: str
    index_changes: Dict[str, float]  # {"SPY": 1.2, "QQQ": -0.5, ...}
    
    # 핵심 이벤트
    key_events: List[str]
    fed_analysis: Optional[str] = None
    economic_analysis: Optional[str] = None
    
    # 특징주
    featured_stocks: List[Dict] = field(default_factory=list)
    top_gainers: List[Dict] = field(default_factory=list)
    top_losers: List[Dict] = field(default_factory=list)
    
    # 전문가 의견
    analyst_views: List[AnalystQuote] = field(default_factory=list)
    
    # 전망
    outlook: str = ""
    watch_points: List[str] = field(default_factory=list)
    
    # 메타데이터
    data_sources: List[str] = field(default_factory=list)


class DailyBriefingGenerator:
    """
    일일 브리핑 생성기
    
    월스트리트 스타일의 한국어 시황 브리핑을 자동 생성
    
    구조:
    1️⃣ 간밤 시황 요약
    2️⃣ 핵심 이벤트 분석
    3️⃣ 월가 전문가 의견 인용
    4️⃣ 데이터 기반 분석
    5️⃣ 전망 및 주목 포인트
    """
    
    # 주요 지수
    MAJOR_INDICES = {
        "SPY": "S&P 500",
        "QQQ": "나스닥 100",
        "DIA": "다우존스",
        "IWM": "러셀 2000",
        "VIX": "VIX 공포지수",
    }
    
    # 매크로 지표
    MACRO_TICKERS = {
        "^VIX": "VIX",
        "^TNX": "10년물 국채금리",
        "DX-Y.NYB": "달러 인덱스",
        "GC=F": "금",
        "CL=F": "WTI 유가",
    }
    
    def __init__(
        self,
        claude_client=None,
        gemini_client=None,
    ):
        self.claude_client = claude_client
        self.gemini_client = gemini_client
    
    async def generate_daily_briefing(self) -> MarketBriefing:
        """
        일일 시황 브리핑 생성 (v2.3 Enhanced)
        
        Returns:
            MarketBriefing: 브리핑 객체
        """
        logger.info("일일 브리핑 생성 시작 (v2.3)")
        
        # 1. 시장 데이터 수집
        market_data = await self._get_market_data()
        
        # 2. 시장 지표 수집 (from market indicators API)
        market_indicators = await self._get_market_indicators()
        
        # 3. KIS 포트폴리오 수집
        portfolio_data = await self._get_kis_portfolio()
        
        # 4. 특징주 분석
        featured = await self._get_featured_stocks()
        
        # 5. 매크로 데이터
        macro_data = await self._get_macro_data()
        
        # 6. v2.3 구조로 AI 브리핑 생성
        summary = await self._generate_summary_with_ai_v23(
            market_data, macro_data, featured, market_indicators, portfolio_data
        )
        
        # 7. 주목 포인트 생성
        watch_points = self._generate_watch_points(market_data, macro_data)
        
        return MarketBriefing(
            timestamp=datetime.now(),
            market_summary=summary,
            index_changes=market_data.get('changes', {}),
            key_events=self._extract_key_events(market_data),
            featured_stocks=featured.get('notable', []),
            top_gainers=featured.get('gainers', []),
            top_losers=featured.get('losers', []),
            outlook=self._generate_outlook(market_data, macro_data),
            watch_points=watch_points,
            data_sources=["Market Indicators API", "KIS Portfolio", "Yahoo Finance"],
        )
    
    async def _get_market_data(self) -> Dict:
        """시장 데이터 수집"""
        data = {"changes": {}, "prices": {}}
        
        for ticker, name in self.MAJOR_INDICES.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                
                if len(hist) >= 2:
                    today = hist['Close'].iloc[-1]
                    yesterday = hist['Close'].iloc[-2]
                    change = (today - yesterday) / yesterday * 100
                    
                    data['changes'][name] = round(change, 2)
                    data['prices'][name] = round(today, 2)
            except Exception as e:
                logger.error(f"{ticker} 데이터 수집 실패: {e}")
        
        return data
    
    async def _get_macro_data(self) -> Dict:
        """매크로 데이터 수집"""
        data = {}
        
        for ticker, name in self.MACRO_TICKERS.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                
                if len(hist) >= 1:
                    data[name] = {
                        "value": round(hist['Close'].iloc[-1], 2),
                        "change": None,
                    }
                    if len(hist) >= 2:
                        yesterday = hist['Close'].iloc[-2]
                        today = hist['Close'].iloc[-1]
                        change = (today - yesterday) / yesterday * 100
                        data[name]["change"] = round(change, 2)
            except Exception as e:
                logger.error(f"{ticker} 매크로 데이터 수집 실패: {e}")
        
        return data
    
    async def _get_featured_stocks(self) -> Dict:
        """특징주 분석 - S&P500 섹터별 상위 종목"""
        # S&P500 섹터별 대표 종목 (섹터별 Top 5)
        try:
            from backend.data.sp500_universe import SP500_SECTORS
            # 각 섹터에서 상위 5개씩 선택
            sample_stocks = []
            for sector, tickers in SP500_SECTORS.items():
                sample_stocks.extend(tickers[:5])
        except ImportError:
            # 폴백: 기존 하드코딩 리스트
            sample_stocks = ["NVDA", "AAPL", "MSFT", "GOOGL", "META", "TSLA", "AMD", "AMZN",
                           "JPM", "UNH", "XOM", "JNJ", "PG", "HD", "NEE", "LIN"]
        
        results = {"notable": [], "gainers": [], "losers": [], "by_sector": {}}
        
        for ticker in sample_stocks[:50]:  # 최대 50개만 조회 (API 제한 고려)
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                
                if len(hist) >= 2:
                    today = hist['Close'].iloc[-1]
                    yesterday = hist['Close'].iloc[-2]
                    change = (today - yesterday) / yesterday * 100
                    
                    info = {
                        "ticker": ticker,
                        "price": round(today, 2),
                        "change_pct": round(change, 2),
                        "volume": int(hist['Volume'].iloc[-1]),
                    }
                    
                    if abs(change) >= 3:
                        results["notable"].append(info)
                    
                    if change >= 2:
                        results["gainers"].append(info)
                    elif change <= -2:
                        results["losers"].append(info)
                        
            except Exception as e:
                logger.error(f"{ticker} 특징주 분석 실패: {e}")
        
        # 정렬 - Top 3만 유지
        results["gainers"].sort(key=lambda x: x["change_pct"], reverse=True)
        results["losers"].sort(key=lambda x: x["change_pct"])
        results["gainers"] = results["gainers"][:5]
        results["losers"] = results["losers"][:5]
        
        return results
    
    async def _get_market_indicators(self) -> Dict:
        """Market Indicators API에서 시장 지표 조회"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8001/api/market/indicators", timeout=10)
                data = response.json()
                return data.get('data', {})
        except Exception as e:
            logger.error(f"Market indicators 조회 실패: {e}")
            return {}
    
    async def _get_kis_portfolio(self) -> Dict:
        """KIS 포트폴리오 데이터 조회"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8001/api/portfolio", timeout=10)
                data = response.json()
                return {
                    "total_value": data.get('total_value', 0),
                    "cash": data.get('cash', 0),
                    "cash_pct": (data.get('cash', 0) / max(data.get('total_value', 1), 1)) * 100,
                    "positions": [
                        {
                            "ticker": pos.get('symbol', pos.get('ticker', '')),
                            "quantity": pos.get('quantity', 0),
                            "market_value": pos.get('market_value', 0),
                            "weight_pct": (pos.get('market_value', 0) / max(data.get('total_value', 1), 1)) * 100,
                            "pnl_pct": pos.get('profit_loss_pct', 0)
                        }
                        for pos in data.get('positions', [])
                    ]
                }
        except Exception as e:
            logger.error(f"KIS 포트폴리오 조회 실패: {e}")
            return {"positions": [], "cash": 0, "total_value": 0, "cash_pct": 0}

    async def _generate_summary_with_ai_v23(
        self,
        market_data: Dict,
        macro_data: Dict,
        featured: Dict,
        market_indicators: Dict,
        portfolio_data: Dict,
    ) -> str:
        """AI로 v2.3 구조 브리핑 생성 (한국어)"""
        
        # 시장 지표 포맷팅
        indicators_str = self._format_market_indicators(market_indicators)
        
        # 포트폴리오 포맷팅
        portfolio_str = self._format_portfolio(portfolio_data)
        
        prompt = f"""당신은 트레이딩 전문가입니다. 다음 3단계 구조로 브리핑을 작성하세요:

## 제공되는 데이터

### 시장 지표 (실시간)
{indicators_str}

### 시장 데이터
{self._format_market_data(market_data)}

### 매크로 데이터
{self._format_macro_data(macro_data)}

### 현재 포트폴리오 (KIS 계좌)
{portfolio_str}

---

## 📋 작성 구조 (v2.3)

### 🚦 시장 상태

**Trend**: UP/SIDE/DOWN (S&P, NASDAQ 기준으로 판단)
**Risk Score**: 0-100 (VIX 기반: VIX 15 이하=30점, 15-25=50점, 25+=70점)
**Confidence**: 판단 신뢰도 %

**주요 동력**: 위 지표에서 가장 영향력 큰 2-3개 요인 나열

### 📋 실행 시나리오

**시나리오는 반드시 IF-THEN-STOP 형식으로 작성:**

#### 🟢 Base Case (확률 50-70%)
**IF**: [구체적 조건, 예: QQQ > 460]
**THEN**: [구체적 행동, 예: Tech 비중 +5%]
**Stop**: [손절 조건]

#### 🟡 Alternative (확률 20-40%)
**IF**: [조건]
**THEN**: [행동]
**Stop**: [손절]

#### 🔴 Tail Risk (확률 10-20%)
**IF**: [조건]
**THEN**: [방어 행동]
**Stop**: [손절]

### 💼 포트폴리오 영향

**현재 포트폴리오를 기반으로** 다음을 작성:

**권장 비중 변화**:
- Cash: {portfolio_data.get('cash_pct', 0):.1f}% → X% (±Y%)
- 각 포지션 조정 (실제 보유 종목만)

**Focus Assets** (실제 보유 종목 중 3개):
- 🔼 [Ticker] (현재 비중): [이유]
- 🔽 [Ticker] (현재 비중): [이유]
- ➡️ [Ticker] (현재 비중): [이유]

**Commentary**: 1-2문장으로 핵심 조언

---

## ⚠️ 필수 준수사항
- 모든 판단에 구체적 수치 근거 제시
- 추상적 표현 금지 ("대체로", "전반적으로" 등)
- 교과서적 설명 금지 ("VIX란..." 등)
- **보유하지 않은 종목은 절대 권장하지 마세요**
- IF-THEN-STOP 형식 엄수

## 출력 형식
위 3개 섹션(시장 상태 + 실행 시나리오 + 포트폴리오 영향)을 Markdown 형식으로 작성하세요.
"""
        
        if self.claude_client:
            try:
                response = await self.claude_client.generate(prompt)
                return response
            except Exception as e:
                logger.error(f"Claude 브리핑 생성 실패: {e}")
        
        # AI 없을 때 기본 브리핑
        return self._generate_basic_briefing_v23(market_data, macro_data, market_indicators, portfolio_data)
    
    def _format_market_indicators(self, indicators: Dict) -> str:
        """시장 지표 포맷팅"""
        if not indicators:
            return "시장 지표 데이터 없음"
        
        lines = []
        for key in ['sp500', 'nasdaq', 'vix', 'us10y', 'dxy']:
            if key in indicators:
                ind = indicators[key]
                lines.append(
                    f"- {ind.get('name', key)}: {ind.get('price', 0):.2f} "
                    f"({ind.get('change_pct', 0):+.2f}%)"
                )
        return "\n".join(lines)
    
    def _format_portfolio(self, portfolio: Dict) -> str:
        """포트폴리오 포맷팅"""
        if not portfolio.get('positions'):
            return "포트폴리오 데이터 없음"
        
        lines = [
            f"- 총 자산: ${portfolio.get('total_value', 0):,.2f}",
            f"- 현금: ${portfolio.get('cash', 0):,.2f} ({portfolio.get('cash_pct', 0):.1f}%)",
            f"- 보유 종목:"
        ]
        
        for pos in portfolio.get('positions', [])[:5]:  # 상위 5개만
            lines.append(
                f"  - {pos.get('ticker', 'N/A')}: "
                f"{pos.get('weight_pct', 0):.1f}% "
                f"(P&L: {pos.get('pnl_pct', 0):+.1f}%)"
            )
        
        return "\n".join(lines)
    
    def _generate_basic_briefing_v23(
        self,
        market_data: Dict,
        macro_data: Dict,
        market_indicators: Dict,
        portfolio_data: Dict,
    ) -> str:
        """기본 v2.3 브리핑 (AI 없을 때)"""
        sp500_change = market_data.get('changes', {}).get('S&P 500', 0)
        vix = macro_data.get('VIX', {}).get('value', 20)
        
        trend = "UP" if sp500_change > 0.5 else "DOWN" if sp500_change < -0.5 else "SIDE"
        risk_score = 30 if vix < 15 else 70 if vix > 25 else 50
        
        return f"""## 🚦 시장 상태

**Trend**: {trend}  
**Risk Score**: {risk_score}/100  
**Confidence**: 75%

**주요 동력**: S&P {sp500_change:+.2f}%, VIX {vix:.1f}

## 📋 실행 시나리오

### 🟢 Base Case (60%)
**IF**: 현재 추세 유지  
**THEN**: 현금 비중 유지  
**Stop**: N/A

## 💼 포트폴리오 영향

**권장 조치**: 현상 유지
**Commentary**: AI 분석 불가 - 수동 판단 필요
"""
    
    async def _generate_summary_with_ai(
        self,
        market_data: Dict,
        macro_data: Dict,
        featured: Dict,
    ) -> str:
        """AI로 시황 요약 생성 (한국어) - Legacy"""
        # v2.3로 대체되었으므로 기본 구현만 유지
        return self._generate_basic_summary(market_data, macro_data)
    
    def _generate_basic_summary(
        self,
        market_data: Dict,
        macro_data: Dict,
    ) -> str:
        """기본 시황 요약 (AI 없을 때)"""
        changes = market_data.get('changes', {})
        
        sp500_change = changes.get('S&P 500', 0)
        nasdaq_change = changes.get('나스닥 100', 0)
        vix = macro_data.get('VIX', {}).get('value', 0)
        
        direction = "상승" if sp500_change > 0 else "하락"
        
        summary = f"미국 증시는 S&P 500이 {sp500_change:+.2f}%, 나스닥이 {nasdaq_change:+.2f}% {direction}했습니다."
        
        if vix > 25:
            summary += f" VIX가 {vix:.1f}로 시장 변동성이 높은 상태입니다."
        elif vix < 15:
            summary += f" VIX가 {vix:.1f}로 시장이 안정적입니다."
        
        return summary
    
    def _format_market_data(self, data: Dict) -> str:
        """시장 데이터 포맷팅"""
        lines = []
        for name, change in data.get('changes', {}).items():
            lines.append(f"- {name}: {change:+.2f}%")
        return "\n".join(lines)
    
    def _format_macro_data(self, data: Dict) -> str:
        """매크로 데이터 포맷팅"""
        lines = []
        for name, info in data.items():
            value = info.get('value', 'N/A')
            change = info.get('change')
            if change is not None:
                lines.append(f"- {name}: {value} ({change:+.2f}%)")
            else:
                lines.append(f"- {name}: {value}")
        return "\n".join(lines)
    
    def _format_featured_stocks(self, data: Dict) -> str:
        """특징주 포맷팅"""
        lines = []
        for stock in data.get('notable', []):
            lines.append(f"- {stock['ticker']}: {stock['change_pct']:+.2f}%")
        return "\n".join(lines) if lines else "특이사항 없음"
    
    def _extract_key_events(self, market_data: Dict) -> List[str]:
        """핵심 이벤트 추출"""
        events = []
        changes = market_data.get('changes', {})
        
        # 큰 변동 이벤트
        for name, change in changes.items():
            if abs(change) >= 2:
                direction = "급등" if change > 0 else "급락"
                events.append(f"{name} {direction} ({change:+.2f}%)")
        
        return events
    
    def _generate_watch_points(
        self,
        market_data: Dict,
        macro_data: Dict,
    ) -> List[str]:
        """주목 포인트 생성"""
        points = []
        
        vix = macro_data.get('VIX', {}).get('value', 0)
        if vix > 20:
            points.append(f"⚠️ VIX {vix:.1f} - 변동성 주의")
        
        treasury = macro_data.get('10년물 국채금리', {}).get('change')
        if treasury and abs(treasury) >= 2:
            direction = "급등" if treasury > 0 else "급락"
            points.append(f"📈 10년물 금리 {direction}")
        
        oil = macro_data.get('WTI 유가', {}).get('change')
        if oil and abs(oil) >= 3:
            direction = "급등" if oil > 0 else "급락"
            points.append(f"🛢️ 유가 {direction}")
        
        return points
    
    def _generate_outlook(
        self,
        market_data: Dict,
        macro_data: Dict,
    ) -> str:
        """전망 생성"""
        vix = macro_data.get('VIX', {}).get('value', 20)
        sp500 = market_data.get('changes', {}).get('S&P 500', 0)
        
        if vix > 25:
            return "변동성이 높아 신중한 접근이 필요합니다."
        elif vix < 15 and sp500 > 0:
            return "시장 분위기가 양호하며 위험자산 선호가 지속될 전망입니다."
        else:
            return "혼조세 속에 박스권 등락이 예상됩니다."
    
    def to_markdown(self, briefing: MarketBriefing) -> str:
        """브리핑을 Markdown 형식으로 변환"""
        md = f"""# 📊 일일 시황 브리핑

**생성 시간**: {briefing.timestamp.strftime('%Y-%m-%d %H:%M')}

## 📈 시장 요약

{briefing.market_summary}

## 📉 주요 지수

| 지수 | 변동률 |
|------|--------|
"""
        for name, change in briefing.index_changes.items():
            emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            md += f"| {name} | {emoji} {change:+.2f}% |\n"
        
        if briefing.top_gainers:
            md += "\n## 🚀 상승 종목\n"
            for stock in briefing.top_gainers[:5]:
                md += f"- **{stock['ticker']}**: {stock['change_pct']:+.2f}%\n"
        
        if briefing.top_losers:
            md += "\n## 📉 하락 종목\n"
            for stock in briefing.top_losers[:5]:
                md += f"- **{stock['ticker']}**: {stock['change_pct']:+.2f}%\n"
        
        if briefing.watch_points:
            md += "\n## 👀 주목 포인트\n"
            for point in briefing.watch_points:
                md += f"- {point}\n"
        
        md += f"\n## 📌 전망\n\n{briefing.outlook}\n"
        
        return md
