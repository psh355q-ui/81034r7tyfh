# GNN Impact Analysis v0.1 Specification

## 1. Objective
- **Goal**: Quantify the "Ripple Effect" of news to related assets.
- **Philosophy**: "News hits the center first, then spreads." (Signal Amplification/Damping).
- **Benchmark**: Simple Sector Rotation or Correlation-based pairs trading.

## 2. Graph Definition

### 2.1 Nodes
- **Entities**: Stock Tickers (e.g., AAPL, NVDA, TSLA).
- **Features**: 
    - Recent Price Momentum (1h, 1d)
    - News Sentiment Score
    - Sector ID embedding

### 2.2 Edges (Hybrid Structure)
The graph combines dynamic news context with static knowledge.

| Edge Type | Source | Weight Calculation | Update freq |
| :--- | :--- | :--- | :--- |
| **Dynamic (Primary)** | News Co-occurrence | `Count(News both appeared) * Recency_Decay` | Real-time (Event-driven) |
| **Static (Filter)** | Knowledge Graph | `1.0` if in Supply Chain/Competitor list, else `0.0` | Daily/Weekly |
| **Correlation (Gate)** | Price Correlation | `Corr(30d)` (if < 0.3, set Dynamic Edge Weight to 0) | Daily |

**Edge Weight Formula:**
$$ W_{ij} = \text{Norm}(\text{NewsCount}_{ij}) \times \mathbb{I}(\text{Sector or KG Match}) \times \text{Gate}(\text{Correlation}_{ij}) $$

## 3. Propagation Logic (2-Hop + Decay)
Do not use full GCN/GAT training for MVP. Use simplistic "Signal Diffusion".

### 3.1 Diffusion Rule
- **Source Node ($S$)**: Impact = Original Signal Strength (e.g., Sentiment 0.8)
- **Hop 1 ($N_1$)**: $I_{N1} = I_S \times W_{S,N1} \times \text{DecayFactor (0.7)}$
- **Hop 2 ($N_2$)**: $I_{N2} = I_{N1} \times W_{N1,N2} \times \text{DecayFactor (0.4)}$
- **Hop 3+**: Ignored.

### 3.2 Output
- **Graph Impact Score ($G_i$)**: Aggregated impact from all connected source events.
- **Final Signal Adjustment**:
$$ \text{FinalSignal}_i = \text{BaseSignal}_i \times (1 + \alpha G_i) $$
*Where $\alpha$ is a sensitivity hyperparameter (e.g., 0.5).*

## 4. LLM Verification Layer (Noise Filter)
Before establishing a *strong* Dynamic Edge (> Threshold), call LLM to verify meaningfulness.

- **Trigger**: New high-weight edge detected between $A$ and $B$.
- **Prompt**: "News says A and B are related. Is this (1) Supply Chain/Partnership, (2) Theme/Sentiment, (3) Just a list? Return score 0.0-1.0."
- **Action**: Multiply Edge Weight by LLM Score.

## 5. Implementation Plan

### Phase 1: Dynamic Graph Builder
- [ ] Implement `NewsCooccurrenceBuilder` (Parse news -> Extract Tickers -> Edge List).
- [ ] Implement `CorrelationGate` (Fetch price history -> Calculate Corr -> Mask Edges).

### Phase 2: Propagation Engine
- [ ] Implement BFS-based `SignalDiffuser`.
- [ ] Apply Decay Logic (Fixed 0.5 for MVP).

### Phase 3: Integration
- [ ] Integrate into `SignalGenerator`.
- [ ] Visualizer: "Why did I buy B?" -> Show "Because A had news (link)".

## 6. Q&A (Design Decisions)

### Q1. Decay: Fixed vs Dynamic?
- **Decision**: **Fixed (0.5) for MVP**.
- **Reason**: Dynamic decay based on volatility is valid (High Vol -> Low Trust), but adds complexity. v0.1 should focus on establishing the *pipeline* of propagation.
- **Future**: $Decay = \frac{k}{\text{MarketVol}}$.

### Q2. Asymmetric Hop Limits (Large vs Small Cap)?
- **Decision**: **Symmetric (2-Hop) for simple MVP**.
- **Reason**: While Large Caps influence Small Caps more, hardcoding directionality makes the graph rigid. Let the *News Co-occurrence* naturally filter this (Small caps are rarely mentioned *with* Large caps unless relevant, but Large caps are mentioned with everyone).

### Q3. Non-News Events (Earnings)?
- **Decision**: **Treat as High-Impact News Node**.
- **Reason**: Earnings, Guidance, and Fed Announcements are just nodes with very high initial `Impact` scores (e.g., 2.0 vs 0.5 normally). No separate graph needed.
