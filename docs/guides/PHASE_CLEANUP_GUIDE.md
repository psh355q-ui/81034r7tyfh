# Phase 정리 권장사항

**작성일**: 2025-12-25  
**목적**: docs 폴더 정리 및 Phase 중복 제거

---

## 🚨 현재 문제점

### 1. Phase 번호 중복
- Phase 6: 3개 이상의 서로 다른 내용
- Phase 14-18: 각각 2-3개의 중복 문서
- Phase 20-21: 구버전 + 신버전 혼재

### 2. 날짜 접두사 불일치
- `251210_*` (2025-12-10)
- `251215_*` (2025-12-15)
- `251222_*`, `251223_*`, `251225_*` (최신)
- 접두사 없는 파일

### 3. Spec-Kit vs Phase 보고서 구분 필요

**Spec-Kit** (보존):
- `00_Spec_Kit/`: 개발 계획, 스펙, 시스템 개요
- GitHub의 [spec-kit](https://github.com/github/spec-kit) 개념 기반
- **절대 이동/삭제 금지** ⭐

**Phase 보고서** (정리 필요):
- `02_Phase_Reports/`: 구버전 중복 많음
- `10_Progress_Reports/`: 최신 진행 보고 (보존)
- `docs/*.md`: 루트에 산재된 Phase 문서

---

## ✅ 권장 정리 방안 (수정)

### 📌 보존 대상 (절대 이동 금지)

**1. Spec-Kit 전체** ⭐:
```
00_Spec_Kit/  ← 개발 계획, 스펙 문서 (보존)
├── 00_Project_Summary.md
├── 01_DB_Storage_Analysis.md
├── 2025_System_Overview.md
└── ... (전체 18개 파일)
```

**2. 최신 Progress Reports**:
```
10_Progress_Reports/
├── 251222_Phase20_Complete.md
├── 251222_Phase21_Complete.md
├── 251223_Phase24_Complete.md
├── 251223_Phase25*.md (전체)
├── 251223_Phase26_REAL_MODE_완료.md
└── 251223_Phase27_Final_완료.md
```

**3. 최신 완료 보고서**:
```
docs/
├── PHASE_MASTER_INDEX.md (NEW)
├── phase20_completion_report.md
├── phase_21_completion.md
├── 251225_work_summary.md
└── 251224_work_summary.md
```

### Step 1: 아카이브 이동 (Phase Reports만)

**이동 대상** (구버전 Phase 보고서):
```
docs/99_Archive/old_phase_reports/
```

**이동할 파일** (02_Phase_Reports 내 중복분):
1. `251210_Phase*.md` (Phase 6, 14, 15, 16, 17, 18 중복본)
2. `251210_PHASE_*.md` (Phase A, B, C 구버전)
3. Phase 20-21 구버전 (2025-12-22 이전)

**절대 이동 금지** ⭐:
- `00_Spec_Kit/` 전체 (Spec-Driven Development 문서)
- `10_Progress_Reports/2512*` (최신 1주일)
- `docs/PHASE_MASTER_INDEX.md` (NEW)
- `docs/phase20_completion_report.md`
- `docs/phase_21_completion.md`

### Step 2: 문서 재조직 (간소화)

**현재 구조 유지**:
```
docs/
├── 00_Spec_Kit/  ⭐ 보존 (Spec-Driven Development)
├── 01_Quick_Start/
├── 02_Phase_Reports/  → 중복 제거만
├── 03_Integration_Guides/
├── 04_Feature_Guides/
├── 05_Deployment/
├── ... (기타 폴더 유지)
├── 10_Progress_Reports/  ⭐ 보존 (최신 진행 보고)
└── 99_Archive/
    └── old_phase_reports/  (중복 이동)
```

**변경 최소화**:
- 폴더 구조 유지
- **02_Phase_Reports** 내 중복본만 아카이브
- Spec-Kit, Progress Reports 보존

### Step 3: README 업데이트

**docs/README.md**에 다음 추가:
```markdown
# Documentation Index

## Quick Links
- [Phase Master Index](PHASE_MASTER_INDEX.md) - 전체 Phase 목록 ⭐
- [Spec-Kit](00_Spec_Kit/README.md) - 개발 계획 및 스펙
- [Latest Progress](10_Progress_Reports/) - 최신 진행 보고
- [Quick Start](01_Quick_Start/QUICKSTART.md)

## 폴더 구조
- `00_Spec_Kit/`: Spec-Driven Development 문서 (보존)
- `02_Phase_Reports/`: Phase 완료 보고서 (중복 제거됨)
- `10_Progress_Reports/`: 최신 개발 진행 (2025-12)
- `99_Archive/`: 구버전 문서

## Phase 번호 참고
중복 번호는 PHASE_MASTER_INDEX.md를 참고하세요.
```

---

## 🔧 실행 명령 (권장)

### 1. 아카이브 폴더 생성
```bash
mkdir -p docs/99_Archive/old_phase_reports
```

### 2. 중복 Phase 보고서만 이동 (예시)

**⚠️ 중요**: `00_Spec_Kit/`은 절대 건드리지 마세요!

```bash
# Phase 6-18 구버전 (02_Phase_Reports 내)
mv docs/02_Phase_Reports/251210_Phase6_*.md docs/99_Archive/old_phase_reports/
mv docs/02_Phase_Reports/251210_Phase14_*.md docs/99_Archive/old_phase_reports/
mv docs/02_Phase_Reports/251210_Phase15_*.md docs/99_Archive/old_phase_reports/
mv docs/02_Phase_Reports/251210_Phase16_*.md docs/99_Archive/old_phase_reports/
mv docs/02_Phase_Reports/251210_Phase17_*.md docs/99_Archive/old_phase_reports/
mv docs/02_Phase_Reports/251210_Phase18_*.md docs/99_Archive/old_phase_reports/

# Phase A, B, C 구버전
mv docs/02_Phase_Reports/251210_PHASE_A_*.md docs/99_Archive/old_phase_reports/
mv docs/02_Phase_Reports/251210_PHASE_B_*.md docs/99_Archive/old_phase_reports/
mv docs/02_Phase_Reports/251210_PHASE_C_*.md docs/99_Archive/old_phase_reports/

# 루트에 있는 중복 문서
mv docs/Phase*.md docs/99_Archive/old_phase_reports/  # phase20_, phase_21 제외
```

### 3. 정리 확인
```bash
# Phase 20-27 최신본 확인
ls -la docs/phase*.md
ls -la docs/10_Progress_Reports/2512*.md

# 00_Spec_Kit 보존 확인
ls -la docs/00_Spec_Kit/
```

---

## 📋 정리 체크리스트

### 즉시 실행 가능
- [x] PHASE_MASTER_INDEX.md 생성 ✅
- [ ] 99_Archive/old_phases/ 폴더 생성
- [ ] 구버전 Phase 문서 이동
- [ ] docs/README.md 업데이트

### 검토 필요
- [ ] 각 Phase 문서의 최신 버전 확인
- [ ] 중복 내용 병합 가능 여부 검토
- [ ] API 문서와 Phase 보고서 연결

### 장기 계획
- [ ] 문서 자동 생성 스크립트
- [ ] Phase 번호 자동 검증
- [ ] Changelog 자동화

---

## ⚠️ 주의사항

### 절대 삭제하지 말 것
- `10_Progress_Reports/2512*` (최근 1주일 내)
- `docs/phase20_completion_report.md`
- `docs/phase_21_completion.md`
- `docs/*work_summary.md` (전체)

### 이동만 할 것 (삭제 금지)
- 구버전 문서도 참고용으로 Archive에 보존
- Git history로 복구 가능하지만 안전하게 이동

---

**다음 단계**: 사용자 확인 후 실행
