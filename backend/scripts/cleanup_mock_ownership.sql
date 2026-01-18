-- KIS Portfolio Ownership Auto-Sync: Mock Data Cleanup
-- 기존 테스트 데이터 삭제 후 실제 KIS 포트폴리오와 동기화

-- 1. 기존 mock ownership 데이터 삭제 (CFT_TEST 등)
DELETE FROM position_ownership
WHERE
    reasoning LIKE '%test%'
    OR ticker = 'CFT_TEST';

-- 2. 모든 기존 ownership 삭제 (선택적 - 새로 시작할 경우)
-- DELETE FROM position_ownership;

-- 3. 확인: 현재 ownership 상태
SELECT po.ticker, po.ownership_type, s.name as strategy_name, s.persona_type, po.reasoning, po.created_at
FROM
    position_ownership po
    JOIN strategies s ON po.strategy_id = s.id
ORDER BY po.created_at DESC;

-- 4. 확인: 사용 가능한 전략 목록
SELECT
    id,
    name,
    display_name,
    persona_type,
    priority,
    is_active
FROM strategies
ORDER BY priority DESC;