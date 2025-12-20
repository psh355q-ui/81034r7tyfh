"""
5432 포트 DB에 trading_signals 테이블과 샘플 데이터 생성
"""
import psycopg2
from datetime import datetime, timedelta

# 5432 포트 DB 연결 (DATABASE_URL과 동일)
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="ai_trading",
    user="postgres",
    password="Qkqhdi1!"
)
conn.autocommit = True
cur = conn.cursor()

print("✅ DB 연결 성공 (5432 포트)!\n")

# 0. 기존 테이블 삭제 (Clean Slate)
print("🗑️ 기존 테이블 삭제 중...")
cur.execute("DROP TABLE IF EXISTS trading_signals CASCADE")
cur.execute("DROP TABLE IF EXISTS analysis_results CASCADE")
cur.execute("DROP TABLE IF EXISTS news_articles CASCADE")
print("✅ 기존 테이블 삭제 완료\n")

# 1. trading_signals 테이블 생성
print("📝 trading_signals 테이블 생성 중...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS trading_signals (
        id SERIAL PRIMARY KEY,
        analysis_id INTEGER,
        ticker VARCHAR(20) NOT NULL,
        action VARCHAR(10) NOT NULL,
        signal_type VARCHAR(50),
        confidence FLOAT,
        reasoning TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        alert_sent BOOLEAN DEFAULT FALSE,
        alert_sent_at TIMESTAMP,
        entry_price FLOAT,
        exit_price FLOAT,
        actual_return_pct FLOAT,
        outcome_recorded_at TIMESTAMP
    )
""")
print("✅ trading_signals 테이블 생성 완료\n")

# 2. analysis_results 테이블도 생성 (참조 무결성 위해)
print("📝 analysis_results 테이블 생성 중...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS analysis_results (
        id SERIAL PRIMARY KEY,
        article_id INTEGER,
        theme VARCHAR(255),
        content TEXT,
        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        model_name VARCHAR(50),
        analysis_duration_seconds FLOAT,
        bull_case TEXT,
        bear_case TEXT,
        step1_direct_impact TEXT,
        step2_secondary_impact TEXT,
        step3_conclusion TEXT
    )
""")
print("✅ analysis_results 테이블 생성 완료\n")

# 2-1. news_articles 테이블 생성 (AnalysisResult가 참조함)
print("📝 news_articles 테이블 생성 중...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS news_articles (
        id SERIAL PRIMARY KEY,
        title VARCHAR(500),
        content TEXT,
        url VARCHAR(1000) UNIQUE,
        source VARCHAR(100),
        published_date TIMESTAMP,
        crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        content_hash VARCHAR(64)
    )
""")
print("✅ news_articles 테이블 생성 완료\n")

# 3. 샘플 데이터 추가
print("📝 샘플 데이터 추가 중 (NewsArticle + AnalysisResult + TradingSignals)...")

now = datetime.now()

# 3-0. Dummy News Article 생성
cur.execute("""
    INSERT INTO news_articles
    (title, content, url, source, published_date, content_hash)
    VALUES
    ('AI Tech Boom Continues', 'AI is taking over the world...', 'http://example.com/ai-boom', 'Bloomberg', %s, 'hash123')
    RETURNING id
""", (now,))
article_id = cur.fetchone()[0]
print(f"✅ Dummy News Article 생성 (ID: {article_id})")

# 3-1. Dummy Analysis Result 생성
cur.execute("""
    INSERT INTO analysis_results 
    (article_id, theme, content, analyzed_at, model_name, bull_case, bear_case)
    VALUES 
    (%s, 'AI Boom and Tech Rally', 'Detailed analysis of AI sector growth...', %s, 'gemini-pro', 'Tech stocks will fly', 'Inflation might hurt')
    RETURNING id
""", (article_id, now))
analysis_id = cur.fetchone()[0]
print(f"✅ Dummy Analysis Result 생성 (ID: {analysis_id})")

signals = [
    ("AAPL", "BUY", "PRIMARY", 0.92, "Strong Q4 results and new product lineup", 180.50),
    ("NVDA", "BUY", "PRIMARY", 0.95, "AI chip demand surge", 495.30),
    ("TSLA", "BUY", "HIDDEN", 0.78, "Model 3 production ramp-up", 245.00),
    ("MSFT", "BUY", "PRIMARY", 0.89, "Cloud revenue growth acceleration", 380.00),
    ("GOOGL", "BUY", "PRIMARY", 0.85, "Search ad revenue beat expectations", 142.50),
]

for ticker, action, signal_type, confidence, reasoning, price in signals:
    cur.execute("""
        INSERT INTO trading_signals 
        (analysis_id, ticker, action, signal_type, confidence, reasoning, entry_price, generated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (analysis_id, ticker, action, signal_type, confidence, reasoning, price, now))
    print(f"  ✓ {ticker} {action} - ${price} ({int(confidence*100)}%)")

print(f"\n✅ 5개 signals 생성 완료!\n")

# 4. 확인
cur.execute("SELECT COUNT(*) FROM trading_signals")
count = cur.fetchone()[0]
print(f"📊 총 {count}개 signals 존재\n")

cur.execute("""
    SELECT ticker, action, entry_price, confidence 
    FROM trading_signals 
    ORDER BY generated_at DESC 
    LIMIT 5
""")
print("📊 최근 signals:")
for row in cur.fetchall():
    ticker, action, price, conf = row
    print(f"  {ticker} {action} - ${price:.2f} ({int(conf*100)}%)")

cur.close()
conn.close()
print("\n🎉 완료!")
