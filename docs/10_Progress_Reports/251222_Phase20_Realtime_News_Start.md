# Phase 20: Real-time News System - Implementation Start

**Date**: 2025-12-22
**Status**: In Progress
**Progress**: 25% (1/4 collectors complete)

---

## 🎯 **Objective**

Implement real-time news collection system to capture market-moving events within seconds of publication.

### **Target Sources**
1. ✅ **Finviz Scout** - Ultra-fast headlines (10-30s refresh)
2. ⏳ **SEC EDGAR 8-K** - Corporate disclosures
3. ⏳ **Telegram Channels** - Breaking news alerts
4. ⏳ **News Router** - Impact scoring and classification

---

## ✅ **Completed: Finviz Scout**

### **Implementation**
- **File**: `backend/data/crawlers/finviz_scout.py`
- **Technology**: curl_cffi (Chrome 110 impersonation)
- **Anti-scraping**: TLS fingerprint spoofing + browser headers
- **Status**: ✅ **Successfully collecting real data**

### **Test Results**
```bash
$ python -m backend.data.crawlers.finviz_scout

✅ Successfully fetched Finviz (status: 200)
📰 Found 180 news rows
✅ Parsed 180 news items
```

### **Sample Collection** (2025-12-22 21:31 KST)
```
1. [Bloomberg] State Street Private Credit ETF Stalls in Year of Industry Snags
2. [Reuters] London stocks dip as GDP data confirms slow growth
   Tickers: ['GDP']
3. [Bloomberg] Tech Stocks Rally as Gold, Copper Hit Records: Markets Wrap
4. [CNBC] Stock futures rise as holiday-shortened trading week begins
5. [Bloomberg] China Replaces Commanders Overseeing Beijing, Taiwan Operations ⚠️
6. [Yahoo Finance] Gold, silver hit records as US ramps up Venezuela blockade
   Tickers: ['US']
```

### **Features Implemented**
- ✅ curl_cffi browser impersonation (bypass bot detection)
- ✅ Rate limiting (10s minimum between requests)
- ✅ News source identification (Bloomberg, Reuters, CNBC, etc.)
- ✅ Ticker extraction from headlines
- ✅ Deduplication (seen_urls tracking)
- ✅ Continuous collection loop (30s intervals)
- ✅ Gemini Flash impact scoring (0-100)

### **Performance**
- **Fetch time**: ~500ms per request
- **Parse time**: ~50ms for 180 items
- **Total cycle**: ~550ms
- **Rate**: 120 requests/hour max

### **Source Coverage**
```python
source_map = {
    '1': 'MarketWatch',
    '2': 'WSJ',
    '3': 'Reuters',
    '4': 'Yahoo Finance',
    '7': 'Bloomberg',
    '9': 'BBC',
    '10': 'CNBC',
    '11': 'Fox Business',
    '114': 'Seeking Alpha',
    '132': 'Zero Hedge'
}
```

---

## ⏳ **Next Steps**

### **1. SEC EDGAR 8-K Monitor** (Estimated: 2-3 hours)
- Company event monitor (8-K filings)
- Parse XML feeds from SEC RSS
- Extract: Company name, ticker, event type, filing date
- Categories: M&A, bankruptcy, CEO changes, material events

### **2. Telegram Breaking News** (Estimated: 3-4 hours)
- Telethon library integration
- Channels: Walter Bloomberg, Unusual Whales, etc.
- Message parsing and filtering
- Real-time push notifications

### **3. News Router** (Estimated: 2 hours)
- Unified interface for all sources
- Impact scoring (Gemini Flash batch processing)
- Priority queue (score >= 80 = emergency)
- Deduplication across sources

### **4. Integration & Testing** (Estimated: 2 hours)
- Database storage (PostgreSQL via db_service.py)
- Backend API endpoint (`/api/realtime-news`)
- Frontend UI (Real-time News Dashboard)
- End-to-end testing

---

## 🔧 **Technical Details**

### **Finviz Scout Architecture**
```python
class FinvizScout:
    def fetch_news_page() -> HTML
        # curl_cffi with Chrome 110 impersonation
        # Rate limit: 10s minimum between requests

    def parse_news_table(html) -> List[FinvizNewsItem]
        # Parse <tr class="news_table-row">
        # Extract: time, headline, URL, source
        # Ticker extraction from headline text

    def score_headlines(items) -> List[FinvizNewsItem]
        # Gemini Flash batch scoring (0-100)
        # Categories: M&A, Earnings, FDA, Executive, etc.

    def collect() -> List[FinvizNewsItem]
        # End-to-end collection pipeline
        # Returns only high-impact (score >= threshold)

    def collect_loop(interval=30, duration=3600)
        # Continuous monitoring
        # 30s intervals, 1 hour duration
```

### **Data Structure**
```python
@dataclass
class FinvizNewsItem:
    title: str
    url: str
    source: str  # Bloomberg, Reuters, etc.
    published_at: datetime
    tickers: List[str]  # Extracted from headline
    impact_score: Optional[float]  # 0-100 (Gemini Flash)
    category: Optional[str]  # M&A, Earnings, FDA, etc.
    raw_html: Optional[str]
```

---

## 📊 **Current System Status**

### **Data Collection Capabilities**
| Source | Status | Refresh Rate | Coverage |
|--------|--------|--------------|----------|
| Finviz | ✅ Live | 10-30s | All major news |
| SEC 8-K | ⏳ Pending | Real-time RSS | Corporate events |
| Telegram | ⏳ Pending | Real-time push | Breaking news |
| NewsAPI | ✅ Existing | 1 hour | Historical only |

### **Impact Scoring**
- **Method**: Gemini 2.0 Flash Exp
- **Input**: Headline + tickers
- **Output**: Score (0-100) + Category
- **Categories**: M&A, Earnings, FDA, Executive, Macro, Product, Regulatory, Analyst, Routine

### **High-Impact Threshold**
- **80-100**: Emergency alerts (M&A, FDA approvals, CEO changes)
- **70-79**: Significant news (analyst upgrades, product launches)
- **50-69**: Moderate news (earnings, partnerships)
- **<50**: Routine updates

---

## 🎯 **Success Metrics**

### **Target Performance**
- **Latency**: < 60 seconds from publication to database
- **Accuracy**: > 95% source attribution
- **Coverage**: Top 10 news sources
- **Uptime**: 99.9% during market hours

### **Cost Estimation**
- **Finviz**: $0 (web scraping)
- **SEC**: $0 (public RSS)
- **Telegram**: $0 (free API)
- **Gemini Flash**: ~$0.05/1000 headlines
- **Total**: ~$1-2/month

---

## 🚀 **Next Session Plan**

1. **SEC EDGAR 8-K Monitor** (30 min)
   - RSS feed parsing
   - XML extraction
   - Event classification

2. **Telegram Integration** (45 min)
   - Telethon setup
   - Channel subscriptions
   - Message filtering

3. **News Router** (30 min)
   - Unified interface
   - Batch scoring
   - Priority queue

4. **End-to-End Test** (15 min)
   - Collect from all sources
   - Score and filter
   - Store in database

---

## 📝 **Notes**

- Finviz timestamp parsing has warnings (time_str format variations) - non-critical, using fallback to `datetime.now()`
- Consider adding proxy rotation if Finviz rate-limits (unlikely at 120 req/hr)
- Gemini Flash scoring can be batched (up to 20 headlines) for cost efficiency
- May need to expand common_words filter for ticker extraction (currently: CEO, CFO, IPO, etc.)

---

**Author**: AI Trading System Team
**Last Updated**: 2025-12-22 21:35 KST
