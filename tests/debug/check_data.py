"""Check what data is in the database"""
from backend.database.repository import get_sync_session
from backend.database.models import TradingSignal, NewsArticle, AnalysisResult

db = get_sync_session()

print("=" * 80)
print("Database Contents")
print("=" * 80)
print()

# Count records
total_signals = db.query(TradingSignal).count()
total_news = db.query(NewsArticle).count()
total_analysis = db.query(AnalysisResult).count()

print(f"Total signals: {total_signals}")
print(f"Total news articles: {total_news}")
print(f"Total analyses: {total_analysis}")
print()

# Show news sources
print("News sources:")
for source in db.query(NewsArticle.source).distinct().all():
    count = db.query(NewsArticle).filter_by(source=source[0]).count()
    print(f"  - {source[0]}: {count} articles")
print()

# Show signals by type
print("Signals by type:")
for signal_type in db.query(TradingSignal.signal_type).distinct().all():
    count = db.query(TradingSignal).filter_by(signal_type=signal_type[0]).count()
    print(f"  - {signal_type[0]}: {count} signals")
print()

# Show active vs closed positions
active = db.query(TradingSignal).filter(TradingSignal.exit_price.is_(None)).count()
closed = db.query(TradingSignal).filter(TradingSignal.exit_price.isnot(None)).count()
print(f"Active positions: {active}")
print(f"Closed positions: {closed}")
print()

# Show recent signals
print("Recent signals (last 5):")
recent = db.query(TradingSignal).order_by(TradingSignal.generated_at.desc()).limit(5).all()
for signal in recent:
    print(f"  - {signal.ticker} ({signal.signal_type}): {signal.action} @ ${signal.entry_price}")
print()

db.close()
