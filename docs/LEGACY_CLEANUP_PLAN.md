# Legacy Code Cleanup Plan

**작성일**: 2026-01-25
**목적**: 레거시 코드 정리 및 시스템 간소화
**우선순위**: HIGH (시스템 복잡도 감소, 유지보수성 향상)

---

## 📋 목차

1. [발견된 레거시 코드](#발견된-레거시-코드)
2. [영향 분석](#영향-분석)
3. [정리 계획](#정리-계획)
4. [실행 순서](#실행-순서)
5. [백업 및 복구 계획](#백업-및-복구-계획)

---

## 발견된 레거시 코드

### 1. Debate System (Legacy AI Agents)

#### 위치
- `backend/ai/debate/` - **14개 파일** (구형 8-Agent Debate System)
- `backend/ai/legacy/debate/` - **14개 파일** (중복 백업)

#### 파일 목록
```
backend/ai/debate/
├── __init__.py
├── news_agent.py
├── trader_agent.py
├── risk_agent.py
├── analyst_agent.py
├── macro_agent.py
├── institutional_agent.py
├── chip_war_agent.py
├── sentiment_agent.py
├── skeptic_agent.py
├── ai_debate_engine.py
├── constitutional_debate_engine.py
├── priority_calculator.py
├── chip_war_agent_helpers.py
└── (동일 파일들이 backend/ai/legacy/debate/에도 존재)
```

#### 사용 현황
- ✅ **War Room MVP** (`backend/routers/war_room_mvp_router.py`) - 프로덕션용 (3+1 에이전트, 사용 중)
- ⚠️ **War Room Legacy** (`backend/api/war_room_router.py`) - 구형 (8 에이전트, debate 시스템 사용)
- ⚠️ **Phase Integration Router** (`backend/api/phase_integration_router.py`) - debate_engine 사용

#### 의존성 분석
```
사용 중인 파일들:
1. backend/api/war_room_router.py → debate 에이전트 임포트
2. backend/api/phase_integration_router.py → AIDebateEngine 임포트
3. backend/ai/reporters/report_orchestrator.py → debate 에이전트 임포트
4. backend/orchestration/data_accumulation_orchestrator.py → debate 에이전트 임포트
5. backend/tests/ → 테스트 파일들
```

---

### 2. Deprecated Reporters

#### 위치
- `backend/ai/reporters/deprecated/` - **0개 파일** (디렉토리만 존재)

**상태**: 이미 정리됨 ✅

---

### 3. Old Main API File

#### 위치
- `backend/api/main.py`

#### 상태
확인 필요 - `backend/main.py`와 중복 여부 확인

---

## 영향 분석

### 현재 상황

| 컴포넌트 | 상태 | 프로덕션 사용 | 제거 가능 |
|---------|------|-------------|----------|
| **War Room MVP** | ✅ 프로덕션 | YES | NO |
| **War Room Legacy** | ⚠️ 레거시 | YES (등록됨) | 조건부 |
| **Phase Integration** | ⚠️ 레거시 | YES (등록됨) | 조건부 |
| **Debate Agents** | ⚠️ 레거시 | 간접적 (위 2개 통해) | 조건부 |
| **Legacy/Debate** | ⚠️ 중복 | NO | YES |

### 리스크 평가

#### HIGH Risk (즉시 제거 불가)
- `backend/ai/debate/` - `war_room_router.py`, `phase_integration_router.py`에서 사용 중

#### MEDIUM Risk (조건부 제거)
- `backend/api/war_room_router.py` - 등록되어 있지만 MVP로 대체 가능
- `backend/api/phase_integration_router.py` - Phase A/B/C 통합 API (사용 여부 확인 필요)

#### LOW Risk (즉시 제거 가능)
- `backend/ai/legacy/debate/` - 완전 중복 백업 (어디서도 임포트 안 됨)
- `backend/ai/reporters/deprecated/` - 빈 디렉토리

---

## 정리 계획

### Phase 1: 안전한 제거 (LOW Risk)

#### 1.1 Legacy Debate 중복 제거
```bash
# 완전 중복 - 즉시 제거 가능
rm -rf backend/ai/legacy/debate/
```

**이유**: `backend/ai/legacy/debate/`는 어떤 파일에서도 임포트되지 않음 (Grep 결과 0건)

#### 1.2 빈 디렉토리 제거
```bash
# 빈 디렉토리 - 즉시 제거 가능
rm -rf backend/ai/reporters/deprecated/
```

**예상 효과**:
- 코드베이스 -28개 파일
- 유지보수 부담 감소

---

### Phase 2: 라우터 마이그레이션 (MEDIUM Risk)

#### 2.1 War Room Router 사용 현황 조사

**확인 사항**:
1. 프론트엔드에서 `/api/war-room/` 엔드포인트 사용 여부
2. 외부 클라이언트/스크립트에서 호출 여부
3. 텔레그램 봇에서 사용 여부

**조사 방법**:
```bash
# 프론트엔드 검색
grep -r "war-room" frontend/src/

# 로그 분석 (최근 30일)
# - war_room_router 호출 로그 확인
# - war_room_mvp_router 호출 로그 비교
```

#### 2.2 Phase Integration Router 사용 현황 조사

**확인 사항**:
1. `/phase` 엔드포인트 호출 빈도
2. Phase A/B/C 모듈 실제 사용 여부
3. 대체 가능 여부

#### 2.3 마이그레이션 전략

**Option A: Deprecation Warning (권장)**
```python
# backend/api/war_room_router.py 상단에 추가

import warnings

warnings.warn(
    "War Room Legacy API is deprecated. "
    "Please migrate to War Room MVP API (/api/war-room-mvp/). "
    "This endpoint will be removed in v3.0.0",
    DeprecationWarning,
    stacklevel=2
)
```

**Option B: Redirect to MVP**
```python
# Legacy 엔드포인트를 MVP로 리다이렉트
@router.post("/api/war-room/debate")
async def debate_redirect(...):
    # MVP로 요청 포워딩
    return await war_room_mvp_debate(...)
```

**Option C: 완전 제거**
- 사용 빈도가 0이면 즉시 제거
- 아니면 Option A → 1개월 대기 → 제거

---

### Phase 3: Debate Agents 제거 (HIGH Risk)

#### 3.1 조건부 제거 (Phase 2 완료 후)

**전제조건**:
- ✅ War Room Legacy Router 제거 완료
- ✅ Phase Integration Router 제거 또는 MVP로 마이그레이션 완료

**실행**:
```bash
# 모든 의존성 제거 후
rm -rf backend/ai/debate/
```

#### 3.2 아카이빙 (제거 전)

**백업 위치**: `backend/ai/archived/debate_legacy_20260125/`

```bash
# 아카이브 디렉토리 생성
mkdir -p backend/ai/archived/debate_legacy_20260125/

# 백업
cp -r backend/ai/debate/ backend/ai/archived/debate_legacy_20260125/

# README 추가
cat > backend/ai/archived/debate_legacy_20260125/README.md <<EOF
# Legacy Debate System Archive

**아카이브 날짜**: 2026-01-25
**이유**: War Room MVP (3+1 Agent)로 대체됨

## 원본 위치
- backend/ai/debate/

## 대체 시스템
- backend/ai/mvp/war_room_mvp.py (프로덕션)
- backend/routers/war_room_mvp_router.py (API)

## 에이전트 비교

### Legacy (8 Agents)
- News Agent (14%)
- Trader Agent (16%)
- Risk Agent (16%)
- Analyst Agent (12%)
- Macro Agent (14%)
- Institutional Agent (14%)
- Chip War Agent (14%)
- PM Agent (중재자)

### MVP (3+1 Agents)
- Trader Agent MVP (35%)
- Risk Agent MVP (30%)
- Analyst Agent MVP (35%)
- PM Agent MVP (최종 결정권자)

## 복원 방법
필요 시 이 디렉토리를 backend/ai/debate/로 복사
EOF
```

---

## 실행 순서

### Week 1: 조사 및 안전한 제거

#### Day 1: 사용 현황 조사
```bash
# 1. 프론트엔드 검색
grep -r "war-room" frontend/src/ > war_room_usage.txt
grep -r "/phase" frontend/src/ > phase_usage.txt

# 2. 로그 분석 (수동)
# - 최근 30일 API 호출 로그 확인
# - war_room_router vs war_room_mvp_router 비교

# 3. 텔레그램 봇 확인
grep -r "war_room" backend/services/telegram_service.py
```

#### Day 2-3: 안전한 제거 실행 (Phase 1)
```bash
# Legacy 중복 제거
git rm -rf backend/ai/legacy/debate/
git commit -m "chore: remove legacy debate duplicate backup"

# 빈 디렉토리 제거
git rm -rf backend/ai/reporters/deprecated/
git commit -m "chore: remove empty deprecated directory"

# Structure Map 업데이트
python backend/utils/structure_mapper.py
git add docs/architecture/structure-map.md
git commit -m "docs: update structure map after cleanup"
```

#### Day 4-5: Deprecation Warning 추가 (Phase 2 시작)
```python
# backend/api/war_room_router.py 수정
# - Deprecation Warning 추가
# - 로깅 강화 (호출 빈도 추적)

# backend/api/phase_integration_router.py 수정
# - 동일한 Deprecation Warning
```

---

### Week 2: 모니터링 및 마이그레이션

#### Day 6-10: 사용 패턴 모니터링
- Deprecation Warning 발생 횟수 추적
- 사용자 피드백 수집
- 대체 경로 안내

#### Day 11-12: 마이그레이션 가이드 작성
```markdown
# docs/guides/WAR_ROOM_MIGRATION_GUIDE.md

## Legacy → MVP 마이그레이션 가이드

### API 엔드포인트 변경
- AS-IS: POST /api/war-room/debate
- TO-BE: POST /api/war-room-mvp/debate

### 응답 형식 변경
- 8 에이전트 → 3+1 에이전트
- 가중치 조정 필요
```

#### Day 13-14: 마이그레이션 지원
- 사용자 질문 대응
- 버그 수정
- 문서 업데이트

---

### Week 3-4: 최종 제거 (Phase 3)

#### 전제조건 체크
- [ ] War Room Legacy 호출 로그 0건 (연속 7일)
- [ ] Phase Integration 호출 로그 0건 (연속 7일)
- [ ] 사용자 피드백 확인
- [ ] 백업 완료

#### 최종 제거 실행
```bash
# 1. 아카이빙
mkdir -p backend/ai/archived/debate_legacy_20260125/
cp -r backend/ai/debate/ backend/ai/archived/debate_legacy_20260125/
# (README 추가 - 위 참조)

# 2. 라우터 제거
git rm backend/api/war_room_router.py
git rm backend/api/phase_integration_router.py

# 3. main.py에서 등록 제거
# backend/main.py 수정:
# - war_room_router 임포트 제거
# - phase_router 임포트 제거
# - include_router() 호출 제거

# 4. Debate 에이전트 제거
git rm -rf backend/ai/debate/

# 5. 테스트 제거 (필요 시)
git rm backend/tests/test_chip_war_agent.py
git rm backend/tests/test_priority_calculator.py
git rm backend/tests/test_skeptic_live.py
git rm backend/tests/test_phase_e_integration.py

# 6. 커밋
git commit -m "refactor: remove legacy debate system (replaced by War Room MVP)"

# 7. Structure Map 업데이트
python backend/utils/structure_mapper.py
git add docs/architecture/structure-map.md
git commit -m "docs: update structure map after debate system removal"
```

---

## 백업 및 복구 계획

### 백업 전략

#### 1. Git 기반 백업 (권장)
```bash
# 제거 전 태그 생성
git tag -a legacy-debate-backup-20260125 -m "Backup before debate system removal"
git push origin legacy-debate-backup-20260125

# 복원 방법 (필요 시)
git checkout legacy-debate-backup-20260125 -- backend/ai/debate/
git checkout legacy-debate-backup-20260125 -- backend/api/war_room_router.py
```

#### 2. 파일 시스템 백업
```bash
# 백업 디렉토리 생성
mkdir -p backups/legacy_code_20260125/

# 백업 실행
cp -r backend/ai/debate/ backups/legacy_code_20260125/
cp -r backend/ai/legacy/ backups/legacy_code_20260125/
cp backend/api/war_room_router.py backups/legacy_code_20260125/
cp backend/api/phase_integration_router.py backups/legacy_code_20260125/

# 압축
tar -czf backups/legacy_code_20260125.tar.gz backups/legacy_code_20260125/
```

### 복구 계획

#### 시나리오 1: 즉시 복구 필요
```bash
# Git 태그에서 복원
git checkout legacy-debate-backup-20260125 -- backend/ai/debate/
git checkout legacy-debate-backup-20260125 -- backend/api/war_room_router.py

# main.py 수정 (라우터 재등록)
# 서버 재시작
```

#### 시나리오 2: 부분 복구 필요
```bash
# 특정 파일만 복원
git checkout legacy-debate-backup-20260125 -- backend/ai/debate/chip_war_agent.py
```

#### 시나리오 3: 아카이브에서 참조
```bash
# 코드 참조만 필요한 경우
ls backend/ai/archived/debate_legacy_20260125/
cat backend/ai/archived/debate_legacy_20260125/trader_agent.py
```

---

## 예상 효과

### 정량적 효과

| 항목 | Before | After | 감소량 |
|------|--------|-------|--------|
| **Python 파일** | ~300개 | ~272개 | -28개 |
| **AI Debate 코드** | 14개 | 0개 | -14개 |
| **Legacy 백업** | 14개 | 0개 | -14개 |
| **API 라우터** | 57개 | 55개 | -2개 |
| **유지보수 복잡도** | HIGH | MEDIUM | ↓ |

### 정성적 효과

✅ **코드 명확성 향상**
- War Room 시스템이 하나로 통일 (MVP만 존재)
- 개발자가 어떤 시스템을 사용해야 할지 명확함

✅ **유지보수 부담 감소**
- 2개 War Room 시스템 → 1개로 감소
- 중복 코드 제거 (legacy/debate/ 완전 제거)

✅ **테스트 부담 감소**
- 레거시 에이전트 테스트 불필요
- MVP 테스트에만 집중

✅ **문서 간소화**
- 레거시 시스템 설명 제거
- MVP 중심 문서화

⚠️ **주의사항**
- 기존 사용자 마이그레이션 필요
- Deprecation 기간 충분히 확보 (최소 2주)

---

## 체크리스트

### Phase 1: 안전한 제거
- [ ] `backend/ai/legacy/debate/` 제거
- [ ] `backend/ai/reporters/deprecated/` 제거
- [ ] Structure Map 업데이트
- [ ] 커밋 및 푸시

### Phase 2: 라우터 마이그레이션
- [ ] War Room Legacy 사용 현황 조사
- [ ] Phase Integration 사용 현황 조사
- [ ] Deprecation Warning 추가
- [ ] 마이그레이션 가이드 작성
- [ ] 사용 패턴 모니터링 (2주)

### Phase 3: 최종 제거
- [ ] 호출 로그 0건 확인 (7일 연속)
- [ ] 백업 실행 (Git 태그 + 아카이브)
- [ ] `backend/api/war_room_router.py` 제거
- [ ] `backend/api/phase_integration_router.py` 제거
- [ ] `backend/ai/debate/` 제거
- [ ] `backend/main.py` 라우터 등록 제거
- [ ] 테스트 파일 정리
- [ ] Structure Map 업데이트
- [ ] 문서 업데이트

---

## 참고 문서

- [SYSTEM_STATUS_MAP.md](SYSTEM_STATUS_MAP.md) - 전체 시스템 현황
- [War Room MVP](../backend/ai/mvp/war_room_mvp.py) - 프로덕션 시스템
- [War Room MVP Router](../backend/routers/war_room_mvp_router.py) - 프로덕션 API

---

**작성자**: AI Trading System Team
**최종 업데이트**: 2026-01-25
**다음 리뷰**: Phase 1 완료 후 (Week 1)
