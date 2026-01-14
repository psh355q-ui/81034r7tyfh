---
description: Documentation standards including filename conventions, folder structure, and category mapping.
---

# Documentation Standards

문서의 체계적인 관리와 검색 효율성을 높이기 위해 다음 표준을 엄격히 준수해야 합니다.

## 1. 폴더 구조 규칙 (Folder Structure)

문서의 **성격**에 따라 반드시 지정된 폴더에 위치해야 합니다.

| 폴더 경로 | 포함 내용 |
|-----------|-----------|
| `docs/guides/` | 사용자 매뉴얼, 설치 가이드, 배포 가이드 |
| `docs/architecture/` | 시스템 구조도, 아키텍처 분석, 다이어그램 |
| `docs/api/` | API 명세서, 엔드포인트 설명 |
| `docs/rules/` | 개발 규칙, 컨벤션, 템플릿 |
| `docs/features/{category}/` | 시스템 컴포넌트별 상세 기능 명세 (Active Document) |
| `docs/planning/active/` | 현재 진행 중인 기획서, 로드맵 |
| `docs/planning/history/` | 완료되었거나 보류된 과거 기획서 |
| `docs/reports/{Year}/` | 테스트 결과, Phase 완료 보고서, 회고 (연도별 폴더링) |
| `docs/discussions/` | 아이디어 스케치, 회의록, AI 토론 (구 ai토론) |
| `docs/archive/{Year}/` | 더 이상 참조하지 않는 폐기 문서 |

### Features 하위 카테고리
- `news`: 뉴스 수집 및 분석
- `debate`: AI 토론, 에이전트
- `risk`: 리스크 관리, 스로틀링
- `execution`: 주문 실행, 브로커
- `reasoning`: 추론, 지식 그래프

## 2. 파일명 규칙 (Filename Convention)

### A. 리포트/기획서/회의록 (Transactional)
시간 흐름에 따라 생성되는 문서는 `YYMMDD` 접두어를 사용합니다.

**Format**: `YYMMDD_Category_Description.md`

- **예시**:
  - `260114_Implementation_Docs_Consolidation.md`
  - `260120_Report_Phase5_Test_Result.md`

### B. 기능 명세/가이드 (Active/Living)
지속적으로 업데이트되는 문서는 명확한 영문 이름을 사용하되, `YYMMDD`를 생략할 수 있습니다.

**Format**: `Description_Spec.md` 또는 `Description_Guide.md`

- **예시**:
  - `docs/features/news/News_System_Spec.md`
  - `docs/guides/Quick_Start_Guide.md`

## 3. 문서 카테고리 (Category Key)

| 카테고리 | 설명 | 대상 폴더 |
|----------|------|-----------|
| `Implementation` | 구현 완료 보고 | `docs/reports/{Year}` |
| `Planning` | 기획, 설계 | `docs/planning/active` |
| `Rule` | 규칙 변경 | `docs/rules` |
| `Analysis` | 리서치 분석 | `docs/architecture` or `reports` |
| `Discussion` | 토론, 아이디어 | `docs/discussions` |

## 4. 작성 가이드

1. **위치 준수**: 문서를 생성하기 전에 `docs/` 내의 어느 폴더에 속하는지 먼저 판단하십시오.
2. **Context 연결**: 문서 내에서 관련된 소스 코드 경로는 반드시 절대 경로 또는 관련도 높은 상대 경로로 명시합니다.
3. **이미지**: `docs/images/` 폴더 사용을 권장합니다.
