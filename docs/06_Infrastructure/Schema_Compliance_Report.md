# Database Standards Compliance Report

**Generated**: 2025-12-27 14:33
**Validation Tool**: db-schema-manager/scripts/compare_to_db.py

---

## 📊 Executive Summary

| 테이블 | 상태 | 스키마 일치 | 발견된 문제 |
|--------|------|------------|------------|
| stock_prices | ✅ PASS | 100% | 0 |
| news_articles | ❌ FAIL | ~70% | 5개 컬럼 누락, 1개 nullable 불일치 |
| trading_signals | ❌ FAIL | ~65% | 6개 컬럼 누락, 1개 nullable 불일치 |
| data_collection_progress | ⚠️ WARNING | ~95% | 1개 타입 불일치 |

**전체 준수율**: 25% (1/4 테이블)

---

## ✅ PASS: stock_prices

```
✅ stock_prices: Schema matches perfectly!
```

**분석**:
- 모든 컬럼이 스키마 정의와 정확히 일치
- TimescaleDB `time` 컬럼 올바르게 사용
- 인덱스 정의 일치
- **액션**: 없음 (표준 준수)

---

## ❌ FAIL: news_articles

### 발견된 문제

#### 1. 누락된 컬럼 (5개)
```
❌ Missing columns in DB:
- created_at
- is_analyzed
- published_date  
- sentiment_label
- source
```

#### 2. Nullable 불일치
```
⚠️ Nullable mismatch for 'url':
- 스키마 정의: NOT NULL (unique=true)
- 실제 DB: NULL
```

### 원인 분석
1. **실제 테이블**이 오래된 버전
2. 스키마 JSON은 최신 요구사항 반영
3. 마이그레이션 미실행

### 수정 방법

#### Option 1: ALTER TABLE (권장)
```sql
-- 누락 컬럼 추가
ALTER TABLE news_articles 
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN is_analyzed BOOLEAN DEFAULT FALSE,
ADD COLUMN published_date TIMESTAMP,
ADD COLUMN sentiment_label VARCHAR(20),
ADD COLUMN source VARCHAR(100);

-- url을 NOT NULL로 변경
UPDATE news_articles SET url = 'unknown' WHERE url IS NULL;
ALTER TABLE news_articles ALTER COLUMN url SET NOT NULL;
```

#### Option 2: 테이블 재생성
```bash
# 1. 스키마에서 SQL 생성
python backend/ai/skills/system/db-schema-manager/scripts/generate_migration.py news_articles

# 2. 기존 데이터 백업
pg_dump -t news_articles ai_trading > backup_news.sql

# 3. 테이블 드롭 및 재생성
# (생성된 SQL 실행)

# 4. 데이터 복원
psql ai_trading < backup_news.sql
```

---

## ❌ FAIL: trading_signals

### 발견된 문제

#### 1. 누락된 컬럼 (6개)
```
❌ Missing columns in DB:
- created_at
- executed_at
- metadata
- exit_price
- outcome_recorded_at
- (1개 더 - 출력 잘림)
```

#### 2. Nullable 불일치
```
⚠️ Nullable mismatch for 'source':
- 스키마 정의: NOT NULL
- 실제 DB: NULL
```

### 원인 분석
- 초기 버전 테이블 사용 중
- 필수 추적 컬럼들 누락
- `source` 필드 nullable 처리 (표준 위반)

### 수정 방법

```sql
-- 누락 컬럼 추가
ALTER TABLE trading_signals 
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN executed_at TIMESTAMP,
ADD COLUMN metadata JSONB,
ADD COLUMN exit_price FLOAT,
ADD COLUMN outcome_recorded_at TIMESTAMP;

-- source를 NOT NULL로 변경 (기존 데이터 처리 필요)
UPDATE trading_signals SET source = 'unknown' WHERE source IS NULL;
ALTER TABLE trading_signals ALTER COLUMN source SET NOT NULL;
```

---

## ⚠️ WARNING: data_collection_progress

### 발견된 문제

#### 1. 타입 불일치
```
❌ Type mismatch for 'progress_pct':
- 스키마 정의: FLOAT
- 실제 DB: DOUBLE PRECISION
```

### 원인 분석
- PostgreSQL의 FLOAT는 자동으로 DOUBLE PRECISION으로 변환됨
- 기능적으로 동일하므로 **큰 문제 없음**

### 수정 방법

#### Option 1: 스키마 JSON 수정 (권장)
```json
{
  "name": "progress_pct",
  "type": "DOUBLE PRECISION",  // FLOAT → DOUBLE PRECISION
  "nullable": false,
  "default": 0.0
}
```

#### Option 2: 유지
- FLOAT와 DOUBLE PRECISION은 기능적으로 동일
- 성능 영향 없음
- **액션**: 스키마 JSON만 업데이트

---

## 🎯 수정 우선순위

### High Priority (즉시)

1. **news_articles**
   - [ ] `source` 컬럼 추가 (데이터 소스 추적 필수)
   - [ ] `created_at` 컬럼 추가 (감사 추적 필수)
   - [ ] `is_analyzed` 컬럼 추가 (처리 상태 추적)

2. **trading_signals**
   - [ ] `source` 컬럼 NOT NULL 설정 (추적성 필수)
   - [ ] `created_at` 컬럼 추가 (감사 추적 필수)
   - [ ] `metadata` 컬럼 추가 (AI 모델 정보 저장)

### Medium Priority (1주일 내)

3. **news_articles**
   - [ ] `published_date` 컬럼 추가
   - [ ] `sentiment_label` 컬럼 추가
   - [ ] `url` NOT NULL 제약 조건 추가

4. **trading_signals**
   - [ ] `executed_at` 컬럼 추가
   - [ ] `exit_price` 컬럼 추가
   - [ ] `outcome_recorded_at` 컬럼 추가

### Low Priority (참고)

5. **data_collection_progress**
   - [ ] 스키마 JSON 타입 수정 (DOUBLE PRECISION)

---

## 📋 실행 계획

### Phase 1: 백업 (필수)
```bash
# 전체 DB 백업
pg_dump ai_trading > backup_$(date +%Y%m%d).sql

# 개별 테이블 백업
pg_dump -t news_articles ai_trading > backup_news_articles.sql
pg_dump -t trading_signals ai_trading > backup_trading_signals.sql
```

### Phase 2: 마이그레이션 스크립트 생성
```bash
cd backend/database/migrations

# 새 마이그레이션 생성
cat > fix_schema_compliance.sql << 'EOF'
-- news_articles 수정
ALTER TABLE news_articles 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS is_analyzed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS published_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS sentiment_label VARCHAR(20),
ADD COLUMN IF NOT EXISTS source VARCHAR(100);

-- trading_signals 수정
ALTER TABLE trading_signals 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS executed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS metadata JSONB,
ADD COLUMN IF NOT EXISTS exit_price FLOAT,
ADD COLUMN IF NOT EXISTS outcome_recorded_at TIMESTAMP;

-- source 필드 NOT NULL 처리 (기존 데이터 있으면)
UPDATE news_articles SET source = 'legacy' WHERE source IS NULL;
UPDATE trading_signals SET source = 'legacy' WHERE source IS NULL;

ALTER TABLE news_articles ALTER COLUMN source SET NOT NULL;
ALTER TABLE trading_signals ALTER COLUMN source SET NOT NULL;
EOF
```

### Phase 3: 실행 및 검증
```bash
# 1. 마이그레이션 실행
psql -U postgres -d ai_trading -f fix_schema_compliance.sql

# 2. 재검증
python backend/ai/skills/system/db-schema-manager/scripts/compare_to_db.py news_articles
python backend/ai/skills/system/db-schema-manager/scripts/compare_to_db.py trading_signals

# 3. 성공 확인
# ✅ news_articles: Schema matches perfectly!
# ✅ trading_signals: Schema matches perfectly!
```

---

## 🎓 학습 사항

### 왜 불일치가 발생했나?

1. **점진적 개발**: 테이블이 시간이 지나면서 진화
2. **수동 ALTER TABLE**: 일부는 수동으로 추가됨
3. **스키마 관리 부재**: 단일 진실의 소스 없었음

### 앞으로 방지 방법

1. **새 테이블**: 반드시 스키마 JSON 먼저 작성
2. **변경 사항**: 스키마 JSON 업데이트 → SQL 생성 → 실행
3. **정기 검증**: Weekly `compare_to_db.py` 실행
4. **CI/CD 통합**: PR 시 자동 스키마 검증

---

## ✅ 완료 체크리스트

```markdown
- [x] 스키마 검증 실행
- [x] 불일치 항목 식별
- [x] 수정 우선순위 결정
- [ ] 백업 실행
- [ ] 마이그레이션 스크립트 작성
- [ ] 마이그레이션 실행
- [ ] 재검증 (100% 일치 목표)
- [ ] models.py 업데이트
- [ ] Repository 업데이트
```

---

**Next Steps**: 백업을 먼저 실행한 후 High Priority 항목부터 수정하세요.
