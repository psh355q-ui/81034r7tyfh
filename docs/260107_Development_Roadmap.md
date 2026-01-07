# 2026-01-07 Development Roadmap (Phase 4 & 5 Integration)

**작성일**: 2026-01-07
**목표**: 시스템의 기능적 완성을 넘어 "운용 가능한(Operational)" 상태로 전환.

---

## 📅 Today's Plan (2026-01-07)

### 1. Shadow Trading Week 1 Final Report 📊
*   **목표**: 1/4~1/7 기간의 Shadow Trading 시뮬레이션 결과 확정.
*   **작업 내용**:
    *   [ ] `generate_week1_report.py` 재실행 및 Day 5-7 데이터 반영 확인.
    *   [ ] 수익률(PnL) 및 승률(Win Rate) 최종 산출.
    *   [ ] `lessons_learned` 섹션에 "AI의 판단 근거" 추가.

### 2. Report Orchestrator 연동 심화 🔗
*   **목표**: Mock 데이터 제거 및 실시간 데이터 연결.
*   **작업 내용**:
    *   [ ] **News Agent 연동**: `NewsAgent.get_recent_news()` 실제 호출로 변경.
    *   [ ] **Deep Reasoning 연동**: `deep_reasoning_history` 테이블에서 최신 인사이트 조회 쿼리 구현.
    *   [ ] **자동화**: `apscheduler`를 사용하여 매일 아침(08:00) 리포트 자동 생성 설정.

### 3. User Feedback Loop 준비 🗣️
*   **목표**: 사용자가 AI의 결정에 피드백을 줄 수 있는 인터페이스 초안.
*   **작업 내용**:
    *   [ ] Frontend: `ReportViewer` 컴포넌트 생성 (Markdown 렌더링).
    *   [ ] Feedback Button: "Good Decision" / "Bad Decision" + 코멘트 기능.

---

## 🚀 Future Roadmap (Week 2 ~)

### Phase 5: API & Dashboard Integration (1/10 ~)
*   [ ] **Dashboard Upgrade**: Daily Briefing 탭 추가.
*   [ ] **Mobile Optimization**: 모바일에서 리포트 가독성 확보.

### Phase 6: Full Autonomy Test (1/20 ~)
*   [ ] **Real Trading (Small cap)**: Shadow Trading에서 검증된 로직으로 소액 실거래 테스트.

---

## 📝 Summary
우리는 이제 "개발(Development)" 단계에서 "운용(Operation)" 단계로 진입하고 있습니다.
오늘의 핵심은 **"데이터의 진실성(Veracity)"**과 **"리포트의 유용성(Utility)"**을 확보하는 것입니다.
