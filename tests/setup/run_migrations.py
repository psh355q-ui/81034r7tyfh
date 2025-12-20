"""
Database Migration Runner

Alembic 마이그레이션 실행 스크립트

작성일: 2025-12-15
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*60)
print(" "*15 + "🗄️ Database Migration Runner")
print("="*60)
print()

print("📋 사용 가능한 마이그레이션:")
print()

# Versions 디렉토리 확인
versions_dir = project_root / "backend" / "migrations" / "versions"

if versions_dir.exists():
    migration_files = list(versions_dir.glob("*.py"))
    migration_files = [f for f in migration_files if f.name != "__init__.py"]
    
    for i, mig_file in enumerate(migration_files, 1):
        print(f"{i}. {mig_file.name}")
    
    print(f"\n총 {len(migration_files)}개 마이그레이션")
else:
    print("⚠️ migrations/versions 디렉토리를 찾을 수 없습니다.")

print()
print("="*60)
print()

print("ℹ️ 마이그레이션 실행 방법:")
print()
print("1. PostgreSQL 실행 확인:")
print("   postgres 서비스가 실행 중이어야 합니다.")
print()
print("2. 데이터베이스 연결 설정:")
print("   .env 파일 또는 환경 변수에서 DATABASE_URL 확인")
print()
print("3. Alembic 명령어:")
print("   cd backend")
print("   alembic upgrade head          # 최신 버전으로 업그레이드")
print("   alembic current               # 현재 버전 확인")
print("   alembic history               # 마이그레이션 히스토리")
print("   alembic downgrade -1          # 한 단계 다운그레이드")
print()

print("="*60)
print()

# 환경 변수 확인
print("📊 현재 환경 설정:")
print()

db_url = os.getenv("DATABASE_URL")
if db_url:
    # 비밀번호 숨기기
    safe_url = db_url
    if "@" in safe_url:
        parts = safe_url.split("@")
        if ":" in parts[0]:
            user_pass = parts[0].split("://")[1]
            user = user_pass.split(":")[0]
            parts[0] = parts[0].split("://")[0] + "://" + user + ":****"
            safe_url = "@".join(parts)
    
    print(f"DATABASE_URL: {safe_url}")
else:
    print("⚠️ DATABASE_URL 환경 변수가 설정되지 않았습니다.")
    print()
    print("예시:")
    print('DATABASE_URL="postgresql://user:password@localhost:5432/ai_trading"')

print()
print("="*60)
print()

# 마이그레이션 파일 내용 요약
print("📝 마이그레이션 내용:")
print()

migrations_info = {
    "251215_shadow_trades.py": {
        "테이블": "shadow_trades",
        "목적": "거부된 제안의 가상 추적",
        "주요 컬럼": ["ticker", "action", "virtual_pnl", "rejection_reason"]
    },
    "251215_proposals.py": {
        "테이블": "proposals",
        "목적": "AI 제안 및 승인 워크플로우",
        "주요 컬럼": ["ticker", "action", "status", "is_constitutional", "telegram_message_id"]
    }
}

for filename, info in migrations_info.items():
    if any(f.name == filename for f in migration_files):
        print(f"✅ {filename}")
        print(f"   테이블: {info['테이블']}")
        print(f"   목적: {info['목적']}")
        print(f"   주요 컬럼: {', '.join(info['주요 컬럼'])}")
        print()

print("="*60)
print()

print("🚀 다음 단계:")
print()
print("1. PostgreSQL이 실행 중인지 확인")
print("2. DATABASE_URL 환경 변수 설정 확인")
print("3. 백업 (권장): pg_dump로 현재 DB 백업")
print("4. 마이그레이션 실행:")
print()
print("   cd backend")
print("   alembic upgrade head")
print()
print("5. 검증:")
print("   - 테이블 생성 확인 (shadow_trades, proposals)")
print("   - 인덱스 생성 확인")
print()

print("="*60)
