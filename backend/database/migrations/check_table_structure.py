"""
DB 테이블 구조 확인 스크립트
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, inspect
from backend.config.settings import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)
inspector = inspect(engine)

print("=== data_collection_progress 테이블 구조 ===\n")

try:
    columns = inspector.get_columns('data_collection_progress')
    for col in columns:
        nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
        default = f" DEFAULT {col.get('default', '')}" if col.get('default') else ""
        print(f"{col['name']:30} {str(col['type']):30} {nullable}{default}")
    
    print("\n=== Indexes ===\n")
    indexes = inspector.get_indexes('data_collection_progress')
    for idx in indexes:
        print(f"{idx['name']}: {idx['column_names']}")
        
except Exception as e:
    print(f"Error: {e}")
    print("\n테이블이 존재하지 않을 수 있습니다.")
