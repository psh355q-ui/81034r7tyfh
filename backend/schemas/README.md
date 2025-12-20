# Schemas Package - Phase 0 Foundation

**작성일**: 2025-12-03
**Phase**: 0 (Foundation)
**목적**: 모든 AI 모듈의 공통 데이터 구조 통일

---

## 📋 개요

Phase 0에서는 GPT의 권장사항에 따라 모든 모듈이 공유하는 BaseSchema를 먼저 정의했습니다.
이를 통해 Phase A 이후 모듈 간 데이터 통합이 원활하게 이루어집니다.

---

## 📦 스키마 구조

### 1. AI 칩 관련 스키마

#### `ChipInfo`
GPU/TPU/ASIC 정보 표현

```python
ChipInfo(
    model="NVIDIA H100",
    vendor="NVIDIA",
    process_node="4nm",
    perf_tflops=1979.0,
    tdp_watts=700.0,
    efficiency_score=0.92,
    segment="training"
)
```

**Usage**: `unit_economics_engine`, `chip_efficiency_comparator`

---

### 2. 공급망 관계 스키마

#### `SupplyChainEdge`
회사 간 관계 표현 (공급/경쟁/파트너 등)

```python
SupplyChainEdge(
    source="TSM",
    target="NVDA",
    relation=RelationType.SUPPLIER,
    confidence=0.98
)
```

**Usage**: `ai_value_chain_graph`

---

### 3. 경제성 스키마

#### `UnitEconomics`
단위 경제학 메트릭 (토큰당 비용, TCO 등)

```python
UnitEconomics(
    token_cost=1.2e-8,
    tco_monthly=1250.0,
    lifetime_tokens=2.5e12
)
```

**Usage**: `unit_economics_engine` 출력

---

### 4. 뉴스 분석 스키마

#### `NewsFeatures`
뉴스 특성 및 분류 결과

```python
NewsFeatures(
    headline="NVIDIA Blackwell breaks records",
    segment=MarketSegment.TRAINING,
    sentiment=0.85,
    keywords=["blackwell", "training"],
    tickers_mentioned=["NVDA", "TSM"]
)
```

**Usage**: `news_segment_classifier` 출력

---

### 5. 정책 리스크 스키마

#### `PolicyRisk`
정책 이벤트 리스크 지수 (PERI: 0~100)

```python
PolicyRisk(
    fed_conflict_score=0.45,
    successor_signal_score=0.30,
    gov_fed_tension_score=0.60,
    # ... PERI 자동 계산됨
    peri=40.5  # 0~100 스케일
)
```

**Usage**: `peri_calculator` 출력 (Phase B4)

**핵심 기능**: 6개 하위 점수 입력 시 PERI 자동 계산

---

### 6. 통합 컨텍스트 스키마

#### `MarketContext`
모든 AI 모듈의 공통 입출력 구조

```python
MarketContext(
    ticker="NVDA",
    company_name="NVIDIA",
    chip_info=[...],           # ChipInfo 리스트
    supply_chain=[...],        # SupplyChainEdge 리스트
    unit_economics=...,        # UnitEconomics
    news=...,                  # NewsFeatures
    policy_risk=...,           # PolicyRisk
    market_regime=MarketRegime.BULL
)
```

**Usage**:
- **Ingestion Layer**: 원시 데이터 → MarketContext 변환
- **Reasoning Layer**: MarketContext 기반 AI 분석
- **Signal Layer**: MarketContext → 매매 신호 변환

---

### 7. Multi-AI 입력 스키마

#### `MultimodelInput`
3개 AI 모델의 동일 스키마 기반 입력

```python
MultimodelInput(
    claude_context=context,      # Claude용 컨텍스트
    chatgpt_context=context,     # ChatGPT용 컨텍스트
    gemini_context=context,      # Gemini용 컨텍스트
    ensemble_weights={
        "claude": 0.5,
        "chatgpt": 0.3,
        "gemini": 0.2
    }
)
```

**Usage**: Phase A5 `DeepReasoningStrategy` Ensemble

---

### 8. 투자 시그널 스키마

#### `InvestmentSignal`
최종 매매 신호

```python
InvestmentSignal(
    ticker="NVDA",
    action=SignalAction.BUY,
    confidence=0.9,
    reasoning="Training market leader",
    position_size=0.2,
    metadata={
        "segment": "training",
        "hidden_beneficiaries": ["TSM", "AVGO"]
    }
)
```

**Usage**: `DeepReasoningStrategy` 최종 출력

---

## ✅ 검증 완료

### 테스트 결과 (2025-12-03)

```
✓ Imports                    [PASS]
✓ ChipInfo                   [PASS]
✓ PolicyRisk                 [PASS]
✓ MarketContext              [PASS]
✓ Full Pipeline              [PASS]
✓ JSON Serialization         [PASS]

Total: 6 tests | Passed: 6 | Failed: 0
```

### 검증된 기능

1. **Import**: 모든 스키마 정상 임포트
2. **ChipInfo**: NVIDIA H100, Google TPU 생성 성공
3. **PolicyRisk**: PERI 자동 계산 (40.50) 정확
4. **MarketContext**: 통합 컨텍스트 생성 성공
5. **Full Pipeline**: 뉴스 → 컨텍스트 → 시그널 전체 파이프라인 동작
6. **JSON**: 직렬화/역직렬화 정상 작동

---

## 🔗 연관 Phase

### Phase A: AI 칩 분석 (12일)
BaseSchema를 활용하는 첫 번째 단계

**통합 예정 모듈**:
- `unit_economics_engine.py` → `backend/ai/economics/`
- `chip_efficiency_comparator.py` → `backend/ai/economics/`
- `ai_value_chain.py` → `backend/data/knowledge/`
- `news_segment_classifier.py` → `backend/ai/news/`
- `deep_reasoning_strategy.py` → `backend/ai/strategies/`

---

## 📚 참조 문서

- [MASTER_INTEGRATION_ROADMAP_v5.md](../../MASTER_INTEGRATION_ROADMAP_v5.md)
- [DEVELOPMENT_PREPARATION_REPORT.md](../../DEVELOPMENT_PREPARATION_REPORT.md)

---

## 🎯 다음 단계

### Phase A 준비

```bash
# Downloads 코드를 backend로 이동
cp d:/code/downloads/unit_economics_engine.py backend/ai/economics/
cp d:/code/downloads/chip_efficiency_comparator.py backend/ai/economics/
cp d:/code/downloads/ai_value_chain.py backend/data/knowledge/
cp d:/code/downloads/news_segment_classifier.py backend/ai/news/
cp d:/code/downloads/deep_reasoning_strategy.py backend/ai/strategies/

# Import 경로 수정
# BaseSchema 적용
```

---

**Phase 0 완료 상태**: ✅ 검증 완료
**다음 작업**: Phase A (AI 칩 분석 시스템 통합)
