# RAG Foundation - Implementation Tasks

## Task Breakdown (Phase 7.5 - 2 Weeks)

### Week 1: Infrastructure & Core Modules

#### Setup Phase (Day 1-2)

**Task 1.1: pgvector Extension Installation** [P]
- File: `docker-compose.yml`
- Description: Add pgvector to TimescaleDB container
- Steps:
  1. Update TimescaleDB Dockerfile to include pgvector
  2. Add pgvector extension creation to init script
  3. Test extension availability
- Test: `SELECT * FROM pg_extension WHERE extname = 'vector';`
- Estimated: 2 hours

**Task 1.2: Database Schema Creation** [Sequential to 1.1]
- File: `backend/alembic/versions/xxx_add_vector_store.py`
- Description: Create document_embeddings and embedding_costs tables
- Steps:
  1. Generate Alembic migration
  2. Add document_embeddings table with vector column
  3. Create IVFFlat index
  4. Add embedding_costs table
- Test: Run migration, verify hypertables created
- Estimated: 3 hours

**Task 1.3: Environment Configuration** [P]
- File: `backend/.env.example`, `backend/config/settings.py`
- Description: Add OpenAI API key configuration
- Steps:
  1. Add OPENAI_API_KEY to .env.example
  2. Update Settings class to load OpenAI key
  3. Add embedding model configuration
- Test: Load settings, verify key present
- Estimated: 1 hour

#### Core Development (Day 3-5)

**Task 1.4: DocumentEmbedder Implementation** [Sequential to 1.3]
- File: `backend/data/vector_store/embedder.py`
- Description: OpenAI Embedding API wrapper
- Steps:
  1. Create DocumentEmbedder class
  2. Implement embed_text() method
  3. Implement embed_batch() with rate limiting
  4. Add cost calculation
  5. Add content hashing for deduplication
- Test: Unit tests for embedding API
- Estimated: 4 hours

**Task 1.5: TextChunker Implementation** [P]
- File: `backend/data/vector_store/chunker.py`
- Description: Document chunking logic
- Steps:
  1. Create TextChunker class
  2. Implement chunk_by_tokens() method
  3. Implement chunk_by_sections() for SEC filings
  4. Add overlap handling
- Test: Unit tests for chunking logic
- Estimated: 3 hours

**Task 1.6: VectorStore Implementation** [Sequential to 1.2, 1.4]
- File: `backend/data/vector_store/store.py`
- Description: TimescaleDB + pgvector interface
- Steps:
  1. Create VectorStore class
  2. Implement add_document() method
  3. Implement search_similar() with filters
  4. Add deduplication logic
  5. Add cost tracking integration
- Test: Integration tests for CRUD + search
- Estimated: 6 hours

**Task 1.7: AutoTagger Implementation** [Sequential to 1.3]
- File: `backend/data/vector_store/tagger.py`
- Description: AI-powered automatic tag generation
- Steps:
  1. Create AutoTagger class
  2. Implement rule-based ticker extraction
  3. Implement AI-based sector classification (Claude Haiku)
  4. Implement topic keyword matching
  5. Implement entity extraction (NER)
  6. Add confidence scoring
- Test: Unit tests for tag generation
- Estimated: 4 hours

**Task 1.8: CostTracker Implementation** [P]
- File: `backend/data/vector_store/cost_tracker.py`
- Description: Embedding cost monitoring
- Steps:
  1. Create CostTracker class
  2. Implement track_cost() method
  3. Add daily/monthly aggregation queries
  4. Add budget alert logic
- Test: Unit tests for cost calculation
- Estimated: 2 hours

#### Testing (Day 6-7)

**Task 1.9: Unit Tests** [Sequential to 1.4-1.8]
- File: `backend/tests/test_vector_store.py`
- Description: Comprehensive unit test suite
- Steps:
  1. Test DocumentEmbedder.embed_text()
  2. Test DocumentEmbedder.embed_batch()
  3. Test TextChunker.chunk_by_tokens()
  4. Test AutoTagger.generate_tags()
  5. Test VectorStore.add_document() with auto-tagging
  6. Test VectorStore.search_similar() with tag filters
  7. Test VectorStore.find_related_tickers()
  8. Test incremental update logic
  9. Test cost tracking
- Coverage: > 90%
- Estimated: 5 hours

**Task 1.10: Performance Benchmarks** [Sequential to 1.6]
- File: `backend/tests/benchmark_vector_search.py`
- Description: Measure search latency with tags
- Steps:
  1. Insert 1,000 test documents with tags
  2. Run 100 search queries (plain + tag-filtered)
  3. Measure p50, p95, p99 latency
  4. Verify tag filtering doesn't degrade performance
  5. Verify < 100ms p95
- Test: Performance report
- Estimated: 2 hours

---

### Week 2: Data Ingestion & Integration

#### Data Pipeline (Day 8-10)

**Task 2.1: SEC Filing Downloader Enhancement** [P]
- File: `backend/data/sec/edgar_api.py`
- Description: Add historical filing download
- Steps:
  1. Extend existing SECEdgarAPI class
  2. Add get_company_filings() method (10-year range)
  3. Add section extraction logic
  4. Add rate limiting (10 requests/second)
- Test: Download 10-K for AAPL 2020-2024
- Estimated: 3 hours

**Task 2.2: SEC Backfill Script with Incremental Updates** [Sequential to 2.1, 1.6, 1.7]
- File: `backend/scripts/backfill/embed_sec_filings.py`
- Description: Batch embedding with incremental update support
- Steps:
  1. Create backfill_sec_filings() function
  2. Add incremental update logic (check document_sync_status)
  3. Add progress tracking
  4. Add resume capability (for failures)
  5. Add cost reporting
  6. Integrate with VectorStore + AutoTagger
  7. Add daily_incremental_update() scheduler function
- Test: Embed 10 sample tickers, verify incremental mode skips existing docs
- Cost Target: Initial $0.50, Daily $0.0001
- Estimated: 6 hours

**Task 2.3: News Backfill Script** [P to 2.2]
- File: `backend/scripts/backfill/embed_news.py`
- Description: Embed historical news articles
- Steps:
  1. Use existing NewsAPI integration
  2. Download 1-year news for top 50 tickers
  3. Chunk and embed articles
  4. Track costs
- Test: Embed 100 news articles, verify deduplication
- Estimated: 3 hours

**Task 2.4: Market Regime Data Collection** [P to 2.2]
- File: `backend/scripts/backfill/embed_regimes.py`
- Description: Create regime snapshots from FRED data
- Steps:
  1. Download VIX, Fed Rate, CPI (1990-2024)
  2. Create monthly regime snapshots
  3. Label regimes (BULL, BEAR, CRISIS, RECOVERY)
  4. Embed regime descriptions
- Test: 408 months × 1 regime = 408 embeddings
- Estimated: 4 hours

#### Integration (Day 11-13)

**Task 2.5: NonStandardRiskFactor RAG Integration** [Sequential to 1.6]
- File: `backend/data/features/non_standard_risk.py`
- Description: Add vector search to risk analysis
- Steps:
  1. Add VectorStore dependency injection
  2. Modify calculate() method to use RAG
  3. Implement _analyze_historical_impact() helper
  4. Add similar_events to response
- Test: Calculate risk for ticker with known lawsuit, verify similar cases found
- Estimated: 3 hours

**Task 2.6: ChatGPTStrategy RAG Integration** [Sequential to 1.6]
- File: `backend/ai/strategies/chatgpt_strategy.py`
- Description: Add regime memory to market detection
- Steps:
  1. Add VectorStore dependency injection
  2. Create detect_regime_with_memory() method
  3. Search similar historical regimes
  4. Weight by similarity scores
- Test: Detect regime for simulated 2008 conditions
- Estimated: 3 hours

**Task 2.7: RAG Retriever Module** [Sequential to 1.6]
- File: `backend/ai/rag/retriever.py`
- Description: Generic RAG retrieval interface
- Steps:
  1. Create RAGRetriever class
  2. Implement retrieve() method with caching
  3. Add context augmentation logic
  4. Add explainability (return sources)
- Test: Retrieve context for sample query
- Estimated: 4 hours

**Task 2.8: API Endpoints** [Sequential to 1.6]
- File: `backend/api/routes/vector_search.py`
- Description: REST API for vector search with tag filtering
- Steps:
  1. POST /api/v1/vector/search (similarity search with tag filters)
  2. POST /api/v1/vector/embed (embed text)
  3. GET /api/v1/vector/stats (cost tracking)
  4. GET /api/v1/vector/tags/{ticker} (get all tags for ticker)
  5. GET /api/v1/vector/related/{ticker} (find related tickers)
  6. POST /api/v1/vector/incremental-update (trigger daily update)
  7. Add authentication
- Test: Integration tests for all endpoints
- Estimated: 4 hours

#### Polish & Validation (Day 14)

**Task 2.9: Monitoring Dashboard** [Sequential to 1.7]
- File: `backend/monitoring/grafana_dashboards/rag.json`
- Description: Add RAG metrics to Grafana
- Steps:
  1. Create Prometheus metrics (embedding_api_calls, embedding_cost_usd)
  2. Add Grafana dashboard
  3. Add cost alert (>$0.10/day)
  4. Add latency panels
- Test: Generate test load, verify dashboard updates
- Estimated: 2 hours

**Task 2.10: Documentation** [Sequential to all]
- File: `docs/RAG_GUIDE.md`, `backend/README.md`
- Description: Comprehensive RAG documentation
- Steps:
  1. Create RAG_GUIDE.md with architecture
  2. Add usage examples
  3. Add cost optimization tips
  4. Update main README.md
- Estimated: 2 hours

**Task 2.11: Integration Testing** [Sequential to 2.5, 2.6]
- File: `backend/tests/test_rag_integration.py`
- Description: End-to-end RAG tests
- Steps:
  1. Test full risk analysis with RAG
  2. Test regime detection with memory
  3. Test cost tracking accuracy
  4. Test cache hit rates
- Coverage: Key user flows
- Estimated: 3 hours

**Task 2.12: Production Deployment** [Sequential to all]
- File: `deployment/README.md`
- Description: Deploy to production
- Steps:
  1. Run all migrations
  2. Start backfill script (background job)
  3. Enable RAG features via feature flags
  4. Monitor costs for 24 hours
- Test: Production smoke tests
- Estimated: 2 hours

---

## Task Dependencies Graph

```
Day 1-2 (Setup):
    1.1 (pgvector) ──→ 1.2 (schema)
    1.3 (config)

Day 3-5 (Core):
    1.2 ──→ 1.6 (VectorStore)
    1.3 ──→ 1.4 (Embedder) ──→ 1.6
    1.5 (Chunker)

Day 6-7 (Testing):
    1.4, 1.5, 1.6, 1.7 ──→ 1.8 (Unit Tests)
    1.6 ──→ 1.9 (Benchmarks)

Day 8-10 (Pipeline):
    2.1 (SEC API)
    2.1, 1.6 ──→ 2.2 (SEC Backfill)
    2.3 (News Backfill)
    2.4 (Regime Data)

Day 11-13 (Integration):
    1.6 ──→ 2.5 (Risk RAG)
    1.6 ──→ 2.6 (Regime RAG)
    1.6 ──→ 2.7 (Retriever)
    1.6 ──→ 2.8 (API)

Day 14 (Polish):
    1.7 ──→ 2.9 (Monitoring)
    ALL ──→ 2.10 (Docs)
    2.5, 2.6 ──→ 2.11 (Integration Tests)
    ALL ──→ 2.12 (Deploy)
```

---

## Effort Summary

| Phase | Tasks | Estimated Hours | Notes |
|-------|-------|-----------------|-------|
| Week 1 | 1.1 - 1.10 | 31 hours | Infrastructure + Core + AutoTagger |
| Week 2 | 2.1 - 2.12 | 35 hours | Pipeline + Incremental Updates + Integration |
| **Total** | **22 tasks** | **66 hours** | ~2 weeks (1 developer) |

---

## Risk Mitigation

| Risk | Task | Mitigation |
|------|------|------------|
| OpenAI API rate limit | 2.2 | Batch size limit (100 docs), exponential backoff |
| Cost overrun | All | Daily monitoring (Task 2.9), auto-stop at $1/month |
| pgvector performance | 1.6 | IVFFlat index tuning, VACUUM schedule |
| Long backfill time | 2.2 | Resume capability, run overnight |

---

## Success Criteria

### Week 1 Completion
- [ ] pgvector installed and tested
- [ ] VectorStore can add documents and search
- [ ] Unit test coverage > 90%
- [ ] Search latency p95 < 100ms

### Week 2 Completion
- [ ] 10 sample tickers embedded (5 years × 10 = 50 docs)
- [ ] RAG integrated into Risk + Regime modules
- [ ] Total cost < $0.50
- [ ] Integration tests passing

### Overall Phase 7.5 Success
- [ ] False positive reduction verified
- [ ] Monthly cost < $1.00
- [ ] Documentation complete
- [ ] Production deployment successful

---

**Created**: 2025-11-22
**Phase**: 7.5 (RAG Foundation)
**Status**: Ready for implementation
**Executor**: Claude Code + Human review
