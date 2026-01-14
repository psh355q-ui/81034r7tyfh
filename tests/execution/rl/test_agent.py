
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import os

# Mocking stable_baselines3 to avoid dependency in CI/CD environment
with patch.dict('sys.modules', {'stable_baselines3': MagicMock(), 'stable_baselines3.common.vec_env': MagicMock()}):
    from backend.execution.rl.agent import ExecutionAgent

class TestExecutionAgent(unittest.TestCase):
    def setUp(self):
        self.mock_env = MagicMock()
        # Mocking Observation Space and Action Space
        self.mock_env.observation_space.shape = (4,)
        self.mock_env.action_space.n = 3
        
        self.agent = ExecutionAgent(env=self.mock_env, verbose=0)
        
        # Inject Mock Model
        self.agent.model = MagicMock()

    def test_train(self):
        self.agent.train(total_timesteps=1000)
        self.agent.model.learn.assert_called_once()
        args, kwargs = self.agent.model.learn.call_args
        self.assertEqual(kwargs['total_timesteps'], 1000)

    def test_predict(self):
        mock_obs = np.array([1.0, 0.0, 0.5, 0.5])
        self.agent.model.predict.return_value = (1, None) # Action 1, State None
        
        action = self.agent.predict(mock_obs)
        self.assertEqual(action, 1)
        self.agent.model.predict.assert_called_with(mock_obs, deterministic=True)

    def test_save_and_load(self):
        path = "test_agent_model"
        self.agent.save(path)
        self.agent.model.save.assert_called_with(path)
        
        # Load is typically a class method or requires re-instantiation logic
        # Here checking instance method delegation
        self.agent.load(path)
        # Assuming load updates internal model or calls PPO.load
        # Since we mocked PPO in the module, let's verify logic in implementation
        
    def tearDown(self):
        if os.path.exists("test_agent_model.zip"):
            os.remove("test_agent_model.zip")

if __name__ == '__main__':
    unittest.main()
