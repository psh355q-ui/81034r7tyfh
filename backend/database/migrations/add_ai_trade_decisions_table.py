"""
Add AI Trade Decisions Table - v2.3

트레이딩 프로토콜 저장용 테이블
- JSON 원본 저장 (JSONB)
- 주요 필드 인덱싱 (검색/분석용)
- 백테스트 검증 지원

작성일: 2026-01-24
"""

import logging
from sqlalchemy import text
from backend.database.repository import get_sync_session

logger = logging.getLogger(__name__)


def upgrade():
    """AI 트레이딩 결정 테이블 생성"""
    print("🔄 Creating ai_trade_decisions table...")

    db = get_sync_session()

    try:
        # 테이블 존재 여부 확인
        check_sql = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'ai_trade_decisions'
            );
        """)
        result = db.execute(check_sql)
        exists = result.scalar()

        if exists:
            print("⚠️ ai_trade_decisions table already exists, skipping creation")
            return

        # 테이블 생성
        create_sql = text("""
            CREATE TABLE ai_trade_decisions (
                -- PK
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ DEFAULT NOW(),

                -- 핵심 메타데이터 (인덱싱용)
                mode VARCHAR(20) NOT NULL,              -- CLOSING, MORNING, INTRADAY, KOREAN
                execution_intent VARCHAR(20) NOT NULL,  -- AUTO, HUMAN_APPROVAL
                market_trend VARCHAR(10),               -- UP, SIDE, DOWN
                risk_level VARCHAR(10),                 -- LOW, MEDIUM, HIGH
                risk_score INTEGER,                     -- 0-100

                -- 전체 JSON 데이터
                full_report_json JSONB NOT NULL,

                -- 백테스트용 (JSON에서 추출)
                target_asset VARCHAR(50),
                suggested_action VARCHAR(20),
                suggested_size_pct NUMERIC(5, 4),       -- -1.0000 ~ 1.0000
                expected_rr_ratio NUMERIC(5, 2),        -- 기대 손익비

                -- 사후 검증용 (트레이딩 후 업데이트)
                actual_profit_loss NUMERIC(12, 2),
                is_strategy_correct BOOLEAN,
                validated_at TIMESTAMPTZ,
                validation_notes TEXT,

                -- 버전 관리
                model_version VARCHAR(100),
                prompt_version VARCHAR(50) DEFAULT 'v2.3',

                -- 연관 브리핑 (선택)
                briefing_file_path VARCHAR(255),

                -- 감사
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        db.execute(create_sql)

        # 인덱스 생성
        indexes = [
            "CREATE INDEX idx_ai_decisions_created_at ON ai_trade_decisions(created_at DESC);",
            "CREATE INDEX idx_ai_decisions_mode ON ai_trade_decisions(mode);",
            "CREATE INDEX idx_ai_decisions_intent ON ai_trade_decisions(execution_intent);",
            "CREATE INDEX idx_ai_decisions_risk ON ai_trade_decisions(risk_level);",
            "CREATE INDEX idx_ai_decisions_trend ON ai_trade_decisions(market_trend);",
            "CREATE INDEX idx_ai_decisions_asset ON ai_trade_decisions(target_asset);",
            "CREATE INDEX idx_ai_decisions_validated ON ai_trade_decisions(is_strategy_correct) WHERE is_strategy_correct IS NOT NULL;",
            # JSONB 인덱스 (검색 최적화)
            "CREATE INDEX idx_ai_decisions_json_gin ON ai_trade_decisions USING GIN (full_report_json);",
        ]

        for idx_sql in indexes:
            db.execute(text(idx_sql))

        db.commit()
        print("✅ ai_trade_decisions table created with indexes")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create ai_trade_decisions table: {e}")
        raise
    finally:
        db.close()


def downgrade():
    """테이블 삭제"""
    print("🔄 Dropping ai_trade_decisions table...")

    db = get_sync_session()

    try:
        # 인덱스 삭제 (테이블 삭제 시 자동 삭제되지만 명시적으로)
        drop_indexes = [
            "DROP INDEX IF EXISTS idx_ai_decisions_json_gin;",
            "DROP INDEX IF EXISTS idx_ai_decisions_validated;",
            "DROP INDEX IF EXISTS idx_ai_decisions_asset;",
            "DROP INDEX IF EXISTS idx_ai_decisions_trend;",
            "DROP INDEX IF EXISTS idx_ai_decisions_risk;",
            "DROP INDEX IF EXISTS idx_ai_decisions_intent;",
            "DROP INDEX IF EXISTS idx_ai_decisions_mode;",
            "DROP INDEX IF EXISTS idx_ai_decisions_created_at;",
        ]

        for idx_sql in drop_indexes:
            db.execute(text(idx_sql))

        # 테이블 삭제
        db.execute(text("DROP TABLE IF EXISTS ai_trade_decisions;"))

        db.commit()
        print("✅ ai_trade_decisions table dropped")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to drop ai_trade_decisions table: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
