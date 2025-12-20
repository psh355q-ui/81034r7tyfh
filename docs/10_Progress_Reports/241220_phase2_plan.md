# News Intelligence Phase 2 계획서

**날짜**: 2024년 12월 20일  
**버전**: 2.0  
**상태**: 계획 단계

---

## 📋 개요

Phase 1 (Gemini 실시간 검색)이 완료되었습니다. Phase 2에서는 통합 AI 분석 탭을 구현하여 모든 AI 분석 결과를 한곳에서 관리합니다.

---

## 🎯 Phase 2 목표

### 통합 AI 분석 탭
4가지 분석 타입을 하나의 탭에 통합:
1. **종목 분석** (/analysis)
2. **심층 추론** (/deep-reasoning)
3. **CEO 분석** (/ceo-analysis)  
4. **Gemini 검색** (현재)

---

## 📊 Phase 2 세부 계획

### Phase 2A: 탭 UI (우선순위: 높음)
**예상 시간**: 1시interval  
**목표**: Gemini 결과를 전용 탭에 표시

**작업 내용**:
- [ ] NewsAggregation에 탭 상태 추가
- [ ] 2탭 헤더 생성 (RSS / AI 분석)
- [ ] Tab 2에 Gemini 결과 표시
- [ ] 타임스탬프 포맷팅 (YYMMDD HHMMSS)
- [ ] 메타데이터 표시 (감정, 긴급도, 영향도)
- [ ] 관련 티커 칩으로 표시

**UI 구조**:
```
┌─────────────────────────────────────┐
│ 📰 뉴스 기사 (50)  │  🤖 AI 분석 (3)│
└─────────────────────────────────────┘

Tab 1: RSS 뉴스 (기존)
Tab 2: AI 분석 (신규)
  ├── Gemini 검색 결과
  ├── 종목 분석 결과
  ├── 심층 추론 결과
  └── CEO 분석 결과
```

---

### Phase 2B: 데이터베이스 저장 (우선순위: 중간)
**예상 시간**: 2시간  
**목표**: 분석 결과 영구 저장

**DB 스키마**:
```sql
CREATE TABLE ai_analysis_results (
    id SERIAL PRIMARY KEY,
    analysis_type VARCHAR(50),  -- 'stock', 'deep_reasoning', 'ceo', 'gemini_search'
    analyzed_at TIMESTAMP DEFAULT NOW(),
    ticker VARCHAR(10),
    
    -- 공통 필드
    sentiment FLOAT,  -- -1.0 ~ 1.0
    confidence FLOAT,  -- 0.0 ~ 1.0
    action VARCHAR(20),  -- BUY/SELL/HOLD/N/A
    summary TEXT,
    
    -- 타입별 데이터 (JSON)
    analysis_data JSONB,
    
    -- RAG용
    embedding VECTOR(1536)
);
```

**작업 내용**:
- [ ] AIAnalysisResult 모델 생성
- [ ] 마이그레이션 스크립트
- [ ] Gemini 결과 저장 로직
- [ ] GET /api/analysis/all 엔드포인트
- [ ] 프론트엔드에서 저장된 분석 로드
- [ ] 보관 정책 (예: 30일 후 삭제)

---

### Phase 2C: 분석 통합 (우선순위: 중간)
**예상 시간**: 3시간  
**목표**: 4가지 분석 타입 통합 표시

**작업 내용**:
- [ ] AnalysisCard 컴포넌트 생성
- [ ] 타입별 아이콘 및 색상
- [ ] 통합 메타데이터 표시
- [ ] 타입 필터 (Stock / Deep / CEO / Gemini)
- [ ] 티커 필터
- [ ] 날짜 범위 필터
- [ ] 상세보기 모달

**카드 예시**:
```tsx
┌──────────────────────────────────────┐
│ 🎯 [종목 분석]  📅 24.12.20 19:30   │
│                                      │
│ NVDA - 매수 추천                     │
│ 신뢰도: 85% | 목표가: $500          │
│ 근거: 강력한 실적, AI 수요 증가...   │
│                                      │
│ [상세보기] [관련 뉴스]               │
└──────────────────────────────────────┘
```

---

## 🔮 Phase 3: 고급 기능 (추후)

### 3A. 자동 태깅 (30분)
- 키워드 추출 (earnings, lawsuit 등)
- 패턴 매칭
- 태그 칩 표시
- 태그별 필터

### 3B. 임베딩 & RAG (2시간)
- OpenAI text-embedding-3-small 사용
- pgvector에 저장
- 의미 기반 검색 엔드포인트
- "관련 기사" 추천
- RAG Q&A

### 3C. 섹터 분석 (1시간)
- 회사-섹터 매핑
- 섹터 영향도 계산
- 섹터별 필터링
- 섹터 히트맵 시각화

---

## 📅 일정 계획

### 즉시 (다음 세션)
- **Week 1**: Phase 2A (탭 UI)
- **Week 1**: Phase 2B (DB 저장)

### 단기 (2주 이내)
- **Week 2**: Phase 2C (분석 통합)
- **Week 2**: 테스트 및 버그 수정

### 장기 (1개월 이내)
- **Week 3-4**: Phase 3 (고급 기능)

---

## 💰 비용 예측

### 현재
- Gemini: $0.00/일
- DB 저장: 무료 (로컬)
- **총계**: $0.00/일

### Phase 2 구현 후
- Gemini: $0.00/일 (실험 기간)
- DB 저장: 무료
- **총계**: $0.00/일

### Phase 3 구현 후 (미래)
- Gemini: ~$0.80/일 (20검색 x $0.04)
- OpenAI Embedding: ~$0.10/일
- DB: 무료
- **총계**: ~$0.90/일 (~$27/월)

---

## ⚠️ 위험 요소

### 기술적 위험
1. **JSX 구조 복잡도**
   - NewsAggregation.tsx 파일이 크고 복잡
   - 완화: 작은 단위로 나누어 수정

2. **DB 마이그레이션**
   - 기존 데이터와 충돌 가능성
   - 완화: 백업 후 진행

3. **성능**
   - 많은 분석 결과 로드 시 느려질 수 있음
   - 완화: 페이지네이션, 가상 스크롤

### 비용 위험
1. **Gemini 비용 증가**
   - 2026년 1월부터 유료
   - 완화: 사용량 제한, 캐싱

---

## 📊 성공 지표

### Phase 2A
- ✅ 탭 UI 작동
- ✅ Gemini 결과 표시
- ✅ 타임스탬프 정확

### Phase 2B
- ✅ DB 저장 성공
- ✅ 페이지 새로고침 후 데이터 유지
- ✅ 조회 API 작동

### Phase 2C
- ✅ 4가지 타입 모두 표시
- ✅ 필터 작동
- ✅ 상세보기 작동

---

## 🎯 다음 단계

1. NewsAggregation.tsx 파일 구조 리뷰
2. 탭 컴포넌트 분리 (if needed)
3. Phase 2A 구현 시작
4. 테스트 및 피드백

---

## 📝 참고 문서

- Phase 1 완료 보고: `241220_gemini_search_implementation.md`
- 구현 계획: `implementation_plan.md` (artifacts)
- 작업 목록: `task.md` (artifacts)
