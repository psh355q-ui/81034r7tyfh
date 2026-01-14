# Refined Documentation Consolidation Plan

사용자의 피드백을 반영하여, 단순 날짜 기준이 아닌 **"시스템 구조 및 현행화 여부"**를 기준으로 문서를 정리합니다.

## 1. 정리 원칙 (Principles)

1.  **Structure-Based Organization**: `backend/` 코드 구조와 유사하게 `docs/features/` 하위 폴더를 구성하여 문서를 매핑합니다.
2.  **Preserve Active Legacy**: 오래된 작성일(`25xxxx`)이라도 현재 시스템의 기능을 설명하는 유일한 문서라면 `archive`가 아닌 `features`로 이동하고 현행화(Renaming)합니다.
3.  **Clear Separation**:
    - **Guide**: 설치, 실행, 운영 방법 (`guides/`)
    - **Feature**: 기능 상세, 알고리즘 설명 (`features/`)
    - **Report**: 테스트 결과, Phase 완료 보고 (`reports/`)
    - **Planning**: 기획, 설계 (구/신) (`planning/`)
    - **Discussion**: 아이디어, 회의록 (`discussions/`)

## 2. 폴더 구조 설계 (Target Structure)

```text
docs/
├── guides/                     # 사용자 가이드 (Quick Start, How-to)
├── architecture/               # 시스템 구조도, 분석 리포트
├── api/                        # API 명세
├── rules/                      # 개발 규칙 (Rule files)
├── features/                   # 시스템 기능 상세 (Backend 구조와 매핑)
│   ├── news/                   # News Agent, Crawler
│   ├── debate/                 # Debate Engine, Agents
│   ├── risk/                   # Risk Management, Throttling
│   ├── execution/              # Order Execution, Broker
│   └── reasoning/              # Deep Reasoning, Knowledge Graph
├── planning/                   # 기획서
│   └── active/                 # 현재 진행 중인 기획
│   └── history/                # 과거 기획 (참조용)
├── reports/                    # 완료 보고서, 테스트 결과
│   └── 2025/
│   └── 2026/
├── discussions/                # (ex-ai토론) 회의록, 아이디어
└── archive/                    # 더 이상 참조하지 않는 폐기 문서
```

## 3. 주요 파일 이동 계획 (Migration Map)

### A. Features (기능 설명 문서)
파일명에 다음 키워드가 포함된 경우 `docs/features/{category}/`로 이동하고 이름을 다듬습니다.

- `RiskManagement`, `Risk` -> `docs/features/risk/Risk_Management_Spec.md`
- `Debate`, `Agent` -> `docs/features/debate/Debate_Engine_Spec.md`
- `News`, `Crawler`, `RSS` -> `docs/features/news/News_System_Spec.md`
- `Knowledge`, `Reasoning` -> `docs/features/reasoning/Deep_Reasoning_Spec.md`

### B. Discussions (ai토론)
- `docs/ai토론/*.md` -> `docs/discussions/`
- 폴더명은 주제별(예: `260114_Structure`)로 정리하거나, 날짜별(`2026-01`)로 정리합니다.

### C. Reports (보고서)
- `*_Report.md`, `*_Result.md` -> `docs/reports/{Year}/`

## 4. 실행 절차 (Execution Steps)

1.  **디렉토리 생성**: 위 구조에 맞춰 폴더 생성.
2.  **스마트 이동 (Smart Move)**:
    - 스크립트를 통해 파일 내용을 간단히 스캔(키워드 검색)하거나, 파일명 패턴 매칭을 통해 적절한 폴더로 이동.
    - 이동 시 사용자에게 **로그(Log)**를 남겨 추적 가능하게 함.
3.  **검증**: 이동 후 깨진 링크 점검 (주요 파일 위주).

## 5. 승인 요청

이 구조대로 정리를 진행하시겠습니까? 특히 `docs/features`를 시스템 컴포넌트별로 나누는 방식이 마음에 드시는지 확인 부탁드립니다.
