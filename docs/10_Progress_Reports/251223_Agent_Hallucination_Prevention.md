# Agent Hallucination Prevention Strategies

**Date**: 2025-12-23
**Status**: Design Phase
**Phase**: 24.6 (Anti-Hallucination Systems)

---

## 🎯 Objective

Extend each agent's self-learning system with **hallucination prevention** strategies to ensure:
1. **No overconfident predictions** (false certainty)
2. **No spurious pattern detection** (overfitting to noise)
3. **Statistical validation** of learned patterns
4. **Human-in-the-loop checkpoints** for extreme predictions
5. **Adversarial testing** to detect brittleness

**Key Insight**: AI that learns from every prediction can become overconfident or detect false patterns in noise. We must validate all learnings rigorously.

---

## 🧠 Hallucination Prevention by Agent

### 1. **NewsAgent** - Sentiment Analysis Expert

#### Original Self-Learning Strategy
```python
class NewsAgentLearning:
    def learn_source_credibility(self, source, predicted_sentiment, actual_market_move):
        # Tracks which sources are reliable
        correlation = calculate_correlation(predicted_sentiment, actual_market_move)
        self.source_credibility[source] = correlation
```

#### ⚠️ Hallucination Risk
- **Small sample size**: Source may look reliable after 3 lucky predictions
- **Confirmation bias**: Agent may overweight sources that confirm its existing beliefs
- **Spurious correlation**: News + market move correlation may be random

#### ✅ Anti-Hallucination Strategy: **Statistical Significance Gating**

```python
class NewsAgentLearning:
    MIN_SAMPLE_SIZE = 30  # Minimum predictions before trusting pattern
    MIN_P_VALUE = 0.05    # Statistical significance threshold

    def learn_source_credibility(self, source, predicted_sentiment, actual_market_move):
        # Track all predictions from this source
        self.source_history[source].append({
            "predicted_sentiment": predicted_sentiment,
            "actual_move": actual_market_move,
            "timestamp": datetime.now()
        })

        history = self.source_history[source]

        # GATE 1: Sample size check
        if len(history) < self.MIN_SAMPLE_SIZE:
            logger.warning(
                f"⚠️ Source {source} only has {len(history)} samples "
                f"(need {self.MIN_SAMPLE_SIZE}). Using default credibility."
            )
            return  # Don't update credibility yet

        # GATE 2: Statistical significance test
        correlation, p_value = pearsonr(
            [h["predicted_sentiment"] for h in history],
            [h["actual_move"] for h in history]
        )

        if p_value > self.MIN_P_VALUE:
            logger.warning(
                f"⚠️ Source {source} correlation not significant "
                f"(p={p_value:.3f}). Pattern may be noise."
            )
            # Apply conservative credibility
            self.source_credibility[source] = 0.5  # Neutral
        else:
            # Statistically validated pattern
            self.source_credibility[source] = abs(correlation)
            logger.info(
                f"✅ Source {source} credibility validated: {correlation:.2f} "
                f"(p={p_value:.4f}, n={len(history)})"
            )

        # GATE 3: Temporal stability check (pattern must hold over time)
        recent_30d = [h for h in history if (datetime.now() - h["timestamp"]).days <= 30]
        older_data = [h for h in history if (datetime.now() - h["timestamp"]).days > 30]

        if len(recent_30d) >= 10 and len(older_data) >= 10:
            recent_corr, _ = pearsonr(
                [h["predicted_sentiment"] for h in recent_30d],
                [h["actual_move"] for h in recent_30d]
            )
            older_corr, _ = pearsonr(
                [h["predicted_sentiment"] for h in older_data],
                [h["actual_move"] for h in older_data]
            )

            # Pattern must be stable across time periods
            if abs(recent_corr - older_corr) > 0.3:
                logger.warning(
                    f"⚠️ Source {source} correlation unstable over time "
                    f"(recent={recent_corr:.2f}, old={older_corr:.2f})"
                )
                # Use conservative average
                self.source_credibility[source] = (recent_corr + older_corr) / 2
```

**Key Protections**:
- ✅ No credibility updates until 30+ predictions
- ✅ Pattern must be statistically significant (p < 0.05)
- ✅ Pattern must be temporally stable (no sudden shifts)

---

### 2. **TraderAgent** - Technical Analysis Expert

#### Original Self-Learning Strategy
```python
class TraderAgentLearning:
    def optimize_indicator_weights(self, predicted_move, actual_move):
        # Adjusts RSI/MACD/Bollinger weights based on accuracy
        if prediction_was_correct:
            self.indicator_weights[best_indicator] += 0.05
```

#### ⚠️ Hallucination Risk
- **Overfitting**: Agent may overweight indicators that worked in last 5 trades (noise)
- **Regime change blindness**: Weights optimized for bull market fail in bear market
- **Look-ahead bias**: Backtest on same data used for optimization

#### ✅ Anti-Hallucination Strategy: **Walk-Forward Validation**

```python
class TraderAgentLearning:
    TRAIN_WINDOW = 90  # Days
    TEST_WINDOW = 30   # Days
    MIN_WIN_RATE = 0.55  # Minimum to beat random (50%)

    def optimize_indicator_weights(self):
        """
        Walk-forward optimization to prevent overfitting

        Train on 90 days → Test on next 30 days → Repeat
        Only use weights that beat 55% win rate on OUT-OF-SAMPLE test data
        """
        history = self.prediction_history[-120:]  # Last 120 days

        if len(history) < 120:
            logger.warning("⚠️ Insufficient data for walk-forward validation")
            return

        # Split into train/test
        train_data = history[:90]
        test_data = history[90:120]

        # Optimize weights on training data
        candidate_weights = self._grid_search_weights(train_data)

        # CRITICAL: Test on unseen data
        test_performance = self._backtest_weights(candidate_weights, test_data)

        # GATE 1: Out-of-sample win rate must beat random
        if test_performance["win_rate"] < self.MIN_WIN_RATE:
            logger.warning(
                f"⚠️ Optimized weights failed out-of-sample test: "
                f"{test_performance['win_rate']:.1%} < {self.MIN_WIN_RATE:.0%}. "
                f"Keeping current weights (may be overfitted)."
            )
            return  # Don't update weights

        # GATE 2: Ensemble check - weights must work across multiple regimes
        regimes = self._detect_market_regimes(train_data)  # bull/bear/sideways
        regime_performance = {}

        for regime in regimes:
            regime_data = [d for d in train_data if d["regime"] == regime]
            regime_perf = self._backtest_weights(candidate_weights, regime_data)
            regime_performance[regime] = regime_perf["win_rate"]

        # Weights must work in ALL regimes (no single-regime overfitting)
        if any(wr < 0.52 for wr in regime_performance.values()):
            logger.warning(
                f"⚠️ Weights fail in some regimes: {regime_performance}. "
                f"Applying conservative ensemble."
            )
            # Use equal weights instead of optimized (safer)
            candidate_weights = {ind: 1.0 / len(self.indicators) for ind in self.indicators}

        # GATE 3: Stability check - new weights can't be radically different
        max_weight_change = max(
            abs(candidate_weights[ind] - self.current_weights[ind])
            for ind in self.indicators
        )

        if max_weight_change > 0.30:
            logger.warning(
                f"⚠️ Weight change too large ({max_weight_change:.1%}). "
                f"Applying gradual update instead of full jump."
            )
            # Smooth transition: 70% old + 30% new
            self.indicator_weights = {
                ind: 0.7 * self.current_weights[ind] + 0.3 * candidate_weights[ind]
                for ind in self.indicators
            }
        else:
            # Safe to update
            self.indicator_weights = candidate_weights
            logger.info(
                f"✅ Weights updated (out-of-sample: {test_performance['win_rate']:.1%})"
            )
```

**Key Protections**:
- ✅ Walk-forward validation (train on past, test on future)
- ✅ Out-of-sample win rate must beat 55%
- ✅ Weights must work across all market regimes
- ✅ Gradual weight updates (no sudden jumps)

---

### 3. **RiskAgent** - Risk Management Expert

#### Original Self-Learning Strategy
```python
class RiskAgentLearning:
    def calibrate_var_model(self, predicted_var_95, actual_max_drawdown):
        # Adjusts VaR confidence level if predictions are off
        error = actual_max_drawdown - predicted_var_95
        self.var_multiplier += error * 0.01
```

#### ⚠️ Hallucination Risk
- **Underestimating tail risk**: VaR calibrated on normal times fails in black swans
- **False confidence**: 95% VaR looks good until the 1-in-20 event happens
- **Recency bias**: Recent calm markets → agent lowers risk estimates

#### ✅ Anti-Hallucination Strategy: **Stress Testing + Adversarial Scenarios**

```python
class RiskAgentLearning:
    STRESS_SCENARIOS = [
        {"name": "COVID-like crash", "max_drawdown": -0.35, "duration_days": 30},
        {"name": "2008 Financial Crisis", "max_drawdown": -0.50, "duration_days": 180},
        {"name": "Flash Crash", "max_drawdown": -0.10, "duration_days": 1},
        {"name": "Dot-com Bubble", "max_drawdown": -0.78, "duration_days": 900},
    ]

    def calibrate_var_model(self, predicted_var_95, actual_max_drawdown):
        # GATE 1: Don't trust VaR from calm periods
        recent_90d = self.market_history[-90:]
        max_volatility_90d = max(d["volatility"] for d in recent_90d)

        if max_volatility_90d < 0.15:  # Very calm (VIX-like < 15)
            logger.warning(
                f"⚠️ Market too calm (vol={max_volatility_90d:.1%}). "
                f"VaR calibration may underestimate tail risk. "
                f"Applying stress-test floor."
            )
            # Don't lower VaR during calm times (prevents complacency)
            if self.var_multiplier < 1.0:
                self.var_multiplier = 1.0

        # GATE 2: Adversarial stress testing
        # Simulate VaR model performance in historical crashes
        stress_test_results = {}

        for scenario in self.STRESS_SCENARIOS:
            # Would our current VaR model have protected us?
            predicted_var = self.current_var_model.predict(scenario["inputs"])
            actual_loss = scenario["max_drawdown"]

            coverage = (predicted_var < actual_loss)  # VaR should be MORE negative
            stress_test_results[scenario["name"]] = {
                "predicted_var": predicted_var,
                "actual_loss": actual_loss,
                "covered": coverage
            }

        # VaR must work in at least 3/4 stress scenarios
        coverage_rate = sum(1 for r in stress_test_results.values() if r["covered"]) / len(self.STRESS_SCENARIOS)

        if coverage_rate < 0.75:
            logger.error(
                f"⚠️ VaR model FAILS stress tests ({coverage_rate:.0%} coverage). "
                f"Forcing conservative floor."
            )
            # Force worst-case VaR from stress scenarios
            worst_case_var = min(s["max_drawdown"] for s in self.STRESS_SCENARIOS)
            self.var_floor = worst_case_var  # Never allow VaR better than -50%

        # GATE 3: Tail event counter
        # Track how often "impossible" events (>3 sigma) happen
        tail_events = [d for d in self.market_history if abs(d["return"]) > 3 * d["predicted_std"]]
        tail_event_rate = len(tail_events) / len(self.market_history)

        # If tail events happen >1% (should be 0.3% for normal distribution)
        if tail_event_rate > 0.01:
            logger.warning(
                f"⚠️ Tail events happening {tail_event_rate:.1%} of the time "
                f"(expected 0.3%). Market has fat tails. Increasing VaR buffer."
            )
            self.fat_tail_multiplier = 1.5  # 50% safety buffer
        else:
            self.fat_tail_multiplier = 1.0

        # Final VaR calculation with all safety factors
        self.calibrated_var = (
            self.base_var
            * self.var_multiplier
            * self.fat_tail_multiplier
        )
        self.calibrated_var = min(self.calibrated_var, self.var_floor)  # Floor

        logger.info(
            f"✅ VaR calibrated: {self.calibrated_var:.1%} "
            f"(stress coverage: {coverage_rate:.0%}, tail events: {tail_event_rate:.1%})"
        )
```

**Key Protections**:
- ✅ Don't calibrate VaR during calm periods (recency bias)
- ✅ Stress test against historical crashes
- ✅ Track tail event frequency (detect fat tails)
- ✅ Conservative floor based on worst-case scenarios

---

### 4. **MacroAgent** - Economic Analysis Expert

#### Original Self-Learning Strategy
```python
class MacroAgentLearning:
    def learn_indicator_lag_effects(self, gdp_release, market_reaction):
        # Learns how long after GDP release the market reacts
        lag_days = calculate_lag(gdp_release.date, market_reaction.peak_date)
        self.indicator_lags["GDP"] = lag_days
```

#### ⚠️ Hallucination Risk
- **Confounding variables**: GDP + Fed announcement same week → agent attributes all movement to GDP
- **Spurious causation**: Market moved 3 days after GDP, but correlation ≠ causation
- **Sample size**: Only 4 GDP releases per year → small sample

#### ✅ Anti-Hallucination Strategy: **Causal Inference + Confounding Control**

```python
class MacroAgentLearning:
    MIN_SAMPLES_PER_INDICATOR = 12  # At least 3 years of quarterly data

    def learn_indicator_lag_effects(self, indicator_name, releases):
        """
        Use causal inference to isolate indicator's true effect

        Controls for confounding variables:
        - Other macro releases in same week
        - Fed announcements
        - Earnings season
        - Geopolitical events
        """
        if len(releases) < self.MIN_SAMPLES_PER_INDICATOR:
            logger.warning(
                f"⚠️ Only {len(releases)} samples for {indicator_name}. "
                f"Need {self.MIN_SAMPLES_PER_INDICATOR}. Using default lag."
            )
            return

        # GATE 1: Confounding detection
        for release in releases:
            # Check for confounding events ±3 days
            confounders = self._detect_confounders(
                release.date,
                window_days=3,
                confounding_events=[
                    "FOMC_announcement",
                    "earnings_season",
                    "other_macro_release",
                    "geopolitical_shock"
                ]
            )

            release.confounders = confounders
            release.is_clean = (len(confounders) == 0)

        # Only learn from "clean" releases (no confounders)
        clean_releases = [r for r in releases if r.is_clean]

        if len(clean_releases) < 8:
            logger.warning(
                f"⚠️ Only {len(clean_releases)} clean samples for {indicator_name} "
                f"(after removing confounders). Pattern may be unreliable."
            )
            # Use all data but flag as low confidence
            self.indicator_confidence[indicator_name] = "LOW"
        else:
            self.indicator_confidence[indicator_name] = "HIGH"

        # GATE 2: Granger causality test
        # Does indicator PREDICT market moves, or just correlate?
        from statsmodels.tsa.stattools import grangercausalitytests

        # Prepare time series: [indicator values, market returns]
        indicator_series = [r.surprise for r in clean_releases]  # Actual - Expected
        market_returns = [r.market_reaction_7d for r in clean_releases]

        try:
            granger_result = grangercausalitytests(
                np.column_stack([market_returns, indicator_series]),
                maxlag=4,  # Test lags 1-4 quarters
                verbose=False
            )

            # Check if any lag has significant Granger causality (p < 0.05)
            significant_lags = [
                lag for lag in range(1, 5)
                if granger_result[lag][0]["ssr_ftest"][1] < 0.05  # p-value
            ]

            if not significant_lags:
                logger.warning(
                    f"⚠️ {indicator_name} fails Granger causality test. "
                    f"Correlation may be spurious (correlation ≠ causation)."
                )
                self.indicator_causal[indicator_name] = False
                # Don't update lag (use default)
                return
            else:
                # Use the lag with strongest Granger causality
                best_lag = min(
                    significant_lags,
                    key=lambda lag: granger_result[lag][0]["ssr_ftest"][1]  # Lowest p-value
                )
                self.indicator_lags[indicator_name] = best_lag
                self.indicator_causal[indicator_name] = True
                logger.info(
                    f"✅ {indicator_name} Granger-causal with lag={best_lag} quarters "
                    f"(p={granger_result[best_lag][0]['ssr_ftest'][1]:.4f})"
                )

        except Exception as e:
            logger.error(f"⚠️ Granger causality test failed for {indicator_name}: {e}")
            self.indicator_causal[indicator_name] = False

        # GATE 3: Cross-validation with hold-out test
        # Train on 2015-2020 → Test on 2021-2024
        train_releases = [r for r in clean_releases if r.date.year <= 2020]
        test_releases = [r for r in clean_releases if r.date.year > 2020]

        if len(test_releases) >= 4:
            # Learn lag from training data
            train_lag = self._calculate_lag(train_releases)

            # Test on hold-out data
            test_accuracy = self._test_lag_accuracy(test_lag, test_releases)

            if test_accuracy < 0.60:  # Must predict >60% of test cases correctly
                logger.warning(
                    f"⚠️ {indicator_name} lag fails out-of-sample test "
                    f"({test_accuracy:.0%} accuracy). May be overfit."
                )
                # Use ensemble of train/test lags
                self.indicator_lags[indicator_name] = (train_lag + self._calculate_lag(test_releases)) / 2
            else:
                logger.info(
                    f"✅ {indicator_name} lag validated on hold-out data ({test_accuracy:.0%})"
                )
```

**Key Protections**:
- ✅ Remove confounding events (Fed announcements, earnings)
- ✅ Granger causality test (correlation ≠ causation)
- ✅ Out-of-sample testing (train on past, test on recent)
- ✅ Minimum sample size enforcement

---

### 5. **InstitutionalAgent** - Dark Pool Expert

#### Original Self-Learning Strategy
```python
class InstitutionalAgentLearning:
    def learn_institution_credibility(self, institution, predicted_move, actual_move):
        # Tracks which institutions are "smart money"
        if prediction_matches_outcome:
            self.institution_credibility[institution] += 0.05
```

#### ⚠️ Hallucination Risk
- **Survivorship bias**: Only track successful institutions (ignore failed ones)
- **Random luck**: Institution may have 5 lucky predictions in a row
- **Insider trading detection**: High accuracy may indicate illegal activity (not skill)

#### ✅ Anti-Hallucination Strategy: **Ensemble Validation + Anomaly Detection**

```python
class InstitutionalAgentLearning:
    MIN_TRADES = 20  # Minimum trades before trusting pattern
    MAX_ACCURACY = 0.85  # If >85% accurate, flag as suspicious (possible insider)

    def learn_institution_credibility(self, institution, predicted_move, actual_move):
        # Track all institutional trades
        self.institution_history[institution].append({
            "predicted_move": predicted_move,
            "actual_move": actual_move,
            "timestamp": datetime.now()
        })

        history = self.institution_history[institution]

        # GATE 1: Sample size
        if len(history) < self.MIN_TRADES:
            logger.warning(
                f"⚠️ {institution} only has {len(history)} trades. "
                f"Need {self.MIN_TRADES} for credibility."
            )
            return

        # GATE 2: Accuracy vs random baseline
        accuracy = sum(
            1 for h in history
            if np.sign(h["predicted_move"]) == np.sign(h["actual_move"])
        ) / len(history)

        # Use bootstrap to test if accuracy is statistically significant
        bootstrap_accuracies = []
        for _ in range(1000):
            # Randomly shuffle actual_moves (null hypothesis: no predictive power)
            shuffled = random.sample([h["actual_move"] for h in history], len(history))
            bootstrap_acc = sum(
                1 for i, h in enumerate(history)
                if np.sign(h["predicted_move"]) == np.sign(shuffled[i])
            ) / len(history)
            bootstrap_accuracies.append(bootstrap_acc)

        p_value = sum(1 for ba in bootstrap_accuracies if ba >= accuracy) / 1000

        if p_value > 0.05:
            logger.warning(
                f"⚠️ {institution} accuracy ({accuracy:.0%}) not significant "
                f"(p={p_value:.3f}). May be random luck."
            )
            self.institution_credibility[institution] = 0.5  # Neutral
            return

        # GATE 3: Insider trading detection
        if accuracy > self.MAX_ACCURACY:
            logger.error(
                f"🚨 {institution} accuracy suspiciously high ({accuracy:.0%}). "
                f"Possible insider trading. Flagging for manual review."
            )
            self.institution_flags[institution] = "INSIDER_TRADING_SUSPECTED"

            # Report to compliance (in real system)
            self._report_to_compliance(institution, accuracy, history)

            # DO NOT use this institution's signals
            self.institution_credibility[institution] = 0.0
            return

        # GATE 4: Temporal consistency (no sudden skill changes)
        recent_50 = history[-50:]
        older_50 = history[-100:-50] if len(history) >= 100 else []

        if len(older_50) >= 20:
            recent_accuracy = sum(
                1 for h in recent_50
                if np.sign(h["predicted_move"]) == np.sign(h["actual_move"])
            ) / len(recent_50)

            older_accuracy = sum(
                1 for h in older_50
                if np.sign(h["predicted_move"]) == np.sign(h["actual_move"])
            ) / len(older_50)

            # Skill shouldn't suddenly change by >20%
            if abs(recent_accuracy - older_accuracy) > 0.20:
                logger.warning(
                    f"⚠️ {institution} accuracy unstable "
                    f"(recent={recent_accuracy:.0%}, old={older_accuracy:.0%}). "
                    f"Using conservative average."
                )
                accuracy = (recent_accuracy + older_accuracy) / 2

        # GATE 5: Ensemble check - institution must beat multiple benchmarks
        benchmarks = {
            "random": 0.50,
            "market_trend": self._calculate_trend_following_accuracy(history),
            "mean_reversion": self._calculate_mean_reversion_accuracy(history)
        }

        beats_all_benchmarks = all(accuracy > bench for bench in benchmarks.values())

        if not beats_all_benchmarks:
            logger.warning(
                f"⚠️ {institution} doesn't beat all benchmarks: {benchmarks}. "
                f"May be using simple strategy, not proprietary insight."
            )
            # Reduce credibility
            accuracy = accuracy * 0.8

        # Final credibility assignment
        self.institution_credibility[institution] = min(accuracy, self.MAX_ACCURACY)
        logger.info(
            f"✅ {institution} credibility: {accuracy:.0%} "
            f"(p={p_value:.4f}, n={len(history)})"
        )
```

**Key Protections**:
- ✅ Bootstrap significance testing (vs random)
- ✅ Insider trading detection (>85% accuracy flagged)
- ✅ Temporal consistency check
- ✅ Ensemble benchmark comparison
- ✅ Compliance reporting for suspicious activity

---

### 6. **AnalystAgent** - Earnings Analysis Expert

#### Original Self-Learning Strategy
```python
class AnalystAgentLearning:
    def optimize_metric_weights(self, predicted_beat_miss, actual_beat_miss):
        # Adjusts weights for P/E, revenue growth, margin, etc.
        if prediction_was_correct:
            self.metric_weights[best_metric] += 0.05
```

#### ⚠️ Hallucination Risk
- **Sector overfitting**: Weights optimized for tech stocks fail for energy stocks
- **Earnings season bias**: Patterns from Q4 holiday season don't generalize to Q2
- **Look-ahead bias**: Training on same data used for evaluation

#### ✅ Anti-Hallucination Strategy: **Sector-Aware Cross-Validation**

```python
class AnalystAgentLearning:
    SECTORS = ["Tech", "Finance", "Healthcare", "Energy", "Consumer", "Industrial"]
    MIN_SAMPLES_PER_SECTOR = 30

    def optimize_metric_weights(self):
        """
        Optimize weights separately for each sector

        Prevents overfitting to single sector's dynamics
        Uses cross-validation within each sector
        """
        all_predictions = self.prediction_history

        # GATE 1: Sector-specific optimization
        sector_weights = {}

        for sector in self.SECTORS:
            sector_predictions = [p for p in all_predictions if p["sector"] == sector]

            if len(sector_predictions) < self.MIN_SAMPLES_PER_SECTOR:
                logger.warning(
                    f"⚠️ Only {len(sector_predictions)} samples for {sector}. "
                    f"Using global weights."
                )
                sector_weights[sector] = self.global_weights.copy()
                continue

            # GATE 2: K-fold cross-validation (prevent overfitting)
            from sklearn.model_selection import KFold

            kfold = KFold(n_splits=5, shuffle=True, random_state=42)
            fold_accuracies = []

            for train_idx, test_idx in kfold.split(sector_predictions):
                train_data = [sector_predictions[i] for i in train_idx]
                test_data = [sector_predictions[i] for i in test_idx]

                # Train weights on this fold
                candidate_weights = self._optimize_weights_on_data(train_data)

                # Test on held-out fold
                test_accuracy = self._evaluate_weights(candidate_weights, test_data)
                fold_accuracies.append(test_accuracy)

            # Weights must perform consistently across all folds
            mean_accuracy = np.mean(fold_accuracies)
            std_accuracy = np.std(fold_accuracies)

            if std_accuracy > 0.15:  # High variance across folds = overfitting
                logger.warning(
                    f"⚠️ {sector} weights unstable across folds "
                    f"(mean={mean_accuracy:.0%}, std={std_accuracy:.0%}). "
                    f"Using regularized weights."
                )
                # Apply L2 regularization to prevent extreme weights
                candidate_weights = self._regularize_weights(candidate_weights, lambda_=0.1)

            if mean_accuracy < 0.55:  # Must beat random
                logger.warning(
                    f"⚠️ {sector} optimized weights fail cross-validation "
                    f"({mean_accuracy:.0%}). Using equal weights."
                )
                sector_weights[sector] = {metric: 1.0 / len(self.metrics) for metric in self.metrics}
            else:
                sector_weights[sector] = candidate_weights
                logger.info(
                    f"✅ {sector} weights optimized: {mean_accuracy:.0%} ± {std_accuracy:.0%}"
                )

        # GATE 3: Quarterly seasonality check
        # Weights must work in all quarters (Q1/Q2/Q3/Q4)
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        for sector in self.SECTORS:
            quarterly_accuracies = {}

            for quarter in quarters:
                quarter_predictions = [
                    p for p in all_predictions
                    if p["sector"] == sector and p["quarter"] == quarter
                ]

                if len(quarter_predictions) >= 8:
                    accuracy = self._evaluate_weights(
                        sector_weights[sector],
                        quarter_predictions
                    )
                    quarterly_accuracies[quarter] = accuracy

            # If any quarter has <50% accuracy, weights are overfitted
            if any(acc < 0.50 for acc in quarterly_accuracies.values()):
                logger.warning(
                    f"⚠️ {sector} weights fail in some quarters: {quarterly_accuracies}. "
                    f"Applying quarter-agnostic ensemble."
                )
                # Average weights across all quarters
                sector_weights[sector] = self._ensemble_weights_across_quarters(sector)

        # GATE 4: Metric importance stability
        # Top 3 metrics shouldn't change drastically over time
        recent_predictions = all_predictions[-100:]
        older_predictions = all_predictions[-200:-100] if len(all_predictions) >= 200 else []

        if len(older_predictions) >= 50:
            recent_weights = self._optimize_weights_on_data(recent_predictions)
            older_weights = self._optimize_weights_on_data(older_predictions)

            # Get top 3 metrics from each period
            recent_top3 = sorted(recent_weights.items(), key=lambda x: x[1], reverse=True)[:3]
            older_top3 = sorted(older_weights.items(), key=lambda x: x[1], reverse=True)[:3]

            # At least 2/3 top metrics should be the same
            recent_top_metrics = {m[0] for m in recent_top3}
            older_top_metrics = {m[0] for m in older_top3}
            overlap = len(recent_top_metrics & older_top_metrics)

            if overlap < 2:
                logger.warning(
                    f"⚠️ Top metrics changed drastically over time. "
                    f"Recent: {recent_top_metrics}, Old: {older_top_metrics}. "
                    f"Using stable long-term average."
                )
                # Use weights from all-time data (more stable)
                sector_weights = {
                    sector: self._optimize_weights_on_data(
                        [p for p in all_predictions if p["sector"] == sector]
                    )
                    for sector in self.SECTORS
                }

        # Store final weights
        self.sector_specific_weights = sector_weights
        logger.info("✅ All sector weights optimized with cross-validation")
```

**Key Protections**:
- ✅ Sector-specific weights (no overfitting to single industry)
- ✅ K-fold cross-validation (train/test split)
- ✅ Quarterly seasonality check (Q1/Q2/Q3/Q4 stability)
- ✅ Metric importance stability over time

---

## 🔄 Central Hallucination Prevention System

### AgentLearningOrchestrator (Enhanced)

```python
class AgentLearningOrchestrator:
    """
    Coordinates all agent learning + hallucination prevention
    """

    async def daily_learning_cycle(self):
        """
        Daily routine with hallucination checks
        """
        logger.info("🧠 Starting daily learning cycle")

        # 1. Collect yesterday's predictions
        yesterday_predictions = await self.collect_predictions()

        # 2. Fetch actual market outcomes
        actual_outcomes = await self.fetch_market_outcomes()

        # 3. Run agent-specific learning
        learning_reports = {}
        for agent_name, agent in self.agents.items():
            report = await agent.learn_from_outcomes(
                yesterday_predictions[agent_name],
                actual_outcomes
            )
            learning_reports[agent_name] = report

        # 4. HALLUCINATION DETECTION: Cross-agent validation
        await self._cross_agent_hallucination_check(learning_reports)

        # 5. HALLUCINATION DETECTION: Temporal consistency
        await self._temporal_consistency_check(learning_reports)

        # 6. HALLUCINATION DETECTION: Adversarial testing
        await self._adversarial_robustness_test()

        # 7. Generate summary report
        summary = self._generate_learning_summary(learning_reports)

        logger.info(f"✅ Daily learning complete: {summary}")
        return summary

    async def _cross_agent_hallucination_check(self, learning_reports):
        """
        If one agent suddenly has very different predictions from others,
        flag as potential hallucination
        """
        # Example: All agents say BUY except one says SELL with 95% confidence
        for ticker in self.tracked_tickers:
            predictions = {
                agent_name: report["predictions"].get(ticker)
                for agent_name, report in learning_reports.items()
            }

            # Count BUY/SELL/HOLD votes
            votes = [p["action"] for p in predictions.values() if p]
            if not votes:
                continue

            vote_counts = {action: votes.count(action) for action in ["BUY", "SELL", "HOLD"]}
            majority_vote = max(vote_counts, key=vote_counts.get)

            # Check for outliers
            for agent_name, prediction in predictions.items():
                if not prediction:
                    continue

                if prediction["action"] != majority_vote and prediction["confidence"] > 0.80:
                    logger.warning(
                        f"🚨 HALLUCINATION ALERT: {agent_name} has {prediction['action']} "
                        f"({prediction['confidence']:.0%}) for {ticker}, but majority says "
                        f"{majority_vote}. Flagging for review."
                    )

                    # Reduce confidence of outlier agent
                    self.agents[agent_name].apply_confidence_penalty(ticker, penalty=0.20)

    async def _temporal_consistency_check(self, learning_reports):
        """
        Agent's strategy shouldn't change drastically overnight
        """
        for agent_name, report in learning_reports.items():
            previous_weights = self.agent_weight_history[agent_name][-2] if len(self.agent_weight_history[agent_name]) >= 2 else None
            current_weights = report.get("updated_weights")

            if previous_weights and current_weights:
                # Calculate weight change magnitude
                weight_changes = [
                    abs(current_weights[k] - previous_weights[k])
                    for k in current_weights.keys()
                ]
                max_change = max(weight_changes)

                if max_change > 0.30:  # 30% change in one day
                    logger.warning(
                        f"🚨 HALLUCINATION ALERT: {agent_name} changed weights by "
                        f"{max_change:.0%} in one day. Possible overfitting to recent noise."
                    )

                    # Force gradual update instead
                    self.agents[agent_name].force_gradual_weight_update(
                        previous_weights,
                        current_weights,
                        alpha=0.3  # 30% new, 70% old
                    )

    async def _adversarial_robustness_test(self):
        """
        Monthly test: Feed agents synthetic adversarial scenarios
        to detect brittleness
        """
        if datetime.now().day != 1:  # Run on 1st of month
            return

        logger.info("🧪 Running monthly adversarial robustness test")

        adversarial_scenarios = [
            {
                "name": "Sudden sector rotation",
                "ticker": "NVDA",
                "fake_news": "Biden announces $1T renewable energy mandate",
                "expected_smart_response": "NEUTRAL (energy policy doesn't affect chips directly)"
            },
            {
                "name": "Fake earnings leak",
                "ticker": "GOOGL",
                "fake_earnings": {"revenue": 100e9, "eps": 2.50},  # Way too good
                "expected_smart_response": "FLAG_AS_SUSPICIOUS (numbers too perfect)"
            },
            {
                "name": "Coordinated institutional buying",
                "ticker": "TSLA",
                "fake_dark_pool": [
                    ("BlackRock", "BUY", 1e6),
                    ("Vanguard", "BUY", 1e6),
                    ("StateStreet", "BUY", 1e6),
                ],
                "expected_smart_response": "Check for confounding events before BUY"
            }
        ]

        for scenario in adversarial_scenarios:
            # Feed fake data to agents
            agent_responses = {}
            for agent_name, agent in self.agents.items():
                response = await agent.analyze_scenario(scenario)
                agent_responses[agent_name] = response

            # Check if agents fell for the trap
            for agent_name, response in agent_responses.items():
                if response["action"] != scenario["expected_smart_response"]:
                    logger.error(
                        f"🚨 {agent_name} FAILED adversarial test: {scenario['name']}. "
                        f"Responded {response['action']}, expected {scenario['expected_smart_response']}."
                    )

                    # Mark agent as brittle, reduce confidence
                    self.agent_robustness_scores[agent_name] -= 0.10
                else:
                    logger.info(f"✅ {agent_name} passed adversarial test: {scenario['name']}")

        logger.info("🧪 Adversarial testing complete")
```

---

## 📊 Hallucination Prevention Summary

| Agent | Primary Risk | Prevention Strategy | Key Protection |
|-------|-------------|-------------------|----------------|
| **NewsAgent** | Small sample bias | Statistical Significance Gating | p-value < 0.05, n ≥ 30 |
| **TraderAgent** | Overfitting indicators | Walk-Forward Validation | Out-of-sample win rate > 55% |
| **RiskAgent** | Underestimating tail risk | Stress Testing + Adversarial | VaR must work in 3/4 crisis scenarios |
| **MacroAgent** | Spurious causation | Causal Inference + Confounding Control | Granger causality test |
| **InstitutionalAgent** | Random luck / Insider trading | Ensemble Validation + Anomaly Detection | Bootstrap test, flag >85% accuracy |
| **AnalystAgent** | Sector overfitting | Sector-Aware Cross-Validation | K-fold, quarterly stability |

---

## 🎯 Implementation Checklist

### Phase 25.1: Anti-Hallucination Infrastructure
- [ ] Add statistical testing libraries (scipy, statsmodels)
- [ ] Create `HallucinationDetector` base class
- [ ] Implement bootstrap significance testing
- [ ] Implement Granger causality testing
- [ ] Create adversarial scenario generator

### Phase 25.2: Agent-Specific Implementation
- [ ] NewsAgent: Statistical significance gating
- [ ] TraderAgent: Walk-forward validation
- [ ] RiskAgent: Stress testing system
- [ ] MacroAgent: Confounding control
- [ ] InstitutionalAgent: Insider trading detection
- [ ] AnalystAgent: Sector-aware cross-validation

### Phase 25.3: Central Coordination
- [ ] AgentLearningOrchestrator: Cross-agent validation
- [ ] AgentLearningOrchestrator: Temporal consistency checks
- [ ] AgentLearningOrchestrator: Monthly adversarial testing
- [ ] Hallucination alert system (Slack/email notifications)

### Phase 25.4: Testing & Validation
- [ ] Unit tests for each hallucination prevention method
- [ ] Integration test: Run 30-day learning simulation
- [ ] Adversarial test suite: 20 trap scenarios
- [ ] Measure false positive rate (legit patterns flagged as hallucination)

---

## 📈 Expected Impact

### Before Anti-Hallucination
- ❌ Agent learns from 3 lucky predictions → overconfident
- ❌ VaR calibrated on calm markets → fails in crash
- ❌ Macro agent attributes causation to correlation
- ❌ Analyst overfits to tech sector → fails on energy stocks

### After Anti-Hallucination
- ✅ Minimum 30 samples + p < 0.05 required
- ✅ VaR stress-tested against historical crashes
- ✅ Granger causality ensures real predictive power
- ✅ Sector-specific weights prevent overfitting

**Result**: Agents learn conservatively, only trust statistically validated patterns, and remain robust to adversarial scenarios.

---

**Status**: ✅ **ANTI-HALLUCINATION DESIGN COMPLETE**
**Next Step**: Implement Phase 25.1 (Statistical testing infrastructure)
**Overall Progress**: 99% → **99.5%**

🛡️ **AI now learns safely with hallucination prevention!**
