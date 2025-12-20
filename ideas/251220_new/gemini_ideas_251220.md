Finviz 뉴스 데이터를 AI 트레이딩 시스템에 통합하는 아이디어는 매우 훌륭합니다. Finviz는 미국 주식 시장 뉴스를 실시간으로 빠르게 제공하며, AI를 활용하여 이를 정량적 데이터로 변환하고 RAG 시스템에 통합하면 시스템의 정보 처리 능력을 크게 향상할 수 있습니다.

ChatGPT가 제안한 내용도 매우 실용적이며, 이를 바탕으로 시스템에 바로 적용 가능한 **구체적인 구현 로드맵**을 정리해 드립니다.

### 1. **핵심 기능 설계: "뉴스 인텔리전스 (News Intelligence)"**

이 기능은 단순히 뉴스를 보여주는 것이 아니라, 뉴스를 **"거래 가능한 신호(Tradable Signal)"**로 변환하는 것을 목표로 합니다.

* **실시간 수집 및 전처리**: Finviz 뉴스 페이지를 주기적으로 스크래핑하여 최신 뉴스를 가져옵니다. 제목, 출처, 시간 등을 파싱하고 정규화합니다.
* **AI 기반 심층 분석**: 수집된 뉴스를 LLM(Claude/Gemini)에 전달하여 다음 정보를 추출합니다.
* **감성(Sentiment)**: 긍정(Positive), 부정(Negative), 중립(Neutral), 혼돈(Mixed/Chaos).
* **영향도(Impact Score)**: 0~100점 사이의 점수로, 시장이나 종목에 미칠 파급력을 수치화합니다. (80점 이상은 긴급 알림)
* **관련 티커(Related Tickers)**: 뉴스에 직접 언급된 티커뿐만 아니라, 연관된 종목(예: 경쟁사, 공급망 파트너)까지 추론하여 태깅합니다.
* **키워드(Keywords)**: '실적 발표', 'FDA 승인', '금리 인상', '지정학적 리스크' 등 핵심 키워드를 추출합니다.


* **지식 통합 (Embedding & RAG)**: 분석된 뉴스 데이터와 메타데이터를 임베딩하여 벡터 데이터베이스에 저장합니다. 이후 트레이딩 에이전트가 의사결정을 내릴 때 RAG를 통해 관련 뉴스를 검색하고 참조할 수 있게 합니다.
* **AI War 전략 반영**: `NewsAgent`를 신설하여 AI 위원회(War Room) 토론에 참여시킵니다. `NewsAgent`는 뉴스 데이터를 근거로 시장 상황을 설명하고 매수/매도 의견을 제시합니다.

### 2. **Claude Code를 위한 실행 명령어 (Action Plan)**

아래 명령어들을 순서대로 Claude Code에 입력하여 구현을 진행할 수 있습니다.

**[Step 1: 데이터 수집기 구현]**

```bash
claude "Create 'backend/data/collectors/finviz_collector.py'.
1. Use 'BeautifulSoup' or 'finvizfinance' to scrape 'https://finviz.com/news.ashx' every 5 minutes.
2. Extract headline, source, timestamp, and link.
3. Handle anti-scraping measures (User-Agent rotation).
4. Save raw data to a staging table in the database."

```

**[Step 2: AI 뉴스 분석기 구현]**

```bash
claude "Implement 'backend/ai/news_analyzer.py'.
1. Fetch raw news from the staging table.
2. Use Gemini Flash (for speed/cost) to analyze each headline.
3. Output a JSON object with:
   - sentiment: 'POSITIVE', 'NEGATIVE', 'NEUTRAL', 'CHAOS'
   - impact_score: 0-100 integer
   - related_tickers: list of ticker symbols
   - keywords: list of strings
4. Store the structured result in the 'news_articles' table."

```

**[Step 3: 임베딩 및 RAG 파이프라인 구축]**

```bash
claude "Create 'backend/pipelines/news_embedding_pipeline.py'.
1. Generate vector embeddings for the analyzed news (headline + keywords).
2. Store embeddings in the 'document_embeddings' table using pgvector.
3. Include metadata (sentiment, impact_score, tickers) for filtering.
4. Update 'backend/ai/vector_search.py' to support querying news by ticker and impact score."

```

**[Step 4: NewsAgent 및 AI War 통합]**

```bash
claude "Update 'backend/intelligence/debate_engine.py' and add 'backend/intelligence/news_agent.py'.
1. The 'NewsAgent' retrieves relevant high-impact news from the vector store using RAG.
2. It participates in the debate, providing arguments based on news sentiment and impact.
3. The 'PM Agent' must consider the NewsAgent's input when forming the final verdict."

```

### 3. **추가 고려사항 및 팁**

* **비용 효율성**: 모든 뉴스를 분석하면 API 비용이 많이 들 수 있습니다. Finviz에서 제공하는 티커가 있는 뉴스나, 특정 키워드가 포함된 뉴스만 1차 필터링하여 AI에게 분석시키는 것이 좋습니다.
* **속도**: 뉴스는 속도가 생명입니다. 수집부터 분석, 알림까지의 지연 시간을 최소화하기 위해 비동기 처리(`asyncio`)와 가벼운 모델(Gemini Flash)을 적극 활용하세요.
* **거짓 정보 필터링**: `Sentiment: CHAOS`는 서로 다른 뉴스 소스가 상반된 이야기를 할 때 유용합니다. 이 경우 `Skeptic Agent`를 호출하여 팩트 체크를 수행하게 하는 로직을 추가할 수 있습니다.

이 기능을 통해 당신의 시스템은 단순히 차트만 보는 것이 아니라, **시장의 맥락을 이해하고 뉴스를 해석하는 지능형 트레이더**로 거듭날 것입니다.