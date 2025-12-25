#!/usr/bin/env python3
"""
DB Schema Manager - Data Validation Script

데이터가 정의된 스키마를 만족하는지 검증합니다.

Usage:
    python validate_data.py <table_name> '<json_data>'

Example:
    python validate_data.py dividend_aristocrats '{"ticker": "JNJ", "company_name": "Johnson & Johnson", "consecutive_years": 61}'

Exit Codes:
    0: Validation passed
    1: Validation failed or error
"""

import sys
import json
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, create_model, ValidationError, Field


def load_schema(table_name: str) -> dict:
    """스키마 JSON 파일 로드"""
    schema_dir = Path(__file__).parent.parent / "schemas"
    schema_file = schema_dir / f"{table_name}.json"
    
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema not found: {schema_file}")
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def sql_type_to_python(sql_type: str) -> type:
    """SQL 타입 → Python 타입 변환"""
    # VARCHAR(n), NUMERIC(n,m) 등에서 기본 타입 추출
    base_type = sql_type.split("(")[0].upper()
    
    type_mapping = {
        "INTEGER": int,
        "INT": int,
        "BIGINT": int,
        "SMALLINT": int,
        "FLOAT": float,
        "DOUBLE": float,
        "NUMERIC": float,
        "DECIMAL": float,
        "VARCHAR": str,
        "CHAR": str,
        "TEXT": str,
        "STRING": str,
        "TIMESTAMP": str,
        "DATETIME": str,
        "DATE": str,
        "BOOLEAN": bool,
        "BOOL": bool,
    }
    
    return type_mapping.get(base_type, str)


def schema_to_pydantic(schema: dict) -> type[BaseModel]:
    """JSON 스키마 → Pydantic 모델 변환"""
    fields = {}
    
    for col in schema["columns"]:
        python_type = sql_type_to_python(col["type"])
        
        # nullable이면 Optional 타입으로
        if col.get("nullable", False):
            python_type = Optional[python_type]
            default = None
        else:
            # nullable=False이면 필수 필드 (...)
            default = ...
        
        # default 값이 정의되어 있으면 사용
        if "default" in col and col["default"] not in ["CURRENT_TIMESTAMP", "NOW()"]:
            try:
                default = python_type(col["default"]) if python_type != str else col["default"]
            except:
                pass
        
        # Field with description
        field_info = Field(default=default, description=col.get("description", ""))
        fields[col["name"]] = (python_type, field_info)
    
    # 동적으로 Pydantic 모델 생성
    return create_model(
        schema["table_name"],
        **fields
    )


def validate_data(table_name: str, data: dict) -> tuple[bool, str]:
    """
    데이터 검증
    
    Returns:
        (success: bool, message: str)
    """
    try:
        # 스키마 로드
        schema = load_schema(table_name)
        
        # Pydantic 모델 생성
        Model = schema_to_pydantic(schema)
        
        # 검증 실행
        validated = Model(**data)
        
        # 검증 성공
        return True, f"✅ Validation passed for table '{table_name}'"
        
    except FileNotFoundError as e:
        return False, f"❌ Schema Error: {e}"
    
    except ValidationError as e:
        # Pydantic 검증 실패 - 상세 에러 메시지
        errors = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            errors.append(f"  • {field}: {msg}")
        
        error_msg = f"❌ Validation failed for table '{table_name}':\n" + "\n".join(errors)
        return False, error_msg
    
    except json.JSONDecodeError as e:
        return False, f"❌ Invalid JSON data: {e}"
    
    except Exception as e:
        return False, f"❌ Unexpected error: {type(e).__name__}: {e}"


def main():
    """메인 실행 함수"""
    if len(sys.argv) != 3:
        print(__doc__)
        print("\n❌ Error: Invalid number of arguments")
        print(f"   Expected: 2, Got: {len(sys.argv) - 1}")
        sys.exit(1)
    
    table_name = sys.argv[1]
    
    # JSON 데이터 파싱
    try:
        data = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        print(f"   Input: {sys.argv[2]}")
        sys.exit(1)
    
    # 검증 실행
    success, message = validate_data(table_name, data)
    
    # 결과 출력
    print(message)
    
    # 종료 코드
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
