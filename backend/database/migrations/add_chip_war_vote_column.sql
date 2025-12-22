-- Phase 24: Add chip_war_vote column to ai_debate_sessions
-- Date: 2025-12-23
-- Purpose: Support ChipWarAgent (8th agent) in War Room

-- Add chip_war_vote column
ALTER TABLE ai_debate_sessions
ADD COLUMN chip_war_vote VARCHAR(10);

-- Add comment
COMMENT ON COLUMN ai_debate_sessions.chip_war_vote IS 'Chip War Agent vote (Phase 24: NVDA vs GOOGL TPU competition)';

-- Verify
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'ai_debate_sessions'
  AND column_name = 'chip_war_vote';
