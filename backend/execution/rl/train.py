"""
Execution RL Training Script

Entry point for training the Execution Agent.
"""

import os
import argparse
from backend.execution.rl.env import ExecutionEnv
from backend.execution.rl.agent import ExecutionAgent
from unittest.mock import MagicMock

def main():
    parser = argparse.ArgumentParser(description="Train Execution RL Agent")
    parser.add_argument("--timesteps", type=int, default=10000, help="Total training timesteps")
    parser.add_argument("--save_path", type=str, default="models/execution_rl_v0", help="Path to save model")
    args = parser.parse_args()

    # 1. Setup Data Sources (Mock for now, real DB in production)
    # Ideally, we load historical tick data here and pass a replay buffer to the env
    mock_tick_flow = MagicMock()
    mock_tick_flow.get_flow.return_value = 0.0 # Neural flow
    
    mock_vwap = MagicMock()
    mock_vwap.get_vwap.return_value = 100.0
    
    # 2. Setup Environment
    config = {
        "total_shares": 1000,
        "max_duration_seconds": 1800,
        "initial_price": 100.0
    }
    
    env = ExecutionEnv(config, tick_flow_source=mock_tick_flow, vwap_source=mock_vwap)
    
    # 3. Setup Agent
    agent = ExecutionAgent(env=env, verbose=1)
    
    # 4. Train
    print("Start Training...")
    agent.train(total_timesteps=args.timesteps)
    
    # 5. Save
    os.makedirs(os.path.dirname(args.save_path), exist_ok=True)
    agent.save(args.save_path)
    print(f"Done. Model saved to {args.save_path}")

if __name__ == "__main__":
    main()
