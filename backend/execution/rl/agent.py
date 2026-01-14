"""
Execution RL Agent

Wrapper around Stable Baselines3 PPO agent.
Handles model training, prediction, and persistence.
"""

import os
import logging
from typing import Optional, Any

try:
    from stable_baselines3 import PPO
except ImportError:
    PPO = None

logger = logging.getLogger(__name__)

class ExecutionAgent:
    """
    RL Agent for Trade Execution using PPO.
    """
    def __init__(self, env: Any, model_path: Optional[str] = None, verbose: int = 1):
        self.env = env
        self.model_path = model_path
        self.verbose = verbose
        
        if PPO:
            if model_path and os.path.exists(model_path + ".zip"):
                self.model = PPO.load(model_path, env=env)
                logger.info(f"Loaded PPO model from {model_path}")
            else:
                self.model = PPO(
                    "MlpPolicy", 
                    env, 
                    verbose=verbose,
                    learning_rate=3e-4,
                    n_steps=2048,
                    batch_size=64,
                    n_epochs=10,
                    gamma=0.99,
                    gae_lambda=0.95,
                    clip_range=0.2,
                )
                logger.info("Initialized new PPO model")
        else:
            logger.warning("Stable Baselines3 not found. Using Mock Model.")
            self.model = MockPPO()

    def train(self, total_timesteps: int = 10000):
        """Train the agent."""
        logger.info(f"Starting training for {total_timesteps} timesteps...")
        self.model.learn(total_timesteps=total_timesteps)
        logger.info("Training completed.")

    def predict(self, observation, deterministic: bool = True):
        """Predict action for a given observation."""
        action, _ = self.model.predict(observation, deterministic=deterministic)
        return action

    def save(self, path: str):
        """Save the model."""
        self.model.save(path)
        logger.info(f"Model saved to {path}")
            
    def load(self, path: str):
        """Load the model."""
        if PPO:
            self.model = PPO.load(path, env=self.env)
            logger.info(f"Model loaded from {path}")
        else:
            logger.warning("Cannot load real model without Stable Baselines3.")


class MockPPO:
    """Mock PPO for environments without stable-baselines3."""
    def __init__(self, *args, **kwargs):
        pass
        
    def learn(self, total_timesteps, **kwargs):
        pass
        
    def predict(self, observation, deterministic=True):
        # Random action 0, 1, or 2
        return (0, None)
        
    def save(self, path):
        pass
        
    def load(self, path, env=None):
        return self
