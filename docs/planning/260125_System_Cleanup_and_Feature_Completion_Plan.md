# AI Trading System - 시스템 정리 및 기능 완성 계획

**작성일**: 2026-01-25
**기간**: 2026-01-27 ~ 2026-06-30 (6개월)
**목표**: 레거시 정리 + 부분 구현 기능 100% 완성

---

## 📋 Executive Summary

### 현재 상황
- ✅ **핵심 기능**: 100% 구현 완료 (War Room MVP, Briefing v2.3, Intelligence v2.0)
- ⚠️ **레거시 코드**: 15% 존재 (debate/, war_room_router 등)
- ⚠️ **부분 구현**: 3개 기능 (Persona 50%, WebSocket 70%, Risk 30%)
- ⚠️ **문서 과다**: 583개 → 200개 핵심 문서로 압축 필요

### 목표 (2026-06-30)
- ✅ 레거시 코드 100% 제거
- ✅ 문서 200개로 압축 (65% 감소)
- ✅ Persona-based Trading 100% 완성
- ✅ Real-time Execution 100% 완성
- ✅ Advanced Risk Models 100% 완성
- 🆕 Mobile App (PWA) 80% 완성

---

## 📅 전체 타임라인

```
Week 1-2  (2026-01-27 ~ 2026-02-09): 레거시 정리 Phase 2 (War Room 조사)
Week 3-4  (2026-02-10 ~ 2026-02-23): 레거시 정리 Phase 3 (Debate 제거)
Week 5-6  (2026-02-24 ~ 2026-03-09): 문서 압축 (583 → 200)
Week 7-12 (2026-03-10 ~ 2026-04-20): Persona-based Trading 완성
Week 13-18(2026-04-21 ~ 2026-06-01): Real-time Execution 완성
Week 19-22(2026-06-02 ~ 2026-06-29): Advanced Risk Models 완성
Week 23-26(2026-06-30 ~ 2026-07-27): Mobile App (PWA) MVP (보너스)
```

---

## 🎯 Phase 0: 사전 준비 (Week 0 - 이번 주)

### 작업 항목

#### T0.1 개발 환경 점검
```bash
# 시스템 체크
0_시스템_체크.bat

# DB 상태 확인
python backend/scripts/check_db_health.py

# Structure Map 최신화
python backend/utils/structure_mapper.py
```

#### T0.2 브랜치 전략 수립
```bash
# 메인 작업 브랜치 생성
git checkout -b feature/system-cleanup-2026

# 하위 브랜치 (필요 시)
# - feature/legacy-removal
# - feature/persona-trading
# - feature/realtime-execution
# - feature/advanced-risk
```

#### T0.3 백업 생성
```bash
# 현재 상태 태그
git tag -a backup-before-cleanup-20260125 -m "Backup before major cleanup"
git push origin backup-before-cleanup-20260125

# 전체 백업
tar -czf backups/full_backup_20260125.tar.gz backend/ frontend/ docs/
```

#### T0.4 체크리스트 확인
- [ ] 모든 테스트 통과 확인
- [ ] 프로덕션 배포 정상 확인
- [ ] 백업 완료
- [ ] 팀원/사용자 공지 (있다면)

---

## 🧹 Phase 1: 레거시 코드 정리 (Week 1-4)

### Week 1-2: War Room Legacy 조사 및 Deprecation

#### 목표
- War Room Legacy (`war_room_router.py`) 사용 현황 파악
- Phase Integration Router 사용 현황 파악
- Deprecation Warning 추가

#### 상세 작업

##### Day 1 (2026-01-27 월): 사용 현황 조사
```bash
# 1. 프론트엔드 검색
cd frontend
grep -r "war-room" src/ > ../analysis/frontend_war_room_usage.txt
grep -r "/phase" src/ > ../analysis/frontend_phase_usage.txt

# 2. 백엔드 검색
cd ../backend
grep -r "war_room_router" . > ../analysis/backend_war_room_refs.txt
grep -r "phase_integration_router" . > ../analysis/backend_phase_refs.txt

# 3. 로그 분석 스크립트 작성
cat > scripts/analyze_api_usage.py <<'EOF'
"""
Analyze API usage from logs

Parse logs to find:
- /api/war-room/* call count
- /api/war-room-mvp/* call count
- /phase/* call count

Time range: Last 30 days
"""

import re
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_logs(log_file_path: str):
    war_room_legacy = defaultdict(int)
    war_room_mvp = defaultdict(int)
    phase_integration = defaultdict(int)

    with open(log_file_path, 'r') as f:
        for line in f:
            if '/api/war-room/' in line and '/api/war-room-mvp/' not in line:
                # Legacy War Room
                date = extract_date(line)
                war_room_legacy[date] += 1
            elif '/api/war-room-mvp/' in line:
                # MVP War Room
                date = extract_date(line)
                war_room_mvp[date] += 1
            elif '/phase/' in line:
                # Phase Integration
                date = extract_date(line)
                phase_integration[date] += 1

    return {
        'war_room_legacy': dict(war_room_legacy),
        'war_room_mvp': dict(war_room_mvp),
        'phase_integration': dict(phase_integration)
    }

def extract_date(log_line: str) -> str:
    # Extract date from log line
    # Format: YYYY-MM-DD
    match = re.search(r'\d{4}-\d{2}-\d{2}', log_line)
    return match.group(0) if match else 'unknown'

if __name__ == '__main__':
    import sys
    log_file = sys.argv[1] if len(sys.argv) > 1 else 'logs/app.log'
    results = analyze_logs(log_file)

    print("=== API Usage Analysis ===")
    print(f"\nWar Room Legacy: {sum(results['war_room_legacy'].values())} calls")
    print(f"War Room MVP: {sum(results['war_room_mvp'].values())} calls")
    print(f"Phase Integration: {sum(results['phase_integration'].values())} calls")
EOF
```

##### Day 2 (2026-01-28 화): 분석 결과 정리
```bash
# 로그 분석 실행
python scripts/analyze_api_usage.py logs/app.log > analysis/api_usage_report.txt

# 결과 정리 문서 작성
cat > docs/analysis/260128_API_Usage_Analysis.md <<'EOF'
# API Usage Analysis Report

**Date**: 2026-01-28
**Period**: Last 30 days

## Results

### War Room Legacy (/api/war-room/*)
- Total calls: [TO BE FILLED]
- Daily average: [TO BE FILLED]
- Peak usage: [TO BE FILLED]

### War Room MVP (/api/war-room-mvp/*)
- Total calls: [TO BE FILLED]
- Daily average: [TO BE FILLED]
- Peak usage: [TO BE FILLED]

### Phase Integration (/phase/*)
- Total calls: [TO BE FILLED]
- Daily average: [TO BE FILLED]
- Peak usage: [TO BE FILLED]

## Recommendation

### If Legacy calls > 0:
- Add Deprecation Warning
- Monitor for 2 weeks
- Migrate users to MVP

### If Legacy calls == 0:
- Safe to remove immediately
- Proceed to Phase 3
EOF
```

##### Day 3-4 (2026-01-29 수 ~ 2026-01-30 목): Deprecation Warning 추가
```python
# backend/api/war_room_router.py 수정

import warnings
from datetime import datetime

# 파일 상단에 추가
DEPRECATION_MESSAGE = """
⚠️ DEPRECATION WARNING ⚠️

This War Room Legacy API is deprecated and will be removed on 2026-02-28.

Please migrate to War Room MVP API:
- Old: POST /api/war-room/debate
- New: POST /api/war-room-mvp/debate

Migration Guide: docs/guides/WAR_ROOM_MIGRATION_GUIDE.md

For questions, contact: [your-email]
"""

logger.warning(DEPRECATION_MESSAGE)

# 각 엔드포인트에 로깅 추가
@router.post("/debate")
async def debate_endpoint(...):
    logger.warning(
        f"[DEPRECATED] War Room Legacy called at {datetime.now()} - "
        f"Please migrate to /api/war-room-mvp/debate"
    )

    # 기존 로직...
```

##### Day 5 (2026-01-31 금): Migration Guide 작성
```markdown
# docs/guides/WAR_ROOM_MIGRATION_GUIDE.md

# War Room Migration Guide: Legacy → MVP

**Last Update**: 2026-01-31
**Deadline**: 2026-02-28

## Why Migrate?

War Room MVP offers:
- ✅ Faster response (Two-Stage architecture)
- ✅ Lower cost (GLM-4.7 vs multiple models)
- ✅ Better accuracy (3+1 agent vs 8 agent)
- ✅ Active maintenance (Legacy is frozen)

## API Changes

### Endpoint
- AS-IS: `POST /api/war-room/debate`
- TO-BE: `POST /api/war-room-mvp/debate`

### Request Schema
[TO BE FILLED - 실제 스키마 비교]

### Response Schema
[TO BE FILLED - 실제 응답 비교]

## Migration Steps

### Step 1: Update Frontend
```tsx
// Before
const response = await fetch('/api/war-room/debate', {
  method: 'POST',
  body: JSON.stringify(data)
});

// After
const response = await fetch('/api/war-room-mvp/debate', {
  method: 'POST',
  body: JSON.stringify(data)
});
```

### Step 2: Update Scripts
[TO BE FILLED]

### Step 3: Test
[TO BE FILLED]
```

##### Week 2 (2026-02-03 ~ 2026-02-09): 모니터링 및 사용자 지원
- Deprecation Warning 발생 횟수 추적
- 사용자 문의 대응
- Migration Guide 개선

---

### Week 3-4: 레거시 제거 (Phase 3)

#### 전제조건 체크
```bash
# 체크리스트
- [ ] War Room Legacy 호출 0건 (연속 7일)
- [ ] Phase Integration 호출 0건 (연속 7일)
- [ ] Migration 완료 확인
- [ ] 백업 완료
```

#### Day 15-16 (2026-02-10 ~ 2026-02-11): 아카이빙
```bash
# 1. 아카이브 디렉토리 생성
mkdir -p backend/ai/archived/debate_legacy_20260210/

# 2. 백업
cp -r backend/ai/debate/ backend/ai/archived/debate_legacy_20260210/

# 3. README 작성
cat > backend/ai/archived/debate_legacy_20260210/README.md <<'EOF'
# Legacy Debate System Archive

**Archive Date**: 2026-02-10
**Reason**: Replaced by War Room MVP (3+1 Agent)

## Original Location
- backend/ai/debate/

## Replacement System
- backend/ai/mvp/war_room_mvp.py (Production)
- backend/routers/war_room_mvp_router.py (API)

## Agent Comparison

### Legacy (8 Agents)
- News Agent (14%)
- Trader Agent (16%)
- Risk Agent (16%)
- Analyst Agent (12%)
- Macro Agent (14%)
- Institutional Agent (14%)
- Chip War Agent (14%)
- PM Agent (Mediator)

### MVP (3+1 Agents)
- Trader Agent MVP (35%)
- Risk Agent MVP (30%)
- Analyst Agent MVP (35%)
- PM Agent MVP (Final Decision Maker)

## Performance Comparison

| Metric | Legacy | MVP |
|--------|--------|-----|
| Response Time | 30-45s | 15-20s |
| Cost per Call | $0.15 | $0.05 |
| Accuracy | 65% | 78% |

## Restore Instructions

If needed, copy this directory back to `backend/ai/debate/`

DO NOT restore without team approval.
EOF

# 4. Git 태그
git tag -a debate-legacy-archived-20260210 -m "Archive debate system before removal"
git push origin debate-legacy-archived-20260210
```

#### Day 17 (2026-02-12 수): 라우터 제거
```bash
# 1. War Room Legacy Router 제거
git rm backend/api/war_room_router.py

# 2. Phase Integration Router 제거
git rm backend/api/phase_integration_router.py

# 3. main.py 수정
# - war_room_router 임포트 제거
# - phase_router 임포트 제거
# - include_router() 호출 제거

# 커밋
git add backend/main.py
git commit -m "refactor: remove war room legacy and phase integration routers

- Remove backend/api/war_room_router.py
- Remove backend/api/phase_integration_router.py
- Update main.py router registration
- Archived in backend/ai/archived/debate_legacy_20260210/

BREAKING CHANGE: /api/war-room/* and /phase/* endpoints removed
Use /api/war-room-mvp/* instead

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### Day 18 (2026-02-13 목): Debate 에이전트 제거
```bash
# 1. Debate 디렉토리 제거
git rm -rf backend/ai/debate/

# 2. 테스트 제거 (debate 관련)
git rm backend/tests/test_chip_war_agent.py
git rm backend/tests/test_priority_calculator.py
git rm backend/tests/test_skeptic_live.py
git rm backend/tests/test_phase_e_integration.py

# 3. 기타 참조 정리
# backend/ai/reporters/report_orchestrator.py
# backend/orchestration/data_accumulation_orchestrator.py
# - debate 임포트 제거
# - MVP로 대체

# 커밋
git commit -m "refactor: remove legacy debate system

- Remove backend/ai/debate/ (14 files)
- Remove debate-related tests (4 files)
- Update report_orchestrator.py to use MVP
- Update data_accumulation_orchestrator.py to use MVP

Total removed: ~6,000 lines

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### Day 19-20 (2026-02-14 금 ~ 2026-02-15 토): 검증 및 테스트
```bash
# 1. Structure Map 업데이트
python backend/utils/structure_mapper.py

# 2. 전체 테스트 실행
npm run test:backend

# 3. 시스템 체크
0_시스템_체크.bat

# 4. 프로덕션 배포 테스트
# - 로컬에서 전체 기능 테스트
# - War Room MVP 정상 작동 확인
# - 브레이킹 체인지 없는지 확인

# 5. 문서 업데이트
# - SYSTEM_STATUS_MAP.md 업데이트
# - LEGACY_CLEANUP_PLAN.md 완료 체크
# - CHANGELOG.md 업데이트
```

---

## 📚 Phase 2: 문서 압축 (Week 5-6)

### 목표
- 583개 문서 → 200개 핵심 문서
- 레거시/중복 문서 아카이빙
- 문서 구조 재편

### Week 5: 분석 및 분류 (2026-02-24 ~ 2026-03-02)

#### Day 21 (2026-02-24 월): 문서 분류 스크립트 작성
```python
# scripts/classify_docs.py

"""
Document Classification Script

Classify all 583 docs into:
1. KEEP (핵심 문서, 200개 목표)
2. ARCHIVE (과거 기록, 보관)
3. DELETE (중복/쓸모없음, 삭제)

Criteria:
- KEEP: 최신, 참조 많음, 프로덕션 관련
- ARCHIVE: 완료된 Phase, 과거 토론
- DELETE: 중복, 오래됨 (6개월+), 참조 없음
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import re
from collections import defaultdict

def classify_document(file_path: Path) -> str:
    """Classify a single document"""

    # 1. Check file age
    stat = file_path.stat()
    age_days = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days

    # 2. Check references
    refs = count_references(file_path)

    # 3. Check directory
    if 'legacy' in str(file_path) or 'archive' in str(file_path):
        return 'ARCHIVE'

    if 'deleted' in str(file_path):
        return 'DELETE'

    # 4. Check date in filename
    filename = file_path.name
    date_match = re.search(r'(\d{6})_', filename)
    if date_match:
        file_date = datetime.strptime(date_match.group(1), '%y%m%d')
        if (datetime.now() - file_date).days > 180:  # 6개월 이상
            return 'ARCHIVE'

    # 5. Check importance
    if refs >= 5:
        return 'KEEP'

    if age_days > 90 and refs == 0:
        return 'DELETE'

    # Default
    return 'ARCHIVE' if age_days > 60 else 'KEEP'

def count_references(file_path: Path) -> int:
    """Count how many times this file is referenced"""
    # Search in all Python/TypeScript files
    # Return reference count
    pass

if __name__ == '__main__':
    docs_dir = Path('docs')
    classifications = defaultdict(list)

    for md_file in docs_dir.rglob('*.md'):
        category = classify_document(md_file)
        classifications[category].append(md_file)

    print(f"KEEP: {len(classifications['KEEP'])}")
    print(f"ARCHIVE: {len(classifications['ARCHIVE'])}")
    print(f"DELETE: {len(classifications['DELETE'])}")

    # Save results
    with open('analysis/doc_classification.json', 'w') as f:
        import json
        json.dump({
            'KEEP': [str(p) for p in classifications['KEEP']],
            'ARCHIVE': [str(p) for p in classifications['ARCHIVE']],
            'DELETE': [str(p) for p in classifications['DELETE']]
        }, f, indent=2)
```

#### Day 22-24 (2026-02-25 화 ~ 2026-02-27 목): 수동 검토
```bash
# 1. 분류 결과 확인
python scripts/classify_docs.py
cat analysis/doc_classification.json

# 2. 수동 검토 (중요!)
# - KEEP 목록 확인 (200개 이하로 조정)
# - ARCHIVE 목록 확인 (레거시만 포함)
# - DELETE 목록 확인 (복구 불가능)

# 3. 조정된 분류 저장
cp analysis/doc_classification.json analysis/doc_classification_final.json
# (수동으로 조정)
```

#### Day 25 (2026-02-28 금): 핵심 문서 선정
```markdown
# docs/analysis/260228_Core_Documentation_List.md

# Core Documentation (200 Files)

## 00. Root Level (10 files)
1. README.md - Main entry
2. CLAUDE.md - AI development guide
3. QUICK_START.md - Quick start
4. SYSTEM_STATUS_MAP.md - System overview
5. LEGACY_CLEANUP_PLAN.md - Cleanup plan
6. PARTIAL_IMPLEMENTATION_REVIEW.md - Feature review
7. PROJECT_OVERVIEW.md - Project overview
8. RETROSPECTIVE.md - Retrospective
9. IMPLEMENTATION_SUMMARY.md - Implementation summary
10. Live_Trading.md - Live trading guide

## 01. Architecture (5 files)
1. docs/architecture/ARCHITECTURE.md
2. docs/architecture/SYSTEM_ARCHITECTURE.md
3. docs/architecture/SYSTEM_ARCHITECTURE_FULL.md
4. docs/architecture/structure-map.md (auto-generated)
5. docs/architecture/260104_Complete_Development_History_and_Structure.md

## 02. Planning (20 files)
Active plans only:
1. 01-multi-strategy-orchestration-plan.md
2. 02-multi-strategy-orchestration-tasks.md
3. 260118_market_intelligence_roadmap.md
4. 260124_Daily_Briefing_v2.3_Protocol_Implementation_Plan.md
5. 12-db-modernization-plan.md
... (15 more core plans)

[CONTINUE FOR ALL 200 FILES]
```

### Week 6: 실행 (2026-03-03 ~ 2026-03-09)

#### Day 26-27 (2026-03-03 월 ~ 2026-03-04 화): 아카이브 이동
```bash
# 1. ARCHIVE 문서 이동
mkdir -p docs/archive/2026_Q1_cleanup/

# 스크립트 실행
python scripts/archive_docs.py

# scripts/archive_docs.py 내용:
import json
import shutil
from pathlib import Path

with open('analysis/doc_classification_final.json') as f:
    classification = json.load(f)

archive_dir = Path('docs/archive/2026_Q1_cleanup')
archive_dir.mkdir(parents=True, exist_ok=True)

for doc_path in classification['ARCHIVE']:
    src = Path(doc_path)
    # Preserve directory structure
    rel_path = src.relative_to('docs')
    dst = archive_dir / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(src, dst)

print(f"Archived {len(classification['ARCHIVE'])} documents")
```

#### Day 28 (2026-03-05 수): 불필요 문서 삭제
```bash
# DELETE 문서 삭제
python scripts/delete_docs.py

# 확인 후 커밋
git add .
git commit -m "docs: archive old documentation and remove duplicates

- Archive 350+ legacy documents to docs/archive/2026_Q1_cleanup/
- Delete 33 duplicate/obsolete documents
- Retain 200 core documents
- Total reduction: 583 → 200 files (65% reduction)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### Day 29-30 (2026-03-06 목 ~ 2026-03-07 금): 문서 재구조화
```bash
# 핵심 문서 재구조화
docs/
├── README.md (메인 인덱스)
├── QUICK_START.md
├── CLAUDE.md
├── SYSTEM_STATUS_MAP.md
├── 00_Core/ (핵심 스펙 20개)
├── 01_Architecture/ (5개)
├── 02_Planning/ (액티브 계획 20개)
├── 03_Guides/ (실용 가이드 30개)
├── 04_API/ (API 문서 20개)
├── 05_Features/ (기능별 15개)
├── archive/ (350+ 아카이브)
└── templates/ (문서 템플릿 10개)

# README 업데이트
cat > docs/README.md <<'EOF'
# AI Trading System Documentation

**Last Update**: 2026-03-07
**Total Documents**: 200 core + 350+ archived

## Quick Links
- [Quick Start](QUICK_START.md)
- [System Overview](SYSTEM_STATUS_MAP.md)
- [Architecture](01_Architecture/SYSTEM_ARCHITECTURE.md)
- [Planning](02_Planning/)
- [Guides](03_Guides/)

## Document Structure
...
EOF
```

---

## 🎨 Phase 3: Persona-based Trading 완성 (Week 7-12)

### Week 7-8: Daily Briefing 페르소나 분리

#### Day 35-37 (2026-03-10 ~ 2026-03-12): DailyBriefingService 수정
```python
# backend/services/daily_briefing_service.py 확장

class PersonaBriefingService:
    """Persona-specific briefing generation"""

    PERSONA_CONFIGS = {
        'trading': {
            'time_horizon': '1-5 days',
            'focus': ['technical_analysis', 'short_term_catalysts', 'intraday_signals'],
            'style': 'concise_actionable',
            'sections': ['market_pulse', 'key_movers', 'quick_actions'],
        },
        'long_term': {
            'time_horizon': '6-18 months',
            'focus': ['fundamentals', 'themes', 'macro_trends'],
            'style': 'analytical_educational',
            'sections': ['market_narrative', 'deep_dive', 'strategic_positioning'],
        },
        'dividend': {
            'time_horizon': '1+ years',
            'focus': ['dividend_safety', 'valuation', 'income_stability'],
            'style': 'conservative_detailed',
            'sections': ['income_highlights', 'safety_check', 'value_opportunities'],
        },
        'aggressive': {
            'time_horizon': '1 day',
            'focus': ['volatility', 'momentum', 'breakouts'],
            'style': 'fast_numerical',
            'sections': ['hot_stocks', 'volatility_plays', 'instant_alerts'],
        }
    }

    async def generate_persona_briefing(
        self,
        persona: str = 'trading',
        mode: str = 'CLOSING'  # CLOSING or MORNING
    ) -> Dict:
        """Generate persona-specific briefing"""

        config = self.PERSONA_CONFIGS[persona]

        # 1. Fetch data filtered by persona focus
        data = await self._fetch_persona_data(config['focus'])

        # 2. Build persona-specific prompt
        prompt = self._build_persona_prompt(persona, mode, data, config)

        # 3. Generate with appropriate style
        briefing = await self._generate_with_style(prompt, config['style'])

        # 4. Structure by persona sections
        structured = self._structure_output(briefing, config['sections'])

        return {
            'persona': persona,
            'mode': mode,
            'time_horizon': config['time_horizon'],
            'briefing': structured,
            'generated_at': datetime.now().isoformat()
        }

    def _build_persona_prompt(
        self,
        persona: str,
        mode: str,
        data: Dict,
        config: Dict
    ) -> str:
        """Build persona-specific prompt"""

        if persona == 'trading':
            return f"""
You are a short-term trader (1-5 day horizon).

Mode: {mode}
Focus: {', '.join(config['focus'])}

Market Data:
{data}

Generate a concise, actionable briefing with:
1. Market Pulse (30초 요약)
2. Key Movers (상위 3개)
3. Quick Actions (즉시 실행 가능한 트레이드 아이디어)

Style: Direct, numerical, action-oriented
"""
        elif persona == 'long_term':
            return f"""
You are a long-term investor (6-18 month horizon).

Mode: {mode}
Focus: {', '.join(config['focus'])}

Market Data:
{data}

Generate an analytical briefing with:
1. Market Narrative (전체 스토리)
2. Deep Dive (주요 테마 3개 심층 분석)
3. Strategic Positioning (포트폴리오 조정 제안)

Style: Analytical, educational, big-picture
"""
        # ... (dividend, aggressive 추가)
```

#### Day 38-40 (2026-03-13 ~ 2026-03-15): API 엔드포인트 추가
```python
# backend/api/briefing_router.py 확장

@router.get("/api/briefing/persona/{persona}")
async def get_persona_briefing(
    persona: str,
    mode: str = Query('CLOSING', regex='^(CLOSING|MORNING)$'),
    db: Session = Depends(get_sync_session)
):
    """
    Get persona-specific briefing

    Personas:
    - trading: 1-5 day horizon, technical focus
    - long_term: 6-18 month horizon, fundamental focus
    - dividend: 1+ year horizon, income focus
    - aggressive: 1 day horizon, volatility focus
    """

    if persona not in ['trading', 'long_term', 'dividend', 'aggressive']:
        raise HTTPException(400, f"Invalid persona: {persona}")

    service = PersonaBriefingService()
    briefing = await service.generate_persona_briefing(persona, mode)

    # Cache for 1 hour
    cache_key = f"persona_briefing:{persona}:{mode}"
    await cache.set(cache_key, briefing, ex=3600)

    return briefing

@router.get("/api/briefing/all-personas")
async def get_all_persona_briefings(
    mode: str = Query('CLOSING')
):
    """Get briefings for all personas"""

    personas = ['trading', 'long_term', 'dividend', 'aggressive']
    service = PersonaBriefingService()

    results = {}
    for persona in personas:
        results[persona] = await service.generate_persona_briefing(persona, mode)

    return results
```

### Week 9-10: UI 통합

#### Day 45-47 (2026-03-17 ~ 2026-03-19): Persona Selector 컴포넌트
```tsx
// frontend/src/components/PersonaSelector.tsx

import { Select, Tag } from 'antd';
import { UserOutlined, RiseOutlined, DollarOutlined, ThunderboltOutlined } from '@ant-design/icons';

const PERSONAS = [
  {
    key: 'trading',
    label: 'Trading',
    icon: <RiseOutlined />,
    color: 'blue',
    description: '단기 (1-5일)',
    horizon: '1-5 days'
  },
  {
    key: 'long_term',
    label: 'Long-term',
    icon: <UserOutlined />,
    color: 'green',
    description: '장기 (6-18개월)',
    horizon: '6-18 months'
  },
  {
    key: 'dividend',
    label: 'Dividend',
    icon: <DollarOutlined />,
    color: 'gold',
    description: '배당 (1년+)',
    horizon: '1+ year'
  },
  {
    key: 'aggressive',
    label: 'Aggressive',
    icon: <ThunderboltOutlined />,
    color: 'red',
    description: '초단기 (1일)',
    horizon: '1 day'
  }
];

export const PersonaSelector: React.FC<{
  value?: string;
  onChange?: (value: string) => void;
}> = ({ value = 'trading', onChange }) => {
  return (
    <Select
      value={value}
      onChange={onChange}
      style={{ width: 200 }}
      size="large"
    >
      {PERSONAS.map(persona => (
        <Select.Option key={persona.key} value={persona.key}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {persona.icon}
            <span>{persona.label}</span>
            <Tag color={persona.color} style={{ marginLeft: 'auto' }}>
              {persona.description}
            </Tag>
          </div>
        </Select.Option>
      ))}
    </Select>
  );
};

// 사용 예시
export const DashboardHeader: React.FC = () => {
  const [activePersona, setActivePersona] = useState('trading');

  return (
    <div className="dashboard-header">
      <h1>AI Trading Dashboard</h1>
      <PersonaSelector value={activePersona} onChange={setActivePersona} />
    </div>
  );
};
```

#### Day 48-50 (2026-03-20 ~ 2026-03-22): 페르소나별 대시보드 레이아웃
```tsx
// frontend/src/pages/PersonaDashboard.tsx

import { useQuery } from '@tanstack/react-query';
import { PersonaSelector } from '@/components/PersonaSelector';
import { TradingDashboard } from './personas/TradingDashboard';
import { LongTermDashboard } from './personas/LongTermDashboard';
import { DividendDashboard } from './personas/DividendDashboard';
import { AggressiveDashboard } from './personas/AggressiveDashboard';

export const PersonaDashboard: React.FC = () => {
  const [activePersona, setActivePersona] = useState('trading');

  // Fetch persona-specific briefing
  const { data: briefing, isLoading } = useQuery(
    ['briefing', activePersona, 'CLOSING'],
    () => fetchPersonaBriefing(activePersona, 'CLOSING'),
    {
      refetchInterval: 60000, // 1분마다 갱신
      staleTime: 30000 // 30초 캐시
    }
  );

  // Render persona-specific layout
  const renderDashboard = () => {
    switch (activePersona) {
      case 'trading':
        return <TradingDashboard briefing={briefing} />;
      case 'long_term':
        return <LongTermDashboard briefing={briefing} />;
      case 'dividend':
        return <DividendDashboard briefing={briefing} />;
      case 'aggressive':
        return <AggressiveDashboard briefing={briefing} />;
      default:
        return <TradingDashboard briefing={briefing} />;
    }
  };

  return (
    <div className="persona-dashboard">
      <PersonaSelector value={activePersona} onChange={setActivePersona} />
      {isLoading ? <Spin size="large" /> : renderDashboard()}
    </div>
  );
};
```

### Week 11-12: 리포트별 페르소나 적용

#### Day 55-60 (2026-03-24 ~ 2026-03-29): Weekly/Monthly Report 페르소나 확장
```python
# backend/services/weekly_report_generator.py 확장

class PersonaWeeklyReportGenerator:
    """Generate persona-specific weekly reports"""

    async def generate_persona_report(
        self,
        persona: str,
        week_start: datetime
    ) -> Dict:
        """Generate weekly report for specific persona"""

        # Fetch week's data
        data = await self._fetch_week_data(week_start)

        if persona == 'trading':
            # 단기: 일별 주요 이벤트, 승률 통계, 빠른 학습 포인트
            return await self._generate_trading_weekly(data)

        elif persona == 'long_term':
            # 장기: 테마 진행 상황, 펀더멘털 변화, 포지션 조정 제안
            return await self._generate_long_term_weekly(data)

        elif persona == 'dividend':
            # 배당: 배당 발표, 배당 귀족주 변동, 수익률 분석
            return await self._generate_dividend_weekly(data)

        elif persona == 'aggressive':
            # 초단기: 변동성 분석, 최고/최저 수익 거래, 위험 경고
            return await self._generate_aggressive_weekly(data)
```

---

## ⚡ Phase 4: Real-time Execution 완성 (Week 13-18)

### Week 13-15: 실시간 시장 데이터 WebSocket

#### Day 65-70 (2026-04-21 ~ 2026-04-26): Market Data WebSocket Manager
```python
# backend/api/market_data_ws.py (신규)

from fastapi import WebSocket, WebSocketDisconnect
from typing import Set, List, Dict
import asyncio
import yfinance as yf
from datetime import datetime

class MarketDataWebSocketManager:
    """Real-time market data streaming via WebSocket"""

    def __init__(self):
        self.active_connections: Dict[WebSocket, Set[str]] = {}
        self.quote_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[websocket] = set()
        logger.info(f"[MarketDataWS] New connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            symbols = self.active_connections[websocket]
            del self.active_connections[websocket]

            # Stop quote tasks if no more subscribers
            for symbol in symbols:
                if not self._has_subscribers(symbol):
                    self._stop_quote_task(symbol)

        logger.info(f"[MarketDataWS] Connection closed. Total: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, symbols: List[str]):
        """Subscribe to symbols"""
        if websocket not in self.active_connections:
            return

        for symbol in symbols:
            self.active_connections[websocket].add(symbol)

            # Start quote task if not running
            if symbol not in self.quote_tasks:
                self.quote_tasks[symbol] = asyncio.create_task(
                    self._stream_quotes(symbol)
                )

    async def unsubscribe(self, websocket: WebSocket, symbols: List[str]):
        """Unsubscribe from symbols"""
        if websocket not in self.active_connections:
            return

        for symbol in symbols:
            self.active_connections[websocket].discard(symbol)

            # Stop quote task if no more subscribers
            if not self._has_subscribers(symbol):
                self._stop_quote_task(symbol)

    async def _stream_quotes(self, symbol: str):
        """Stream real-time quotes for a symbol"""
        try:
            while True:
                # Fetch latest quote
                ticker = yf.Ticker(symbol)
                info = ticker.info

                quote = {
                    'symbol': symbol,
                    'price': info.get('currentPrice'),
                    'change': info.get('regularMarketChangePercent'),
                    'volume': info.get('volume'),
                    'timestamp': datetime.now().isoformat()
                }

                # Broadcast to subscribers
                await self._broadcast_to_subscribers(symbol, {
                    'type': 'quote',
                    'data': quote
                })

                # Wait 5 seconds (adjust based on API limits)
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info(f"[MarketDataWS] Quote stream stopped for {symbol}")
        except Exception as e:
            logger.error(f"[MarketDataWS] Error streaming {symbol}: {e}")

    async def _broadcast_to_subscribers(self, symbol: str, message: Dict):
        """Broadcast message to all subscribers of a symbol"""
        disconnected = []

        for websocket, symbols in self.active_connections.items():
            if symbol in symbols:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"[MarketDataWS] Broadcast error: {e}")
                    disconnected.append(websocket)

        # Remove disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

    def _has_subscribers(self, symbol: str) -> bool:
        """Check if symbol has any subscribers"""
        for symbols in self.active_connections.values():
            if symbol in symbols:
                return True
        return False

    def _stop_quote_task(self, symbol: str):
        """Stop quote streaming task"""
        if symbol in self.quote_tasks:
            self.quote_tasks[symbol].cancel()
            del self.quote_tasks[symbol]

# Global instance
market_data_ws_manager = MarketDataWebSocketManager()

# FastAPI endpoint
@router.websocket("/api/market-data/ws")
async def market_data_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time market data"""
    await market_data_ws_manager.connect(websocket)

    try:
        while True:
            # Receive client messages
            message = await websocket.receive_json()

            if message['type'] == 'subscribe':
                await market_data_ws_manager.subscribe(
                    websocket,
                    message['symbols']
                )
            elif message['type'] == 'unsubscribe':
                await market_data_ws_manager.unsubscribe(
                    websocket,
                    message['symbols']
                )

    except WebSocketDisconnect:
        market_data_ws_manager.disconnect(websocket)
```

#### Day 71-75 (2026-04-27 ~ 2026-05-01): 프론트엔드 WebSocket 클라이언트
```tsx
// frontend/src/hooks/useMarketDataWebSocket.ts

import { useState, useEffect, useRef } from 'react';

interface Quote {
  symbol: string;
  price: number;
  change: number;
  volume: number;
  timestamp: string;
}

export const useMarketDataWebSocket = (symbols: string[]) => {
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8001/api/market-data/ws');
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[MarketDataWS] Connected');
      setIsConnected(true);

      // Subscribe to symbols
      ws.send(JSON.stringify({
        type: 'subscribe',
        symbols: symbols
      }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'quote') {
        const quote = message.data;
        setQuotes((prev) => ({
          ...prev,
          [quote.symbol]: quote
        }));
      }
    };

    ws.onerror = (error) => {
      console.error('[MarketDataWS] Error:', error);
    };

    ws.onclose = () => {
      console.log('[MarketDataWS] Disconnected');
      setIsConnected(false);
    };

    // Cleanup
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'unsubscribe',
          symbols: symbols
        }));
        ws.close();
      }
    };
  }, [symbols.join(',')]);

  return { quotes, isConnected };
};

// 사용 예시
export const RealTimeChart: React.FC = () => {
  const { quotes, isConnected } = useMarketDataWebSocket(['NVDA', 'MSFT', 'AAPL']);

  return (
    <div>
      <div>Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}</div>
      {Object.values(quotes).map(quote => (
        <div key={quote.symbol}>
          {quote.symbol}: ${quote.price} ({quote.change > 0 ? '+' : ''}{quote.change}%)
        </div>
      ))}
    </div>
  );
};
```

### Week 16-17: 모바일 알림 확장

#### Day 80-85 (2026-05-05 ~ 2026-05-10): Push Notification Service
```python
# backend/services/push_notification_service.py (신규)

from firebase_admin import messaging, credentials, initialize_app
import os
from typing import Dict, List

# Firebase 초기화
cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
initialize_app(cred)

class PushNotificationService:
    """Send push notifications to mobile devices"""

    async def send_conflict_alert(
        self,
        user_tokens: List[str],
        conflict: Dict
    ):
        """Send conflict alert to mobile devices"""

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title='⚠️ Strategy Conflict Detected',
                body=f"{conflict['ticker']}: {conflict['message']}"
            ),
            data={
                'type': 'conflict',
                'ticker': conflict['ticker'],
                'conflicting_strategy': conflict['conflicting_strategy'],
                'owning_strategy': conflict['owning_strategy'],
                'resolution': conflict['resolution']
            },
            tokens=user_tokens
        )

        response = messaging.send_multicast(message)

        return {
            'success_count': response.success_count,
            'failure_count': response.failure_count
        }

    async def send_signal_alert(
        self,
        user_tokens: List[str],
        signal: Dict
    ):
        """Send trading signal alert"""

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=f"🚨 {signal['action']} Signal: {signal['ticker']}",
                body=f"Confidence: {signal['confidence']:.0%} | Reason: {signal['reasoning'][:50]}..."
            ),
            data={
                'type': 'signal',
                'ticker': signal['ticker'],
                'action': signal['action'],
                'confidence': str(signal['confidence']),
                'reasoning': signal['reasoning']
            },
            tokens=user_tokens
        )

        response = messaging.send_multicast(message)

        return {
            'success_count': response.success_count,
            'failure_count': response.failure_count
        }

    async def send_daily_briefing(
        self,
        user_tokens: List[str],
        briefing_summary: str
    ):
        """Send daily briefing notification"""

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title='📊 Daily Briefing Available',
                body=briefing_summary
            ),
            data={
                'type': 'briefing',
                'url': '/briefing/latest'
            },
            tokens=user_tokens
        )

        response = messaging.send_multicast(message)

        return {
            'success_count': response.success_count,
            'failure_count': response.failure_count
        }

# Event Bus 통합
from backend.events.subscribers import event_bus

@event_bus.subscribe('CONFLICT_DETECTED')
async def on_conflict_detected(event):
    """Send push notification on conflict"""
    push_service = PushNotificationService()

    # Get user tokens from DB
    # (사용자가 앱에서 등록한 FCM 토큰)
    user_tokens = await get_user_fcm_tokens()

    await push_service.send_conflict_alert(user_tokens, event.data)

@event_bus.subscribe('TRADING_SIGNAL_GENERATED')
async def on_signal_generated(event):
    """Send push notification on signal"""
    push_service = PushNotificationService()
    user_tokens = await get_user_fcm_tokens()

    await push_service.send_signal_alert(user_tokens, event.data)
```

### Week 18: Live Dashboard

#### Day 90-95 (2026-05-26 ~ 2026-05-31): Live Dashboard 통합
```tsx
// frontend/src/pages/LiveDashboard.tsx

import { useMarketDataWebSocket } from '@/hooks/useMarketDataWebSocket';
import { useConflictWebSocket } from '@/hooks/useConflictWebSocket';
import { RealTimeChart } from '@/components/RealTimeChart';
import { ConflictAlert } from '@/components/ConflictAlert';
import { LiveSignals } from '@/components/LiveSignals';

export const LiveDashboard: React.FC = () => {
  const { quotes, isConnected: marketConnected } = useMarketDataWebSocket([
    'NVDA', 'MSFT', 'AAPL', 'GOOGL', 'AMZN'
  ]);

  const { conflicts, isConnected: conflictConnected } = useConflictWebSocket();

  return (
    <div className="live-dashboard">
      <div className="connection-status">
        <Tag color={marketConnected ? 'green' : 'red'}>
          Market Data: {marketConnected ? 'Connected' : 'Disconnected'}
        </Tag>
        <Tag color={conflictConnected ? 'green' : 'red'}>
          Conflict Alerts: {conflictConnected ? 'Connected' : 'Disconnected'}
        </Tag>
      </div>

      <Row gutter={16}>
        <Col span={16}>
          <RealTimeChart quotes={quotes} />
        </Col>
        <Col span={8}>
          <ConflictAlert conflicts={conflicts} />
          <LiveSignals />
        </Col>
      </Row>
    </div>
  );
};
```

---

## 📈 Phase 5: Advanced Risk Models 완성 (Week 19-22)

### Week 19-20: VaR 계산

#### Day 100-105 (2026-06-02 ~ 2026-06-07): VaR Calculator 구현
```python
# backend/analytics/var_calculator.py (신규)

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from scipy.stats import norm

class VaRCalculator:
    """Value at Risk Calculator"""

    def __init__(self):
        self.confidence_levels = [0.95, 0.99]
        self.time_horizons = [1, 10]  # days

    def calculate_historical_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> float:
        """
        Historical VaR calculation

        Args:
            returns: Array of historical returns
            confidence_level: Confidence level (0.95 = 95%)
            time_horizon: Time horizon in days

        Returns:
            VaR value (negative number indicating loss)
        """
        # Sort returns
        sorted_returns = np.sort(returns)

        # Find percentile
        index = int((1 - confidence_level) * len(sorted_returns))
        var = sorted_returns[index]

        # Scale by time horizon (sqrt rule)
        var_scaled = var * np.sqrt(time_horizon)

        return var_scaled

    def calculate_parametric_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> float:
        """
        Parametric VaR (assumes normal distribution)

        VaR = mean + z_score * std * sqrt(horizon)
        """
        mean = np.mean(returns)
        std = np.std(returns)
        z_score = norm.ppf(1 - confidence_level)

        var = mean + z_score * std * np.sqrt(time_horizon)

        return var

    def calculate_monte_carlo_var(
        self,
        portfolio: Dict[str, float],  # {symbol: weight}
        returns_history: pd.DataFrame,  # Columns = symbols
        confidence_level: float = 0.95,
        time_horizon: int = 1,
        simulations: int = 10000
    ) -> Tuple[float, np.ndarray]:
        """
        Monte Carlo VaR simulation

        Returns:
            (VaR value, simulated returns array)
        """
        # Calculate portfolio statistics
        symbols = list(portfolio.keys())
        weights = np.array([portfolio[s] for s in symbols])

        # Historical mean and covariance
        mean_returns = returns_history[symbols].mean().values
        cov_matrix = returns_history[symbols].cov().values

        # Simulate portfolio returns
        simulated_returns = np.random.multivariate_normal(
            mean_returns,
            cov_matrix,
            size=simulations
        )

        # Calculate portfolio returns
        portfolio_returns = simulated_returns @ weights

        # Scale by time horizon
        portfolio_returns_scaled = portfolio_returns * np.sqrt(time_horizon)

        # Calculate VaR
        var = np.percentile(portfolio_returns_scaled, (1 - confidence_level) * 100)

        return var, portfolio_returns_scaled

    def calculate_conditional_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95
    ) -> float:
        """
        Conditional VaR (Expected Shortfall)

        Average loss given that VaR is exceeded
        """
        var = self.calculate_historical_var(returns, confidence_level)

        # Returns worse than VaR
        tail_returns = returns[returns <= var]

        # Average of tail
        cvar = np.mean(tail_returns) if len(tail_returns) > 0 else var

        return cvar

    async def calculate_portfolio_var(
        self,
        portfolio_id: str,
        db: Session
    ) -> Dict:
        """Calculate VaR for entire portfolio"""

        # Fetch portfolio positions
        positions = await self._fetch_portfolio_positions(portfolio_id, db)

        # Fetch historical returns (252 days = 1 year)
        returns_df = await self._fetch_returns_history(
            list(positions.keys()),
            days=252
        )

        results = {}

        # Historical VaR
        for conf_level in self.confidence_levels:
            for horizon in self.time_horizons:
                key = f"historical_var_{int(conf_level*100)}_{horizon}d"

                # Monte Carlo simulation
                var, simulations = self.calculate_monte_carlo_var(
                    portfolio=positions,
                    returns_history=returns_df,
                    confidence_level=conf_level,
                    time_horizon=horizon,
                    simulations=10000
                )

                results[key] = {
                    'var': float(var),
                    'conf_level': conf_level,
                    'time_horizon': horizon,
                    'method': 'monte_carlo',
                    'simulations': 10000
                }

        # Conditional VaR (CVaR)
        portfolio_returns = returns_df @ np.array(list(positions.values()))
        results['cvar_95'] = self.calculate_conditional_var(
            portfolio_returns.values,
            confidence_level=0.95
        )

        return results
```

#### Day 106-110 (2026-06-08 ~ 2026-06-12): DB 모델 및 API
```python
# backend/database/models.py 추가

class PortfolioRisk(Base):
    __tablename__ = 'portfolio_risk'

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(UUID, ForeignKey('portfolios.id'))

    # VaR values (negative = loss)
    var_1day_95 = Column(Float)  # 1-day 95% VaR
    var_1day_99 = Column(Float)  # 1-day 99% VaR
    var_10day_95 = Column(Float)  # 10-day 95% VaR
    var_10day_99 = Column(Float)  # 10-day 99% VaR

    # Conditional VaR
    cvar_95 = Column(Float)
    cvar_99 = Column(Float)

    # Metadata
    method = Column(String(50))  # historical, parametric, monte_carlo
    simulations = Column(Integer)  # For Monte Carlo
    calculated_at = Column(DateTime, default=datetime.utcnow)

    portfolio = relationship('Portfolio', back_populates='risk_metrics')

# backend/api/risk_router.py (신규)

@router.get("/api/portfolios/{portfolio_id}/var")
async def get_portfolio_var(
    portfolio_id: str,
    db: Session = Depends(get_sync_session)
):
    """Get portfolio VaR metrics"""

    calculator = VaRCalculator()
    var_metrics = await calculator.calculate_portfolio_var(portfolio_id, db)

    # Save to DB
    risk_record = PortfolioRisk(
        portfolio_id=portfolio_id,
        var_1day_95=var_metrics['historical_var_95_1d']['var'],
        var_1day_99=var_metrics['historical_var_99_1d']['var'],
        var_10day_95=var_metrics['historical_var_95_10d']['var'],
        var_10day_99=var_metrics['historical_var_99_10d']['var'],
        cvar_95=var_metrics['cvar_95'],
        method='monte_carlo',
        simulations=10000
    )
    db.add(risk_record)
    db.commit()

    return var_metrics
```

### Week 21: Sharpe/Sortino Ratio

#### Day 111-115 (2026-06-09 ~ 2026-06-13): Risk-Adjusted Metrics
```python
# backend/analytics/risk_adjusted_metrics.py (신규)

class RiskAdjustedMetrics:
    """Calculate risk-adjusted performance metrics"""

    def __init__(self, risk_free_rate: float = 0.04):
        """
        Args:
            risk_free_rate: Annual risk-free rate (default 4%)
        """
        self.risk_free_rate = risk_free_rate
        self.daily_rfr = risk_free_rate / 252

    def calculate_sharpe_ratio(
        self,
        returns: np.ndarray,
        annualize: bool = True
    ) -> float:
        """
        Sharpe Ratio = (Return - RFR) / Std Dev

        Higher is better
        > 1.0 = Good
        > 2.0 = Very Good
        > 3.0 = Excellent
        """
        excess_return = np.mean(returns) - self.daily_rfr
        std_dev = np.std(returns)

        sharpe = excess_return / std_dev if std_dev > 0 else 0

        if annualize:
            sharpe *= np.sqrt(252)

        return sharpe

    def calculate_sortino_ratio(
        self,
        returns: np.ndarray,
        annualize: bool = True
    ) -> float:
        """
        Sortino Ratio = (Return - RFR) / Downside Dev

        Only penalizes downside volatility
        Better than Sharpe for asymmetric returns
        """
        excess_return = np.mean(returns) - self.daily_rfr

        # Downside returns only
        downside_returns = returns[returns < self.daily_rfr]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0

        sortino = excess_return / downside_std if downside_std > 0 else 0

        if annualize:
            sortino *= np.sqrt(252)

        return sortino

    def calculate_calmar_ratio(
        self,
        returns: np.ndarray,
        annualize: bool = True
    ) -> float:
        """
        Calmar Ratio = Annual Return / Max Drawdown

        Measures return vs worst drawdown
        """
        annual_return = np.mean(returns) * 252 if annualize else np.mean(returns)

        # Calculate max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)

        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        return calmar

    def calculate_all_ratios(
        self,
        returns: np.ndarray
    ) -> Dict[str, float]:
        """Calculate all risk-adjusted ratios"""

        return {
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'sortino_ratio': self.calculate_sortino_ratio(returns),
            'calmar_ratio': self.calculate_calmar_ratio(returns),
            'annual_return': np.mean(returns) * 252,
            'annual_volatility': np.std(returns) * np.sqrt(252),
            'max_drawdown': self._calculate_max_drawdown(returns)
        }

    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

# backend/database/models.py 추가

class StrategyPerformance(Base):
    __tablename__ = 'strategy_performance'

    id = Column(Integer, primary_key=True)
    strategy_id = Column(UUID, ForeignKey('strategies.id'))

    # Risk-adjusted metrics
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    calmar_ratio = Column(Float)

    # Basic metrics
    annual_return = Column(Float)
    annual_volatility = Column(Float)
    max_drawdown = Column(Float)

    # Period
    start_date = Column(Date)
    end_date = Column(Date)
    measured_at = Column(DateTime, default=datetime.utcnow)

    strategy = relationship('Strategy', back_populates='performance_metrics')
```

### Week 22: Beta/Correlation

#### Day 116-120 (2026-06-14 ~ 2026-06-18): Correlation Analyzer
```python
# backend/analytics/correlation_analyzer.py (신규)

class CorrelationAnalyzer:
    """Analyze portfolio correlations and diversification"""

    def calculate_beta(
        self,
        stock_returns: np.ndarray,
        market_returns: np.ndarray
    ) -> Dict[str, float]:
        """
        Calculate beta to market (SPY)

        Beta = Cov(stock, market) / Var(market)

        Beta > 1: More volatile than market
        Beta = 1: Matches market
        Beta < 1: Less volatile than market
        """
        covariance = np.cov(stock_returns, market_returns)[0][1]
        market_variance = np.var(market_returns)

        beta = covariance / market_variance if market_variance > 0 else 1.0

        # R-squared (correlation strength)
        correlation = np.corrcoef(stock_returns, market_returns)[0][1]
        r_squared = correlation ** 2

        return {
            'beta': beta,
            'r_squared': r_squared,
            'correlation': correlation
        }

    def calculate_correlation_matrix(
        self,
        returns_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for portfolio

        Returns correlation matrix (symbols × symbols)
        """
        return returns_df.corr()

    def calculate_diversification_score(
        self,
        correlation_matrix: pd.DataFrame
    ) -> float:
        """
        Calculate diversification score (0-100)

        Lower correlation = higher diversification
        Score = (1 - avg_correlation) * 100
        """
        # Get upper triangle (exclude diagonal)
        upper_triangle = correlation_matrix.values[
            np.triu_indices_from(correlation_matrix.values, k=1)
        ]

        avg_correlation = np.mean(upper_triangle)

        # Convert to 0-100 scale
        diversification_score = (1 - avg_correlation) * 100

        return max(0, min(100, diversification_score))

    def identify_clusters(
        self,
        correlation_matrix: pd.DataFrame,
        threshold: float = 0.7
    ) -> List[List[str]]:
        """
        Identify highly correlated clusters

        Clusters: Groups of stocks with correlation > threshold
        """
        from scipy.cluster.hierarchy import linkage, fcluster

        # Hierarchical clustering
        linkage_matrix = linkage(correlation_matrix, method='average')

        # Form clusters
        cluster_labels = fcluster(linkage_matrix, t=1-threshold, criterion='distance')

        # Group by cluster
        clusters = {}
        for i, symbol in enumerate(correlation_matrix.index):
            cluster_id = cluster_labels[i]
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(symbol)

        return list(clusters.values())

    async def analyze_portfolio_correlation(
        self,
        portfolio_id: str,
        db: Session
    ) -> Dict:
        """Comprehensive portfolio correlation analysis"""

        # Fetch positions
        positions = await self._fetch_portfolio_positions(portfolio_id, db)
        symbols = list(positions.keys())

        # Fetch returns (1 year)
        returns_df = await self._fetch_returns_history(symbols, days=252)

        # Fetch market returns (SPY)
        market_returns = await self._fetch_market_returns(days=252)

        # 1. Correlation matrix
        corr_matrix = self.calculate_correlation_matrix(returns_df)

        # 2. Beta to market for each stock
        betas = {}
        for symbol in symbols:
            betas[symbol] = self.calculate_beta(
                returns_df[symbol].values,
                market_returns.values
            )

        # 3. Diversification score
        div_score = self.calculate_diversification_score(corr_matrix)

        # 4. Identify clusters
        clusters = self.identify_clusters(corr_matrix, threshold=0.7)

        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'betas': betas,
            'diversification_score': div_score,
            'clusters': clusters,
            'summary': {
                'avg_correlation': corr_matrix.values[
                    np.triu_indices_from(corr_matrix.values, k=1)
                ].mean(),
                'max_correlation': corr_matrix.values[
                    np.triu_indices_from(corr_matrix.values, k=1)
                ].max(),
                'portfolio_beta': np.mean([b['beta'] for b in betas.values()])
            }
        }
```

---

## 🎉 Phase 6: 최종 검증 및 문서화 (Week 23-26)

### Week 23: 통합 테스트

#### Day 121-125 (2026-06-19 ~ 2026-06-23): E2E 테스트
```bash
# E2E 테스트 시나리오

# 1. Persona-based Trading
- [ ] Trading 페르소나 브리핑 생성
- [ ] Long-term 페르소나 브리핑 생성
- [ ] Dividend 페르소나 브리핑 생성
- [ ] Aggressive 페르소나 브리핑 생성
- [ ] 페르소나 전환 UI 테스트

# 2. Real-time Execution
- [ ] WebSocket 연결 테스트
- [ ] 실시간 시세 스트리밍 테스트
- [ ] Conflict alert WebSocket 테스트
- [ ] Push notification 테스트 (Firebase)
- [ ] Live Dashboard 렌더링 테스트

# 3. Advanced Risk Models
- [ ] VaR 계산 (Historical, Parametric, Monte Carlo)
- [ ] Sharpe/Sortino/Calmar Ratio 계산
- [ ] Beta 계산 (vs SPY)
- [ ] Correlation matrix 생성
- [ ] Diversification score 계산

# 실행
cd frontend
npm run test:e2e
```

### Week 24: 문서화

#### Day 126-130 (2026-06-24 ~ 2026-06-28): 문서 업데이트
```markdown
# 업데이트할 문서 목록

1. SYSTEM_STATUS_MAP.md
   - Persona-based Trading: 50% → 100%
   - Real-time Execution: 70% → 100%
   - Advanced Risk Models: 30% → 100%

2. API 문서
   - /api/briefing/persona/{persona}
   - /api/market-data/ws
   - /api/portfolios/{id}/var
   - /api/portfolios/{id}/correlation

3. 사용자 가이드
   - Persona 선택 가이드
   - WebSocket 연결 가이드
   - Risk Metrics 해석 가이드

4. 개발자 가이드
   - Persona 확장 방법
   - WebSocket 클라이언트 작성
   - Risk Model 커스터마이징
```

### Week 25-26: 배포 및 모니터링

#### Day 131-140 (2026-06-29 ~ 2026-07-08): 프로덕션 배포
```bash
# 1. 프로덕션 체크리스트
- [ ] 모든 테스트 통과
- [ ] 성능 테스트 (부하 테스트)
- [ ] 보안 검사
- [ ] 백업 생성
- [ ] 롤백 계획 수립

# 2. 배포 실행
git tag -a v3.0.0 -m "Release v3.0.0: Complete feature set"
git push origin v3.0.0

# 3. 모니터링 설정
- Prometheus 메트릭 확인
- 로그 모니터링
- 사용자 피드백 수집

# 4. 공지
- 사용자 공지 (새로운 기능)
- Migration 가이드 제공
- FAQ 업데이트
```

---

## 📊 최종 검증 체크리스트

### 레거시 정리
- [ ] backend/ai/legacy/debate/ 제거 ✅ (Phase 1 완료)
- [ ] backend/ai/debate/ 제거
- [ ] backend/api/war_room_router.py 제거
- [ ] backend/api/phase_integration_router.py 제거
- [ ] 관련 테스트 제거
- [ ] Structure Map 업데이트

### 문서 압축
- [ ] 583개 → 200개 핵심 문서
- [ ] legacy/archive 이동
- [ ] 문서 구조 재편
- [ ] README 업데이트

### Persona-based Trading
- [ ] DailyBriefingService 페르소나 분리
- [ ] API 엔드포인트 (/api/briefing/persona/{persona})
- [ ] PersonaSelector UI 컴포넌트
- [ ] 페르소나별 대시보드 레이아웃
- [ ] Weekly/Monthly Report 페르소나 확장

### Real-time Execution
- [ ] MarketDataWebSocketManager 구현
- [ ] 프론트엔드 WebSocket 클라이언트
- [ ] Push Notification Service (Firebase)
- [ ] Email/SMS 알림
- [ ] Live Dashboard

### Advanced Risk Models
- [ ] VaR Calculator (Historical, Parametric, Monte Carlo)
- [ ] RiskAdjustedMetrics (Sharpe, Sortino, Calmar)
- [ ] CorrelationAnalyzer (Beta, Correlation Matrix)
- [ ] DB 모델 (PortfolioRisk, StrategyPerformance)
- [ ] API 엔드포인트

---

## 📅 마일스톤 요약

| Week | Phase | 주요 작업 | 완료 기준 |
|------|-------|----------|----------|
| 1-2 | 레거시 조사 | War Room Legacy 사용 현황, Deprecation | 조사 보고서 완성 |
| 3-4 | 레거시 제거 | Debate 제거, Router 제거 | 레거시 코드 0% |
| 5-6 | 문서 압축 | 583 → 200 문서 | 핵심 200개 선정 |
| 7-12 | Persona Trading | Briefing 분리, UI, Report | 100% 완성 |
| 13-18 | Real-time | WebSocket, Push, Dashboard | 100% 완성 |
| 19-22 | Risk Models | VaR, Sharpe, Beta | 100% 완성 |
| 23-26 | 최종 검증 | 테스트, 문서, 배포 | v3.0.0 릴리스 |

---

## 🎯 성공 지표

### 정량적 지표

| 지표 | Before | After (목표) |
|------|--------|-------------|
| **레거시 코드** | 15% | 0% |
| **문서 수** | 583개 | 200개 |
| **Persona Trading** | 50% | 100% |
| **Real-time** | 70% | 100% |
| **Risk Models** | 30% | 100% |
| **전체 완성도** | 85% | 100% |

### 정성적 지표

- ✅ 코드베이스 명확성 (단일 War Room 시스템)
- ✅ 문서 접근성 (200개 핵심 문서)
- ✅ 사용자 경험 (페르소나별 맞춤 서비스)
- ✅ 실시간성 (WebSocket 실시간 업데이트)
- ✅ 리스크 관리 (고급 Risk Metrics)

---

## 📞 참고 문서

- [SYSTEM_STATUS_MAP.md](../SYSTEM_STATUS_MAP.md) - 시스템 현황
- [LEGACY_CLEANUP_PLAN.md](../LEGACY_CLEANUP_PLAN.md) - 레거시 정리
- [PARTIAL_IMPLEMENTATION_REVIEW.md](../PARTIAL_IMPLEMENTATION_REVIEW.md) - 부분 구현 검토

---

**작성자**: AI Trading System Team
**최종 업데이트**: 2026-01-25
**다음 리뷰**: Week 2 종료 시 (2026-02-09)
**상태**: 📋 Ready to Execute
