"""
Constitutional AI Investment Committee - End-to-End Example

전체 워크플로우 시연:
1. 뉴스 입력
2. AI Debate (5 agents)
3. Constitutional Validation
4. Commander Approval (Telegram)
5. Shadow Trade (거부 시)
6. Shield Report

작성일: 2025-12-15
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# 프로젝트 루트 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.constitution import Constitution


class ConstitutionalWorkflowDemo:
    """
    Constitutional AI Investment Committee 워크플로우 데모
    
    실제 시스템의 작동 방식을 시연합니다.
    """
    
    def __init__(self):
        """초기화"""
        self.constitution = Constitution()
        
        # 포트폴리오 상태 (시뮬레이션)
        self.portfolio_state = {
            'total_capital': 10_000_000,  # ₩10M
            'current_allocation': {
                'stock': 0.70,
                'cash': 0.30
            },
            'daily_trades': 0,
            'weekly_trades': 0,
            'daily_loss': 0.0,
            'total_drawdown': 0.0
        }
        
        # 통계
        self.stats = {
            'proposals_created': 0,
            'constitutional_passes': 0,
            'constitutional_failures': 0,
            'approvals': 0,
            'rejections': 0,
            'shadow_trades': 0
        }
    
    def simulate_ai_debate(self, news_title: str) -> Dict[str, Any]:
        """
        AI Debate 시뮬레이션
        
        실제로는 AIDebateEngine이 실행되지만,
        여기서는 결과를 시뮬레이션합니다.
        """
        print(f"\n{'='*60}")
        print(f"🎭 AI Debate Starting...")
        print(f"{'='*60}")
        print(f"News: {news_title}")
        print()
        
        # 5명의 Agent 투표 시뮬레이션
        agents = [
            ("Trader", "BUY", 0.85, "강한 수급 신호 감지"),
            ("Risk", "HOLD", 0.65, "VIX 22, 주의 필요"),
            ("Analyst", "BUY", 0.70, "펀더멘털 양호"),
            ("Macro", "BUY", 0.75, "RISK_ON 체제"),
            ("Institutional", "BUY", 0.80, "기관 매수 증가")
        ]
        
        print("Agent Votes:")
        for name, action, conf, reason in agents:
            print(f"  [{name:12s}] {action:4s} ({conf:.0%}) - {reason}")
        
        # 투표 집계
        buy_votes = sum(1 for _, a, _, _ in agents if a == "BUY")
        consensus = buy_votes / len(agents)
        
        print(f"\nConsensus: {buy_votes}/{len(agents)} ({consensus:.0%})")
        
        # 최종 시그널
        final_action = "BUY" if buy_votes >= 3 else "HOLD"
        
        print(f"Final Signal: {final_action}")
        print()
        
        return {
            'ticker': 'AAPL',
            'action': final_action,
            'target_price': 195.50,
            'position_value': 1_500_000,  # ₩1.5M
            'order_value_usd': 15000,
            'shares': 77,
            'reasoning': agents[0][3],  # Trader의 근거
            'confidence': 0.78,
            'consensus_level': consensus,
            'debate_summary': "5명 중 4명이 BUY 투표",
            'model_votes': {name: action for name, action, _, _ in agents}
        }
    
    def validate_with_constitution(
        self,
        ai_proposal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> tuple[bool, list[str], list[str]]:
        """
        헌법 검증
        
        Args:
            ai_proposal: AI 제안
            market_context: 시장 컨텍스트
        
        Returns:
            (is_valid, violations, violated_articles)
        """
        print(f"{'='*60}")
        print(f"🏛️ Constitutional Validation")
        print(f"{'='*60}")
        
        # Proposal 준비
        proposal = {
            'ticker': ai_proposal['ticker'],
            'action': ai_proposal['action'],
            'position_value': ai_proposal['position_value'],
            'order_value_usd': ai_proposal['order_value_usd'],
            'is_approved': False
        }
        
        # Context 준비
        context = {
            'total_capital': self.portfolio_state['total_capital'],
            'current_allocation': self.portfolio_state['current_allocation'],
            'market_regime': market_context['regime'],
            'daily_trades': self.portfolio_state['daily_trades'],
            'weekly_trades': self.portfolio_state['weekly_trades'],
            'daily_volume_usd': 50_000_000
        }
        
        # 헌법 검증
        is_valid, violations, violated_articles = self.constitution.validate_proposal(
            proposal, context
        )
        
        # 결과 출력
        if is_valid:
            print("✅ Constitutional Check: PASS")
            print("   제안이 모든 헌법 조항을 준수합니다.")
            self.stats['constitutional_passes'] += 1
        else:
            print("❌ Constitutional Check: FAIL")
            print("\nViolations:")
            for v in violations:
                print(f"   • {v}")
            print("\nViolated Articles:")
            for a in violated_articles:
                print(f"   • {a}")
            self.stats['constitutional_failures'] += 1
        
        print()
        
        return is_valid, violations, violated_articles
    
    def create_proposal(
        self,
        ai_proposal: Dict[str, Any],
        is_constitutional: bool,
        violated_articles: list[str],
        market_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Proposal 객체 생성 (딕셔너리)
        
        Args:
            ai_proposal: AI 제안
            is_constitutional: 헌법 준수 여부
            violated_articles: 위반 조항
            market_context: 시장 컨텍스트
        
        Returns:
            Proposal 딕셔너리
        """
        
        proposal = {
            'id': str(uuid.uuid4()),
            'ticker': ai_proposal['ticker'],
            'action': ai_proposal['action'],
            'target_price': ai_proposal['target_price'],
            'position_size': ai_proposal['position_value'] / self.portfolio_state['total_capital'],
            'order_value_usd': ai_proposal['order_value_usd'],
            'shares': ai_proposal['shares'],
            'reasoning': ai_proposal['reasoning'],
            'confidence': ai_proposal['confidence'],
            'consensus_level': ai_proposal['consensus_level'],
            'debate_summary': ai_proposal['debate_summary'],
            'is_constitutional': is_constitutional,
            'violated_articles': ', '.join(violated_articles) if violated_articles else None,
            'status': 'PENDING',
            'market_regime': market_context['regime'],
            'vix': market_context['vix']
        }
        
        self.stats['proposals_created'] += 1
        
        return proposal
    
    def commander_decision(self, proposal: Proposal) -> str:
        """
        Commander 결정 시뮬레이션
        
        실제로는 텔레그램 버튼으로 결정하지만,
        여기서는 헌법 준수 여부로 자동 결정합니다.
        
        Returns:
            'APPROVE' or 'REJECT'
        """
        print(f"{'='*60}")
        print(f"👤 Commander Decision")
        print(f"{'='*60}")
        
        print(f"\n제안 요약:")
        print(f"  Ticker: {proposal['ticker']}")
        print(f"  Action: {proposal['action']}")
        print(f"  Target: ${proposal['target_price']}")
        print(f"  Amount: ${proposal['order_value_usd']:,}")
        print(f"  Constitutional: {proposal['is_constitutional']}")
        print(f"  Consensus: {proposal['consensus_level']:.0%}")
        
        # 자동 결정 (실제로는 사용자 클릭)
        if proposal['is_constitutional'] and proposal['consensus_level'] >= 0.70:
            decision = 'APPROVE'
            print(f"\n✅ Commander Decision: APPROVE")
            print(f"   헌법 준수 + 높은 합의")
            proposal['status'] = 'APPROVED'
            proposal['approved_by'] = "demo_commander"
            self.stats['approvals'] += 1
        else:
            decision = 'REJECT'
            reason = "헌법 위반" if not proposal['is_constitutional'] else "합의 부족"
            print(f"\n❌ Commander Decision: REJECT")
            print(f"   사유: {reason}")
            proposal['status'] = 'REJECTED'
            proposal['rejection_reason'] = reason
            self.stats['rejections'] += 1
        
        print()
        return decision
    
    def create_shadow_trade(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Shadow Trade 생성 (거부된 제안 추적)
        
        Args:
            proposal: 거부된 제안
        
        Returns:
            ShadowTrade 객체
        """
        print(f"{'='*60}")
        print(f"🛡️ Shadow Trade Created")
        print(f"{'='*60}")
        
        shadow = {
            'proposal_id': proposal['id'],
            'ticker': proposal['ticker'],
            'action': proposal['action'],
            'entry_price': proposal['target_price'],
            'shares': proposal['shares'],
            'rejection_reason': proposal.get('rejection_reason'),
            'violated_articles': proposal['violated_articles'],
            'tracking_days': 7,
            'status': 'TRACKING'
        }
        
        print(f"\nShadow Trade:")
        print(f"  Ticker: {shadow['ticker']}")
        print(f" Action: {shadow['action']}")
        print(f"  Entry: ${shadow['entry_price']}")
        print(f"  Reason: {shadow['rejection_reason']}")
        print(f"  Tracking: {shadow['tracking_days']} days")
        print(f"\n이 제안이 실제로 실행되었다면 어떻게 되었을지 추적합니다.")
        print(f"7일 후 '방어한 손실' 또는 '놓친 기회'로 분류됩니다.")
        
        self.stats['shadow_trades'] += 1
        
        print()
        return shadow
    
    def generate_shield_report(self) -> Dict[str, Any]:
        """
        Shield Report 생성
        
        Returns:
            Shield Report 딕셔너리
        """
        print(f"{'='*60}")
        print(f"📊 Shield Report (방패 보고서)")
        print(f"{'='*60}")
        
        report = {
            'period': '데모',
            'capital_preserved_rate': 99.85,  # 99.85%
            'total_avoided_loss': 1_200_000,  # ₩1.2M
            'defensive_wins': self.stats['rejections'],
            'total_rejected': self.stats['rejections'],
            'market_volatility': 0.25,
            'portfolio_volatility': 0.03,
            'max_drawdown': -0.001
        }
        
        print(f"\n💎 자본 보존")
        print(f"  자본 보존율: {report['capital_preserved_rate']:.2f}% (S등급)")
        print(f"  초기 자본: ₩{self.portfolio_state['total_capital']:,}")
        
        print(f"\n🛡️ 방어 성과")
        print(f"  방어한 손실: ₩{report['total_avoided_loss']:,}")
        print(f"  거부한 제안: {report['total_rejected']}건")
        print(f"  방어 성공: {report['defensive_wins']}건")
        
        print(f"\n🌊 Stress Test")
        print(f"  시장 변동성: {report['market_volatility']:.1%} 🌊")
        print(f"  내 계좌: {report['portfolio_volatility']:.1%} ⎯")
        print(f"  스트레스 감소: {report['market_volatility'] - report['portfolio_volatility']:.1%}p")
        
        print(f"\n📊 Drawdown Protection")
        print(f"  최대 낙폭: {abs(report['max_drawdown']):.2%}")
        
        print()
        return report
    
    def run_complete_workflow(self):
        """
        전체 워크플로우 실행
        
        뉴스 → AI Debate → Constitution → Commander → Shadow/Shield
        """
        print("\n" + "="*60)
        print(" "*10 + "🏛️ Constitutional AI Investment Committee 🏛️")
        print("="*60)
        print("\n전체 워크플로우 시연\n")
        
        # 1. 뉴스 입력
        news = {
            'title': 'Apple announces revolutionary AI chip breakthrough',
            'sentiment': 0.85
        }
        
        # 2. 시장 컨텍스트
        market_context = {
            'regime': 'risk_on',
            'vix': 18.5
        }
        
        # 3. AI Debate
        ai_proposal = self.simulate_ai_debate(news['title'])
        
        # 4. Constitutional Validation
        is_constitutional, violations, violated_articles = self.validate_with_constitution(
            ai_proposal, market_context
        )
        
        # 5. Proposal 생성
        proposal = self.create_proposal(
            ai_proposal, is_constitutional, violated_articles, market_context
        )
        
        # 6. Commander Decision
        decision = self.commander_decision(proposal)
        
        # 7. Shadow Trade (거부 시)
        if decision == 'REJECT':
            shadow = self.create_shadow_trade(proposal)
        
        # 8. Shield Report
        shield_report = self.generate_shield_report()
        
        # 9. 통계 요약
        self.print_statistics()
    
    def print_statistics(self):
        """통계 출력"""
        print(f"{'='*60}")
        print(f"📈 Session Statistics")
        print(f"{'='*60}")
        
        print(f"\nProposals:")
        print(f"  Created: {self.stats['proposals_created']}")
        print(f"  Constitutional Pass: {self.stats['constitutional_passes']}")
        print(f"  Constitutional Fail: {self.stats['constitutional_failures']}")
        
        print(f"\nCommander Decisions:")
        print(f"  Approved: {self.stats['approvals']}")
        print(f"  Rejected: {self.stats['rejections']}")
        
        print(f"\nDefensive Tracking:")
        print(f"  Shadow Trades: {self.stats['shadow_trades']}")
        
        pass_rate = (self.stats['constitutional_passes'] / self.stats['proposals_created'] * 100) if self.stats['proposals_created'] > 0 else 0
        print(f"\nConstitutional Pass Rate: {pass_rate:.0f}%")
        
        print()


def main():
    """메인 함수"""
    demo = ConstitutionalWorkflowDemo()
    demo.run_complete_workflow()
    
    print("\n" + "="*60)
    print("✅ 워크플로우 완료!")
    print("="*60)
    print("\n이것이 Constitutional AI Investment Committee의 작동 방식입니다:")
    print("1. AI가 치열하게 토론")
    print("2. 헌법이 엄격하게 검증")
    print("3. Commander가 최종 결정")
    print("4. 거부된 제안은 Shadow Trade로 추적")
    print("5. Shield Report로 방어 성과 증명")
    print("\n수익률이 아닌 '안전'을 판매하는 시스템입니다.")
    print()


if __name__ == "__main__":
    main()
