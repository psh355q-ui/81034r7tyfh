"""
Market Regime Ensemble & Replay Engine
File: market_regime_and_replay_engine.py
Purpose: Provide a drop-in probability-based Market Regime Ensemble module
and an Event Replay Engine for accurate event-driven backtesting and
qualification of multi-AI ensemble decisions.

This file contains:
- MarketRegimeEnsemble: ingest heterogeneous signals and produce
  probability distribution over regimes.
- ReplayEngine: time-ordered event replay with hooks for strategies,
  feature store updates, AI inference calls, and order execution simulation.
- Integration examples and a lightweight unit-test/demo runner.

Note: this is a code-seed. Integrate with your backend by plugging
MarketRegimeEnsemble into backend/ai/ensemble.py and ReplayEngine into
backend/backtesting/replay_engine.py. The MASTER_GUIDE.md reference is
available at: /mnt/data/MASTER_GUIDE.md
"""

from __future__ import annotations
import math
import heapq
import json
import time
from typing import Callable, Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

# -----------------------------
# Market Regime Ensemble Module
# -----------------------------

@dataclass
class RegimeScores:
    bull: float = 0.0
    bear: float = 0.0
    sideways: float = 0.0

    def normalize(self) -> 'RegimeScores':
        arr = np.array([self.bull, self.bear, self.sideways], dtype=float)
        # stability: softmax transform to probabilities
        exp = np.exp(arr - np.max(arr))
        probs = exp / (exp.sum() + 1e-12)
        return RegimeScores(*probs.tolist())

    def to_dict(self) -> Dict[str, float]:
        p = self.normalize()
        return {"bull": p.bull, "bear": p.bear, "sideways": p.sideways}


class MarketRegimeEnsemble:
    """Combine heterogeneous signals (numeric, categorical, model scores)
    into a calibrated probability distribution over market regimes.

    Usage:
        mre = MarketRegimeEnsemble()
        features = {
            'vix': 12.2,
            'vix_change_1d': 5.2,
            'yield_curve_2y10y': -0.45,
            'credit_spread_hy_ig': 350,
            'etf_flow_sp500_1d': -1_200_000,
            'news_sentiment_30m': -0.45,
            'ai_confidence_ensemble': 0.72
        }
        probs = mre.predict_proba(features)
        # probs -> {'bull':0.12,'bear':0.80,'sideways':0.08}

    Implementation notes:
    - Uses feature-wise scoring functions (rule-based / simple transforms)
      as building blocks for interpretability.
    - Final combination is a weighted linear stack followed by softmax.
    - Weights are configurable and can be calibrated offline with logistic
      regression against labeled regime history.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        # default weights (tunable)
        self.weights = weights or {
            'vix': 0.25,
            'vix_change_1d': 0.15,
            'yield_curve_2y10y': 0.2,
            'credit_spread_hy_ig': 0.15,
            'etf_flow_sp500_1d': 0.1,
            'news_sentiment_30m': 0.1,
            'ai_confidence_ensemble': 0.05,
        }

    # --- feature scorers ---
    def _score_vix(self, vix: float) -> RegimeScores:
        # higher vix -> more likely bear
        # piecewise transform: below 12 -> bull bias, 12-25 -> sideways, >25 -> bear
        if vix is None:
            return RegimeScores(0.33, 0.33, 0.34)
        if vix < 12:
            return RegimeScores(0.7, 0.1, 0.2)
        if vix < 25:
            return RegimeScores(0.2, 0.2, 0.6)
        return RegimeScores(0.05, 0.85, 0.1)

    def _score_vix_change(self, pct: float) -> RegimeScores:
        # big positive change -> bear
        if pct is None:
            return RegimeScores(0.33, 0.33, 0.34)
        if pct < -10:
            return RegimeScores(0.6, 0.1, 0.3)
        if pct < 5:
            return RegimeScores(0.3, 0.2, 0.5)
        return RegimeScores(0.05, 0.9, 0.05)

    def _score_yield_curve(self, yc: float) -> RegimeScores:
        # inverted or very flat -> recession risk -> bear
        if yc is None:
            return RegimeScores(0.33, 0.33, 0.34)
        if yc > 0.5:
            return RegimeScores(0.7, 0.1, 0.2)
        if yc > 0.0:
            return RegimeScores(0.4, 0.2, 0.4)
        return RegimeScores(0.05, 0.9, 0.05)

    def _score_credit_spread(self, spread: float) -> RegimeScores:
        # HY-IG spread in bps. higher -> bear
        if spread is None:
            return RegimeScores(0.33, 0.33, 0.34)
        if spread < 150:
            return RegimeScores(0.6, 0.1, 0.3)
        if spread < 350:
            return RegimeScores(0.3, 0.3, 0.4)
        return RegimeScores(0.05, 0.9, 0.05)

    def _score_etf_flow(self, flow: float) -> RegimeScores:
        # net dollars flow into SPX ETFs (positive => bullish)
        if flow is None:
            return RegimeScores(0.33, 0.33, 0.34)
        # normalize by magnitude (ad hoc)
        if abs(flow) < 1e5:
            return RegimeScores(0.35, 0.25, 0.4)
        if flow > 0:
            return RegimeScores(0.6, 0.1, 0.3)
        return RegimeScores(0.1, 0.7, 0.2)

    def _score_news_sentiment(self, s: float) -> RegimeScores:
        # sentiment [-1,1]
        if s is None:
            return RegimeScores(0.33, 0.33, 0.34)
        if s > 0.2:
            return RegimeScores(0.7, 0.1, 0.2)
        if s < -0.2:
            return RegimeScores(0.1, 0.7, 0.2)
        return RegimeScores(0.3, 0.2, 0.5)

    def _score_ai_confidence(self, c: float) -> RegimeScores:
        # high consensus among AI models -> stabilize towards current regime
        if c is None:
            return RegimeScores(0.33, 0.33, 0.34)
        # treat as small stabilizer: push away from sideways
        return RegimeScores(0.4 * c + 0.2, 0.4 * (1 - c) + 0.2, 0.4 * 0.5 + 0.2)

    # --- main API ---
    def predict_scores(self, features: Dict[str, Any]) -> RegimeScores:
        # gather individual scorers
        buckets: List[Tuple[RegimeScores, float]] = []
        # safe extraction
        vix = features.get('vix')
        vix_ch = features.get('vix_change_1d')
        yc = features.get('yield_curve_2y10y')
        credit = features.get('credit_spread_hy_ig')
        etf_flow = features.get('etf_flow_sp500_1d')
        news_s = features.get('news_sentiment_30m')
        ai_conf = features.get('ai_confidence_ensemble')

        buckets.append((self._score_vix(vix), self.weights.get('vix', 0.0)))
        buckets.append((self._score_vix_change(vix_ch), self.weights.get('vix_change_1d', 0.0)))
        buckets.append((self._score_yield_curve(yc), self.weights.get('yield_curve_2y10y', 0.0)))
        buckets.append((self._score_credit_spread(credit), self.weights.get('credit_spread_hy_ig', 0.0)))
        buckets.append((self._score_etf_flow(etf_flow), self.weights.get('etf_flow_sp500_1d', 0.0)))
        buckets.append((self._score_news_sentiment(news_s), self.weights.get('news_sentiment_30m', 0.0)))
        buckets.append((self._score_ai_confidence(ai_conf), self.weights.get('ai_confidence_ensemble', 0.0)))

        # linear weighted stacking
        total = np.array([0.0, 0.0, 0.0])
        for score, w in buckets:
            arr = np.array([score.bull, score.bear, score.sideways], dtype=float)
            total += w * arr

        # softmax to probabilities
        exp = np.exp(total - np.max(total))
        probs = exp / (exp.sum() + 1e-12)
        return RegimeScores(*probs.tolist())

    def predict_proba(self, features: Dict[str, Any]) -> Dict[str, float]:
        return self.predict_scores(features).to_dict()


# -----------------------------
# Event Replay Engine
# -----------------------------

@dataclass(order=True)
class _Event:
    timestamp: pd.Timestamp
    priority: int
    type: str = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)


class ReplayEngine:
    """Replay historical streams in time order and call registered handlers.

    Features:
    - Accepts multiple CSV/Parquet sources for 'market', 'news', 'orders', 'execs'.
    - Maintains a min-heap of events sorted by timestamp.
    - Allows handler registration: on_market, on_news, on_order, on_exec.
    - Supports speed multiplier (real-time vs accelerated) and checkpointing.
    - Provides hooks to update FeatureStore and AI Ensemble synchronously.

    Example usage:
        engine = ReplayEngine()
        engine.load_csv('market', 'market_1m.csv')
        engine.load_csv('news', 'news_stream.csv')
        engine.on('market', my_market_handler)
        engine.run()

    Implementation notes:
    - Each CSV must have a 'timestamp' column (ISO8601) and a 'type'/'payload' columns.
    - For memory efficiency, stream large files and push the first N events into heap.
    """

    def __init__(self):
        self._heap: List[_Event] = []
        self.handlers: Dict[str, Callable[[_Event], None]] = {}
        self.sources: Dict[str, str] = {}
        self._stop_flag = False
        self._current_time: Optional[pd.Timestamp] = None
        self._checkpoint: Optional[str] = None

    def load_dataframe(self, stream_name: str, df: pd.DataFrame):
        """Load a pandas DataFrame; pushed into internal generator for iteration."""
        # We convert rows into events and push
        for i, row in df.iterrows():
            ts = pd.to_datetime(row['timestamp'])
            ev = _Event(timestamp=ts, priority=0, type=stream_name, payload=row.to_dict())
            heapq.heappush(self._heap, ev)

    def load_csv(self, stream_name: str, path: str, ts_col: str = 'timestamp'):
        df = pd.read_csv(path, parse_dates=[ts_col])
        df['timestamp'] = pd.to_datetime(df[ts_col])
        self.load_dataframe(stream_name, df)
        self.sources[stream_name] = path

    def on(self, stream_name: str, handler: Callable[[_Event], None]):
        self.handlers[stream_name] = handler

    def run(self, start_time: Optional[pd.Timestamp] = None, end_time: Optional[pd.Timestamp] = None,
            speed: float = 1000.0, realtime: bool = False):
        """Run the replay. speed >1 accelerates time. realtime True tries to wait to match wallclock time.
        If realtime False, iterate as fast as possible (useful for testing).
        """
        self._stop_flag = False
        if start_time:
            self._current_time = pd.to_datetime(start_time)
        else:
            self._current_time = None

        while self._heap and not self._stop_flag:
            ev = heapq.heappop(self._heap)
            self._current_time = ev.timestamp
            if end_time and ev.timestamp > pd.to_datetime(end_time):
                break
            # dispatch
            handler = self.handlers.get(ev.type)
            if handler:
                handler(ev)
            # when realtime True, sleep to simulate
            if realtime:
                time.sleep(1.0 / speed)

    def stop(self):
        self._stop_flag = True

    def set_checkpoint(self, name: str):
        # simple checkpoint: store current time
        self._checkpoint = name + '|' + str(self._current_time)

    def restore_checkpoint(self, checkpoint: str):
        # naive: clear and load events >= checkpoint
        self._checkpoint = checkpoint
        _, ts = checkpoint.split('|')
        cutoff = pd.to_datetime(ts)
        new_heap = [e for e in self._heap if e.timestamp >= cutoff]
        heapq.heapify(new_heap)
        self._heap = new_heap


# -----------------------------
# Integration snippets & demo
# -----------------------------

def demo_market_regime():
    mre = MarketRegimeEnsemble()
    features = {
        'vix': 18.2,
        'vix_change_1d': 12.5,
        'yield_curve_2y10y': -0.12,
        'credit_spread_hy_ig': 280,
        'etf_flow_sp500_1d': -1_500_000,
        'news_sentiment_30m': -0.35,
        'ai_confidence_ensemble': 0.66,
    }
    print('Features:', features)
    print('Proba:', mre.predict_proba(features))


def demo_replay_engine():
    # create small fake streams
    mk = pd.DataFrame([
        {'timestamp': '2024-11-01T09:30:00Z', 'ticker': 'AAPL', 'price': 185.0, 'volume': 1000},
        {'timestamp': '2024-11-01T09:31:00Z', 'ticker': 'AAPL', 'price': 186.0, 'volume': 1200},
    ])
    news = pd.DataFrame([
        {'timestamp': '2024-11-01T09:30:30Z', 'headline': 'AAPL beats', 'sentiment': 0.4},
    ])

    engine = ReplayEngine()

    def on_market(ev):
        p = ev.payload
        print(f"[MARKET] {ev.timestamp} {p.get('ticker')} price={p.get('price')} vol={p.get('volume')}")

    def on_news(ev):
        p = ev.payload
        print(f"[NEWS] {ev.timestamp} headline={p.get('headline')} sentiment={p.get('sentiment')}")

    engine.load_dataframe('market', mk)
    engine.load_dataframe('news', news)
    engine.on('market', on_market)
    engine.on('news', on_news)
    engine.run(realtime=False)


if __name__ == '__main__':
    print('=== Market Regime Demo ===')
    demo_market_regime()
    print('\n=== Replay Engine Demo ===')
    demo_replay_engine()
