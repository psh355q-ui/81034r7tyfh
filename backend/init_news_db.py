"""
SQLite 뉴스 DB 초기화
"""
import sys
sys.path.insert(0, 'd:/code/ai-trading-system')

from backend.data.news_models import init_db, DB_PATH

print("=" * 80)
print("SQLite 뉴스 DB 초기화")
print("=" * 80)
print(f"\nDB 경로: {DB_PATH}")
print()

init_db()

print("\n✅ DB 초기화 완료!")
print(f"   위치: {DB_PATH}")
