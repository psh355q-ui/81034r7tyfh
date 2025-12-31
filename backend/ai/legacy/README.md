# Legacy Agents

**Date:** 2025-12-31
**Status:** DEPRECATED - Moved to Legacy

## Purpose

This directory contains the original 8-9 agent system that has been consolidated into the MVP 3+1 system.

## Legacy Agent Structure

### Debate Agents (8 agents):
1. **Trader Agent** → Consolidated into **Trader Agent MVP**
2. **Risk Agent** → Consolidated into **Risk Agent MVP**
3. **Sentiment Agent** → Absorbed by **Risk Agent MVP**
4. **News Agent** → Absorbed by **Analyst Agent MVP**
5. **Analyst Agent** → Absorbed by **Analyst Agent MVP**
6. **Macro Agent** → Absorbed by **Analyst Agent MVP**
7. **Institutional Agent** → Absorbed by **Analyst Agent MVP**
8. **ChipWar Agent** → Split:
   - Opportunities → **Trader Agent MVP**
   - Geopolitics → **Analyst Agent MVP**

### Supporting Agents:
- **Skeptic Agent** → Replaced by **PM Agent MVP** (Hard Rules)
- **DividendRisk Agent** → Absorbed by **Risk Agent MVP**

## Why Legacy?

**Problems with 8-9 Agent System:**
1. **High Cost:** $0.50-1.00 per deliberation (Gemini API calls)
2. **Slow Speed:** 30-60 seconds per decision
3. **Over-Engineering:** Too many agents for simple decisions
4. **Noise Learning:** Daily failure tracking caused false learning

**MVP 3+1 System Benefits:**
1. **67% Cost Reduction:** 9 agents → 4 agents
2. **67% Speed Improvement:** Fewer API calls
3. **Clearer Responsibilities:** Attack / Defense / Information
4. **Position Sizing:** NEW feature (ChatGPT recommendation)
5. **Hard Rules:** Code-enforced, not AI-interpreted
6. **Silence Policy:** Right to refuse judgment

## Migration Path

- **Phase 1 (Current):** MVP system development
- **Phase 2:** Shadow Trading validation (3 months)
- **Phase 3:** $100 real money test (1 week)
- **Phase 4:** Full migration (if successful)
- **Phase 5:** Delete legacy agents (after 6 months)

## Archived Components

```
legacy/
├── debate/              # Original 8 debate agents
│   ├── trader_agent.py
│   ├── risk_agent.py
│   ├── sentiment_agent.py
│   ├── news_agent.py
│   ├── analyst_agent.py
│   ├── macro_agent.py
│   ├── institutional_agent.py
│   ├── chip_war_agent.py
│   └── skeptic_agent.py
└── README.md (this file)
```

## Reference Only

**DO NOT USE THESE AGENTS IN PRODUCTION.**

They are kept for:
1. Reference during MVP development
2. Comparison benchmarks
3. Rollback if MVP fails validation

## Contact

For questions about legacy agents or migration:
- See: `docs/MVP_IMPLEMENTATION_PLAN.md`
- See: `docs/ai토론/` (AI discussion analysis)

---

**Last Updated:** 2025-12-31
**Author:** AI Trading System Team
