# Execution RL v0.1 Specification

## 1. Objective
- **Goal**: Minmize execution cost compared to Arrival VWAP.
- **Philosophy**: "Do not create alpha, preserve alpha." (Execution only, no timing alpha creation).
- **Benchmark**: Traditional TWAP/VWAP execution algorithms.

## 2. State Definition (Observation Space)
The RL agent observes the following state variables at each time step `t`:

| Feature | Description | Rationale |
| :--- | :--- | :--- |
| `remaining_qty_ratio` | Remaining shares / Total order shares | Progress tracking. (1.0 -> 0.0) |
| `elapsed_time_ratio` | Elapsed time / Time limit | Time constraints awareness. (0.0 -> 1.0) |
| `tick_flow_10s` | (Buy Vol - Sell Vol) in last 10s | Immediate order flow imbalance proxy. |
| `tick_flow_30s` | (Buy Vol - Sell Vol) in last 30s | Short-term trend context. |
| `spread_proxy` | (Ask - Bid) / Mid Price (if available) or Volatility | Cost of aggressive execution. |

*Note: `tick_flow` uses transaction data (Ticks) as KIS API order book depth is limited/expensive.*

## 3. Action Space (Discrete)
The agent selects one action at each step:

| Action | Description | Behavior Mapping (KIS API) |
| :--- | :--- | :--- |
| `HOLD` | Wait, do nothing | No order submission. |
| `PASSIVE_BUY` | Limit order at Bid or Mid-price | `buy_limit_order(price=current_bid)` |
| `AGGRESSIVE_BUY` | Market order or Limit at Ask | `buy_market_order()` or `buy_limit_order(price=current_ask)` |

## 4. Reward Design
The reward function balances final execution quality and intermediate progress.

### 4.1 Main Reward (Terminal) - 80-90% Weight
Given at the end of the order execution.
$$ R_{main} = \frac{VWAP_{arrival} - P_{avg\_fill}}{VWAP_{arrival}} \times 100 $$
- Positive if filled price is lower (better) than Arrival VWAP.
- Negative if worse.

### 4.2 Auxiliary Reward (Step-based) - 10-20% Weight
Given at each fill event.
$$ R_{aux} = \frac{P_{market\_at\_step} - P_{fill}}{P_{market\_at\_step}} \times 10 $$
- Encourages "buying the dip" relative to the current moment.
- Capped to prevent gaming.

## 5. Logging & Validation
To verify if the agent is learning meaningful behaviors ("Wait when expesive", "Buy when cheap").

- **Correlation Report**:
    - `tick_flow` vs `action_type`
    - Expectation:
        - `tick_flow` < 0 (Selling pressure) -> Higher `AGGRESSIVE_BUY` freq.
        - `tick_flow` > 0 (Buying pressure) -> Higher `HOLD` / `PASSIVE_BUY` freq.
- **Action Distribution**:
    - Histogram of actions under different market regimes.

## 6. Fail-safe Mechanism (State Machine)
Ensures system stability even if RL agent fails or behaves irrationally.

### 6.1 State Machine Structure
```text
[Execution Controller]
        |
        v
[Rule Layer Watchdog]
        |
        +-- OK --> [RL Executor]
        |
        +-- TRIGGER --> [Fallback Executor (TWAP)]
```

### 6.2 Trigger Conditions (Fallback)
The system switches to Fallback mode if **ANY** condition is met:
1. **Time/Fill Mismatch**: `elapsed_time_ratio > 0.9` AND `filled_qty_ratio < 0.5` (Too slow).
2. **Price Deviation**: `current_price > VWAP_arrival * 1.01` (Buying too high/expensive).
3. **Agent Error**: RL Model returns invalid action or exception.

### 6.3 Fallback Action
- Immediately terminate RL Agent execution.
- Log event: `RL_ABORTED`.
- Remaining quantity is executed via **Time-Weighted Average Price (TWAP)** algo or **Split Market Orders**.

## 7. Implementation Plan

### Phase 1: Infrastructure & Data
- [ ] Implement `TickFlow` calculator (using valid tick data).
- [ ] Implement `ArrivalVWAP` calculator.
- [ ] Setup `ShadowExecutor` for dry-run logging.

### Phase 2: RL Environment & Agent
- [ ] Define Gym-compatible Environment (`ExecutionEnv`).
- [ ] Implement PPO Agent (Stable Baselines 3 or custom).
- [ ] Integrate `AuxiliaryReward` logic.

### Phase 3: Fail-safe & Integration
- [ ] Implement `RuleLayerWatchdog`.
- [ ] Connect `FallbackExecutor` (existing `SmartExecutor` logic).
- [ ] Integration Test with Mock Data.

### Phase 4: Shadow Trading (A/B Test)
- [ ] Run `RL Executor` in Shadow Mode vs `TWAP`.
- [ ] Collect logs and analyze `tick_flow` correlation.

## 8. Q&A (Design Decisions)

### Q1. Architecture: Standalone Service vs Sub-strategy?
- **Decision**: **Sub-strategy of `SmartExecutor`**.
- **Reason**: `SmartExecutor` already handles the high-level workflow (Analyze -> Decide -> Execute). Execution RL is just a sophisticated "Execution Algorithm" (like TWAP/VWAP). Keeping it encapsulated within `SmartExecutor` or a new `RLExecutionEngine` maintains checking separation of concerns.

### Q2. Offline Learning Bias (Data Missing)?
- **Risk**: **Partial Fills & Latency**.
- **Reason**: Offline data assumes "Limit Order at Bid" fills immediately or never fills based on OHLC. In reality, queue position matters.
- **Mitigation**: Use aggressive fill simulation logic for offline training (e.g., "Limit filled only if price moves *through* the limit price").

### Q3. Sell Side RL Symmetry?
- **Decision**: **Symmetric Structure, Asymmetric Weights**.
- **Reason**: The fundamental logic (Wait for better price vs Urgent execution) is symmetric. However, panic selling (stop-loss) often requires much higher urgency/alpha-decay sensitivity than buying.
- **Action**: Use the same architecture but train a separate model (or distinct policy head) for Sell side.
