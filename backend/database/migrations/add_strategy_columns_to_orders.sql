-- ====================================
-- Multi-Strategy Orchestration: Extend orders table
-- ====================================
-- Generated: 2026-01-11
-- Phase: 0, Task: T0.1
-- Description: orders 테이블에 전략 추적 및 충돌 검사 결과 컬럼 추가
-- ====================================

-- Add strategy_id column (VARCHAR(36) to match Strategy.id)
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS strategy_id VARCHAR(36);

-- Add conflict check columns
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS conflict_check_passed BOOLEAN DEFAULT FALSE;

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS conflict_reasoning TEXT;

-- Add foreign key constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_orders_strategy'
        AND table_name = 'orders'
    ) THEN
        ALTER TABLE orders
        ADD CONSTRAINT fk_orders_strategy
        FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Create index for strategy_id
CREATE INDEX IF NOT EXISTS idx_orders_strategy_id ON orders(strategy_id);

-- Create composite index for strategy + status queries
CREATE INDEX IF NOT EXISTS idx_orders_strategy_status ON orders(strategy_id, status);

-- Add column comments
COMMENT ON COLUMN orders.strategy_id IS '주문을 생성한 전략 ID. 전략별 성과 추적 및 충돌 검사에 사용';
COMMENT ON COLUMN orders.conflict_check_passed IS '충돌 검사 통과 여부. TRUE: 충돌 없음, FALSE: 충돌 감지되어 차단됨';
COMMENT ON COLUMN orders.conflict_reasoning IS '충돌 검사 결과 설명. 차단된 경우 이유 포함 (AI 설명 가능성)';

-- Verification
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'orders' AND column_name = 'strategy_id'
    ) THEN
        RAISE NOTICE 'Column strategy_id added to orders table successfully';
    END IF;
END $$;

-- ====================================
-- Migration Complete
-- ====================================
