import sys
import os
import unittest
from datetime import datetime

# Add root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
# Add backend to path to satisfy WarRoomMVP imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.ai.mvp.trader_agent_mvp import TraderAgentMVP
from backend.ai.mvp.risk_agent_mvp import RiskAgentMVP
from backend.ai.mvp.analyst_agent_mvp import AnalystAgentMVP
from backend.ai.mvp.pm_agent_mvp import PMAgentMVP
from backend.ai.schemas.war_room_schemas import RiskOpinion

# Set dummy API key for testing
os.environ['GEMINI_API_KEY'] = 'dummy_key'

class TestStructuredOutputs(unittest.TestCase):
    def test_trader_agent_parsing(self):
        print("\nTesting TraderAgent parsing...")
        agent = TraderAgentMVP()
        valid_json = """
        {
            "action": "buy",
            "confidence": 0.9,
            "opportunity_score": 8.5,
            "reasoning": "Strong breakout imminent",
            "entry_price": 100.0,
            "exit_price": 120.0,
            "timeframe": "1w",
            "momentum_strength": "strong"
        }
        """
        # _parse_response validates and returns TraderOpinion object
        opinion = agent._parse_response(valid_json)
        self.assertEqual(opinion.action, "buy")
        self.assertEqual(opinion.confidence, 0.9)
        self.assertEqual(opinion.momentum_strength, "strong")
        print("TraderAgent: OK")

    def test_risk_agent_parsing(self):
        print("\nTesting RiskAgent parsing...")
        agent = RiskAgentMVP()
        
        valid_json = """
        {
            "risk_level": "medium",
            "confidence": 0.8,
            "reasoning": "Moderate risk",
            "stop_loss_pct": 0.03,
            "recommendation": "approve"
        }
        """
        # agent._parse_response returns dict (deprecated/wrapper)
        res_dict = agent._parse_response(valid_json)
        self.assertEqual(res_dict['risk_level'], 'medium')

        # Test Pydantic validation manually (simulating analyze)
        op_data = {
            'agent': 'risk_mvp',
            'action': res_dict['recommendation'], # 'approve' -> 'approve'
            'confidence': res_dict['confidence'],
            'position_size': 5.0, # Dummy
            'risk_level': res_dict['risk_level'],
            'stop_loss': 100.0, # Dummy
            'reasoning': res_dict['reasoning']
        }
        op = RiskOpinion(**op_data)
        self.assertEqual(op.action, 'approve')
        print("RiskAgent: OK")

    def test_analyst_agent_parsing(self):
        print("\nTesting AnalystAgent parsing...")
        agent = AnalystAgentMVP()
        valid_json = """
        {
            "action": "hold",
            "confidence": 0.7,
            "overall_information_score": 6.5,
            "reasoning": "Mixed signals",
            "news_impact": {"sentiment": "neutral", "impact_score": 5.0}
        }
        """
        opinion = agent._parse_response(valid_json)
        self.assertEqual(opinion.action, 'hold')
        self.assertEqual(opinion.overall_score, 6.5) # check mapping
        print("AnalystAgent: OK")

    def test_pm_agent_parsing(self):
        print("\nTesting PMAgent parsing...")
        agent = PMAgentMVP()
        valid_json = """
        {
            "final_decision": "approve",
            "confidence": 0.95,
            "reasoning": "Good to go",
            "recommended_action": "buy",
            "position_size_adjustment": 1.0,
            "risk_assessment": {"portfolio_risk_score": 2.0}
        }
        """
        decision = agent._parse_response(valid_json)
        self.assertEqual(decision.final_decision, 'approve') # check mapping
        self.assertEqual(decision.confidence, 0.95)
        print("PMAgent: OK")

if __name__ == '__main__':
    unittest.main()
