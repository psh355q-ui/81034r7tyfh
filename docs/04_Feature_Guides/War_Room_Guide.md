# AI War Room Feature Guide

**Feature**: AI War Room - 실시간 토론 시각화  
**Version**: 1.0.0  
**Date**: 2025-12-16

---

## 개요

AI War Room은 5개 AI Agents의 실시간 토론 과정을 카카오톡 스타일로 시각화하는 기능입니다.

---

## 주요 기능

### 1. 5개 AI Agents
- 🧑‍💻 Trader (공격수)
- 👮 Risk (수비수)
- 🕵️ Analyst (분석가)
- 🌍 Macro (매크로)
- 🏛️ Institutional (기관)
- 🤵 PM (중재자)

### 2. 실시간 토론 표시
- 카카오톡 스타일 메시지
- BUY/SELL/HOLD 액션 배지
- 신뢰도 퍼센티지
- 타임스탬프

### 3. Constitutional 검증
- 헌법 검증 결과 표시
- 위반 조항 상세 카드
- 5대 조항 아이콘 시스템

### 4. 헌법 전문 모달
- 📜 헌법 전문 보기 버튼
- 5대 조항 전체 표시
- 토글 기능 (열기/닫기)

---

## 접속 방법

```
URL: http://localhost:3002/war-room
메뉴: 분석 → AI War Room
```

---

## 사용 방법

1. **샘플 토론 시작**:
   - "샘플 토론 시작" 버튼 클릭
   - 5개 Agents 순차 토론 시작

2. **토론 관찰**:
   - 각 Agent 투표 및 이유 확인
   - 합의 수준 바 실시간 업데이트
   - 최종 PM 결정 확인

3. **Constitutional 검증**:
   - 자동 헌법 검증 수행
   - 위반 사항 확인
   - 위반 조항 상세 보기

4. **헌법 학습**:
   - "📜 헌법 전문 보기" 클릭
   - 5대 조항 전체 읽기
   - "❌ 헌법 닫기"로 모달 닫기

---

## 헌법 5대 조항

### 💎 제1조: 자본 보존 우선
수익률보다 안전을 우선합니다. AI는 공격적 수익이 아닌 자본 보존을 최우선 목표로 합니다.

### 📖 제2조: 설명 가능성
모든 AI 판단은 인간이 이해할 수 있어야 합니다. 블랙박스 결정을 금지합니다.

### 👤 제3조: 인간 최종 결정권
AI는 추천만 할 수 있습니다. 모든 거래는 반드시 인간의 최종 승인이 필요합니다.

### 🛡️ 제4조: 강제 개입권
시스템 위험 감지 시 AI가 강제로 개입하여 포지션을 축소할 수 있습니다.

### ⚖️ 제5조: 헌법 개정 절차
헌법 변경은 명시적 절차를 따라야 하며, 모든 개정 이력이 기록됩니다.

---

## 기술 상세

### Frontend Components
- `frontend/src/components/war-room/WarRoom.tsx`
- `frontend/src/components/war-room/WarRoom.css`
- `frontend/src/pages/WarRoomPage.tsx`
- `frontend/src/constants/constitution.ts`

### Styling
- 카카오톡 스타일 메시지 UI
- 그라디언트 배경
- 애니메이션 효과 (fadeIn, slideUp)
- 반응형 디자인

### State Management
- `messages`: 토론 메시지 배열
- `constitutionalResult`: 헌법 검증 결과
- `showConstitution`: 모달 표시 상태
- `consensus`: 합의 수준 (0-1)

---

## 향후 개선 사항

1. **실시간 API 연동**
   - Backend AI Debate API 연결
   - WebSocket 실시간 통신
   - 실제 종목 분석

2. **히스토리 기능**
   - 과거 토론 기록 조회
   - 토론 결과 통계
   - 성과 추적

3. **커스터마이징**
   - Agent 가중치 조정
   - 토론 주제 선택
   - 알림 설정

---

**작성일**: 2025-12-16  
**작성자**: Development Team  
**관련 문서**: `251216_System_Integration_and_War_Room.md`
