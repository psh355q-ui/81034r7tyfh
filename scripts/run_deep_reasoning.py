#!/usr/bin/env python3
"""
Phase 14: Deep Reasoning Strategy - 통합 실행 스크립트
=====================================================

사용법:
    # 심층 추론 테스트
    python scripts/run_deep_reasoning.py --mode reasoning --news "Google announced TPU v6"
    
    # A/B 백테스트
    python scripts/run_deep_reasoning.py --mode backtest
    
    # Knowledge Graph 초기화
    python scripts/run_deep_reasoning.py --mode init_kg
    
    # 전체 데모
    python scripts/run_deep_reasoning.py --mode demo
"""

import asyncio
import argparse
import sys
import os
import json
from datetime import datetime

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def run_reasoning(news_text: str, model: str = None):
    """심층 추론 실행"""
    from backend.ai.reasoning.deep_reasoning import DeepReasoningStrategy
    from backend.ai.ai_client_factory import AIClientFactory
    from backend.config_phase14 import settings
    
    print("=" * 70)
    print("         DEEP REASONING STRATEGY - Phase 14")
    print("=" * 70)
    print(f"\n📰 News: {news_text}\n")
    
    # 모델 선택
    if model:
        client = AIClientFactory.create(model)
    else:
        # Mock 클라이언트 사용 (실제 API 호출 없음)
        from backend.ai.ai_client_factory import MockAIClient
        client = MockAIClient("mock-demo")
        
        # Google TPU 관련 Mock 응답 설정
        client.set_mock_response("tpu", json.dumps({
            "theme": "Rise of Custom AI Silicon - Anti-Nvidia Alliance",
            "step1_direct": {
                "entities": ["Google", "Nvidia", "Anthropic"],
                "impacts": [
                    {"entity": "Google", "impact": "Vertical integration success - AI chip independence", "sentiment": "positive"},
                    {"entity": "Nvidia", "impact": "Loss of hyperscaler inference market", "sentiment": "negative"},
                    {"entity": "Anthropic", "impact": "Cost reduction through TPU adoption", "sentiment": "positive"}
                ]
            },
            "step2_secondary": {
                "value_chain_analysis": "Google's TPU ecosystem expansion reduces industry-wide Nvidia dependency. Broadcom, as TPU design partner, captures hidden value.",
                "beneficiaries": [
                    {"entity": "Broadcom", "reason": "TPU interconnect & ASIC design partner - royalty increase with TPU adoption"}
                ],
                "losers": [
                    {"entity": "Nvidia", "reason": "CUDA moat erosion, losing inference market share to custom silicon"}
                ],
                "reasoning_trace": [
                    "1. Google TPU v6 achieves 2x efficiency vs Nvidia H100 for inference",
                    "2. Anthropic signs 1M TPU contract → validates non-CUDA development path",
                    "3. Broadcom designs TPU interconnects → captures 5-7% of chip cost",
                    "4. More TPU adoption = More Broadcom revenue, less Nvidia dependency",
                    "5. Long-term: 'Nvidia tax' on AI compute diminishes"
                ]
            },
            "step3_strategy": {
                "primary_beneficiary": {
                    "ticker": "GOOGL", 
                    "action": "BUY", 
                    "confidence": 0.85, 
                    "reason": "Full-stack AI advantage: Chip + Model + Service integration"
                },
                "hidden_beneficiary": {
                    "ticker": "AVGO", 
                    "action": "BUY", 
                    "confidence": 0.90, 
                    "reason": "Pick-and-shovel play: TPU design partner, benefits from all custom ASIC growth"
                },
                "loser": {
                    "ticker": "NVDA", 
                    "action": "TRIM", 
                    "confidence": 0.60, 
                    "reason": "Long-term moat erosion, but short-term still dominant"
                },
                "bull_case": "TPU becomes industry standard for AI inference, Google dominates AI infrastructure cost curve",
                "bear_case": "CUDA ecosystem too entrenched, developers resist switching costs"
            },
            "overall_confidence": 0.78
        }))
    
    strategy = DeepReasoningStrategy(ai_client=client)
    
    result = await strategy.analyze_news(news_text)
    
    # 액션 아이템 출력
    print("\n" + "=" * 70)
    print("                     ACTION ITEMS")
    print("=" * 70)
    
    actions = result.get_action_items()
    for action in actions:
        ticker = action.get('ticker', 'N/A')
        act = action.get('action', 'HOLD')
        conf = action.get('confidence', 0)
        reason = action.get('reason', '')
        
        emoji = "🟢" if act in ["BUY", "STRONG_BUY"] else "🔴" if act in ["SELL", "TRIM"] else "⚪"
        print(f"\n{emoji} {ticker}: {act} (Confidence: {conf:.0%})")
        print(f"   Reason: {reason}")
    
    # JSON 저장
    output_path = f"/tmp/reasoning_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2, default=str)
    print(f"\n📁 Result saved to: {output_path}")
    
    return result


async def run_backtest():
    """A/B 백테스트 실행"""
    from backend.backtesting.ab_backtest import ABBacktestEngine
    
    print("=" * 70)
    print("         A/B BACKTEST - Keyword vs CoT+RAG")
    print("=" * 70)
    
    engine = ABBacktestEngine()
    
    # 모든 역사적 이벤트 테스트
    report = await engine.run_comparison()
    
    # 리포트 출력
    engine.print_comparison_report(report)
    
    return report


async def init_knowledge_graph():
    """Knowledge Graph 초기화"""
    from backend.data.knowledge_graph.knowledge_graph import KnowledgeGraph
    from backend.config_phase14 import SEED_KNOWLEDGE
    
    print("=" * 70)
    print("         KNOWLEDGE GRAPH INITIALIZATION")
    print("=" * 70)
    
    kg = KnowledgeGraph()
    
    # 스키마 생성
    print("\n[1/3] Creating schema...")
    kg.ensure_schema()
    
    # Seed 데이터 import
    print("\n[2/3] Importing seed knowledge...")
    count = await kg.import_seed_knowledge(SEED_KNOWLEDGE)
    print(f"  Imported {count} relationships")
    
    # 통계
    print("\n[3/3] Statistics:")
    stats = kg.get_stats()
    for key, value in stats.items():
        if key != 'relation_distribution':
            print(f"  {key}: {value}")
    
    return kg


async def run_demo():
    """전체 데모"""
    print("\n" + "=" * 70)
    print("              PHASE 14: DEEP REASONING DEMO")
    print("=" * 70)
    
    # 1. Knowledge Graph 초기화
    print("\n\n📊 STEP 1: Knowledge Graph Setup")
    print("-" * 50)
    await init_knowledge_graph()
    
    # 2. 심층 추론 테스트
    print("\n\n🧠 STEP 2: Deep Reasoning Test")
    print("-" * 50)
    
    test_news_items = [
        "Google announced that Gemini 3.0 was trained entirely on TPU v6, with Anthropic signing a contract for 1 million TPUs.",
        "OpenAI is reportedly working with Broadcom to design custom AI chips for the $500B Stargate datacenter project.",
        "Samsung Electronics reports breakthrough in 2nm foundry yield, potentially winning major AI chip contracts from Nvidia."
    ]
    
    for news in test_news_items:
        await run_reasoning(news)
        print("\n" + "-" * 50 + "\n")
    
    # 3. A/B 백테스트
    print("\n\n📈 STEP 3: A/B Backtest Comparison")
    print("-" * 50)
    await run_backtest()
    
    print("\n" + "=" * 70)
    print("              DEMO COMPLETE!")
    print("=" * 70)
    print("""
다음 단계:
1. 실제 AI API 키 설정 (.env)
2. PostgreSQL + pgvector 실행 (Knowledge Graph)
3. 실시간 뉴스 피드 연결
4. Trading Agent 통합

자세한 내용은 docs/Phase14_DeepReasoning.md 참조
""")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 14: Deep Reasoning Strategy"
    )
    parser.add_argument(
        "--mode", 
        choices=["reasoning", "backtest", "init_kg", "demo"],
        default="demo",
        help="실행 모드"
    )
    parser.add_argument(
        "--news",
        type=str,
        default="Google announced TPU v6 with 2x efficiency improvement",
        help="분석할 뉴스 텍스트"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="사용할 AI 모델 (예: gemini-1.5-pro, claude-3-haiku-20240307)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "reasoning":
        asyncio.run(run_reasoning(args.news, args.model))
    elif args.mode == "backtest":
        asyncio.run(run_backtest())
    elif args.mode == "init_kg":
        asyncio.run(init_knowledge_graph())
    elif args.mode == "demo":
        asyncio.run(run_demo())


if __name__ == "__main__":
    main()
