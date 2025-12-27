# Infrastructure & Database Documentation

## 📚 문서 목록

### 인프라 구축
1. **[NAS_Deployment_Guide.md](./NAS_Deployment_Guide.md)**
   - Synology DS718+ 기반 운영 환경 구축
   - Docker PostgreSQL + TimescaleDB 설정
   - 자동 백업 및 모니터링
   - 3단계 로드맵: 로컬 → NAS → AWS

2. **[Infrastructure_Management.md](./Infrastructure_Management.md)**
   - 환경별 인프라 구성 (개발/스테이징/운영)
   - 데이터베이스 관리 도구 가이드
   - 백업 전략 및 모니터링
   - 마이그레이션 관리 및 성능 최적화

### 데이터베이스 표준
3. **[Database_Standards.md](./Database_Standards.md)**
   - 통합 데이터베이스 표준 및 규칙
   - 데이터 모델 정의 (시계열, 뉴스, 트레이딩 시그널)
   - Repository 패턴 및 사용 가이드
   - AI 개발 도구용 자동 검증 규칙

4. **[Schema_Compliance_Report.md](./Schema_Compliance_Report.md)**
   - 데이터베이스 스키마 준수 검증 결과
   - 발견된 문제점 및 수정 방법
   - 우선순위별 수정 계획

5. **[Storage_Optimization.md](./Storage_Optimization.md)**
   - DB 용량 최적화 분석
   - 컬럼 통합 전략 (JSONB 활용)
   - 예상 용량 절감 효과

6. **[Completion_Report_20251227.md](./Completion_Report_20251227.md)**
   - **Phase 4 완료 보고서 (Code Refactoring)**
   - Legacy DB 패턴 제거 상세 내용
   - Schema 100% 동기화 결과

## 🎯 빠른 참조

### 개발 환경
- **DB**: 로컬 PostgreSQL 18
- **포트**: 5432
- **관리 도구**: DBeaver, pgcli

### 운영 환경 (계획)
- **하드웨어**: Synology DS718+
- **구성**: Docker PostgreSQL + TimescaleDB
- **백업**: 매일 자동 백업 + Cloud Sync
- **비용**: 초기 ~$230, 월간 ~$5

### 핵심 표준
- 시계열 테이블: `time` 컬럼 필수 (not `date`)
- 모든 테이블: `id`, `created_at` 필수
- Repository 패턴만 사용 (직접 SQL 금지)
- 네이밍: `snake_case`, 불린은 `is_*`, 시간은 `*_at`

## 🔗 관련 도구

### db-schema-manager
```bash
# 위치
backend/ai/skills/system/db-schema-manager/

# 스키마 검증
python scripts/compare_to_db.py {table_name}

# 데이터 검증
python scripts/validate_data.py {table_name} '{json_data}'

# SQL 생성
python scripts/generate_migration.py {table_name}
```

### 마이그레이션
```bash
# Alembic 사용 (권장)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

**Last Updated**: 2025-12-27
