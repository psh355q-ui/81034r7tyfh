#!/usr/bin/env python3
"""
DB Schema Manager - Schema Comparison Script

정의된 스키마와 실제 DB 스키마를 비교합니다.

Usage:
    python compare_to_db.py <table_name>
    python compare_to_db.py --all

Example:
    python compare_to_db.py dividend_aristocrats
    python compare_to_db.py --all

Exit Codes:
    0: All schemas match
    1: Schema mismatch found or error
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
import os

# .env에서 DATABASE_URL 읽기
def get_database_url() -> str:
    """환경변수 또는 .env 파일에서 DATABASE_URL 가져오기"""
    # 환경변수 먼저 확인
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url
    
    # .env 파일 찾기 (프로젝트 루트)
    env_file = Path(__file__).parent.parent.parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL'):
                    if '=' in line:
                        value = line.split('=', 1)[1].strip()
                        return value.strip('"').strip("'")
    
    raise ValueError("DATABASE_URL not found in environment or .env file")


def load_schema(table_name: str) -> dict:
    """JSON 스키마 파일 로드"""
    schema_dir = Path(__file__).parent.parent / "schemas"
    schema_file = schema_dir / f"{table_name}.json"
    
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema not found: {schema_file}")
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_db_schema(table_name: str) -> Dict:
    """실제 DB에서 스키마 정보 가져오기"""
    try:
        import psycopg2
    except ImportError:
        raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")
    
    # DATABASE_URL 가져오기
    db_url = get_database_url()
    
    # AsyncEngine URL → 동기식 변환
    if 'asyncpg' in db_url:
        db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    try:
        # 컬럼 정보 가져오기
        cur.execute("""
            SELECT 
                column_name, 
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = []
        for row in cur.fetchall():
            col_name, data_type, max_len, num_prec, num_scale, nullable, default = row
            
            # 타입 재구성
            if data_type == 'character varying' and max_len:
                sql_type = f"VARCHAR({max_len})"
            elif data_type == 'numeric' and num_prec and num_scale:
                sql_type = f"NUMERIC({num_prec},{num_scale})"
            elif data_type == 'integer':
                sql_type = "INTEGER"
            elif data_type == 'timestamp without time zone':
                sql_type = "TIMESTAMP"
            elif data_type == 'text':
                sql_type = "TEXT"
            else:
                sql_type = data_type.upper()
            
            columns.append({
                "name": col_name,
                "type": sql_type,
                "nullable": (nullable == "YES"),
                "default": default
            })
        
        return {
            "table_name": table_name,
            "columns": columns
        }
    finally:
        cur.close()
        conn.close()


def normalize_type(sql_type: str) -> str:
    """타입 정규화 (비교 용이하게)"""
    sql_type = sql_type.upper().strip()
    
    # VARCHAR(n) → VARCHAR
    if sql_type.startswith('VARCHAR'):
        return 'VARCHAR'
    
    # NUMERIC(n,m) → NUMERIC
    if sql_type.startswith('NUMERIC') or sql_type.startswith('DECIMAL'):
        return 'NUMERIC'
    
    # TIMESTAMP variations
    if 'TIMESTAMP' in sql_type:
        return 'TIMESTAMP'
    
    return sql_type


def compare_schemas(defined: Dict, actual: Dict) -> List[str]:
    """스키마 비교 및 차이점 반환"""
    differences = []
    
    defined_cols = {c["name"]: c for c in defined["columns"]}
    actual_cols = {c["name"]: c for c in actual["columns"]}
    
    # 누락된 컬럼 (정의에는 있지만 DB에는 없음)
    missing_cols = set(defined_cols.keys()) - set(actual_cols.keys())
    if missing_cols:
        differences.append(f"❌ Missing columns in DB: {sorted(missing_cols)}")
    
    # 추가 컬럼 (DB에는 있지만 정의에는 없음)
    extra_cols = set(actual_cols.keys()) - set(defined_cols.keys())
    if extra_cols:
        differences.append(f"⚠️  Extra columns in DB (not in schema): {sorted(extra_cols)}")
    
    # 공통 컬럼의 타입 및 속성 비교
    common_cols = set(defined_cols.keys()) & set(actual_cols.keys())
    for col_name in sorted(common_cols):
        d_col = defined_cols[col_name]
        a_col = actual_cols[col_name]
        
        # 타입 비교 (정규화)
        d_type = normalize_type(d_col["type"])
        a_type = normalize_type(a_col["type"])
        
        if d_type != a_type:
            differences.append(
                f"❌ Type mismatch for '{col_name}': "
                f"defined={d_col['type']}, actual={a_col['type']}"
            )
        
        # Nullable 비교
        if d_col.get("nullable", True) != a_col["nullable"]:
            differences.append(
                f"⚠️  Nullable mismatch for '{col_name}': "
                f"defined={'NULL' if d_col.get('nullable') else 'NOT NULL'}, "
                f"actual={'NULL' if a_col['nullable'] else 'NOT NULL'}"
            )
    
    return differences


def compare_single_table(table_name: str) -> Tuple[bool, List[str]]:
    """단일 테이블 비교"""
    try:
        # 정의된 스키마 로드
        defined = load_schema(table_name)
        
        # 실제 DB 스키마 가져오기
        actual = get_db_schema(table_name)
        
        # 비교
        differences = compare_schemas(defined, actual)
        
        return (len(differences) == 0), differences
    
    except FileNotFoundError as e:
        return False, [f"❌ {e}"]
    except Exception as e:
        return False, [f"❌ Error: {type(e).__name__}: {e}"]


def compare_all_tables() -> Dict[str, Tuple[bool, List[str]]]:
    """모든 정의된 테이블 비교"""
    schema_dir = Path(__file__).parent.parent / "schemas"
    results = {}
    
    for schema_file in schema_dir.glob("*.json"):
        table_name = schema_file.stem
        success, differences = compare_single_table(table_name)
        results[table_name] = (success, differences)
    
    return results


def main():
    """메인 실행"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n❌ Error: Missing table name argument")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == "--all":
        # 모든 테이블 비교
        print("🔍 Comparing all tables...\n")
        results = compare_all_tables()
        
        all_match = True
        for table_name, (success, differences) in sorted(results.items()):
            if success:
                print(f"✅ {table_name}: Schema matches!")
            else:
                print(f"❌ {table_name}: Schema mismatch!")
                for diff in differences:
                    print(f"  {diff}")
                all_match = False
            print()
        
        print(f"\n📊 Summary: {sum(1 for s, _ in results.values() if s)}/{len(results)} tables match")
        sys.exit(0 if all_match else 1)
    
    else:
        # 단일 테이블 비교
        table_name = arg
        success, differences = compare_single_table(table_name)
        
        if success:
            print(f"✅ {table_name}: Schema matches perfectly!")
            sys.exit(0)
        else:
            print(f"❌ {table_name}: Schema mismatch!\n")
            for diff in differences:
                print(diff)
            sys.exit(1)


if __name__ == "__main__":
    main()
