#!/usr/bin/env python3
"""
DB Schema Manager - Migration SQL Generator

JSON 스키마 정의에서 SQL 마이그레이션을 생성합니다.

Usage:
    python generate_migration.py <table_name>
    python generate_migration.py <table_name> --output-file migration.sql

Example:
    python generate_migration.py dividend_aristocrats
    python generate_migration.py news_articles --output-file create_news.sql

Output:
    CREATE TABLE, CREATE INDEX SQL statements
"""

import sys
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime


def load_schema(table_name: str) -> dict:
    """JSON 스키마 파일 로드"""
    schema_dir = Path(__file__).parent.parent / "schemas"
    schema_file = schema_dir / f"{table_name}.json"
    
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema not found: {schema_file}")
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def type_to_sql(column: dict) -> str:
    """컬럼 정의를 SQL 타입으로 변환"""
    sql_type = column["type"]
    
    # Nullable 처리
    if not column.get("nullable", True):
        sql_type += " NOT NULL"
    
    # Default 값 처리
    if "default" in column:
        default_val = column["default"]
        if default_val in ["CURRENT_TIMESTAMP", "NOW()"]:
            sql_type += f" DEFAULT {default_val}"
        elif isinstance(default_val, str):
            sql_type += f" DEFAULT '{default_val}'"
        else:
            sql_type += f" DEFAULT {default_val}"
    
    return sql_type


def generate_create_table_sql(schema: dict) -> str:
    """CREATE TABLE SQL 생성"""
    table_name = schema["table_name"]
    columns = schema["columns"]
    primary_key = schema.get("primary_key")
    
    # 컬럼 정의
    column_defs = []
    for col in columns:
        col_name = col["name"]
        col_type = type_to_sql(col)
        
        # 주석 추가 (PostgreSQL은 inline comment 미지원, 별도 COMMENT 필요)
        column_defs.append(f"    {col_name} {col_type}")
    
    # PRIMARY KEY 추가
    if primary_key:
        if isinstance(primary_key, str):
            column_defs.append(f"    PRIMARY KEY ({primary_key})")
        else:  # list
            column_defs.append(f"    PRIMARY KEY ({', '.join(primary_key)})")
    
    # CREATE TABLE 문
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    sql += ",\n".join(column_defs)
    sql += "\n);\n"
    
    return sql


def generate_create_indexes_sql(schema: dict) -> List[str]:
    """CREATE INDEX SQL 생성"""
    table_name = schema["table_name"]
    indexes = schema.get("indexes", [])
    
    sql_statements = []
    
    for idx in indexes:
        idx_name = idx["name"]
        idx_columns = idx["columns"]
        unique = idx.get("unique", False)
        order = idx.get("order", "ASC")
        
        # UNIQUE 키워드
        unique_keyword = "UNIQUE " if unique else ""
        
        # 컬럼 리스트 (DESC 지원)
        if order == "DESC":
            col_list = ", ".join(f"{col} DESC" for col in idx_columns)
        else:
            col_list = ", ".join(idx_columns)
        
        sql = f"CREATE {unique_keyword}INDEX IF NOT EXISTS {idx_name} ON {table_name}({col_list});"
        sql_statements.append(sql)
    
    return sql_statements


def generate_column_comments_sql(schema: dict) -> List[str]:
    """컬럼 주석 SQL 생성 (PostgreSQL)"""
    table_name = schema["table_name"]
    columns = schema["columns"]
    
    sql_statements = []
    
    for col in columns:
        col_name = col["name"]
        description = col.get("description")
        
        if description:
            # PostgreSQL COMMENT syntax
            sql = f"COMMENT ON COLUMN {table_name}.{col_name} IS '{description}';"
            sql_statements.append(sql)
    
    return sql_statements


def generate_full_migration(table_name: str) -> str:
    """전체 마이그레이션 SQL 생성"""
    schema = load_schema(table_name)
    
    # 헤더
    migration_sql = f"""-- Migration for table: {table_name}
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Description: {schema.get('description', 'N/A')}

"""
    
    # CREATE TABLE
    migration_sql += "-- ====================================\n"
    migration_sql += "-- Create Table\n"
    migration_sql += "-- ====================================\n\n"
    migration_sql += generate_create_table_sql(schema)
    migration_sql += "\n"
    
    # CREATE INDEXES
    index_sqls = generate_create_indexes_sql(schema)
    if index_sqls:
        migration_sql += "-- ====================================\n"
        migration_sql += "-- Create Indexes\n"
        migration_sql += "-- ====================================\n\n"
        for sql in index_sqls:
            migration_sql += sql + "\n"
        migration_sql += "\n"
    
    # COLUMN COMMENTS
    comment_sqls = generate_column_comments_sql(schema)
    if comment_sqls:
        migration_sql += "-- ====================================\n"
        migration_sql += "-- Column Comments\n"
        migration_sql += "-- ====================================\n\n"
        for sql in comment_sqls:
            migration_sql += sql + "\n"
        migration_sql += "\n"
    
    # Footer
    migration_sql += f"-- Migration complete for {table_name}\n"
    
    return migration_sql


def main():
    """메인 실행"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n❌ Error: Missing table name argument")
        sys.exit(1)
    
    table_name = sys.argv[1]
    output_file = None
    
    # --output-file 옵션 처리
    if len(sys.argv) >= 4 and sys.argv[2] == "--output-file":
        output_file = sys.argv[3]
    
    try:
        # SQL 생성
        migration_sql = generate_full_migration(table_name)
        
        # 출력 또는 파일 저장
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(migration_sql)
            print(f"✅ Migration SQL written to: {output_file}")
        else:
            print(migration_sql)
        
        sys.exit(0)
    
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
