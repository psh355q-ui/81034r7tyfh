"""
Execution RL Environment

Gymnasium-compatible environment for Trade Execution.
"""

import math
import logging
import numpy as np
from typing import Optional, Tuple, Dict, Any

# Try importing gymnasium, fallback to gym, then object
try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    try:
        import gym
        from gym import spaces
    except ImportError:
        gym = None
        spaces = None

logger = logging.getLogger(__name__)

class ExecutionEnv(gym.Env if gym else object):
    """
    RL Environment for optimal trade execution.
    
    State:
        - remaining_qty_ratio (0.0 - 1.0)
        - elapsed_time_ratio (0.0 - 1.0)
        - tick_flow_10s (Normalized)
        - tick_flow_30s (Normalized)
        
    Actions:
        0: HOLD
        1: PASSIVE_BUY (Limit @ Bid)
        2: AGGRESSIVE_BUY (Market @ Ask)
    """
    
    metadata = {'render_modes': ['human']}
    
    def __init__(
        self, 
        config: Dict[str, Any],
        tick_flow_source: Any = None,
        vwap_source: Any = None
    ):
        super().__init__()
        
        self.config = config
        self.tick_flow_source = tick_flow_source
        self.vwap_source = vwap_source
        
        # Configuration
        self.total_shares = config.get("total_shares", 1000)
        self.max_duration_seconds = config.get("max_duration_seconds", 1800) # 30 min
        self.initial_price = config.get("initial_price", 100.0)
        
        # Action Space: 0=HOLD, 1=PASSIVE, 2=AGGRESSIVE
        if spaces:
            self.action_space = spaces.Discrete(3)
            # Observation Space: [remaining, time, flow10, flow30]
            self.observation_space = spaces.Box(
                low=np.array([0.0, 0.0, -np.inf, -np.inf]),
                high=np.array([1.0, 1.0, np.inf, np.inf]),
                dtype=np.float32
            )
            
        # Internal State
        self.remaining_shares = self.total_shares
        self.elapsed_seconds = 0
        self.fills = [] # History of fills
        
    def reset(self, seed=None, options=None):
        if gym and hasattr(super(), 'reset'):
            super().reset(seed=seed)
            
        self.remaining_shares = self.total_shares
        self.elapsed_seconds = 0
        self.fills = []
        
        # Reset dependencies if needed
        if self.vwap_source and hasattr(self.vwap_source, 'reset'):
            self.vwap_source.reset()
            
        return self._get_obs(), {}
        
    def step(self, action: int):
        # 1. Time Progression
        dt = 1 # Simulation step 1 second
        self.elapsed_seconds += dt
        
        terminated = False
        truncated = False
        reward = 0.0
        info = {}
        
        # 2. Market Simulation (Simplified for MVP)
        # In real training, we would fetch next tick from data replay
        current_price = self.initial_price # Static price for MVP logic stability test
        
        # 3. Action Execution
        filled_qty = 0
        fill_price = current_price
        
        if action == 1: # PASSIVE_BUY
            # Assume partial fill probability or waiting cost
            # For MVP: Simple deterministic fill for small amount
            filled_qty = min(self.remaining_shares, 10) # 10 shares per sec
            fill_price = current_price # Limit @ Bid (optimistic)
            
        elif action == 2: # AGGRESSIVE_BUY
            # Market order fills larger chunk but with slippage
            filled_qty = min(self.remaining_shares, 50) # 50 shares per sec
            slippage = 0.0005 # 5 bps
            fill_price = current_price * (1 + slippage)
            
        # Update State
        self.remaining_shares -= filled_qty
        if filled_qty > 0:
            self.fills.append({"price": fill_price, "qty": filled_qty, "time": self.elapsed_seconds})
            
            # --- Reward Calculation ---
            # Main Reward: VWAP Advantage (Approximate for step)
            # We give reward only on fills to encourage execution quality
            vwap = self.vwap_source.get_vwap() if self.vwap_source else self.initial_price
            if vwap is None: vwap = self.initial_price
            
            # (VWAP - FillPrice) / VWAP * Scale
            # +: Bought cheaper than VWAP
            # -: Bought expensive
            advantage = (vwap - fill_price) / vwap * 100 
            reward = advantage * (filled_qty / self.total_shares) # Weight by size
            
        # 4. Check Done
        if self.remaining_shares <= 0:
            terminated = True
        elif self.elapsed_seconds >= self.max_duration_seconds:
            truncated = True # Timeout
            
            # Penalty for unexecuted shares
            penalty = -1.0 * (self.remaining_shares / self.total_shares)
            reward += penalty
            
        return self._get_obs(), reward, terminated, truncated, info
        
    def _get_obs(self):
        remaining_ratio = self.remaining_shares / self.total_shares
        time_ratio = self.elapsed_seconds / self.max_duration_seconds
        
        flow10 = 0.0
        flow30 = 0.0
        if self.tick_flow_source:
            # Normalize flow? Let's keep raw for now or use log scale
            flow10 = self.tick_flow_source.get_flow(10)
            flow30 = self.tick_flow_source.get_flow(30)
            
        return np.array([
            remaining_ratio,
            time_ratio,
            flow10,
            flow30
        ], dtype=np.float32)

    def render(self):
        print(f"Time: {self.elapsed_seconds}/{self.max_duration_seconds}, "
              f"Rem: {self.remaining_shares}, "
              f"LastFill: {self.fills[-1] if self.fills else 'None'}")
