# Market Intelligence Report System 설계 문서

**프로젝트**: AI Trading System - Market Intelligence Module
**버전**: v1.0
**작성일**: 2026-01-18
**참고**: 소수몽키 스타일 시장 분석 자동화

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [소수몽키 분석 패턴 분석](#2-소수몽키-분석-패턴-분석)
3. [시스템 아키텍처](#3-시스템-아키텍처)
4. [핵심 컴포넌트 설계](#4-핵심-컴포넌트-설계)
5. [데이터 구조](#5-데이터-구조)
6. [구현 로드맵](#6-구현-로드맵)
7. [API 설계](#7-api-설계)
8. [부록: 테마 및 종목 데이터](#8-부록-테마-및-종목-데이터)

---

## 1. 프로젝트 개요

### 1.1 목표

**"뉴스에서 소수몽키 스타일의 투자 인사이트를 자동으로 도출하는 시스템"**

현재 문제:
```
❌ 수동: WEF 리스크 순위 직접 입력
❌ 수동: 트럼프 발언 직접 정리
❌ 수동: 테마-종목 매핑 하드코딩
```

목표:
```
✅ 자동: 뉴스 수집 → AI 분석 → 인사이트 도출
✅ 자동: "트럼프 국방비 50% 증액" 기사 → "방산주 수혜" 자동 연결
✅ 자동: 패턴 감지 → "지정학 리스크 상승 중" 알림
```

### 1.2 핵심 기능

| 기능 | 설명 |
|------|------|
| **뉴스 자동 수집** | RSS, NewsAPI, Twitter 통합 |
| **AI 태깅** | 주제 분류, 엔티티 추출, 감성 분석 |
| **패턴 감지** | 테마 트렌드, 내러티브 변화, 이벤트 클러스터링 |
| **인사이트 생성** | 일일/주간 브리핑, 테마 심층 분석 |
| **알림 시스템** | Telegram, Slack 실시간 알림 |

---

## 2. 소수몽키 분석 패턴 분석

### 2.1 65개 이미지에서 발견한 7가지 분석 레이어

총 65개의 소수몽키 분석 이미지를 분석한 결과, 다음 7가지 핵심 패턴을 발견:

| 레이어 | 설명 | 예시 |
|--------|------|------|
| **1. 매크로 리스크** | WEF 글로벌 리스크 → 테마 | 지정학 1위 → 방산/원자재 |
| **2. 정책 발언** | 트럼프/국방장관 발언 → 예산 | 국방비 50% 증액 → 3대 분야 |
| **3. 테마 세분화** | 대분류 → 소분류 | 방산 → 드론/우주/해군 |
| **4. 촉매 이벤트** | 정부 프로그램 → 수혜주 | Guntlet(드론 오디션) → AVAV, KTOS |
| **5. 수익률 검증** | 테마 성과 비교 | SHLD +20%, ARKX +21%, ITA +13% |
| **6. 지정학 타임라인** | 이벤트 추적 | 이란/그린란드 일별 진행 |
| **7. 주간 캘린더** | 이벤트 + 실적 통합 | 다보스, PCE, 빅7 실적 |

### 2.2 분석 유형별 상세

#### Type 1: 테마 연결
```
뉴스: "가트너, AI 환멸의 골짜기 전망"
  ↓
테마: AI_HYPE_CYCLE
  ↓
피해: SW주 (IGV, PLTR, CRM, ADBE)
수혜: AI 인프라 (반도체, 전력)
```

#### Type 2: 수혜/피해 분석
```
뉴스: "TSMC CAPEX 50% 상향"
  ↓
직접 수혜: TSM
간접 수혜: ASML, LRCX (장비)
3차 수혜: CAT, URI (공장 건설)
```

#### Type 3: 양극화 탐지
```
비교: 반도체 vs SW
  ↓
SMH (반도체): +13.7% YTD
IGV (SW): -7.0% YTD
  ↓
인사이트: "구글은 반도체와 함께 주도주, 메타는 SW와 함께 소외주"
```

#### Type 4: 내러티브 추적
```
CEO 발언: "메타 10년 투자 확대"
  ↓
테마: BIGTECH_CAPEX
  ↓
수혜: NVDA, AMD, AVGO (AI 인프라)
```

#### Type 5: 지정학 영향
```
이벤트: "그린란드 관세 2/1 10%, 6/1 25%"
  ↓
테마: GEOPOLITICS_TARIFF
  ↓
수혜: 방산(LMT, RTX), 원자재(REMX, SLV)
```

#### Type 6: 실적 프리뷰
```
일정: 빅7 실적 발표
  ↓
핵심 질문: "AI에 돈 쓴 만큼 벌었나?"
  ↓
관전 포인트: 마진/현금흐름 → 주가 양극화 가능성
```

### 2.3 글로벌 리스크 분석 (WEF)

#### 연도별 리스크 순위 변화 (2022-2026)

| 연도 | 1위 | 2위 | 3위 | 핵심 변화 |
|------|-----|-----|-----|----------|
| 2022 | 자산 거품 붕괴 | 기후변화 대응 실패 | 극심한 기상 이변 | 경제 리스크 중심 |
| 2023 | 생계비 위기 | 자연재해/기상이변 | 지정학적 대립 | 인플레 영향 |
| 2024 | 기상이변 | AI발 가짜정보 | 사회/정치 양극화 | AI 리스크 부상 |
| 2025 | 국가간 무력충돌 | 기상이변 | 지정학적 대립 | 지정학 본격화 |
| 2026 | **지정학적 대립** | **국가간 무력충돌** | 극단적 기상이변 | **지정학 1,2위 독점** |

#### 2026년 급상승 리스크
```
1위: 지정학 대립 급증 (+8)
11위: 경기 침체 (+8)
21위: 인플레이션 (+8)
18위: 자산 거품 붕괴 (+7)
```

#### 리스크 → 투자 테마 매핑
```python
RISK_TO_THEME = {
    "지정학적 대립": {
        "themes": ["DEFENSE", "COMMODITIES", "RARE_EARTH"],
        "beneficiaries": ["LMT", "RTX", "NOC", "HII", "REMX", "SLV"],
        "reasoning": "갈등, 탈세계화, 보호무역 → 방산/원자재 수혜"
    },
    "국가간 무력충돌": {
        "themes": ["DEFENSE", "ENERGY", "GOLD"],
        "beneficiaries": ["LMT", "RTX", "XLE", "GLD", "URA"]
    },
    "인플레이션": {
        "themes": ["COMMODITIES", "TIPS", "REAL_ESTATE"],
        "beneficiaries": ["DBC", "TIP", "VNQ", "GLD"]
    }
}
```

---

## 3. 시스템 아키텍처

### 3.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│              MARKET INTELLIGENCE PLATFORM v3.0                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ DATA LAYER │─▶│ ANALYSIS    │─▶│ NARRATIVE   │─▶│ OUTPUT    │  │
│  │            │  │ LAYER       │  │ LAYER       │  │ LAYER     │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │
│                                                                     │
│  [Data Layer]           [Analysis Layer]       [Output Layer]       │
│  ・NewsCollector        ・NewsTagger          ・WeeklyBriefing     │
│  ・RSSFeedManager       ・PatternDetector     ・TelegramAlert      │
│  ・PriceTracker         ・InsightGenerator    ・Dashboard          │
│  ・EarningsCalendar     ・ThemeAnalyzer       ・PDFReport          │
│  ・GeopoliticsTracker   ・NarrativeConnector                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 뉴스 → 인사이트 파이프라인

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEWS → INSIGHT PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Stage 1]        [Stage 2]        [Stage 3]        [Stage 4]      │
│  뉴스 수집    →   분류/태깅    →   패턴 감지    →   인사이트 생성   │
│                                                                     │
│  ・RSS Feeds      ・Topic 분류     ・트렌드 감지    ・투자 시사점   │
│  ・NewsAPI        ・Entity 추출    ・연관성 분석    ・테마 연결     │
│  ・Twitter        ・감성 분석      ・이상치 탐지    ・리포트 생성   │
│  ・SEC Edgar      ・중요도 점수    ・시계열 비교                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 데이터 흐름

```
[뉴스 소스]
    │
    ▼
┌─────────────────┐
│ NewsCollector   │ ← RSS, NewsAPI, Twitter
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ NewsTagger      │ ← LLM 기반 분류/태깅
│ (Claude API)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PatternDetector │ ← 시계열 분석, 트렌드 감지
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ InsightGenerator│ ← 소수몽키 스타일 인사이트
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Output Layer    │ → Telegram, Dashboard, Report
└─────────────────┘
```

---

## 4. 핵심 컴포넌트 설계

### 4.1 NewsTagger (Stage 2)

**역할**: 뉴스 기사를 구조화된 데이터로 변환

```python
# backend/ai/intelligence/news_tagger.py

class NewsTagger:
    """
    뉴스 기사 → 구조화된 태그 추출
    
    Input: "트럼프, 2027년 국방예산 1.5조 달러로 50% 증액 요구"
    
    Output:
    {
        "entities": {
            "person": ["트럼프"],
            "organization": ["미 국방부"],
            "amount": ["1.5조 달러", "50%"],
            "date": ["2027년"]
        },
        "topic": "DEFENSE_BUDGET",
        "sub_topics": ["국방비", "예산", "증액"],
        "sentiment": "BULLISH",
        "importance": 0.95,
        "affected_sectors": ["DEFENSE", "AEROSPACE"],
        "keywords": ["국방예산", "50%", "증액", "꿈의 군대"]
    }
    """
    
    TOPIC_TAXONOMY = {
        "GEOPOLITICS": {
            "sub_topics": ["관세", "제재", "무력충돌", "외교"],
            "keywords": ["tariff", "sanction", "관세", "제재", "군사", "침공"],
            "entities": ["트럼프", "시진핑", "푸틴", "NATO", "UN"]
        },
        "DEFENSE": {
            "sub_topics": ["국방비", "무기", "드론", "우주", "해군"],
            "keywords": ["defense", "military", "국방", "방산", "미사일", "드론"],
            "entities": ["펜타곤", "록히드", "레이시온", "국방부"]
        },
        "AI_TECH": {
            "sub_topics": ["AI투자", "반도체", "데이터센터", "클라우드"],
            "keywords": ["AI", "GPU", "CAPEX", "데이터센터", "반도체", "HBM"],
            "entities": ["엔비디아", "OpenAI", "마이크로소프트", "구글"]
        },
        "MACRO": {
            "sub_topics": ["금리", "인플레", "고용", "GDP"],
            "keywords": ["금리", "CPI", "PCE", "실업률", "FOMC"],
            "entities": ["파월", "연준", "Fed"]
        },
        "EARNINGS": {
            "sub_topics": ["실적발표", "가이던스", "매출", "이익"],
            "keywords": ["실적", "EPS", "매출", "가이던스", "beat", "miss"]
        }
    }
    
    async def tag_news(self, headline: str, content: str) -> Dict:
        """LLM을 사용해 뉴스 태깅"""
        prompt = self._build_tagging_prompt(headline, content)
        response = await self.llm.analyze(prompt)
        return self._parse_response(response)
```

### 4.2 PatternDetector (Stage 3)

**역할**: 시간에 따른 뉴스 패턴 감지

```python
# backend/ai/intelligence/pattern_detector.py

class PatternDetector:
    """
    시간에 따른 뉴스 패턴 감지
    
    기능:
    1. 테마 트렌드 감지 (상승/하락)
    2. 내러티브 변화 감지
    3. 이벤트 클러스터링
    """
    
    async def detect_rising_themes(self, days: int = 7) -> List[Dict]:
        """
        최근 N일간 상승하는 테마 감지
        
        Output:
        [
            {
                "theme": "DEFENSE",
                "trend": "RISING",
                "mention_change": "+340%",
                "key_triggers": [
                    "트럼프 국방비 50% 증액",
                    "국방장관 로켓랩 방문"
                ],
                "related_tickers": ["LMT", "RTX", "AVAV", "RKLB"]
            }
        ]
        """
        
    async def detect_narrative_shift(self) -> List[Dict]:
        """
        내러티브 변화 감지
        
        예: "AI 낙관론" → "AI ROI 검증" 으로 톤 변화
        
        Output:
        [
            {
                "topic": "AI_SENTIMENT",
                "before": "AI 투자 확대 기대",
                "after": "AI ROI 검증 필요",
                "shift_detected": "2026-01-15",
                "evidence": [
                    "가트너 환멸의 골짜기 전망",
                    "SW주 연속 하락"
                ],
                "investment_implication": "HW(반도체) > SW(SaaS)"
            }
        ]
        """
        
    async def detect_event_clustering(self) -> List[Dict]:
        """
        연관 이벤트 클러스터링
        
        Input (개별 뉴스들):
        - "트럼프 국방비 50% 증액"
        - "국방장관 로켓랩 방문"
        - "미일 국방장관 회담"
        - "Guntlet 드론 프로그램"
        
        Output:
        {
            "cluster_name": "미국 국방 현대화 대전환",
            "articles": [4개 기사],
            "sub_themes": {
                "예산": "50% 증액으로 재원 확보",
                "우주": "로켓랩/SpaceX 민간 협력",
                "동맹": "미일 합동훈련 강화",
                "혁신": "기존 방산 → 스타트업 전환"
            },
            "investment_thesis": "전통 방산 + 혁신 방산 동반 수혜"
        }
        """
```

### 4.3 InsightGenerator (Stage 4)

**역할**: 소수몽키 스타일 인사이트 생성

```python
# backend/ai/intelligence/insight_generator.py

class InsightGenerator:
    """
    패턴 + 뉴스 → 소수몽키 스타일 인사이트 생성
    """
    
    async def generate_daily_insight(self, date: str) -> Dict:
        """
        일일 인사이트 생성
        
        Output:
        {
            "date": "2026-01-18",
            "headline": "방산주 강세 지속, 지정학 리스크가 시장 주도",
            
            "top_stories": [
                {
                    "title": "트럼프, 그린란드 매입 때까지 관세 부과",
                    "theme": "GEOPOLITICS",
                    "impact": "방산/원자재 수혜 지속",
                    "tickers": ["SHLD", "REMX", "SLV"]
                }
            ],
            
            "theme_summary": {
                "rising": ["방산", "우주", "지정학"],
                "falling": ["SW/SaaS", "빅테크"],
                "stable": ["반도체"]
            },
            
            "pattern_alerts": [
                {
                    "pattern": "방산 뉴스 7일 연속 증가",
                    "implication": "테마 과열 주의 or 추세 지속"
                }
            ]
        }
        """
        
    async def generate_weekly_briefing(self) -> Dict:
        """
        주간 브리핑 생성 (소수몽키 스타일)
        
        Output:
        {
            "week": "1/13 ~ 1/19",
            "headline": "지정학 이슈가 1,2위, 빅테크 실적 시즌 임박",
            
            "key_themes": [
                {
                    "theme": "GEOPOLITICS",
                    "title": "다보스포럼이 준 힌트 '지정학 갈등'",
                    "insight": "WEF 2026 리스크 1,2위 모두 지정학",
                    "etf_performance": "SHLD +20.3%, XME +19.8%"
                }
            ],
            
            "sector_performance": {
                "winners": [
                    {"theme": "반도체", "etf": "SOXX", "ytd": "+13.7%"},
                    {"theme": "방산", "etf": "SHLD", "ytd": "+20.3%"}
                ],
                "losers": [
                    {"theme": "SW", "etf": "IGV", "ytd": "-7.0%"},
                    {"theme": "빅7", "etf": "MAGS", "ytd": "-1.6%"}
                ]
            },
            
            "next_week_calendar": [...]
        }
        """
        
    async def generate_theme_deep_dive(self, theme: str) -> Dict:
        """
        특정 테마 심층 분석
        
        Process:
        1. 최근 30일 관련 뉴스 수집
        2. 서브테마 자동 분류
        3. 주요 촉매 이벤트 추출
        4. 수혜주 자동 매핑
        """
```

### 4.4 ThemeDeepDive

**역할**: 테마 세분화 및 상세 분석

```python
# backend/ai/intelligence/theme_deep_dive.py

class ThemeDeepDive:
    """
    테마 세분화 분석 엔진
    
    대분류 → 소분류 → 개별 종목 → 촉매 이벤트
    """
    
    DEFENSE_THEME = {
        "name": "DEFENSE",
        "korean": "방산",
        "etfs": ["ITA", "SHLD", "ARKX"],
        "2026_catalyst": "트럼프 국방예산 50% 증액 (GDP 3% → 5%)",
        
        "sub_themes": {
            "DRONE": {
                "korean": "드론/무인기",
                "thesis": "국방부 '드론의 해' 선언, Guntlet 프로그램",
                "stocks": [
                    {"ticker": "AVAV", "name": "에어로바이런먼트", "specialty": "자폭 드론", "ytd": 62.4},
                    {"ticker": "KTOS", "name": "크라토스", "specialty": "정찰 무인기", "ytd": 72.2},
                    {"ticker": "RCAT", "name": "레드캣", "specialty": "초소형 정찰", "ytd": 72.4}
                ],
                "catalyst_events": [
                    {"date": "2026-02-16", "event": "Guntlet 드론 챌린지"},
                    {"date": "2026-07", "event": "첫 12개 기업 납품"},
                    {"date": "2027", "event": "최종 5개 기업, 30만대 발주"}
                ]
            },
            "SPACE": {
                "korean": "우주/위성",
                "thesis": "국방장관 '우주 패권이 미래 전장의 핵심'",
                "stocks": [
                    {"ticker": "RKLB", "name": "로켓랩", "specialty": "발사체 2위", "ytd": 38.0},
                    {"ticker": "ASTS", "name": "AST모바일", "specialty": "우주통신망", "ytd": 59.4},
                    {"ticker": "PL", "name": "플래닛랩스", "specialty": "위성사진", "ytd": 45.9}
                ]
            },
            "NAVY": {
                "korean": "해군/조선",
                "thesis": "황금함대 프로젝트 - 미일 합동훈련 강화",
                "stocks": [
                    {"ticker": "HII", "name": "헌팅턴잉갈스", "specialty": "1위 조선사", "ytd": 25.2},
                    {"ticker": "GD", "name": "제너럴다이나믹스", "specialty": "2위 조선사", "ytd": 9.1},
                    {"ticker": "RTX", "name": "레이시온", "specialty": "레이더/미사일", "ytd": 10.1}
                ]
            }
        }
    }
```

### 4.5 GeopoliticsTracker

**역할**: 지정학 이슈 타임라인 추적

```python
# backend/ai/intelligence/geopolitics_tracker.py

class GeopoliticsTracker:
    """
    지정학 이슈 타임라인 추적
    """
    
    ACTIVE_ISSUES = {
        "IRAN": {
            "korean": "이란",
            "status": "ESCALATING",
            "timeline": [
                {"date": "2025-12-28", "event": "이란 시위 격화 (~1.2만명 사망설)"},
                {"date": "2026-01-12", "event": "트럼프, 군사 개입 시사"},
                {"date": "2026-01-13", "event": "이란 교역국 대상 25% 관세 즉시 부과"},
                {"date": "2026-01-15", "event": "항공모함 중동으로 이동 중"}
            ],
            "investment_impact": {
                "beneficiaries": ["방산", "원유", "금"],
                "tickers": ["LMT", "RTX", "XLE", "GLD"]
            }
        },
        "GREENLAND": {
            "korean": "그린란드",
            "status": "ACTIVE",
            "timeline": [
                {"date": "2025-12-23", "event": "그린란드 특사 임명"},
                {"date": "2026-01-15", "event": "유럽 8개국 그린란드로 군대 이동"},
                {"date": "2026-01-18", "event": "트럼프 '매입할 때까지 관세'"}
            ],
            "tariff_schedule": {
                "2026-02-01": "10%",
                "2026-06-01": "25%"
            },
            "investment_impact": {
                "beneficiaries": ["방산", "희토류", "은"],
                "tickers": ["SHLD", "REMX", "SLV"]
            }
        },
        "TAIWAN": {
            "korean": "대만",
            "status": "MONITORING",
            "timeline": [
                {"date": "2026-01-12~18", "event": "미일 국방장관 회담"},
                {"date": "2026-01-15", "event": "제1 도련선 전력 강화 발표"}
            ],
            "investment_impact": {
                "beneficiaries": ["반도체 장비", "방산"],
                "tickers": ["ASML", "LRCX", "TSM", "HII"]
            }
        }
    }
```

### 4.6 WeeklyCalendar

**역할**: 주간 이벤트 캘린더 생성

```python
# backend/ai/intelligence/weekly_calendar.py

class WeeklyCalendar:
    """
    주간 이벤트 캘린더 (정책/통화/지표/실적/발언)
    """
    
    async def get_weekly_events(self, start_date: str) -> Dict:
        """
        Output 예시 (1/19~1/25):
        {
            "week": "1/19(월) ~ 1/25(일)",
            "weekly_focus": [
                "트럼프 연설 (다보스)",
                "미국 증시 휴장 (MLK Day)",
                "실적 시즌"
            ],
            "daily_events": {
                "1/19(월)": {
                    "market": "미국 증시 휴장 (MLK Day)",
                    "policy": "다보스포럼 (WEF) ~23일"
                },
                "1/21(수)": {
                    "speech": "트럼프 연설 (다보스)",
                    "indicator": "주택착공건수/건축허가건수"
                },
                "1/22(목)": {
                    "indicator": "10, 11월 PCE / 3Q GDP 수정치",
                    "hearing": "보험사 CEO 의회 청문회"
                }
            },
            "big7_earnings": [
                {"date": "1/28(수)", "tickers": ["TSLA", "MSFT", "META"]},
                {"date": "1/29(목)", "tickers": ["AAPL"]},
                {"date": "2/4(수)", "tickers": ["GOOGL"]},
                {"date": "2/5(목)", "tickers": ["AMZN"]},
                {"date": "2/25(수)", "tickers": ["NVDA"]}
            ]
        }
        """
```

---

## 5. 데이터 구조

### 5.1 Database Schema

```sql
-- 뉴스 태깅 결과
CREATE TABLE news_tags (
    id SERIAL PRIMARY KEY,
    news_id INTEGER REFERENCES news_articles(id),
    topic VARCHAR(50) NOT NULL,
    sub_topics TEXT[],
    entities JSONB,
    sentiment VARCHAR(20),
    importance FLOAT,
    affected_sectors TEXT[],
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- 테마 정의
CREATE TABLE themes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    korean_name VARCHAR(100),
    description TEXT,
    etfs TEXT[],
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- 서브테마
CREATE TABLE sub_themes (
    id SERIAL PRIMARY KEY,
    theme_id INTEGER REFERENCES themes(id),
    name VARCHAR(50) NOT NULL,
    korean_name VARCHAR(100),
    thesis TEXT,
    tickers TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- 촉매 이벤트
CREATE TABLE catalyst_events (
    id SERIAL PRIMARY KEY,
    theme_id INTEGER REFERENCES themes(id),
    sub_theme_id INTEGER REFERENCES sub_themes(id),
    event_date DATE,
    event_name VARCHAR(255),
    description TEXT,
    impact TEXT,
    status VARCHAR(20) DEFAULT 'UPCOMING',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 지정학 이슈
CREATE TABLE geopolitics_issues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    korean_name VARCHAR(100),
    status VARCHAR(20),
    beneficiary_sectors TEXT[],
    beneficiary_tickers TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- 지정학 타임라인
CREATE TABLE geopolitics_timeline (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER REFERENCES geopolitics_issues(id),
    event_date DATE,
    event_description TEXT,
    importance VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 패턴 감지 결과
CREATE TABLE detected_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR(50),
    theme VARCHAR(50),
    description TEXT,
    evidence JSONB,
    detected_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- 인사이트 (일일/주간)
CREATE TABLE insights (
    id SERIAL PRIMARY KEY,
    insight_type VARCHAR(20),  -- 'daily' or 'weekly'
    date DATE,
    headline TEXT,
    content JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.2 JSONB 구조 예시

```json
// news_tags.entities
{
    "person": ["트럼프", "피트 헤그세스"],
    "organization": ["국방부", "SpaceX", "로켓랩"],
    "location": ["미국", "그린란드"],
    "amount": ["1.5조 달러", "50%"],
    "date": ["2027년", "2/1"]
}

// detected_patterns.evidence
{
    "theme": "DEFENSE",
    "trend": "RISING",
    "mention_count": {
        "day_1": 12,
        "day_7": 47,
        "change_pct": 291.7
    },
    "key_articles": [
        {"title": "트럼프 국방비 50% 증액", "date": "2026-01-08"},
        {"title": "국방장관 로켓랩 방문", "date": "2026-01-15"}
    ]
}

// insights.content (daily)
{
    "headline": "방산주 강세 지속, 지정학 리스크가 시장 주도",
    "top_stories": [...],
    "theme_summary": {
        "rising": ["방산", "우주"],
        "falling": ["SW/SaaS"]
    },
    "pattern_alerts": [...],
    "calendar_preview": [...]
}
```

---

## 6. 구현 로드맵

### Phase 1: 뉴스 태깅 파이프라인 (Week 1)

| Task | 설명 | 파일 |
|------|------|------|
| 1.1 | NewsTagger 클래스 구현 | `news_tagger.py` |
| 1.2 | LLM 프롬프트 설계 | `prompts/tagging_prompt.py` |
| 1.3 | 기존 RSS 수집기 연동 | `news_collector.py` 수정 |
| 1.4 | news_tags 테이블 생성 | Alembic migration |
| 1.5 | 태깅 API 엔드포인트 | `api/intelligence_router.py` |

### Phase 2: 패턴 감지 (Week 2)

| Task | 설명 | 파일 |
|------|------|------|
| 2.1 | PatternDetector 클래스 구현 | `pattern_detector.py` |
| 2.2 | 테마 빈도 집계 로직 | `theme_aggregator.py` |
| 2.3 | 트렌드 변화 감지 알고리즘 | `trend_detector.py` |
| 2.4 | 이벤트 클러스터링 | `event_clusterer.py` |
| 2.5 | detected_patterns 테이블 | Alembic migration |

### Phase 3: 인사이트 생성 (Week 3)

| Task | 설명 | 파일 |
|------|------|------|
| 3.1 | InsightGenerator 클래스 구현 | `insight_generator.py` |
| 3.2 | 일일 인사이트 생성 | `daily_insight.py` |
| 3.3 | 주간 브리핑 생성 | `weekly_briefing.py` |
| 3.4 | 테마 심층 분석 | `theme_deep_dive.py` |
| 3.5 | insights 테이블 | Alembic migration |

### Phase 4: 출력 및 알림 (Week 4)

| Task | 설명 | 파일 |
|------|------|------|
| 4.1 | Telegram 알림 연동 | `telegram_notifier.py` |
| 4.2 | 주간 캘린더 생성기 | `weekly_calendar.py` |
| 4.3 | 지정학 트래커 | `geopolitics_tracker.py` |
| 4.4 | Dashboard API | `api/dashboard_router.py` |
| 4.5 | PDF 리포트 생성 | `report_generator.py` |

---

## 7. API 설계

### 7.1 뉴스 태깅 API

```
POST /api/intelligence/tag-news
Body: {
    "headline": "트럼프, 국방예산 50% 증액 요구",
    "content": "기사 본문..."
}
Response: {
    "topic": "DEFENSE_BUDGET",
    "entities": {...},
    "sentiment": "BULLISH",
    "importance": 0.95
}
```

### 7.2 패턴 감지 API

```
GET /api/intelligence/patterns/rising-themes?days=7
Response: {
    "themes": [
        {
            "theme": "DEFENSE",
            "trend": "RISING",
            "mention_change": "+340%",
            "key_triggers": [...]
        }
    ]
}
```

### 7.3 인사이트 API

```
GET /api/intelligence/insights/daily?date=2026-01-18
Response: {
    "date": "2026-01-18",
    "headline": "방산주 강세 지속...",
    "top_stories": [...],
    "theme_summary": {...}
}

GET /api/intelligence/insights/weekly?week=2026-W03
Response: {
    "week": "1/13 ~ 1/19",
    "headline": "지정학 이슈가 1,2위...",
    "key_themes": [...],
    "sector_performance": {...}
}
```

### 7.4 테마 API

```
GET /api/intelligence/themes/DEFENSE
Response: {
    "name": "DEFENSE",
    "korean": "방산",
    "sub_themes": ["DRONE", "SPACE", "NAVY"],
    "ytd_performance": "+20.3%",
    "recent_news_count": 47
}

GET /api/intelligence/themes/DEFENSE/deep-dive
Response: {
    "narrative": "트럼프 2기 국방 현대화...",
    "sub_themes_detected": [...],
    "catalyst_timeline": [...],
    "performance": {...}
}
```

### 7.5 지정학 API

```
GET /api/intelligence/geopolitics
Response: {
    "active_issues": [
        {
            "name": "IRAN",
            "status": "ESCALATING",
            "latest_event": "항공모함 중동 이동"
        },
        {
            "name": "GREENLAND",
            "status": "ACTIVE",
            "latest_event": "2/1 관세 10% 예정"
        }
    ]
}

GET /api/intelligence/geopolitics/GREENLAND/timeline
Response: {
    "timeline": [
        {"date": "2025-12-23", "event": "특사 임명"},
        {"date": "2026-01-18", "event": "매입 때까지 관세"}
    ]
}
```

### 7.6 캘린더 API

```
GET /api/intelligence/calendar/weekly?start=2026-01-19
Response: {
    "week": "1/19 ~ 1/25",
    "daily_events": {...},
    "big7_earnings": [...]
}
```

---

## 8. 부록: 테마 및 종목 데이터

### 8.1 2026년 수익률 상위 ETF (지정학 관련)

| Rank | 심볼 | 설명 | 올해 수익률 |
|------|------|------|------------|
| 1 | WGMI | 네오클라우드 | +33.4% |
| 2 | URA | 원자력 | +27.3% |
| 3 | SLV | 은 | +25.8% |
| 4 | ARKX | 우주 | +21.4% |
| 5 | REMX | 희토류 | +20.6% |
| 6 | SHLD | 방산 | +20.3% |
| 7 | XME | 원자재주 | +19.8% |
| 8 | SIL | 은채굴 | +17.8% |
| 9 | BLOK | 코인관련 | +15.7% |
| 10 | OIH | 오일서비스 | +14.7% |

> 10개 중 8개가 지정학 관련 테마

### 8.2 방산 테마 세부 종목

#### 드론 (Drone)
| 티커 | 종목 | 특징 | 올해 수익률 | 시총($B) |
|------|------|------|------------|----------|
| AVAV | 에어로바이런먼트 | 자폭 드론 | +62.4% | 19.6 |
| KTOS | 크라토스 | 정찰 무인기 | +72.2% | 22.1 |
| RCAT | 레드캣 | 초소형 정찰 | +72.4% | 1.6 |
| UMAC | 언유즈얼머신스 | 드론 부품 | +45.3% | 0.7 |

#### 우주 (Space)
| 티커 | 종목 | 특징 | 올해 수익률 | 시총($B) |
|------|------|------|------------|----------|
| RKLB | 로켓랩 | 발사체 2위 | +38.0% | 56 |
| ASTS | AST모바일 | 우주통신망 | +59.4% | 43 |
| PL | 플래닛랩스 | 위성사진 | +45.9% | 9 |
| RDW | 레드와이어 | 우주장비/부품 | +54.1% | 2 |
| LUNR | 인튜이티브머신 | 달 탐사 | +33.0% | 4 |

#### 해군 (Navy / Golden Fleet)
| 티커 | 종목 | 특징 | 올해 수익률 | 시총($B) |
|------|------|------|------------|----------|
| HII | 헌팅턴잉갈스 | 1위 조선사 | +25.2% | 17 |
| GD | 제너럴다이나믹스 | 2위 조선사 | +9.1% | 99 |
| RTX | 레이시온 | 레이더/미사일 | +10.1% | 271 |
| LMT | 록히드마틴 | 이지스/전투시스템 | +20.4% | 135 |
| LHX | L3해리스 | 통합제어/무인함대 | +18.0% | 65 |

### 8.3 전력 인프라 테마 종목

| 티커 | 종목 | 특징 | 올해 수익률 | 주간 수익률 |
|------|------|------|------------|------------|
| BE | 블룸에너지 | 수소연료전지 | +72.1% | +11.5% |
| PLUG | 플러그파워 | 수소연료전지 | +19.8% | +7.8% |
| EOSE | 이오스 | ESS | +52.3% | +14.2% |
| FLNC | 플루언스 | ESS(솔루션) | +36.9% | +16.7% |
| CAT | 캐터필러 | 산업용 발전기 | +12.9% | +4.7% |
| GNRC | 제너랙 | 소규모 발전기 | +18.0% | +5.3% |
| NVTS | 나비타스 | 전력반도체 | +52.8% | +8.3% |

### 8.4 빅테크 (빅7) 현황

| 티커 | 종목 | 올해 수익률 | 고점 하락률 | 주간 수익률 |
|------|------|------------|------------|------------|
| NVDA | 엔비디아 | -0.1% | -12.2% | +0.7% |
| GOOGL | 알파벳 | +5.4% | -3.1% | +0.4% |
| AAPL | 애플 | -6.0% | -11.5% | -1.5% |
| MSFT | 마소 | -4.9% | -17.2% | -4.1% |
| AMZN | 아마존 | +3.6% | -7.5% | -3.3% |
| META | 메타 | -6.0% | -22.1% | -5.0% |
| TSLA | 테슬라 | -2.7% | -12.3% | -1.7% |

### 8.5 SW/SaaS 종목 (IGV Top 10)

| 티커 | 종목 | 비중 | 올해 수익률 | 특이사항 |
|------|------|------|------------|----------|
| PLTR | 팔란티어 | 9.4% | -3.8% | |
| MSFT | 마이크로소프트 | 8.5% | -4.9% | |
| CRM | 세일즈포스 | 7% | -14.8% | 직원수 감소 |
| INTU | 인튜이트 | - | -17.7% | 세금신고 자동화 |
| ORCL | 오라클 | 5.8% | -2.0% | |
| NOW | 서비스나우 | 7% | -16.9% | 직원수 감소 |
| APP | 앱로빈 | 5.6% | -15.6% | |
| ADBE | 어도비 | - | -15.4% | 디자인 업무 대체 |

---

## 9. LLM 프롬프트 템플릿

### 9.1 뉴스 태깅 프롬프트

```python
NEWS_TAGGING_PROMPT = """
당신은 금융 뉴스 분석 전문가입니다.

다음 뉴스를 분석하세요:

제목: {headline}
내용: {content[:1000]}

다음 JSON 형식으로 응답:
{{
    "topic": "대분류 (GEOPOLITICS/DEFENSE/AI_TECH/MACRO/EARNINGS 중 하나)",
    "sub_topics": ["관련 소주제들"],
    "entities": {{
        "person": ["인물들"],
        "organization": ["기관/기업들"],
        "location": ["국가/지역"],
        "amount": ["금액/수치"]
    }},
    "sentiment": "BULLISH/BEARISH/NEUTRAL",
    "importance": 0.0~1.0,
    "key_facts": ["핵심 사실 3개"],
    "investment_relevant": true/false,
    "affected_tickers": ["관련 종목 티커"]
}}
"""
```

### 9.2 인사이트 생성 프롬프트

```python
INSIGHT_GENERATION_PROMPT = """
당신은 소수몽키 스타일의 시장 분석가입니다.

다음 뉴스들을 분석하여 투자 인사이트를 도출하세요:

[오늘의 뉴스]
{news_list}

[최근 7일 트렌드]
{trend_data}

다음을 분석해주세요:

1. **핵심 내러티브**: 이 뉴스들이 말하는 큰 그림은?
   - 단순 사실이 아닌, 시장이 어디로 가는지

2. **테마 연결**: 어떤 투자 테마와 연결되는가?
   - 예: "국방비 증액" → 방산 테마
   - 예: "AI ROI 검증" → SW 피해, HW 수혜

3. **수혜/피해 분석**:
   - 직접 수혜: 뉴스에 직접 언급된 기업
   - 간접 수혜: 공급망/연관 기업
   - 피해: 반대 영향 받는 기업

4. **촉매 이벤트**: 향후 주목할 일정은?

5. **리스크 체크**: 반대 시나리오는?

JSON 형식으로 응답:
{{
    "headline": "한 줄 요약",
    "narrative": "큰 그림 설명 (2-3문장)",
    "themes": [
        {{"name": "테마명", "direction": "BULLISH/BEARISH", "tickers": [...]}}
    ],
    "beneficiaries": [{{"ticker": "XXX", "reason": "이유"}}],
    "victims": [{{"ticker": "XXX", "reason": "이유"}}],
    "catalysts": [{{"date": "날짜", "event": "이벤트"}}],
    "risks": ["리스크1", "리스크2"]
}}
"""
```

---

## 10. 참고 자료

### 10.1 분석한 이미지 목록 (65개)

1. **빅테크/AI 분석** (20개)
   - 가트너 Hype Cycle (환멸의 골짜기)
   - 빅테크 수익성 우려
   - SW주 겹악재 (IGV 하락)
   - 빅테크 양극화 (반도체 vs SW)
   - 빅7 실적 발표 일정
   - 구글-애플 Gemini 계약

2. **WEF/다보스 분석** (19개)
   - 글로벌 리스크 보고서 2022-2026
   - 연도별 리스크 순위 비교
   - 다보스 주제 변화 (4차 산업혁명 → AI → 대화)
   - 트럼프 다보스 연설 분석

3. **방산 테마** (14개)
   - 국방예산 50% 증액
   - 국방장관 로켓랩/SpaceX 방문
   - 드론 Guntlet 프로그램
   - 우주 패권 분석
   - 황금함대 프로젝트
   - 미일 국방장관 회담

4. **지정학 이슈** (12개)
   - 그린란드 관세 타임라인
   - 이란 이슈 타임라인
   - 지정학 수혜 ETF 순위

---

**문서 작성 완료**: 2026-01-18
**다음 단계**: Phase 1 (뉴스 태깅 파이프라인) 구현 시작