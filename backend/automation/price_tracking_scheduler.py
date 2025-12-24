"""
Price Tracking Scheduler - 24시간 후 가격 조회 및 성과 평가

Phase 25.1: Agent Performance Tracking
Date: 2025-12-23

Features:
- 24시간이 지난 PENDING 상태의 price_tracking 레코드 조회
- 현재 가격 조회 (KIS API)
- 수익률 계산
- 에이전트 성과 평가
- 상태 업데이트 (PENDING → COMPLETED)

Usage:
    python backend/automation/price_tracking_scheduler.py
"""

import asyncio
import psycopg2
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_kis_broker():
    """Get KIS Broker instance"""
    try:
        from backend.brokers.kis_broker import KISBroker

        account_no = os.environ.get("KIS_ACCOUNT_NUMBER", "")
        is_virtual = os.environ.get("KIS_IS_VIRTUAL", "true").lower() == "true"

        if not account_no:
            logger.error("KIS_ACCOUNT_NUMBER not set")
            return None

        broker = KISBroker(account_no=account_no, is_virtual=is_virtual)
        return broker

    except Exception as e:
        logger.error(f"Failed to initialize KIS Broker: {e}")
        return None


def evaluate_performance(
    consensus_action: str,
    return_pct: float,
    consensus_confidence: float
) -> tuple[bool, float]:
    """
    Evaluate agent performance

    Args:
        consensus_action: BUY, SELL, HOLD
        return_pct: Actual return percentage
        consensus_confidence: Consensus confidence

    Returns:
        (is_correct, performance_score)

    Logic:
        - BUY: Correct if return_pct > 0
        - SELL: Correct if return_pct < 0
        - HOLD: Correct if abs(return_pct) < 2%
        - performance_score = return_pct * consensus_confidence (weighted)
    """
    is_correct = False

    if consensus_action == "BUY":
        is_correct = return_pct > 0
    elif consensus_action == "SELL":
        is_correct = return_pct < 0
    elif consensus_action == "HOLD":
        is_correct = abs(return_pct) < 2.0  # ±2% range for HOLD

    # Weighted performance score
    if is_correct:
        performance_score = abs(return_pct) * consensus_confidence
    else:
        performance_score = -abs(return_pct) * consensus_confidence

    return is_correct, performance_score


async def evaluate_pending_tracking():
    """Evaluate PENDING price_tracking records (24h+ old)"""

    logger.info("=" * 80)
    logger.info("🔍 Price Tracking Evaluation - 24h Later")
    logger.info("=" * 80)

    # DB connection
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "ai_trading"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

    cursor = conn.cursor()

    # Get KIS Broker
    broker = get_kis_broker()
    if not broker:
        logger.error("KIS Broker not available - aborting")
        return

    try:
        # Find PENDING records older than 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)

        cursor.execute("""
            SELECT
                id, session_id, ticker, initial_price, initial_timestamp,
                consensus_action, consensus_confidence
            FROM price_tracking
            WHERE status = 'PENDING'
            AND initial_timestamp <= %s
            ORDER BY initial_timestamp ASC
        """, (cutoff_time,))

        pending_records = cursor.fetchall()

        logger.info(f"\n📊 Found {len(pending_records)} PENDING records to evaluate\n")

        if not pending_records:
            logger.info("✅ No pending records to evaluate")
            return

        evaluated_count = 0
        failed_count = 0

        for record in pending_records:
            (tracking_id, session_id, ticker, initial_price, initial_timestamp,
             consensus_action, consensus_confidence) = record

            logger.info(f"┌─ Evaluating #{tracking_id} ─────────────────────")
            logger.info(f"│ Session: #{session_id}")
            logger.info(f"│ Ticker: {ticker}")
            logger.info(f"│ Initial Price: ${initial_price}")
            logger.info(f"│ Initial Time: {initial_timestamp}")
            logger.info(f"│ Consensus: {consensus_action} ({consensus_confidence:.1%})")

            try:
                # Get current price from KIS
                price_data = broker.get_price(ticker, exchange="NASDAQ")

                if not price_data:
                    logger.warning(f"│ ⚠️  Failed to get current price for {ticker}")
                    cursor.execute("""
                        UPDATE price_tracking
                        SET status = 'FAILED',
                            notes = 'Failed to fetch final price',
                            evaluated_at = NOW()
                        WHERE id = %s
                    """, (tracking_id,))
                    conn.commit()
                    failed_count += 1
                    logger.info(f"└─────────────────────────────────────────\n")
                    continue

                final_price = price_data["current_price"]
                final_timestamp = datetime.now()

                # Calculate returns
                price_change = final_price - initial_price
                return_pct = (price_change / initial_price) * 100

                # Evaluate performance
                is_correct, performance_score = evaluate_performance(
                    consensus_action=consensus_action,
                    return_pct=return_pct,
                    consensus_confidence=consensus_confidence
                )

                # Update database
                cursor.execute("""
                    UPDATE price_tracking
                    SET final_price = %s,
                        final_timestamp = %s,
                        price_change = %s,
                        return_pct = %s,
                        is_correct = %s,
                        performance_score = %s,
                        status = 'COMPLETED',
                        evaluated_at = NOW()
                    WHERE id = %s
                """, (
                    final_price,
                    final_timestamp,
                    price_change,
                    return_pct,
                    is_correct,
                    performance_score,
                    tracking_id
                ))
                conn.commit()

                # Log results
                logger.info(f"│ ")
                logger.info(f"│ 📈 Final Price: ${final_price}")
                logger.info(f"│ 📊 Price Change: ${price_change:+.2f} ({return_pct:+.2f}%)")
                logger.info(f"│ ")
                logger.info(f"│ 🎯 Evaluation:")
                logger.info(f"│    Correct: {'✅ YES' if is_correct else '❌ NO'}")
                logger.info(f"│    Performance Score: {performance_score:+.4f}")
                logger.info(f"│ ")
                logger.info(f"│ ✅ Status: COMPLETED")
                logger.info(f"└─────────────────────────────────────────\n")

                evaluated_count += 1

            except Exception as e:
                logger.error(f"│ ❌ Error evaluating #{tracking_id}: {e}")
                cursor.execute("""
                    UPDATE price_tracking
                    SET status = 'FAILED',
                        notes = %s,
                        evaluated_at = NOW()
                    WHERE id = %s
                """, (str(e), tracking_id))
                conn.commit()
                failed_count += 1
                logger.info(f"└─────────────────────────────────────────\n")

        # Summary
        logger.info("=" * 80)
        logger.info("📊 Evaluation Summary")
        logger.info("=" * 80)
        logger.info(f"✅ Evaluated: {evaluated_count}")
        logger.info(f"❌ Failed: {failed_count}")
        logger.info(f"📊 Total: {len(pending_records)}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Error in evaluation: {e}", exc_info=True)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()


async def evaluate_agent_votes_tracking():
    """
    Evaluate PENDING agent vote tracking records (24h+ old)

    Phase 25.3: Agent Performance Tracking
    """
    from backend.database.repository import get_database_url
    import psycopg2

    logger.info("=" * 80)
    logger.info("🔍 Agent Vote Tracking Evaluation - 24h Later")
    logger.info("=" * 80)

    # Connect to database
    db_url = get_database_url()
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    try:
        # Find PENDING agent votes that are 24+ hours old
        cursor.execute("""
            SELECT
                id, session_id, agent_name, vote_action, vote_confidence,
                ticker, initial_price, initial_timestamp
            FROM agent_vote_tracking
            WHERE status = 'PENDING'
                AND initial_timestamp <= NOW() - INTERVAL '24 hours'
            ORDER BY initial_timestamp ASC
        """)

        pending_votes = cursor.fetchall()

        if not pending_votes:
            logger.info("✅ No pending agent votes to evaluate")
            return

        logger.info(f"\n📊 Found {len(pending_votes)} PENDING agent votes to evaluate\n")

        evaluated_count = 0
        failed_count = 0

        for vote in pending_votes:
            (
                vote_id, session_id, agent_name, vote_action, vote_confidence,
                ticker, initial_price, initial_timestamp
            ) = vote

            try:
                logger.info(f"┌─ Evaluating Agent Vote #{vote_id} ─────────────────────")
                logger.info(f"│ Session: #{session_id}")
                logger.info(f"│ Agent: {agent_name}")
                logger.info(f"│ Ticker: {ticker}")
                logger.info(f"│ Vote: {vote_action} ({vote_confidence * 100:.1f}%)")
                logger.info(f"│ Initial Price: ${initial_price}")
                logger.info(f"│ Initial Time: {initial_timestamp}")
                logger.info(f"│ ")

                # Get current price
                account_no = os.environ.get("KIS_ACCOUNT_NUMBER", "")
                is_virtual = os.environ.get("KIS_IS_VIRTUAL", "true").lower() == "true"

                if not account_no:
                    logger.warning("KIS_ACCOUNT_NUMBER not set - skipping")
                    failed_count += 1
                    continue

                broker = KISBroker(account_no=account_no, is_virtual=is_virtual)
                price_data = broker.get_price(ticker, exchange="NASDAQ")

                if not price_data:
                    logger.warning(f"Failed to get price for {ticker} - marking as FAILED")
                    cursor.execute("""
                        UPDATE agent_vote_tracking
                        SET status = 'FAILED', evaluated_at = NOW()
                        WHERE id = %s
                    """, (vote_id,))
                    conn.commit()
                    failed_count += 1
                    continue

                final_price = price_data["current_price"]
                final_timestamp = datetime.now()

                # Calculate return
                price_change = final_price - initial_price
                return_pct = (price_change / initial_price) * 100

                # Evaluate performance (same logic as consensus)
                is_correct, performance_score = evaluate_performance(
                    consensus_action=vote_action,
                    return_pct=return_pct,
                    consensus_confidence=vote_confidence
                )

                # Update database
                cursor.execute("""
                    UPDATE agent_vote_tracking
                    SET final_price = %s,
                        final_timestamp = %s,
                        return_pct = %s,
                        is_correct = %s,
                        performance_score = %s,
                        status = 'COMPLETED',
                        evaluated_at = NOW()
                    WHERE id = %s
                """, (
                    final_price,
                    final_timestamp,
                    return_pct,
                    is_correct,
                    performance_score,
                    vote_id
                ))
                conn.commit()

                # Log results
                logger.info(f"│ 📈 Final Price: ${final_price}")
                logger.info(f"│ 📊 Return: {return_pct:+.2f}%")
                logger.info(f"│ 🎯 Correct: {'✅ YES' if is_correct else '❌ NO'}")
                logger.info(f"│ ⭐ Score: {performance_score:+.4f}")
                logger.info(f"│ ✅ Status: COMPLETED")
                logger.info(f"└─────────────────────────────────────────\n")

                evaluated_count += 1

            except Exception as e:
                logger.error(f"│ ❌ Error evaluating vote #{vote_id}: {e}")
                cursor.execute("""
                    UPDATE agent_vote_tracking
                    SET status = 'FAILED', evaluated_at = NOW()
                    WHERE id = %s
                """, (vote_id,))
                conn.commit()
                failed_count += 1
                logger.info(f"└─────────────────────────────────────────\n")

        # Summary
        logger.info("=" * 80)
        logger.info("📊 Agent Vote Evaluation Summary")
        logger.info("=" * 80)
        logger.info(f"✅ Evaluated: {evaluated_count}")
        logger.info(f"❌ Failed: {failed_count}")
        logger.info(f"📊 Total: {len(pending_votes)}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Error in agent vote evaluation: {e}", exc_info=True)
        conn.rollback()

    finally:
        conn.close()


async def daily_learning_cycle():
    """
    일일 학습 사이클 - Phase 25.4
    
    실행 순서:
    1. 24시간 후 성과 평가 (Consensus + Agent Votes)
    2. 가중치 재계산
    3. 경고 체크 (저성과/오버컨피던트)
    
    실행 시점: 매일 자정 (cron: 0 0 * * *)
    """
    logger.info("=" * 80)
    logger.info("🧠 Daily Learning Cycle - Phase 25.4")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("")
    
    # Step 1: 24시간 후 성과 평가
    logger.info("Step 1/3: Evaluating 24h performance...")
    logger.info("")
    
    await evaluate_pending_tracking()  # Consensus
    await evaluate_agent_votes_tracking()  # Individual agents
    
    logger.info("")
    
    # Step 2: 가중치 재계산
    logger.info("Step 2/3: Recalculating agent weights...")
    logger.info("")
    
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from ai.learning.agent_weight_adjuster import AgentWeightAdjuster
        
        adjuster = AgentWeightAdjuster()
        results = await adjuster.recalculate_all_weights(lookback_days=30, save_to_db=True)
        
        logger.info("✅ Weight recalculation completed")
        for agent, data in results.items():
            logger.info(
                f"  {agent}: {data['old_weight']:.3f} → {data['new_weight']:.3f} "
                f"({data['reason']})"
            )
    
    except Exception as e:
        logger.error(f"❌ Failed to recalculate weights: {e}")
    
    logger.info("")
    
    # Step 3: 경고 체크
    logger.info("Step 3/3: Checking for alerts...")
    logger.info("")
    
    try:
        from ai.learning.agent_alert_system import AgentAlertSystem
        
        alert_system = AgentAlertSystem()
        alerts = await alert_system.check_all_alerts(lookback_days=30)
        
        logger.info(f"✅ Alert check completed")
        logger.info(f"  Underperformance alerts: {len(alerts['underperformance'])}")
        logger.info(f"  Overconfidence alerts: {len(alerts['overconfidence'])}")
    
    except Exception as e:
        logger.error(f"❌ Failed to check alerts: {e}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ Daily Learning Cycle Completed")
    logger.info(f"Finished at: {datetime.now().isoformat()}")
    logger.info("=" * 80)


if __name__ == "__main__":
    # Run daily learning cycle (all steps)
    asyncio.run(daily_learning_cycle())
