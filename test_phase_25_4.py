"""
Phase 25.4 Test Script - 가중치 계산 및 경고 시스템 테스트

실행 방법:
    python test_phase_25_4.py
"""

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_weight_adjuster():
    """가중치 계산 엔진 테스트"""
    logger.info("=" * 80)
    logger.info("TEST 1: Agent Weight Adjuster")
    logger.info("=" * 80)
    
    try:
        from backend.ai.learning.agent_weight_adjuster import AgentWeightAdjuster
        
        adjuster = AgentWeightAdjuster()
        
        # 1. 현재 가중치 조회
        logger.info("\n1. Getting current weights...")
        current_weights = await adjuster.get_current_weights()
        for agent, weight in current_weights.items():
            logger.info(f"  {agent}: {weight:.3f}")
        
        # 2. 단일 에이전트 가중치 계산
        logger.info("\n2. Calculating weight for 'trader' agent...")
        new_weight, reason = await adjuster.calculate_agent_weight('trader', lookback_days=30)
        logger.info(f"  New weight: {new_weight:.3f}")
        logger.info(f"  Reason: {reason}")
        
        # 3. 전체 가중치 재계산 (DB 저장 안 함)
        logger.info("\n3. Recalculating all weights (no DB save)...")
        results = await adjuster.recalculate_all_weights(lookback_days=30, save_to_db=False)
        for agent, data in results.items():
            logger.info(
                f"  {agent}: {data['old_weight']:.3f} → {data['new_weight']:.3f} "
                f"({data['change']:+.3f}) - {data['reason']}"
            )
        
        logger.info("\n✅ Weight Adjuster Test PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Weight Adjuster Test FAILED: {e}\n", exc_info=True)
        return False


async def test_alert_system():
    """경고 시스템 테스트"""
    logger.info("=" * 80)
    logger.info("TEST 2: Agent Alert System")
    logger.info("=" * 80)
    
    try:
        from backend.ai.learning.agent_alert_system import AgentAlertSystem
        
        alert_system = AgentAlertSystem()
        
        # 1. 저성과 체크
        logger.info("\n1. Checking for underperformance...")
        underperformance = await alert_system.check_underperformance(lookback_days=30)
        logger.info(f"  Found {len(underperformance)} underperforming agents")
        for alert in underperformance:
            logger.info(
                f"    - {alert['agent_name']}: {alert['accuracy']:.1%} "
                f"({alert['correct_votes']}/{alert['total_votes']})"
            )
        
        # 2. 오버컨피던트 체크
        logger.info("\n2. Checking for overconfidence...")
        overconfidence = await alert_system.check_overconfidence(lookback_days=30)
        logger.info(f"  Found {len(overconfidence)} overconfident agents")
        for alert in overconfidence:
            logger.info(
                f"    - {alert['agent_name']}: gap {alert['gap']:.1%} "
                f"(conf {alert['avg_confidence']:.1%} vs acc {alert['accuracy']:.1%})"
            )
        
        # 3. 최근 경고 조회
        logger.info("\n3. Getting recent alerts (last 24h)...")
        recent_alerts = await alert_system.get_recent_alerts(hours=24)
        logger.info(f"  Found {len(recent_alerts)} recent alerts")
        for alert in recent_alerts[:5]:  # 최대 5개만 표시
            logger.info(
                f"    - [{alert['severity']}] {alert['agent_name']}: {alert['message'][:60]}..."
            )
        
        logger.info("\n✅ Alert System Test PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Alert System Test FAILED: {e}\n", exc_info=True)
        return False


async def test_api_endpoints():
    """API 엔드포인트 테스트 (curl 명령 출력)"""
    logger.info("=" * 80)
    logger.info("TEST 3: API Endpoints (Manual Testing)")
    logger.info("=" * 80)
    
    logger.info("\n📋 다음 명령어로 API를 테스트하세요:\n")
    
    logger.info("1. 현재 가중치 조회:")
    logger.info("   curl http://localhost:8001/api/weights/current\n")
    
    logger.info("2. 가중치 재계산:")
    logger.info("   curl -X POST http://localhost:8001/api/weights/recalculate?lookback_days=30\n")
    
    logger.info("3. 가중치 변경 이력:")
    logger.info("   curl http://localhost:8001/api/weights/history?days=7\n")
    
    logger.info("4. 최근 경고 목록:")
    logger.info("   curl http://localhost:8001/api/alerts/recent?hours=24\n")
    
    logger.info("5. 경고 요약:")
    logger.info("   curl http://localhost:8001/api/alerts/summary?hours=24\n")
    
    logger.info("6. 경고 체크 수동 트리거:")
    logger.info("   curl -X POST http://localhost:8001/api/alerts/check?lookback_days=30\n")
    
    return True


async def test_daily_learning_cycle():
    """일일 학습 사이클 테스트 (실행 안 함, 설명만)"""
    logger.info("=" * 80)
    logger.info("TEST 4: Daily Learning Cycle (Dry Run)")
    logger.info("=" * 80)
    
    logger.info("\n일일 학습 사이클 실행 방법:\n")
    logger.info("  python backend/automation/price_tracking_scheduler.py\n")
    
    logger.info("이 스크립트는:")
    logger.info("  1. 24시간 후 성과 평가 (Consensus + Agent Votes)")
    logger.info("  2. 가중치 재계산")
    logger.info("  3. 경고 체크 (저성과/오버컨피던트)")
    logger.info("를 순서대로 실행합니다.\n")
    
    logger.info("⚠️  주의: 실제 DB에 데이터를 쓰므로 테스트 환경에서만 실행하세요!\n")
    
    return True


async def main():
    """모든 테스트 실행"""
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("Phase 25.4 - Self-Learning System Test Suite")
    logger.info("=" * 80)
    logger.info("\n")
    
    results = []
    
    # Test 1: Weight Adjuster
    result1 = await test_weight_adjuster()
    results.append(("Weight Adjuster", result1))
    
    # Test 2: Alert System
    result2 = await test_alert_system()
    results.append(("Alert System", result2))
    
    # Test 3: API Endpoints (manual)
    result3 = await test_api_endpoints()
    results.append(("API Endpoints", result3))
    
    # Test 4: Daily Learning Cycle (dry run)
    result4 = await test_daily_learning_cycle()
    results.append(("Daily Learning Cycle", result4))
    
    # Summary
    logger.info("=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
