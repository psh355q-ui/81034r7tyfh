# RAG Foundation - Historical Pattern Analysis System

## 1. Overview

AI 트레이딩 시스템에 RAG(Retrieval-Augmented Generation)를 통합하여 과거 패턴 학습 능력을 추가합니다. AI가 "오늘의 뉴스"만이 아닌 "20년 금융 역사"를 참고하여 투자 결정을 내리도록 개선합니다.

## 2. Goals

### Primary Goals
1. **SEC Filing Historical Analysis**: CEO 발언, 실적 발표 패턴 학습
2. **Risk Pattern Database**: 과거 리스크 이벤트 학습 및 조기 감지
3. **Market Regime Memory**: 과거 시장 위기 시기와 현재 비교

### Success Metrics
- False Positive 감소: 30% → 10%
- AI Conviction Score 향상: +15%p
- 리스크 조기 감지: 3일 → 1일
- 월 운영 비용: < $1.00

## 3. Features

### Feature 1: Document Vector Store
**Description**: SEC 파일링, 뉴스, 컨퍼런스콜을 벡터화하여 저장

**User Story**: 
```
As a Trading Agent
I want to search similar historical cases
So that I can predict outcomes based on past patterns
```

**Acceptance Criteria**:
- [ ] TimescaleDB에 pgvector 확장 설치
- [ ] document_embeddings 테이블 생성 (1536 차원 벡터)
- [ ] OpenAI text-embedding-3-small API 통합
- [ ] Cosine Similarity 기반 검색 (<100ms)
- [ ] 청크 분할 로직 (4000 토큰 단위)

### Feature 2: SEC Filing Embedder with Auto-Tagging
**Description**: 과거 10년치 SEC 파일링(10-K/10-Q)을 자동으로 임베딩하고 다차원 태그 생성

**User Story**:
```
As a System Administrator
I want to automatically embed historical SEC filings with smart tags
So that AI can learn from past CEO statements and find related stocks
```

**Acceptance Criteria**:
- [ ] SEC EDGAR API 통합 (이미 Phase 15에 존재)
- [ ] S&P 500 종목 10년치 10-K/10-Q 다운로드
- [ ] **자동 태그 생성 시스템**:
  - [ ] 티커별 태그 (AAPL, MSFT)
  - [ ] 섹터별 태그 (Technology, Healthcare)
  - [ ] 주제별 태그 (supply_chain, regulatory_risk, AI_adoption)
  - [ ] 엔티티 추출 (CEO names, product names, geographic regions)
- [ ] 배치 임베딩 파이프라인 (100 docs/hour)
- [ ] 중복 방지 메커니즘 (hash 기반)
- [ ] 진행률 추적 및 재시작 가능
- [ ] **증분 업데이트**: 마지막 업데이트 이후 신규 문서만 처리

### Feature 3: Risk Pattern Search
**Description**: 비정형 위험 팩터에 Vector Search 추가

**User Story**:
```
As a Trading Agent
I want to find similar past risk events
So that I can estimate potential impact
```

**Acceptance Criteria**:
- [ ] non_standard_risk.py에 vector_search() 메서드 추가
- [ ] "lawsuit", "investigation" 등 과거 케이스 학습
- [ ] 유사도 임계값 설정 (>0.85)
- [ ] 과거 주가 영향도 메타데이터 포함
- [ ] 캐싱 전략 (7일 TTL)

### Feature 4: Market Regime Memory
**Description**: ChatGPT Strategy에 과거 시장 체제 비교 기능 추가

**User Story**:
```
As a Trading Agent
I want to compare current market conditions with historical regimes
So that I can adjust portfolio strategy
```

**Acceptance Criteria**:
- [ ] FRED API 과거 경제 지표 수집 (VIX, Fed Rate, CPI)
- [ ] RegimeMemory 클래스 구현
- [ ] chatgpt_strategy.py 통합
- [ ] 유사 시기 Top 3 반환
- [ ] Regime 변화 감지 알림

### Feature 5: Embedding Cost Tracker
**Description**: OpenAI Embedding API 비용 추적 시스템

**User Story**:
```
As a System Administrator
I want to track embedding API costs
So that I can stay within $1/month budget
```

**Acceptance Criteria**:
- [ ] Prometheus 메트릭 추가 (embedding_api_calls, embedding_tokens)
- [ ] Grafana 대시보드 업데이트
- [ ] 일일 비용 알림 (>$0.10/day)
- [ ] 자동 배치 크기 조절 (비용 기반)

## 4. Non-Functional Requirements

### Performance
- Vector Search latency: < 100ms (p95)
- Embedding API latency: < 2s per request
- Batch embedding throughput: > 100 docs/hour
- Cache hit rate: > 90%

### Cost
- Monthly Embedding API cost: < $1.00
- Storage: Use existing TimescaleDB (no additional cost)
- Cache: Use existing Redis (no additional cost)

### Scalability
- Support 500+ tickers
- Store 10 years of historical data
- Handle 1000+ vector searches per day

### Reliability
- API failure retry: 3 attempts with exponential backoff
- Graceful degradation: Fall back to non-RAG analysis
- Data backup: Daily snapshot to S3-compatible storage

## 5. Technical Constraints

### Must Use
- ✅ TimescaleDB (already deployed)
- ✅ pgvector extension (free)
- ✅ OpenAI text-embedding-3-small ($0.02/1M tokens)
- ✅ Redis (already deployed)

### Must NOT Use
- ❌ Pinecone, Weaviate (expensive cloud vector DBs)
- ❌ Claude API for embeddings (too expensive)
- ❌ Custom embedding models (complexity)

## 6. Dependencies

### External APIs
- OpenAI Embeddings API (new)
- SEC EDGAR API (existing)
- FRED API (existing)

### Internal Modules
- `backend/data/feature_store/` (existing)
- `backend/ai/strategies/chatgpt_strategy.py` (existing)
- `backend/data/features/non_standard_risk.py` (existing)

## 7. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OpenAI API rate limit | Embedding 실패 | Medium | 배치 크기 제한 (20/min), 재시도 로직 |
| pgvector 성능 저하 | Search > 100ms | Low | IVFFlat 인덱스, 주기적 VACUUM |
| 저장 공간 부족 | 임베딩 실패 | Low | 1년 이상 데이터 자동 삭제 |
| 비용 초과 ($1/월) | 예산 초과 | Medium | 일일 모니터링, 자동 중단 |

## 8. Success Criteria

### Phase 7.5 완료 조건
- [ ] pgvector 설치 및 테스트 완료
- [ ] document_embeddings 테이블 생성
- [ ] OpenAI Embedding API 통합 및 테스트
- [ ] S&P 500 10종목 샘플 임베딩 완료
- [ ] Vector Search API 엔드포인트 구현
- [ ] 비용 추적 대시보드 추가
- [ ] 문서화 완료 (README.md 업데이트)

### Acceptance Test
```python
# Test 1: Embedding API
response = await embedder.embed_text("Tesla Q3 earnings miss")
assert len(response.embedding) == 1536
assert response.cost < 0.001  # < $0.001 per request

# Test 2: Vector Search
results = await vector_store.search_similar(
    query="CEO mentions temporary headwinds",
    top_k=5
)
assert len(results) == 5
assert results[0].similarity > 0.85
assert results[0].metadata["ticker"] is not None

# Test 3: Performance
start = time.time()
results = await vector_store.search_similar("lawsuit")
latency = time.time() - start
assert latency < 0.1  # < 100ms
```

## 9. Out of Scope (Phase 8 이후)

- ❌ Real-time embedding (모든 뉴스 즉시 임베딩)
- ❌ Multi-modal RAG (차트, 이미지 분석)
- ❌ Fine-tuning embedding models
- ❌ Hybrid search (keyword + vector)

## 10. References

- **Project Knowledge**: 251210_MASTER_GUIDE.md, PROJECT_STATUS_2025-11-09.md
- **pgvector Docs**: https://github.com/pgvector/pgvector
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **TimescaleDB Vectors**: https://www.timescale.com/blog/pgvector-vs-timescale-vector/

---

**Created**: 2025-11-22
**Phase**: 7.5 (RAG Foundation)
**Estimated Effort**: 2 weeks
**Budget**: $1.00/month
