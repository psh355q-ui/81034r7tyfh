# Multi-Modal Fusion v0.1 Specification

## 1. Objective
- **Goal**: Synthesize diverse signals (News, Price, Graph) into a single actionable "Trading Intent".
- **Philosophy**: "Context-aware Decision Making." (Don't just average scores; understand *when* to trust *what*).
- **Architecture**: **Gated Fusion** (Late Fusion backbone + Rule-based Gates).

## 2. Architecture Overview

### 2.1 The Fusion Pipeline
```text
[News Signal] --(w1)--> [Gate A] --+
                                    |
[Chart Signal] -(w2)--> [Gate B] --(+)--> [Final Intent Score] -> [Position Sizing] -> [Execution RL]
                                    |
[GNN Signal] ---(w3)--> [Gate C] --+
```

### 2.2 Principles
1.  **Explainability**: Every specific weight adjustment or gate closure must be traceable.
2.  **Safety First**: If signals conflict drastically under high volatility, default to "Neutral/Hold".
3.  **Separation of Execution**: Fusion determines "What & How Much" (Intent). Execution RL determines "How" (Execution).

## 3. Gate Definitions (MVP)

### Gate 1: Liquidity Gate (Chart Validity)
Prevents technical analysis from acting on illiquid/manipulated price movements.
- **Input**: User-defined `MinVolume` or `MinTurnover`.
- **Logic**:
  ```python
  if current_volume < threshold:
      chart_weight = 0.0  # Ignore technicals
  else:
      chart_weight = 1.0  # Normal weight
  ```

### Gate 2: GNN Confidence Gate (Graph Validity)
Prevents weak correlations from influencing the decision.
- **Input**: GNN `ImpactScore` and `EdgeConfidence`.
- **Logic**:
  ```python
  if gnn_impact < epsilon:
      gnn_weight = 0.0
  else:
      gnn_weight = alpha * log(impact)
  ```

### Gate 3: Event Priority Gate (News Dominance)
Ensures breaking news overrides technical indicators (The "News First" Principle).
- **Input**: News `ImportanceScore` (from LLM).
- **Logic**:
  ```python
  if news_importance > HIGH_THRESHOLD:
      chart_weight *= 0.5   # Dampen value of lagging indicators
      news_weight *= 1.5    # Amplify relevant news
  ```

## 4. Output Structure: Trading Intent
The output of the Fusion layer is NOT a direct order, but an Intent passed to the Portfolio/Risk Manager.

```json
{
  "ticker": "AAPL",
  "direction": "BUY",
  "confidence": 0.85,
  "rationale": {
    "news": "+0.8 (Strong Earnings)",
    "chart": "-0.2 (Overbought, but dampened by Event Gate)",
    "gnn": "+0.1 (Sector rally)"
  },
  "gates_triggered": ["EventPriorityGate"],
  "recommended_size_adj": 1.0
}
```

## 5. Implementation Plan

### Phase 1: Base Weighted Sum (Late Fusion)
- [ ] Implement `SignalAggregator` class.
- [ ] Define standardized `Signal` interface (score: -1.0 to 1.0, confidence: 0.0 to 1.0).

### Phase 2: Logic Gates Implementation
- [ ] Implement `LiquidityGate`.
- [ ] Implement `EventPriorityGate` (requires News Importance from LLM layer).

### Phase 3: Integration
- [ ] Connect `NewsSignal`, `TechnicalSignal`, `GNNSignal` to Aggregator.
- [ ] Output `TradingIntent` object instead of raw score.

## 6. Q&A (Design Decisions)

### Q1. Rule-based vs Learning-based Gates?
- **Decision**: **Rule-based for v1 (First 3-6 months)**.
- **Reason**: To train a "Gating Network" (Matrix of specific weights), we need labeled ground truth of *which* signal was right in *which* context. We lack this dataset. We must manually encode expert intuition first, collect logs ("Gate Rejection Logs"), and then transition to ML gates later.

### Q2. GNN Impact: Position Size vs Sentiment Confidence?
- **Decision**: **Adjust Signal Confidence**.
- **Reason**: Position sizing belongs to the Risk Management layer (e.g., Kelly Criterion, Volatility Sizing). If GNN increases the composite *Confidence*, the Risk Manager will naturally allocate a larger position. Modifying position size directly in the Fusion layer breaks the Separation of Concerns and bypasses risk checks.

### Q3. Decision Reasoning Report Format?
- **Decision**: **Scorecard Attribution Model**.
- **Format**:
    ```markdown
    | Source | Raw Score | Weight | Gate | Contribution |
    |--------|-----------|--------|------|--------------|
    | News   | +0.90     | 1.5x   | OPEN | +1.35        |
    | Chart  | -0.40     | 0.5x   | DAMP | -0.20        |
    | GNN    | +0.20     | 1.0x   | OPEN | +0.20        |
    | **TOTAL**|         |        |      | **+1.35**    |
    ```
- **Benefit**: Instantly answers "Why did we buy despite the bad chart?" (Answer: News Priority Gate dampened the chart).
