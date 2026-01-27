# System Structure Map
Auto-generated: 2026-01-28 00:40:00

## Phase 0: Meta-Controller V2 Components (Added 2026-01-27~28)

**New Risk Management System**:

```
backend/ai/
├── 📄 correlation_shock_detector.py  (163 lines) - Portfolio correlation spike detection
├── 📄 drawdown_recovery.py            (133 lines) - Automatic defensive mode switching
├── 📄 meta_controller_v2.py           (298 lines) - 3-axis risk integration (VIX+Corr+DD)
└── 📄 liquidity_guardian.py           (283 lines) - Pre-execution liquidity validation

tests/
├── test_correlation_shock_detector.py  (199 lines)
├── test_drawdown_recovery.py           (173 lines)
├── test_meta_controller_v2.py          (281 lines)
├── test_liquidity_guardian.py          (283 lines)
└── integration/
    └── test_meta_controller_backtest.py (350 lines) - COVID-19 crash simulation

docs/validation/
└── meta_controller_v2_backtest_report.md - Historical validation report
```

**Integration**: `backend/ai/mvp/war_room_mvp.py` (Line 76 - MetaControllerV2)

**Status**: ✅ Complete - Commercial-grade risk management system validated

---

## 1. Directory Structure

```text
backend/
├── 📂 .claude/
│   └── 📂 skills/
├── 📄 API_TESTING_GUIDE.md
├── 📄 README.md
├── 📄 __init__.py
├── 📂 ab_test_quick/
├── 📂 ai/
│   ├── 📄 __init__.py
│   ├── 📂 agents/
│   │   └── 📄 failure_learning_agent.py
│   ├── 📄 ai_client_factory.py
│   ├── 📄 ai_review_models.py
│   ├── 📂 analysis/
│   │   └── 📄 thesis_violation_detector.py
│   ├── 📄 analysis_validator.py
│   ├── 📄 chatgpt_client.py
│   ├── 📄 claude_client.py
│   ├── 📂 collective/
│   │   ├── 📄 __init__.py
│   │   └── 📄 ai_role_manager.py
│   ├── 📂 compression/
│   │   ├── 📄 __init__.py
│   │   └── 📄 llmlingua_compressor.py
│   ├── 📂 consensus/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 consensus_engine.py
│   │   ├── 📄 consensus_models.py
│   │   └── 📄 voting_rules.py
│   ├── 📂 core/
│   │   ├── 📄 __init__.py
│   │   └── 📄 decision_protocol.py
│   ├── 📂 cost/
│   │   ├── 📄 __init__.py
│   │   └── 📄 subscription_manager.py
│   ├── 📂 council/
│   │   ├── 📄 __init__.py
│   │   └── 📄 adaptive_weight_manager.py
│   ├── 📂 debate/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 ai_debate_engine.py
│   │   ├── 📄 analyst_agent.py
│   │   ├── 📄 chip_war_agent.py
│   │   ├── 📄 chip_war_agent_helpers.py
│   │   ├── 📄 constitutional_debate_engine.py
│   │   ├── 📄 institutional_agent.py
│   │   ├── 📄 macro_agent.py
│   │   ├── 📄 news_agent.py
│   │   ├── 📄 priority_calculator.py
│   │   ├── 📄 risk_agent.py
│   │   ├── 📄 sentiment_agent.py
│   │   ├── 📄 skeptic_agent.py
│   │   └── 📄 trader_agent.py
│   ├── 📂 economics/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 chip_efficiency_comparator.py
│   │   ├── 📄 chip_intelligence_engine.py
│   │   ├── 📄 chip_war_simulator.py
│   │   ├── 📄 chip_war_simulator_v2.py
│   │   └── 📄 unit_economics_engine.py
│   ├── 📄 embedding_engine.py
│   ├── 📄 enhanced_analysis_cache.py
│   ├── 📄 enhanced_trading_agent.py
│   ├── 📄 ensemble_optimizer.py
│   ├── 📄 failover_manager.py
│   ├── 📄 gemini_client.py
│   ├── 📄 glm_client.py
│   ├── 📄 glm_client_v2.py
│   ├── 📂 intelligence/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 chart_generator.py
│   │   ├── 📄 contrary_signal.py
│   │   ├── 📄 enhanced_news_pipeline.py
│   │   ├── 📄 fact_checker.py
│   │   ├── 📄 horizon_tagger.py
│   │   ├── 📄 insight_postmortem.py
│   │   ├── 📄 market_confirmation.py
│   │   ├── 📄 market_moving_score.py
│   │   ├── 📄 narrative_fatigue.py
│   │   ├── 📄 narrative_state_engine.py
│   │   ├── 📄 news_filter.py
│   │   ├── 📄 policy_feasibility.py
│   │   ├── 📂 prompts/
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 persona_tuned_prompts.py
│   │   ├── 📄 regime_guard.py
│   │   ├── 📄 semantic_weight_adjuster.py
│   │   └── 📄 test_phase3.py
│   ├── 📂 learning/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 agent_alert_system.py
│   │   ├── 📄 agent_weight_adjuster.py
│   │   ├── 📄 agent_weight_manager.py
│   │   ├── 📄 alert_system.py
│   │   ├── 📄 daily_learning_scheduler.py
│   │   ├── 📄 feedback_loop_service.py
│   │   ├── 📄 hallucination_detector.py
│   │   ├── 📄 learning_orchestrator.py
│   │   ├── 📄 news_agent_learning.py
│   │   ├── 📄 remaining_agents_learning.py
│   │   ├── 📄 risk_agent_learning.py
│   │   ├── 📄 statistical_validators.py
│   │   ├── 📄 trader_agent_learning.py
│   │   └── 📄 walk_forward_validator.py
│   ├── 📂 legacy/
│   │   └── 📄 README.md
│   ├── 📂 llm/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 local_embeddings.py
│   │   └── 📄 ollama_client.py
│   ├── 📄 llm_providers.py
│   ├── 📂 macro/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 country_risk_engine.py
│   │   ├── 📄 global_event_graph.py
│   │   ├── 📄 global_market_map.py
│   │   ├── 📄 macro_analyzer_agent.py
│   │   └── 📄 macro_data_collector.py
│   ├── 📄 market_regime.py
│   ├── 📂 memory/
│   │   ├── 📄 __init__.py
│   │   └── 📄 investment_journey_memory.py
│   ├── 📂 meta/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 agent_weight_trainer.py
│   │   ├── 📄 ai_meta_analyzer.py
│   │   ├── 📄 autobiography_engine.py
│   │   ├── 📄 debate_logger.py
│   │   └── 📄 strategy_refiner.py
│   ├── 📄 model_comparison.py
│   ├── 📄 model_registry.py
│   ├── 📄 model_utils.py
│   ├── 📂 monitoring/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 bias_monitor.py
│   │   └── 📄 watchtower_triggers.py
│   ├── 📂 mvp/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 analyst_agent_mvp.py
│   │   ├── 📄 conflict_resolver.py
│   │   ├── 📄 data_helper.py
│   │   ├── 📂 deprecated/
│   │   │   ├── 📄 analyst_agent_mvp.py
│   │   │   ├── 📄 risk_agent_mvp.py
│   │   │   ├── 📄 trader_agent_mvp.py
│   │   │   └── 📄 war_room_mvp.py
│   │   ├── 📄 enhanced_data_provider.py
│   │   ├── 📄 gemini_reasoning_agent_base.py
│   │   ├── 📄 gemini_structuring_agent.py
│   │   ├── 📄 pm_agent_mvp.py
│   │   ├── 📄 reasoning_agent_base.py
│   │   ├── 📄 risk_agent_mvp.py
│   │   ├── 📂 stock_specific/
│   │   │   ├── 📄 base_analyzer.py
│   │   │   ├── 📄 nvda_analyzer.py
│   │   │   └── 📄 tsla_analyzer.py
│   │   ├── 📄 structuring_agent.py
│   │   ├── 📄 test_phase4.py
│   │   ├── 📄 ticker_mappings.py
│   │   ├── 📄 trader_agent_mvp.py
│   │   └── 📄 war_room_mvp.py
│   ├── 📂 news/
│   │   ├── 📄 __init__.py
│   │   └── 📄 news_segment_classifier.py
│   ├── 📄 news_auto_tagger.py
│   ├── 📄 news_context_filter.py
│   ├── 📄 news_embedder.py
│   ├── 📄 news_intelligence_analyzer.py
│   ├── 📄 news_processing_pipeline.py
│   ├── 📂 options/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 smart_options_analyzer.py
│   │   └── 📄 whale_detector.py
│   ├── 📂 order_execution/
│   │   └── 📄 shadow_order_executor.py
│   ├── 📂 portfolio/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 account_partitioning.py
│   │   └── 📄 tax_optimizer.py
│   ├── 📂 profiling/
│   │   └── 📄 deep_profiler.py
│   ├── 📄 prompt_caching.py
│   ├── 📂 rag/
│   │   └── 📄 embedding_service.py
│   ├── 📄 rag_enhanced_analysis.py
│   ├── 📂 reasoning/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 cot_prompts.py
│   │   ├── 📄 deep_reasoning.py
│   │   ├── 📄 deep_reasoning_agent.py
│   │   ├── 📄 engine.py
│   │   ├── 📄 heuristics.py
│   │   ├── 📄 macro_consistency.py
│   │   ├── 📄 macro_consistency_checker.py
│   │   ├── 📄 models.py
│   │   ├── 📄 prompts.py
│   │   ├── 📄 rag_deep_reasoning.py
│   │   └── 📄 skeptic_agent.py
│   ├── 📄 regime_detector.py
│   ├── 📂 reporters/
│   │   ├── 📄 ai_market_reporter.py
│   │   ├── 📄 annual_reporter.py
│   │   ├── 📄 briefing_mode.py
│   │   ├── 📄 enhanced_daily_reporter.py
│   │   ├── 📄 funnel_generator.py
│   │   ├── 📄 monthly_reporter.py
│   │   ├── 📄 prompt_builder.py
│   │   ├── 📄 quarterly_reporter.py
│   │   ├── 📄 report_orchestrator.py
│   │   ├── 📂 schemas/
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 trading_protocol.py
│   │   ├── 📄 test_phase5.py
│   │   ├── 📄 trending_news_detector.py
│   │   ├── 📄 us_market_close_reporter.py
│   │   └── 📄 weekly_reporter.py
│   ├── 📂 risk/
│   │   ├── 📄 __init__.py
│   │   └── 📄 theme_risk_detector.py
│   ├── 📂 router/
│   │   ├── 📄 __init__.py
│   │   └── 📄 persona_router.py
│   ├── 📂 safety/
│   │   ├── 📄 __init__.py
│   │   └── 📄 leverage_guardian.py
│   ├── 📂 scenarios/
│   │   └── 📄 scenario_simulator.py
│   ├── 📂 schemas/
│   │   └── 📄 war_room_schemas.py
│   ├── 📄 correlation_shock_detector.py
│   ├── 📄 drawdown_recovery.py
│   ├── 📄 liquidity_guardian.py
│   ├── 📄 meta_controller_v2.py
│   ├── 📄 sec_analyzer.py
│   ├── 📄 sec_prompts.py
│   ├── 📂 skills/
│   │   ├── 📄 __init__.py
│   │   ├── 📂 analysis/
│   │   │   ├── 📂 ceo-speech-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   ├── 📂 deep-reasoning-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   ├── 📂 emergency-news-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   ├── 📂 news-intelligence-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   └── 📂 quick-analyzer-agent/
│   │   │       └── 📄 SKILL.md
│   │   ├── 📄 base_agent.py
│   │   ├── 📂 common/
│   │   │   ├── 📄 README.md
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 agent_logger.py
│   │   │   ├── 📄 generate_logs.py
│   │   │   ├── 📄 log_schema.py
│   │   │   ├── 📄 logging_decorator.py
│   │   │   ├── 📄 test_logging.py
│   │   │   └── 📄 test_war_room_logging.py
│   │   ├── 📂 debugging/
│   │   │   └── 📂 proposals/
│   │   │       ├── 📄 proposal-20251226-101650-system-signal-consolidation-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-101650-system-signal-generator-agent-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-101650-war-room-war-room-debate-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-131146-system-signal-consolidation-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-131146-system-signal-generator-agent-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-131146-war-room-war-room-debate-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-analysis-ceo_analysis-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-analysis-ceo_analysis-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-ai_chat-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-ai_chat-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-ai_reviews-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-ai_reviews-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-backfill-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-backfill-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-consensus-performance_degradation.md
│   │   │       ├── 📄 proposal-20251226-160707-system-gemini_free-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-gemini_free-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-global_macro-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-global_macro-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-incremental-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-incremental-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-kis-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-kis-performance_degradation.md
│   │   │       ├── 📄 proposal-20251226-160707-system-kis-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-notifications-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-notifications-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-positions-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-positions-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-reports-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-reports-recurring_error.md
│   │   │       ├── 📄 proposal-20251226-160707-system-signal-consolidation-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-signal-generator-agent-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-weights-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-system-weights-performance_degradation.md
│   │   │       ├── 📄 proposal-20251226-160707-war-room-war-room-debate-high_error_rate.md
│   │   │       ├── 📄 proposal-20251226-160707-war-room-war-room-debate-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-analysis-ceo_analysis-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-analysis-ceo_analysis-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-ai_chat-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-ai_chat-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-ai_reviews-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-ai_reviews-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-backfill-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-backfill-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004213-system-backfill-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-consensus-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004213-system-gemini_free-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-gemini_free-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-global_macro-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-global_macro-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-incremental-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-incremental-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004213-system-incremental-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-kis-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-kis-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004213-system-kis-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-log-manager-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004213-system-notifications-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-notifications-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-positions-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-positions-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-reports-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-reports-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004213-system-weights-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-system-weights-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004213-war-room-war-room-debate-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004213-war-room-war-room-debate-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-analysis-ceo_analysis-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-analysis-ceo_analysis-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-ai_chat-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-ai_chat-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-ai_reviews-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-ai_reviews-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-backfill-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-backfill-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004813-system-backfill-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-consensus-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004813-system-gemini_free-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-gemini_free-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-global_macro-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-global_macro-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-incremental-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-incremental-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004813-system-incremental-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-kis-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-kis-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004813-system-kis-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-log-manager-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004813-system-notifications-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-notifications-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-positions-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-positions-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-reports-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-reports-recurring_error.md
│   │   │       ├── 📄 proposal-20251227-004813-system-weights-high_error_rate.md
│   │   │       ├── 📄 proposal-20251227-004813-system-weights-performance_degradation.md
│   │   │       ├── 📄 proposal-20251227-004813-war-room-war-room-debate-high_error_rate.md
│   │   │       └── 📄 proposal-20251227-004813-war-room-war-room-debate-recurring_error.md
│   │   ├── 📂 legacy/
│   │   │   └── 📂 war-room/
│   │   │       ├── 📄 README.md
│   │   │       ├── 📂 analyst-agent/
│   │   │       │   └── 📄 SKILL.md
│   │   │       ├── 📂 institutional-agent/
│   │   │       │   └── 📄 SKILL.md
│   │   │       ├── 📂 macro-agent/
│   │   │       │   └── 📄 SKILL.md
│   │   │       ├── 📂 news-agent/
│   │   │       │   └── 📄 SKILL.md
│   │   │       ├── 📂 pm-agent/
│   │   │       │   └── 📄 SKILL.md
│   │   │       ├── 📂 risk-agent/
│   │   │       │   └── 📄 SKILL.md
│   │   │       └── 📂 trader-agent/
│   │   │           └── 📄 SKILL.md
│   │   ├── 📂 logs/
│   │   │   ├── 📂 analysis/
│   │   │   │   ├── 📂 ceo_analysis/
│   │   │   │   ├── 📂 dividend-intelligence/
│   │   │   │   ├── 📂 gemini-news/
│   │   │   │   ├── 📂 news/
│   │   │   │   └── 📂 news-analyzer/
│   │   │   ├── 📂 checkpoint/
│   │   │   │   └── 📂 reports/
│   │   │   ├── 📂 debugging-agent/
│   │   │   │   └── 📂 proposals/
│   │   │   ├── 📂 economic/
│   │   │   │   └── 📂 reports/
│   │   │   ├── 📂 generate/
│   │   │   │   └── 📂 briefing/
│   │   │   ├── 📂 korean-market/
│   │   │   │   └── 📂 reports/
│   │   │   ├── 📂 premarket/
│   │   │   │   └── 📂 reports/
│   │   │   ├── 📂 read/
│   │   │   │   └── 📂 briefing/
│   │   │   ├── 📂 system/
│   │   │   │   ├── 📂 accountability/
│   │   │   │   ├── 📂 ai_chat/
│   │   │   │   ├── 📂 ai_reviews/
│   │   │   │   ├── 📂 auth/
│   │   │   │   ├── 📂 backfill/
│   │   │   │   ├── 📂 backtest/
│   │   │   │   ├── 📂 consensus/
│   │   │   │   ├── 📂 debugging-agent/
│   │   │   │   │   └── 📂 proposals/
│   │   │   │   ├── 📂 emergency/
│   │   │   │   ├── 📂 feeds/
│   │   │   │   ├── 📂 fle-calculator/
│   │   │   │   ├── 📂 gemini_free/
│   │   │   │   ├── 📂 global_macro/
│   │   │   │   ├── 📂 incremental/
│   │   │   │   ├── 📂 kis/
│   │   │   │   ├── 📂 log-manager/
│   │   │   │   ├── 📂 monitoring/
│   │   │   │   ├── 📂 notifications/
│   │   │   │   ├── 📂 orders/
│   │   │   │   ├── 📂 performance/
│   │   │   │   ├── 📂 phase/
│   │   │   │   ├── 📂 portfolio/
│   │   │   │   ├── 📂 positions/
│   │   │   │   ├── 📂 reports/
│   │   │   │   ├── 📂 signal-consolidation/
│   │   │   │   ├── 📂 signal-generator-agent/
│   │   │   │   ├── 📂 stock_prices/
│   │   │   │   ├── 📂 unknown/
│   │   │   │   └── 📂 weights/
│   │   │   ├── 📂 trading/
│   │   │   │   ├── 📂 ai_signals/
│   │   │   │   ├── 📂 auto_trade/
│   │   │   │   └── 📂 signals/
│   │   │   ├── 📂 trigger/
│   │   │   │   └── 📂 reports/
│   │   │   ├── 📂 war-room/
│   │   │   │   └── 📂 war-room-debate/
│   │   │   └── 📂 weekly/
│   │   │       └── 📂 reports/
│   │   ├── 📂 reporting/
│   │   │   ├── 📂 failure-learning-agent/
│   │   │   │   ├── 📄 SKILL.md
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   └── 📄 failure_analyzer.py
│   │   │   └── 📂 report-orchestrator-agent/
│   │   │       ├── 📄 SKILL.md
│   │   │       ├── 📄 __init__.py
│   │   │       └── 📄 report_orchestrator.py
│   │   ├── 📄 skill_loader.py
│   │   ├── 📂 system/
│   │   │   ├── 📂 backtest-analyzer-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   ├── 📄 conflict_detector.py
│   │   │   ├── 📂 constitution-validator-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   ├── 📂 db-schema-manager/
│   │   │   │   ├── 📄 SKILL.md
│   │   │   │   ├── 📂 docs/
│   │   │   │   │   ├── 📄 MIGRATION_GUIDE.md
│   │   │   │   │   └── 📄 SCHEMA_REGISTRY.md
│   │   │   │   ├── 📂 migrations/
│   │   │   │   ├── 📂 schemas/
│   │   │   │   ├── 📂 scripts/
│   │   │   │   │   ├── 📄 compare_to_db.py
│   │   │   │   │   ├── 📄 generate_migration.py
│   │   │   │   │   └── 📄 validate_data.py
│   │   │   │   └── 📂 templates/
│   │   │   ├── 📂 debugging-agent/
│   │   │   │   ├── 📄 SKILL.md
│   │   │   │   ├── 📂 docs/
│   │   │   │   └── 📂 scripts/
│   │   │   │       ├── 📄 improvement_proposer.py
│   │   │   │       ├── 📄 log_reader.py
│   │   │   │       ├── 📄 pattern_detector.py
│   │   │   │       └── 📄 run_debugging_agent.py
│   │   │   ├── 📂 meta-analyst-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   ├── 📂 notification-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   ├── 📂 portfolio-manager-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   ├── 📂 report-writer-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   └── 📂 signal-generator-agent/
│   │   │       └── 📄 SKILL.md
│   │   ├── 📂 video-production/
│   │   │   ├── 📂 character-designer-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   ├── 📂 director-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   ├── 📂 news-collector-agent/
│   │   │   │   └── 📄 SKILL.md
│   │   │   └── 📂 story-writer-agent/
│   │   │       └── 📄 SKILL.md
│   │   └── 📂 war_room_mvp/
│   │       ├── 📄 README.md
│   │       ├── 📂 analyst_agent_mvp/
│   │       │   ├── 📄 SKILL.md
│   │       │   └── 📄 handler.py
│   │       ├── 📂 orchestrator_mvp/
│   │       │   ├── 📄 SKILL.md
│   │       │   └── 📄 handler.py
│   │       ├── 📂 pm_agent_mvp/
│   │       │   ├── 📄 SKILL.md
│   │       │   └── 📄 handler.py
│   │       ├── 📂 risk_agent_mvp/
│   │       │   ├── 📄 SKILL.md
│   │       │   └── 📄 handler.py
│   │       └── 📂 trader_agent_mvp/
│   │           ├── 📄 SKILL.md
│   │           └── 📄 handler.py
│   ├── 📂 strategies/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 dca_strategy.py
│   │   ├── 📄 deep_reasoning_strategy.py
│   │   └── 📄 global_macro_strategy.py
│   ├── 📄 test_caching.py
│   ├── 📄 test_caching_simple.py
│   ├── 📂 thinking/
│   │   └── 📄 signal_mapper.py
│   ├── 📂 tools/
│   │   └── 📄 search_grounding.py
│   ├── 📂 trading/
│   │   ├── 📄 shadow_trader.py
│   │   └── 📄 shadow_trading_agent.py
│   ├── 📄 trading_agent.py
│   ├── 📄 trading_terms_parser.py
│   ├── 📄 vector_search.py
│   ├── 📂 video/
│   │   ├── 📄 verify_real.py
│   │   └── 📄 video_analyzer.py
│   └── 📂 war_room/
│       ├── 📄 debate_visualizer.py
│       └── 📄 shadow_trading_tracker.py
├── 📂 alembic/
│   ├── 📄 env.py
│   └── 📂 versions/
│       ├── 📄 001_create_features_table.py
│       ├── 📄 add_ai_collective_tables.py
│       ├── 📄 add_analytics_tables.py
│       ├── 📄 add_incremental_update_tables.py
│       └── 📄 add_rag_embedding_tables.py
├── 📄 alert_manager.py
├── 📂 alerts/
│   ├── 📄 __init__.py
│   └── 📄 alert_system.py
├── 📂 analysis/
│   ├── 📄 ceo_news_analyzer.py
│   ├── 📄 financial_forensics.py
│   ├── 📄 market_gap_analyzer.py
│   ├── 📄 options_flow_tracker.py
│   └── 📄 sector_rotation_analyzer.py
├── 📂 analytics/
│   ├── 📄 __init__.py
│   ├── 📄 buffett_index_monitor.py
│   ├── 📄 dividend_analyzer.py
│   ├── 📄 performance_attribution.py
│   ├── 📄 peri_calculator.py
│   ├── 📄 portfolio_manager.py
│   ├── 📄 risk_analytics.py
│   ├── 📄 shadow_trading_analyzer.py
│   ├── 📄 tax_engine.py
│   └── 📄 trade_analytics.py
├── 📂 api/
│   ├── 📄 __init__.py
│   ├── 📄 accountability_router.py
│   ├── 📄 ai_chat_router.py
│   ├── 📄 ai_quality_router.py
│   ├── 📄 ai_review_router.py
│   ├── 📄 ai_signals_router.py
│   ├── 📄 approvals_router.py
│   ├── 📄 auth_router.py
│   ├── 📄 auto_trade_router.py
│   ├── 📄 backtest_router.py
│   ├── 📄 briefing_router.py
│   ├── 📄 ceo_analysis_router.py
│   ├── 📄 chart_router.py
│   ├── 📄 consensus_router.py
│   ├── 📄 correlation_router.py
│   ├── 📄 cost_monitoring.py
│   ├── 📄 data_backfill_router.py
│   ├── 📄 dividend_router.py
│   ├── 📄 emergency_router.py
│   ├── 📄 failure_learning_router.py
│   ├── 📄 feedback_router.py
│   ├── 📄 feeds_discovery_endpoints.py
│   ├── 📄 feeds_router.py
│   ├── 📄 fix_db_errors.py
│   ├── 📄 fle_router.py
│   ├── 📄 forensics_router.py
│   ├── 📄 gemini_free_router.py
│   ├── 📄 gemini_news_router.py
│   ├── 📄 global_macro_router.py
│   ├── 📄 incremental_router.py
│   ├── 📄 intelligence_router.py
│   ├── 📄 journey_router.py
│   ├── 📄 kis_integration_router.py
│   ├── 📄 kis_sync_router.py
│   ├── 📄 logs_router.py
│   ├── 📄 main.py
│   ├── 📄 mock_router.py
│   ├── 📄 monitoring_router.py
│   ├── 📄 multi_asset_router.py
│   ├── 📄 news_analysis_router.py
│   ├── 📄 news_filter.py
│   ├── 📄 news_processing_router.py
│   ├── 📄 news_router.py
│   ├── 📄 notifications_router.py
│   ├── 📄 options_flow_router.py
│   ├── 📄 orders_router.py
│   ├── 📄 partitions_router.py
│   ├── 📄 performance_router.py
│   ├── 📄 persona_router.py
│   ├── 📄 phase_integration_router.py
│   ├── 📄 portfolio_optimization_router.py
│   ├── 📄 portfolio_router.py
│   ├── 📄 position_router.py
│   ├── 📄 reasoning_api.py
│   ├── 📄 reasoning_router.py
│   ├── 📄 reports_router.py
│   ├── 📂 routers/
│   │   └── 📄 shadow.py
│   ├── 📂 schemas/
│   │   └── 📄 strategy_schemas.py
│   ├── 📄 screener_router.py
│   ├── 📄 sec_router.py
│   ├── 📄 sec_semantic_search.py
│   ├── 📄 signal_consolidation_router.py
│   ├── 📄 signals_router.py
│   ├── 📄 simple_news_router.py
│   ├── 📄 stock_price_router.py
│   ├── 📄 strategy_router.py
│   ├── 📄 tax_routes.py
│   ├── 📄 tendency_router.py
│   ├── 📄 thesis_router.py
│   ├── 📄 v2_router.py
│   ├── 📄 war_room_analytics_router.py
│   ├── 📄 war_room_router.py
│   └── 📄 weight_adjustment_router.py
├── 📂 approval/
│   ├── 📄 __init__.py
│   ├── 📄 approval_manager.py
│   └── 📄 approval_models.py
├── 📄 auth.py
├── 📂 automation/
│   ├── 📄 __init__.py
│   ├── 📄 accountability_scheduler.py
│   ├── 📄 auto_trader.py
│   ├── 📄 auto_trading_scheduler.py
│   ├── 📄 create_accountability_tables.py
│   ├── 📄 create_test_interpretations.py
│   ├── 📄 kis_auto_scheduler.py
│   ├── 📄 kis_portfolio_scheduler.py
│   ├── 📄 macro_context_updater.py
│   ├── 📄 ollama_scheduler.py
│   ├── 📄 price_tracking_scheduler.py
│   ├── 📄 price_tracking_verifier.py
│   ├── 📄 scheduler.py
│   └── 📄 signal_to_order_converter.py
├── 📂 backend/
│   └── 📂 data/
├── 📂 backtest/
│   ├── 📄 __init__.py
│   ├── 📄 backtest_engine.py
│   ├── 📄 constitutional_backtest_engine.py
│   ├── 📄 performance_metrics.py
│   ├── 📄 portfolio_manager.py
│   ├── 📄 shadow_trade_tracker.py
│   └── 📄 vintage_backtest.py
├── 📂 backtest_results/
├── 📂 backtesting/
│   ├── 📄 README.md
│   ├── 📄 __init__.py
│   ├── 📄 ab_backtest.py
│   ├── 📄 ai_strategy_backtest.py
│   ├── 📄 automated_backtest.py
│   ├── 📄 backtest_engine.py
│   ├── 📄 backtest_simulator.py
│   ├── 📄 consensus_backtest.py
│   ├── 📄 consensus_performance_analyzer.py
│   ├── 📄 constitutional_backtest_engine.py
│   ├── 📄 engine.py
│   ├── 📄 performance_metrics.py
│   ├── 📄 pit_backtest_engine.py
│   ├── 📄 pit_data_access.py
│   ├── 📄 portfolio_manager.py
│   ├── 📄 shadow_trade_tracker.py
│   └── 📄 signal_backtest_engine.py
├── 📂 brokers/
│   ├── 📄 __init__.py
│   ├── 📄 kis_broker.py
│   ├── 📄 rate_limiter.py
│   └── 📄 test_kis.py
├── 📂 caching/
│   ├── 📄 USAGE_EXAMPLES.py
│   ├── 📄 __init__.py
│   ├── 📄 decorators.py
│   └── 📄 semantic_cache.py
├── 📄 check_db_news.py
├── 📄 check_news.py
├── 📄 check_schema.py
├── 📂 config/
│   ├── 📄 __init__.py
│   ├── 📄 secrets_manager.py
│   ├── 📄 settings.py
│   └── 📄 storage_config.py
├── 📄 config.py
├── 📄 config_phase14.py
├── 📂 constitution/
│   ├── 📄 __init__.py
│   ├── 📄 allocation_rules.py
│   ├── 📄 amendment_mode.py
│   ├── 📄 check_integrity.py
│   ├── 📄 constitution.py
│   ├── 📄 portfolio_phase.py
│   ├── 📄 risk_limits.py
│   └── 📄 trading_constraints.py
├── 📂 contracts/
│   └── 📄 strategy_contracts.py
├── 📂 core/
│   ├── 📄 __init__.py
│   ├── 📄 cache.py
│   ├── 📄 database.py
│   ├── 📄 logging_config.py
│   └── 📂 models/
│       ├── 📄 __init__.py
│       ├── 📄 analytics_models.py
│       ├── 📄 base.py
│       ├── 📄 dividend_models.py
│       ├── 📄 embedding_models.py
│       ├── 📄 news_models.py
│       ├── 📄 sec_analysis_models.py
│       ├── 📄 sec_models.py
│       └── 📄 stock_price_models.py
├── 📂 data/
│   ├── 📄 __init__.py
│   ├── 📂 calendar/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 calendar_manager.py
│   │   ├── 📄 check_status.py
│   │   ├── 📄 fmp_collector.py
│   │   ├── 📄 forex_factory_scraper.py
│   │   ├── 📄 google_news_collector.py
│   │   ├── 📄 realtime_collector.py
│   │   ├── 📄 rss_news_aggregator.py
│   │   ├── 📄 test_finviz_all.py
│   │   ├── 📄 test_finviz_realtime.py
│   │   ├── 📄 test_forex_factory_live.py
│   │   ├── 📄 test_free_sources.py
│   │   ├── 📄 test_google_news.py
│   │   ├── 📄 test_news_api.py
│   │   ├── 📄 test_news_sources.py
│   │   ├── 📄 test_polling_strategy_v2.py
│   │   ├── 📄 test_realtime_news.py
│   │   ├── 📄 test_williams_simple.py
│   │   ├── 📄 test_williams_speech.py
│   │   └── 📄 test_yahoo_finance.py
│   ├── 📂 collectors/
│   │   ├── 📄 __init__.py
│   │   ├── 📂 api_clients/
│   │   │   ├── 📄 fred_client.py
│   │   │   ├── 📄 sec_client.py
│   │   │   └── 📄 yahoo_client.py
│   │   ├── 📄 dart_collector.py
│   │   ├── 📄 dividend_collector.py
│   │   ├── 📄 economic_calendar.py
│   │   ├── 📄 enhanced_fred_collector.py
│   │   ├── 📄 etf_flow_tracker.py
│   │   ├── 📄 finviz_collector.py
│   │   ├── 📄 fred_collector.py
│   │   ├── 📄 free_news_monitor.py
│   │   ├── 📄 smart_money_collector.py
│   │   ├── 📄 stealth_web_crawler.py
│   │   ├── 📄 stock_price_collector.py
│   │   ├── 📄 wall_street_intel.py
│   │   └── 📄 yahoo_collector.py
│   ├── 📂 crawlers/
│   │   ├── 📄 finviz_scout.py
│   │   ├── 📄 multi_source_crawler.py
│   │   └── 📄 sec_edgar_monitor.py
│   ├── 📄 decision_store.py
│   ├── 📄 deep_reasoning_store.py
│   ├── 📂 feature_store/  ⭐ **2-Layer Cache System (Redis + TimescaleDB)**
│   │   ├── 📄 __init__.py
│   │   ├── 📂 ai_factors/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 news_collector.py
│   │   │   └── 📄 non_standard_risk.py
│   │   ├── 📄 cache_layer.py        # Redis (L1 <5ms) + TimescaleDB (L2 <100ms)
│   │   ├── 📄 cache_warmer.py       # Pre-load popular tickers
│   │   ├── 📄 cache_warming.py      # Advanced warming strategies
│   │   ├── 📄 features.py           # 20+ Technical Indicators (ret_5d, vol_20d, etc.)
│   │   ├── 📄 management_credibility_feature.py
│   │   ├── 📄 metrics.py
│   │   ├── 📄 non_standard_risk_integration.py
│   │   └── 📄 store.py              # Main FeatureStore class
│   │
│   │   ⚡ **Redis Cache Performance**:
│   │   - Layer 1 (Redis): <5ms latency, 50 connections
│   │   - Layer 2 (TimescaleDB): <100ms latency, persistent storage
│   │   - Cache Miss (Compute): ~345 seconds (Yahoo Finance API)
│   │   - **Speedup**: 69,000x faster with cache hit
│   │   
│   │   📊 **Cached Data**:
│   │   - Technical Features: ret_5d, ret_20d, vol_20d, mom_20d, rsi_14, macd, etc.
│   │   - Cache Key Format: `feature:{TICKER}:{FEATURE}:{DATE}`
│   │   - Example: `feature:AAPL:ret_5d:2026-01-26`
│   │   - TTL: Intraday (5min), Daily (24h)
│   ├── 📂 features/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 credit_regime_factor.py
│   │   ├── 📄 humanoid_score_factor.py
│   │   ├── 📄 macro_regime_factors.py
│   │   ├── 📄 management_credibility.py
│   │   ├── 📄 non_standard_risk_dual.py
│   │   ├── 📄 supply_chain_risk.py
│   │   ├── 📄 supply_chain_risk_feature.py
│   │   └── 📄 whale_wisdom_factor.py
│   ├── 📄 gemini_news_fetcher.py
│   ├── 📂 integration_test/
│   ├── 📂 knowledge/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 ai_value_chain.py
│   │   └── 📄 memory_builder.py
│   ├── 📂 knowledge_graph/
│   │   ├── 📄 __init__.py
│   │   └── 📄 knowledge_graph.py
│   ├── 📄 migrate_news_schema_v2.py
│   ├── 📂 models/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 feature.py
│   │   ├── 📄 proposal.py
│   │   └── 📄 shadow_trade.py
│   ├── 📄 news_analyzer.py
│   ├── 📄 news_models.py
│   ├── 📄 position_tracker.py
│   ├── 📂 processors/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 news_processor.py
│   │   └── 📄 unified_news_processor.py
│   ├── 📂 prompts/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 analysis_extraction.py
│   │   └── 📄 grounding_search.py
│   ├── 📄 realtime_news_service.py
│   ├── 📄 rss_crawler.py
│   ├── 📄 rss_feed_discovery.py
│   ├── 📄 sec_analysis_cache.py
│   ├── 📄 sec_cik_mapper.py
│   ├── 📄 sec_client.py
│   ├── 📄 sec_file_storage.py
│   ├── 📄 sec_monitor.py
│   ├── 📄 sec_parser.py
│   ├── 📄 sp500_universe.py
│   ├── 📄 stock_price_storage.py
│   ├── 📂 test_positions/
│   └── 📂 vector_store/
│       ├── 📄 __init__.py
│       ├── 📄 chunker.py
│       ├── 📄 embedder.py
│       ├── 📄 store.py
│       └── 📄 tagger.py
├── 📂 data_sources/
│   ├── 📄 __init__.py
│   └── 📄 yahoo_finance.py
├── 📂 database/
│   ├── 📄 __init__.py
│   ├── 📄 db_service.py
│   ├── 📂 igrations/
│   ├── 📂 migrations/
│   │   ├── 📄 add_ai_trade_decisions_table.py
│   │   ├── 📄 add_backfill_columns.py
│   │   ├── 📄 add_debate_id_migration.py
│   │   ├── 📄 add_debate_transcript.py
│   │   ├── 📄 add_v2_2_caching_fields.py
│   │   ├── 📄 analyze_actual_schema.py
│   │   ├── 📄 analyze_storage.py
│   │   ├── 📄 apply_migration.py
│   │   ├── 📄 check_5541_db.py
│   │   ├── 📄 check_5541_detailed.py
│   │   ├── 📄 check_indexes.py
│   │   ├── 📄 check_stock_prices_schema.py
│   │   ├── 📄 check_table_structure.py
│   │   ├── 📄 create_all_tables.py
│   │   ├── 📄 create_economic_events_table.py
│   │   ├── 📄 create_grounding_table.py
│   │   ├── 📄 create_missing_tables_5541.py
│   │   ├── 📄 create_rss_feeds_table.py
│   │   ├── 📄 create_sample_signals.py
│   │   ├── 📄 create_shadow_trading_tables.py
│   │   ├── 📄 create_simple_signals.py
│   │   ├── 📄 drop_and_recreate_economic_events_table.py
│   │   ├── 📄 final_test.py
│   │   ├── 📄 quick_env_test.py
│   │   ├── 📄 recreate_postgres_container.md
│   │   ├── 📄 run_agent_weights_history_migration.py
│   │   ├── 📄 run_migration.py
│   │   ├── 📄 run_migration_5432.py
│   │   ├── 📄 run_migration_direct.py
│   │   ├── 📄 run_migration_final.py
│   │   ├── 📄 run_phase1.py
│   │   ├── 📄 run_shadow_trading_migration.py
│   │   ├── 📄 test_5541.py
│   │   ├── 📄 test_connection.py
│   │   ├── 📄 test_env_config.py
│   │   ├── 📄 test_ipv4.py
│   │   ├── 📄 test_local_postgres.py
│   │   ├── 📄 test_postgres_user.py
│   │   ├── 📄 test_simple_password.py
│   │   ├── 📄 test_trust_auth.py
│   │   ├── 📄 test_users.py
│   │   └── 📄 unify_war_room_schema.py
│   ├── 📄 models.py
│   ├── 📄 models_assets.py
│   ├── 📄 repository.py
│   ├── 📄 repository_multi_strategy.py
│   ├── 📂 schemas/
│   │   └── 📄 constitutional_validation_schema.py
│   ├── 📄 vector_db.py
│   └── 📄 vector_models.py
├── 📂 demos/
│   ├── 📄 __init__.py
│   └── 📄 phase1_demo.py
├── 📂 events/
│   ├── 📄 __init__.py
│   ├── 📄 event_bus.py
│   ├── 📄 event_types.py
│   └── 📄 subscribers.py
├── 📂 examples/
│   ├── 📄 elk_logging_example.py
│   └── 📄 tax_harvesting_example.py
├── 📂 execution/
│   ├── 📄 README.md
│   ├── 📄 __init__.py
│   ├── 📂 data/
│   │   ├── 📄 tick_flow.py
│   │   └── 📄 vwap.py
│   ├── 📄 execution_engine.py
│   ├── 📄 execution_router.py
│   ├── 📄 executors.py
│   ├── 📄 kill_switch.py
│   ├── 📄 kis_broker_adapter.py
│   ├── 📄 order_manager.py
│   ├── 📄 order_validator.py
│   ├── 📄 recovery.py
│   ├── 📂 rl/
│   │   ├── 📄 agent.py
│   │   ├── 📄 env.py
│   │   └── 📄 train.py
│   ├── 📂 safety/
│   │   └── 📄 watchdog.py
│   ├── 📄 safety_guard.py
│   ├── 📄 shadow_trading_mvp.py
│   ├── 📄 smart_executor.py
│   └── 📄 state_machine.py
├── 📂 external_apis/
│   ├── 📄 __init__.py
│   ├── 📄 fred_client.py
│   ├── 📄 sec_client.py
│   └── 📄 yfinance_client.py
├── 📂 fusion/
│   ├── 📄 engine.py
│   ├── 📂 gates/
│   │   ├── 📄 event_priority.py
│   │   └── 📄 liquidity.py
│   └── 📄 normalizer.py
├── 📂 gnn/
│   ├── 📄 builder.py
│   ├── 📄 gate.py
│   └── 📄 propagator.py
├── 📂 graphrag/
│   ├── 📄 graphrag_optimizer.py
│   └── 📄 query_complexity_analyzer.py
├── 📄 health_monitor.py
├── 📂 htmlcov/
├── 📄 init_news_db.py
├── 📂 intelligence/
│   ├── 📄 __init__.py
│   ├── 📂 collector/
│   │   ├── 📄 __init__.py
│   │   └── 📄 economic_calendar.py
│   ├── 📄 dividend_risk_agent.py
│   ├── 📄 economic_calendar.py
│   ├── 📄 four_signal_calculator.py
│   ├── 📄 four_signal_framework.py
│   ├── 📄 news_agent.py
│   ├── 📄 news_clustering.py
│   ├── 📄 news_pipeline_adapter.py
│   ├── 📂 reporter/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 daily_briefing.py
│   │   └── 📄 fed_analyzer.py
│   ├── 📄 source_classifier.py
│   └── 📄 text_similarity.py
├── 📄 live_trading_engine.py
├── 📄 log_manager.py
├── 📂 logs/
├── 📄 main.py
├── 📂 market_data/
│   ├── 📄 __init__.py
│   ├── 📄 price_fetcher.py
│   └── 📄 price_scheduler.py
├── 📂 media/
│   ├── 📄 opal_prompts.py
│   ├── 📄 script_writer.py
│   └── 📄 video_editor.py
├── 📂 metrics/
│   ├── 📄 __init__.py
│   ├── 📄 fle_calculator.py
│   └── 📄 trading_tendency_analyzer.py
├── 📄 metrics_collector.py
├── 📂 migrations/
│   ├── 📄 add_news_status_flags.py
│   └── 📂 versions/
│       ├── 📄 251215_proposals.py
│       └── 📄 251215_shadow_trades.py
├── 📂 ml/
│   └── 📄 local_embeddings.py
├── 📄 mock_api.py
├── 📂 models/
│   ├── 📄 __init__.py
│   └── 📄 trading_decision.py
├── 📂 monitoring/
│   ├── 📄 README.md
│   ├── 📄 __init__.py
│   ├── 📄 ai_trading_metrics.py
│   ├── 📄 alert_manager.py
│   ├── 📄 api_usage_tracker.py
│   ├── 📄 circuit_breaker.py
│   ├── 📄 cost_analytics.py
│   ├── 📄 data_quality_metrics.py
│   ├── 📄 evolution_metrics.py
│   ├── 📄 health_monitor.py
│   ├── 📄 metrics.py
│   ├── 📄 metrics_collector.py
│   ├── 📄 performance_monitor.py
│   ├── 📄 skill_metrics_collector.py
│   ├── 📄 smart_alerts.py
│   └── 📄 trading_metrics.py
├── 📂 news/
│   ├── 📄 __init__.py
│   ├── 📄 enhanced_news_crawler.py
│   ├── 📄 helpers.py
│   ├── 📄 news_context_filter.py
│   ├── 📄 news_crawler.py
│   ├── 📄 rss_crawler.py
│   └── 📄 rss_crawler_with_db.py
├── 📂 notifications/
│   ├── 📄 __init__.py
│   ├── 📄 event_subscriber.py
│   ├── 📄 example_integration.py
│   ├── 📄 notification_manager.py
│   ├── 📄 realtime_notifier.py
│   ├── 📄 sec_alerts.py
│   ├── 📄 slack_notifier.py
│   ├── 📄 telegram_command_bot.py
│   ├── 📄 telegram_commander_bot.py
│   ├── 📄 telegram_notifier.py
│   ├── 📄 test_chatgpt_completion.py
│   ├── 📄 test_pdf_send.py
│   └── 📄 test_telegram.py
├── 📂 orchestration/
│   └── 📄 data_accumulation_orchestrator.py
├── 📂 paper_trading/
│   ├── 📄 __init__.py
│   ├── 📄 live_portfolio.py
│   ├── 📄 market_data_fetcher.py
│   └── 📄 paper_trading_engine.py
├── 📂 pipelines/
│   ├── 📄 news_embedding_pipeline.py
│   └── 📄 sec_embedding_pipeline.py
├── 📂 reporting/
│   ├── 📄 daily_pdf_generator.py
│   ├── 📄 pdf_renderer.py
│   ├── 📄 report_generator.py
│   ├── 📄 report_templates.py
│   ├── 📄 shield_metrics.py
│   └── 📄 shield_report_generator.py
├── 📂 research/
├── 📂 routers/
│   ├── 📄 kill_switch_router.py
│   ├── 📄 tickers.py
│   ├── 📄 war_room_mvp_router.py
│   └── 📄 war_room_mvp_router_backup.py
├── 📂 routing/
│   ├── 📄 __init__.py
│   ├── 📄 intent_classifier.py
│   ├── 📄 model_selector.py
│   ├── 📄 semantic_router.py
│   ├── 📄 skill_router_integration.py
│   ├── 📄 test_semantic_router.py
│   └── 📄 tool_selector.py
├── 📂 rules/
│   └── 📄 constitution_forensics.py
├── 📄 run_backtest.py
├── 📄 run_live_trading.py
├── 📄 run_news_crawler.py
├── 📄 run_paper_trading.py
├── 📂 runners/
│   └── 📄 shadow_runner.py
├── 📂 schedulers/
│   ├── 📄 chip_intelligence_updater.py
│   ├── 📄 correlation_scheduler.py
│   └── 📄 failure_learning_scheduler.py
├── 📂 schemas/
│   ├── 📄 README.md
│   ├── 📄 __init__.py
│   ├── 📄 base_schema.py
│   └── 📄 test_base_schema.py
├── 📂 scripts/
│   ├── 📄 add_chip_war_column.py
│   ├── 📄 add_new_feeds.py
│   ├── 📄 automated_backup.py
│   ├── 📄 backfill_embeddings.py
│   ├── 📄 benchmark_price_storage.py
│   ├── 📄 check_data_readiness.py
│   ├── 📄 check_macro_context.py
│   ├── 📄 check_model_deprecations.py
│   ├── 📄 check_schema.py
│   ├── 📄 check_shadow_data.py
│   ├── 📄 check_shadow_db.py
│   ├── 📄 check_shadow_sqlite.py
│   ├── 📄 check_shadow_status.py
│   ├── 📄 check_unanalyzed.py
│   ├── 📄 check_vector_capability.py
│   ├── 📄 collect_14day_data.py
│   ├── 📄 collect_week1_data.py
│   ├── 📄 create_agent_vote_tracking.py
│   ├── 📄 create_deep_reasoning_table.py
│   ├── 📄 create_price_tracking.py
│   ├── 📄 create_stock_tables.py
│   ├── 📄 debug_settings.py
│   ├── 📄 fix_sqlite_tables.py
│   ├── 📄 generate_daily_briefing.py
│   ├── 📄 generate_week1_report.py
│   ├── 📄 import_kis_data.py
│   ├── 📄 init_database.py
│   ├── 📄 init_dividend_tables.py
│   ├── 📄 init_kg.py
│   ├── 📄 init_kg_PLAN.py
│   ├── 📄 init_kg_via_repo.py
│   ├── 📄 init_vector_db.py
│   ├── 📄 manual_db_migration.py
│   ├── 📄 migrate_dividend_aristocrats.py
│   ├── 📄 migrate_news_to_postgres.py
│   ├── 📄 monitor_collection.py
│   ├── 📄 monitor_free_news.py
│   ├── 📄 monitor_ft.py
│   ├── 📄 performance_benchmark.py
│   ├── 📄 reset_database.py
│   ├── 📄 restore_nke_position.py
│   ├── 📄 seed_strategies.py
│   ├── 📄 seed_test_data.py
│   ├── 📄 seed_test_signals.py
│   ├── 📄 shadow_trading_monitor.py
│   ├── 📄 test_deep_reasoning_features.py
│   ├── 📄 test_kill_switch_debug.py
│   ├── 📄 test_kill_switch_simple.py
│   ├── 📄 test_kill_switch_verify.py
│   ├── 📄 test_news_interpretation.py
│   ├── 📄 test_phase25_4.py
│   ├── 📄 test_price_verifier_flow.py
│   ├── 📄 test_semantic_search.py
│   ├── 📄 test_shadow_api.py
│   ├── 📄 test_structured_outputs.py
│   ├── 📄 test_tax_optimizer.py
│   ├── 📄 test_telegram_alert.py
│   ├── 📄 test_telegram_direct.py
│   ├── 📄 test_telegram_simple.py
│   ├── 📄 test_war_room_single.py
│   ├── 📄 test_watchtower.py
│   ├── 📄 validate_collection.py
│   ├── 📄 verify_annual_report.py
│   ├── 📄 verify_chip_war_column.py
│   ├── 📄 verify_deep_reasoning.py
│   ├── 📄 verify_news_integration_direct.py
│   ├── 📄 verify_news_interpretation.py
│   ├── 📄 verify_phase5_integrity.py
│   ├── 📄 verify_weekly_report.py
│   └── 📄 view_latest_analysis.py
├── 📂 security/
│   ├── 📄 __init__.py
│   ├── 📄 input_guard.py
│   ├── 📄 unicode_security.py
│   ├── 📄 url_security.py
│   └── 📄 webhook_security.py
├── 📂 services/
│   ├── 📄 __init__.py
│   ├── 📄 alert_manager.py
│   ├── 📄 analytics_aggregator.py
│   ├── 📄 annual_report_generator.py
│   ├── 📄 asset_service.py
│   ├── 📄 auto_trade_service.py
│   ├── 📄 broker_position_sync.py
│   ├── 📄 complete_5page_report_generator.py
│   ├── 📄 complete_korean_report_generator.py
│   ├── 📄 complete_report_generator.py
│   ├── 📄 daily_briefing_cache_manager.py
│   ├── 📄 daily_briefing_service.py
│   ├── 📄 daily_price_sync.py
│   ├── 📄 daily_report_scheduler.py
│   ├── 📄 earnings_calendar_service.py
│   ├── 📄 economic_calendar_fetcher.py
│   ├── 📄 economic_calendar_manager.py
│   ├── 📄 economic_calendar_service.py
│   ├── 📄 economic_watcher.py
│   ├── 📄 fast_polling_service.py
│   ├── 📄 final_korean_report_generator.py
│   ├── 📄 fred_economic_calendar.py
│   ├── 📄 korean_font_setup.py
│   ├── 📄 market_data.py
│   ├── 📄 market_language_templates.py
│   ├── 📂 market_scanner/
│   │   ├── 📄 __init__.py
│   │   ├── 📂 filters/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 momentum_filter.py
│   │   │   ├── 📄 options_filter.py
│   │   │   ├── 📄 volatility_filter.py
│   │   │   └── 📄 volume_filter.py
│   │   ├── 📄 massive_api_client.py
│   │   ├── 📄 scanner.py
│   │   ├── 📄 scheduler.py
│   │   └── 📄 universe.py
│   ├── 📄 news_event_handler.py
│   ├── 📄 news_poller.py
│   ├── 📂 notifiers/
│   │   └── 📄 telegram_notifier.py
│   ├── 📄 ollama_cache_service.py
│   ├── 📄 optimized_signal_pipeline.py
│   ├── 📄 ownership_service.py
│   ├── 📄 page1_generator.py
│   ├── 📄 page1_generator_korean.py
│   ├── 📄 page2_generator_korean.py
│   ├── 📄 page3_generator.py
│   ├── 📄 page3_generator_korean.py
│   ├── 📄 page5_generator_korean.py
│   ├── 📄 portfolio_analyzer.py
│   ├── 📄 portfolio_optimizer.py
│   ├── 📄 sample_report_generator.py
│   ├── 📄 setup_free_proxy.py
│   ├── 📄 signal_executor.py
│   ├── 📄 signal_pipeline.py
│   ├── 📄 skeptic_performance_tracker.py
│   ├── 📄 stock_price_scheduler.py
│   ├── 📄 stop_loss_monitor.py
│   ├── 📄 telegram_pdf_sender.py
│   └── 📄 weekly_report_generator.py
├── 📂 signals/
│   ├── 📄 __init__.py
│   ├── 📄 news_signal_generator.py
│   ├── 📄 sector_throttling.py
│   └── 📄 signal_validator.py
├── 📂 skills/
│   ├── 📄 __init__.py
│   ├── 📄 base_skill.py
│   ├── 📂 intelligence/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 claude_skill.py
│   │   ├── 📄 gemini_skill.py
│   │   └── 📄 gpt4o_skill.py
│   ├── 📂 market_data/
│   │   ├── 📄 __init__.py
│   │   └── 📄 news_skill.py
│   ├── 📄 skill_initializer.py
│   ├── 📂 technical/
│   │   ├── 📄 __init__.py
│   │   └── 📄 backtest_skill.py
│   └── 📂 trading/
│       ├── 📄 __init__.py
│       ├── 📄 backtest_skill.py
│       ├── 📄 kis_skill.py
│       ├── 📄 order_skill.py
│       └── 📄 risk_skill.py
├── 📂 strategies/
│   ├── 📄 __init__.py
│   ├── 📄 adaptive_strategy.py
│   ├── 📄 dynamic_screener.py
│   ├── 📄 enhanced_chatgpt_strategy.py
│   ├── 📄 ensemble_strategy.py
│   └── 📄 screener_cache.py
├── 📂 tax/
│   ├── 📄 __init__.py
│   └── 📄 tax_loss_harvesting.py
├── 📄 test_asyncpg.py
├── 📄 test_backfill.py
├── 📄 test_cache_warming.py
├── 📄 test_compression.py
├── 📄 test_enhanced_pipeline.py
├── 📄 test_exact_glm_models.py
├── 📄 test_feature_calculations.py
├── 📄 test_feature_store_full.py
├── 📄 test_glm_45.py
├── 📄 test_glm_4_air.py
├── 📄 test_glm_all_components.py
├── 📄 test_glm_api.py
├── 📄 test_glm_config.py
├── 📄 test_glm_full_pipeline.py
├── 📄 test_glm_intelligence.py
├── 📄 test_glm_json_response.py
├── 📄 test_glm_models.py
├── 📄 test_kis.py
├── 📄 test_mvp_standalone.py
├── 📄 test_mvp_system.py
├── 📄 test_news_analyzer.py
├── 📄 test_newsapi_crawler_logic.py
├── 📄 test_newsapi_direct.py
├── 📄 test_ollama.py
├── 📄 test_openai_api.py
├── 📄 test_paper_trading.py
├── 📄 test_redis_caching.py
├── 📄 test_trading_agent.py
├── 📄 test_unified_processor.py
├── 📄 test_us_market_briefing.py
├── 📂 tests/
│   ├── 📄 __init__.py
│   ├── 📂 ab_test_quick/
│   ├── 📂 backtest_results/
│   ├── 📄 conftest.py
│   ├── 📄 debug_glm_47_response.py
│   ├── 📄 debug_glm_response.py
│   ├── 📄 debug_response_text.py
│   ├── 📄 debug_risk_analyst.py
│   ├── 📂 diagnostic/
│   │   └── 📄 glm_connectivity_check.py
│   ├── 📂 integration/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 test_agents_simple.py
│   │   ├── 📄 test_all_agents.py
│   │   ├── 📄 test_data_collection_5min.py
│   │   ├── 📄 test_end_to_end.py
│   │   ├── 📄 test_event_bus_integration.py
│   │   ├── 📄 test_kis_broker_integration.py
│   │   ├── 📄 test_paper_trading_e2e.py
│   │   ├── 📄 test_paper_trading_quick.py
│   │   └── 📄 test_strategy_repository_integration.py
│   ├── 📂 load/
│   │   └── 📄 locustfile.py
│   ├── 📄 load_test.py
│   ├── 📂 mocks/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 glm_mocks.py
│   │   └── 📄 strategy_mocks.py
│   ├── 📄 quick_test_chatgpt.py
│   ├── 📄 quick_test_phase6.py
│   ├── 📄 run_ab_test.py
│   ├── 📄 run_backtest_tests.py
│   ├── 📄 test_13f_validation.py
│   ├── 📄 test_api_keys.py
│   ├── 📄 test_api_quick.py
│   ├── 📄 test_approval_system.py
│   ├── 📄 test_backtest_engine.py
│   ├── 📄 test_backtest_simple.py
│   ├── 📄 test_cache_warmer.py
│   ├── 📄 test_chatgpt_client.py
│   ├── 📄 test_chip_war_agent.py
│   ├── 📄 test_cik_mapper.py
│   ├── 📄 test_collect_sec_with_tickers.py
│   ├── 📄 test_complete_report_telegram.py
│   ├── 📄 test_conflict_detector.py
│   ├── 📄 test_data_backfill_router.py
│   ├── 📄 test_db_performance.py
│   ├── 📄 test_deep_reasoning_live.py
│   ├── 📄 test_dynamic_screener.py
│   ├── 📄 test_event_subscribers.py
│   ├── 📄 test_fle_calculator.py
│   ├── 📄 test_gemini_client.py
│   ├── 📄 test_glm_client.py
│   ├── 📄 test_glm_integration.py
│   ├── 📄 test_health.py
│   ├── 📄 test_integration.py
│   ├── 📄 test_integration_check.py
│   ├── 📄 test_kill_switch.py
│   ├── 📄 test_kill_switch_integration.py
│   ├── 📄 test_management_credibility.py
│   ├── 📄 test_mock_credibility.py
│   ├── 📄 test_mock_quick.py
│   ├── 📄 test_model_comparison.py
│   ├── 📄 test_model_integration.py
│   ├── 📄 test_model_simple.py
│   ├── 📄 test_models.py
│   ├── 📄 test_non_standard_risk.py
│   ├── 📄 test_order_conflict_integration.py
│   ├── 📄 test_orders_api_conflict.py
│   ├── 📄 test_orders_api_conflict_unit.py
│   ├── 📄 test_ownership_api_pagination.py
│   ├── 📄 test_ownership_transfer.py
│   ├── 📄 test_pdf_telegram.py
│   ├── 📄 test_phase1_performance.py
│   ├── 📄 test_phase6.py
│   ├── 📄 test_phase_e_integration.py
│   ├── 📄 test_portfolio_data.py
│   ├── 📄 test_priority_calculator.py
│   ├── 📄 test_reasoning_api.py
│   ├── 📄 test_risk_integration.py
│   ├── 📄 test_sec_analyzer_enhanced.py
│   ├── 📄 test_sec_with_ticker.py
│   ├── 📄 test_skeptic_live.py
│   ├── 📄 test_skill_loader_mvp.py
│   ├── 📄 test_strategy_repository.py
│   ├── 📄 test_supply_chain_risk.py
│   ├── 📄 test_supply_chain_simple.py
│   ├── 📄 test_tax_loss_harvesting.py
│   ├── 📄 test_telegram_alerts.py
│   ├── 📄 test_trading_agent_with_mgmt.py
│   ├── 📄 test_trading_tendency.py
│   ├── 📄 test_twostage_all_agents.py
│   ├── 📄 test_twostage_e2e.py
│   ├── 📄 test_twostage_e2e_latency.py
│   ├── 📄 test_twostage_simple.py
│   ├── 📄 test_twostage_trader_agent.py
│   ├── 📄 test_war_room_api_dual_mode.py
│   ├── 📄 test_war_room_e2e.py
│   ├── 📄 test_war_room_mvp_handlers.py
│   ├── 📄 test_war_room_with_sec.py
│   ├── 📄 test_warroom_twostage.py
│   ├── 📄 test_warroom_twostage_final.py
│   └── 📂 unit/
│       ├── 📄 __init__.py
│       ├── 📄 run_macro_tests.py
│       ├── 📄 run_phase3_tests.py
│       ├── 📄 test_features.py
│       └── 📄 test_macro_agent.py
├── 📂 trading/
│   ├── 📄 __init__.py
│   ├── 📄 kis_client.py
│   ├── 📄 kis_websocket.py
│   ├── 📄 overseas_stock.py
│   ├── 📄 signal_executor.py
│   └── 📄 war_room_executor.py
├── 📂 utils/
│   ├── 📄 backend_update_manager.py
│   ├── 📄 disclaimer.py
│   ├── 📄 elk_logger.py
│   ├── 📄 retry.py
│   ├── 📄 structure_mapper.py
│   ├── 📄 timezone_manager.py
│   └── 📄 tool_cache.py
└── 📄 warm_cache.py

```

## 2. Module Dependency Graph

```mermaid
graph TD
    subgraph AI [AI]
        ai_claude_client[claude_client]
        ai_embedding_engine[embedding_engine]
        ai_enhanced_analysis_cache[enhanced_analysis_cache]
        ai_enhanced_trading_agent[enhanced_trading_agent]
        ai_model_utils[model_utils]
        ai_news_auto_tagger[news_auto_tagger]
        ai_news_embedder[news_embedder]
        ai_news_intelligence_analyzer[news_intelligence_analyzer]
        ai_news_processing_pipeline[news_processing_pipeline]
        ai_rag_enhanced_analysis[rag_enhanced_analysis]
        ai_regime_detector[regime_detector]
        ai_sec_analyzer[sec_analyzer]
        ai_trading_agent[trading_agent]
        ai_vector_search[vector_search]
        ai_agents_failure_learning_agent[failure_learning_agent]
        ai_collective___init__[__init__]
        ai_consensus_consensus_engine[consensus_engine]
        ai_consensus___init__[__init__]
        ai_core___init__[__init__]
        ai_cost___init__[__init__]
        ai_debate_ai_debate_engine[ai_debate_engine]
        ai_debate_chip_war_agent[chip_war_agent]
        ai_debate_constitutional_debate_engine[constitutional_debate_engine]
        ai_debate_institutional_agent[institutional_agent]
        ai_debate_news_agent[news_agent]
        ai_debate_skeptic_agent[skeptic_agent]
        ai_economics_chip_efficiency_comparator[chip_efficiency_comparator]
        ai_economics_unit_economics_engine[unit_economics_engine]
        ai_intelligence_test_phase3[test_phase3]
        ai_learning_agent_alert_system[agent_alert_system]
        ai_learning_agent_weight_adjuster[agent_weight_adjuster]
        ai_learning_daily_learning_scheduler[daily_learning_scheduler]
        ai_learning_learning_orchestrator[learning_orchestrator]
        ai_learning_news_agent_learning[news_agent_learning]
        ai_learning_remaining_agents_learning[remaining_agents_learning]
        ai_learning_risk_agent_learning[risk_agent_learning]
        ai_learning_trader_agent_learning[trader_agent_learning]
        ai_macro___init__[__init__]
        ai_memory___init__[__init__]
        ai_meta___init__[__init__]
        ai_monitoring_bias_monitor[bias_monitor]
        ai_mvp_analyst_agent_mvp[analyst_agent_mvp]
        ai_mvp_data_helper[data_helper]
        ai_mvp_pm_agent_mvp[pm_agent_mvp]
        ai_mvp_risk_agent_mvp[risk_agent_mvp]
        ai_mvp_test_phase4[test_phase4]
        ai_mvp_trader_agent_mvp[trader_agent_mvp]
        ai_mvp_war_room_mvp[war_room_mvp]
        ai_mvp_deprecated_analyst_agent_mvp[analyst_agent_mvp]
        ai_mvp_deprecated_risk_agent_mvp[risk_agent_mvp]
        ai_mvp_deprecated_trader_agent_mvp[trader_agent_mvp]
        ai_mvp_deprecated_war_room_mvp[war_room_mvp]
        ai_news_news_segment_classifier[news_segment_classifier]
        ai_order_execution_shadow_order_executor[shadow_order_executor]
        ai_portfolio___init__[__init__]
        ai_rag_embedding_service[embedding_service]
        ai_reasoning_deep_reasoning[deep_reasoning]
        ai_reasoning_deep_reasoning_agent[deep_reasoning_agent]
        ai_reasoning_engine[engine]
        ai_reasoning_heuristics[heuristics]
        ai_reasoning_rag_deep_reasoning[rag_deep_reasoning]
        ai_reporters_annual_reporter[annual_reporter]
        ai_reporters_enhanced_daily_reporter[enhanced_daily_reporter]
        ai_reporters_monthly_reporter[monthly_reporter]
        ai_reporters_quarterly_reporter[quarterly_reporter]
        ai_reporters_report_orchestrator[report_orchestrator]
        ai_reporters_test_phase5[test_phase5]
        ai_reporters_trending_news_detector[trending_news_detector]
        ai_reporters_us_market_close_reporter[us_market_close_reporter]
        ai_reporters_weekly_reporter[weekly_reporter]
        ai_risk___init__[__init__]
        ai_router___init__[__init__]
        ai_safety___init__[__init__]
        ai_skills_base_agent[base_agent]
        ai_skills_common_logging_decorator[logging_decorator]
        ai_skills_common_test_logging[test_logging]
        ai_skills_reporting_failure-learning-agent_failure_analyzer[failure_analyzer]
        ai_skills_reporting_failure-learning-agent___init__[__init__]
        ai_skills_reporting_report-orchestrator-agent_report_orchestrator[report_orchestrator]
        ai_skills_reporting_report-orchestrator-agent___init__[__init__]
        ai_skills_system_conflict_detector[conflict_detector]
        ai_skills_war_room_mvp_analyst_agent_mvp_handler[handler]
        ai_skills_war_room_mvp_orchestrator_mvp_handler[handler]
        ai_skills_war_room_mvp_pm_agent_mvp_handler[handler]
        ai_skills_war_room_mvp_risk_agent_mvp_handler[handler]
        ai_skills_war_room_mvp_trader_agent_mvp_handler[handler]
        ai_strategies_dca_strategy[dca_strategy]
        ai_strategies_deep_reasoning_strategy[deep_reasoning_strategy]
        ai_strategies_global_macro_strategy[global_macro_strategy]
        ai_trading_shadow_trader[shadow_trader]
        ai_trading_shadow_trading_agent[shadow_trading_agent]
        ai_video_verify_real[verify_real]
        ai_war_room_shadow_trading_tracker[shadow_trading_tracker]
    end
    subgraph ALERTS [ALERTS]
        alerts___init__[__init__]
    end
    subgraph ANALYSIS [ANALYSIS]
        analysis_ceo_news_analyzer[ceo_news_analyzer]
        analysis_market_gap_analyzer[market_gap_analyzer]
    end
    subgraph ANALYTICS [ANALYTICS]
        analytics_performance_attribution[performance_attribution]
        analytics_peri_calculator[peri_calculator]
        analytics_portfolio_manager[portfolio_manager]
        analytics_risk_analytics[risk_analytics]
        analytics_trade_analytics[trade_analytics]
    end
    subgraph API [API]
        api_accountability_router[accountability_router]
        api_ai_chat_router[ai_chat_router]
        api_ai_quality_router[ai_quality_router]
        api_ai_review_router[ai_review_router]
        api_ai_signals_router[ai_signals_router]
        api_approvals_router[approvals_router]
        api_auth_router[auth_router]
        api_auto_trade_router[auto_trade_router]
        api_backtest_router[backtest_router]
        api_briefing_router[briefing_router]
        api_ceo_analysis_router[ceo_analysis_router]
        api_consensus_router[consensus_router]
        api_correlation_router[correlation_router]
        api_cost_monitoring[cost_monitoring]
        api_data_backfill_router[data_backfill_router]
        api_dividend_router[dividend_router]
        api_emergency_router[emergency_router]
        api_failure_learning_router[failure_learning_router]
        api_feedback_router[feedback_router]
        api_feeds_router[feeds_router]
        api_fle_router[fle_router]
        api_forensics_router[forensics_router]
        api_gemini_free_router[gemini_free_router]
        api_gemini_news_router[gemini_news_router]
        api_global_macro_router[global_macro_router]
        api_incremental_router[incremental_router]
        api_intelligence_router[intelligence_router]
        api_journey_router[journey_router]
        api_kis_integration_router[kis_integration_router]
        api_kis_sync_router[kis_sync_router]
        api_logs_router[logs_router]
        api_mock_router[mock_router]
        api_monitoring_router[monitoring_router]
        api_multi_asset_router[multi_asset_router]
        api_news_analysis_router[news_analysis_router]
        api_news_filter[news_filter]
        api_news_processing_router[news_processing_router]
        api_news_router[news_router]
        api_notifications_router[notifications_router]
        api_options_flow_router[options_flow_router]
        api_orders_router[orders_router]
        api_partitions_router[partitions_router]
        api_performance_router[performance_router]
        api_persona_router[persona_router]
        api_phase_integration_router[phase_integration_router]
        api_portfolio_optimization_router[portfolio_optimization_router]
        api_portfolio_router[portfolio_router]
        api_position_router[position_router]
        api_reasoning_api[reasoning_api]
        api_reasoning_router[reasoning_router]
        api_reports_router[reports_router]
        api_screener_router[screener_router]
        api_sec_router[sec_router]
        api_sec_semantic_search[sec_semantic_search]
        api_signals_router[signals_router]
        api_signal_consolidation_router[signal_consolidation_router]
        api_simple_news_router[simple_news_router]
        api_stock_price_router[stock_price_router]
        api_strategy_router[strategy_router]
        api_tax_routes[tax_routes]
        api_tendency_router[tendency_router]
        api_thesis_router[thesis_router]
        api_v2_router[v2_router]
        api_war_room_analytics_router[war_room_analytics_router]
        api_war_room_router[war_room_router]
        api_weight_adjustment_router[weight_adjustment_router]
    end
    subgraph APPROVAL [APPROVAL]
        approval___init__[__init__]
    end
    subgraph AUTOMATION [AUTOMATION]
        automation_accountability_scheduler[accountability_scheduler]
        automation_auto_trader[auto_trader]
        automation_auto_trading_scheduler[auto_trading_scheduler]
        automation_create_accountability_tables[create_accountability_tables]
        automation_create_test_interpretations[create_test_interpretations]
        automation_kis_portfolio_scheduler[kis_portfolio_scheduler]
        automation_macro_context_updater[macro_context_updater]
        automation_ollama_scheduler[ollama_scheduler]
        automation_price_tracking_scheduler[price_tracking_scheduler]
        automation_price_tracking_verifier[price_tracking_verifier]
        automation_scheduler[scheduler]
        automation_signal_to_order_converter[signal_to_order_converter]
        automation___init__[__init__]
    end
    subgraph BACKTEST [BACKTEST]
        backtest_backtest_engine[backtest_engine]
        backtest_constitutional_backtest_engine[constitutional_backtest_engine]
        backtest_shadow_trade_tracker[shadow_trade_tracker]
        backtest_vintage_backtest[vintage_backtest]
    end
    subgraph BACKTESTING [BACKTESTING]
        backtesting_consensus_backtest[consensus_backtest]
        backtesting_constitutional_backtest_engine[constitutional_backtest_engine]
        backtesting_shadow_trade_tracker[shadow_trade_tracker]
    end
    subgraph CACHING [CACHING]
        caching_decorators[decorators]
        caching_USAGE_EXAMPLES[USAGE_EXAMPLES]
    end
    subgraph CONFIG [CONFIG]
        config_settings[settings]
    end
    subgraph CONTRACTS [CONTRACTS]
        contracts_strategy_contracts[strategy_contracts]
    end
    subgraph CORE [CORE]
        core_models_analytics_models[analytics_models]
        core_models_embedding_models[embedding_models]
        core_models_news_models[news_models]
        core_models_stock_price_models[stock_price_models]
    end
    subgraph DATA [DATA]
        data_decision_store[decision_store]
        data_deep_reasoning_store[deep_reasoning_store]
        data_news_analyzer[news_analyzer]
        data_rss_crawler[rss_crawler]
        data_rss_feed_discovery[rss_feed_discovery]
        data_sec_analysis_cache[sec_analysis_cache]
        data_sec_client[sec_client]
        data_sec_file_storage[sec_file_storage]
        data_sec_parser[sec_parser]
        data_stock_price_storage[stock_price_storage]
        data_calendar_rss_news_aggregator[rss_news_aggregator]
        data_calendar_test_forex_factory_live[test_forex_factory_live]
        data_calendar_test_google_news[test_google_news]
        data_calendar_test_realtime_news[test_realtime_news]
        data_calendar_test_williams_speech[test_williams_speech]
        data_collectors_finviz_collector[finviz_collector]
        data_collectors_free_news_monitor[free_news_monitor]
        data_collectors_smart_money_collector[smart_money_collector]
        data_collectors_stealth_web_crawler[stealth_web_crawler]
        data_feature_store_store[store]
        data_knowledge_ai_value_chain[ai_value_chain]
        data_knowledge_memory_builder[memory_builder]
        data_knowledge_graph_knowledge_graph[knowledge_graph]
        data_models_proposal[proposal]
        data_models_shadow_trade[shadow_trade]
        data_processors_unified_news_processor[unified_news_processor]
    end
    subgraph DATABASE [DATABASE]
        database_models_assets[models_assets]
        database_repository[repository]
        database_repository_multi_strategy[repository_multi_strategy]
        database_vector_models[vector_models]
        database___init__[__init__]
        database_migrations_add_ai_trade_decisions_table[add_ai_trade_decisions_table]
        database_migrations_add_v2_2_caching_fields[add_v2_2_caching_fields]
        database_migrations_apply_migration[apply_migration]
        database_migrations_check_table_structure[check_table_structure]
        database_migrations_create_all_tables[create_all_tables]
        database_migrations_create_economic_events_table[create_economic_events_table]
        database_migrations_create_rss_feeds_table[create_rss_feeds_table]
        database_migrations_drop_and_recreate_economic_events_table[drop_and_recreate_economic_events_table]
        database_migrations_run_migration[run_migration]
        database_schemas_constitutional_validation_schema[constitutional_validation_schema]
    end
    subgraph DEMOS [DEMOS]
        demos_phase1_demo[phase1_demo]
    end
    subgraph EVENTS [EVENTS]
        events_subscribers[subscribers]
    end
    subgraph EXAMPLES [EXAMPLES]
        examples_elk_logging_example[elk_logging_example]
        examples_tax_harvesting_example[tax_harvesting_example]
    end
    subgraph EXECUTION [EXECUTION]
        execution_kis_broker_adapter[kis_broker_adapter]
        execution_order_manager[order_manager]
        execution_safety_guard[safety_guard]
        execution_rl_train[train]
    end
    subgraph FUSION [FUSION]
        fusion_engine[engine]
        fusion_gates_event_priority[event_priority]
        fusion_gates_liquidity[liquidity]
    end
    subgraph INTELLIGENCE [INTELLIGENCE]
        intelligence_news_agent[news_agent]
    end
    subgraph MARKET_DATA [MARKET_DATA]
        market_data_price_scheduler[price_scheduler]
    end
    subgraph MONITORING [MONITORING]
        monitoring_data_quality_metrics[data_quality_metrics]
        monitoring_performance_monitor[performance_monitor]
    end
    subgraph NEWS [NEWS]
        news_news_crawler[news_crawler]
        news_rss_crawler[rss_crawler]
        news_rss_crawler_with_db[rss_crawler_with_db]
        news___init__[__init__]
    end
    subgraph NOTIFICATIONS [NOTIFICATIONS]
        notifications_event_subscriber[event_subscriber]
        notifications_telegram_commander_bot[telegram_commander_bot]
        notifications_test_chatgpt_completion[test_chatgpt_completion]
    end
    subgraph ORCHESTRATION [ORCHESTRATION]
        orchestration_data_accumulation_orchestrator[data_accumulation_orchestrator]
    end
    subgraph PIPELINES [PIPELINES]
        pipelines_news_embedding_pipeline[news_embedding_pipeline]
        pipelines_sec_embedding_pipeline[sec_embedding_pipeline]
    end
    subgraph REPORTING [REPORTING]
        reporting_pdf_renderer[pdf_renderer]
        reporting_report_generator[report_generator]
        reporting_shield_report_generator[shield_report_generator]
    end
    subgraph ROUTERS [ROUTERS]
        routers_kill_switch_router[kill_switch_router]
        routers_war_room_mvp_router[war_room_mvp_router]
    end
    subgraph ROUTING [ROUTING]
        routing_model_selector[model_selector]
        routing_semantic_router[semantic_router]
        routing_skill_router_integration[skill_router_integration]
        routing_test_semantic_router[test_semantic_router]
        routing_tool_selector[tool_selector]
        routing___init__[__init__]
    end
    subgraph RUNNERS [RUNNERS]
        runners_shadow_runner[shadow_runner]
    end
    subgraph SCHEDULERS [SCHEDULERS]
        schedulers_chip_intelligence_updater[chip_intelligence_updater]
        schedulers_correlation_scheduler[correlation_scheduler]
        schedulers_failure_learning_scheduler[failure_learning_scheduler]
    end
    subgraph SCRIPTS [SCRIPTS]
        scripts_add_new_feeds[add_new_feeds]
        scripts_backfill_embeddings[backfill_embeddings]
        scripts_benchmark_price_storage[benchmark_price_storage]
        scripts_check_data_readiness[check_data_readiness]
        scripts_check_macro_context[check_macro_context]
        scripts_check_model_deprecations[check_model_deprecations]
        scripts_check_shadow_db[check_shadow_db]
        scripts_create_agent_vote_tracking[create_agent_vote_tracking]
        scripts_create_deep_reasoning_table[create_deep_reasoning_table]
        scripts_create_stock_tables[create_stock_tables]
        scripts_debug_settings[debug_settings]
        scripts_fix_sqlite_tables[fix_sqlite_tables]
        scripts_generate_daily_briefing[generate_daily_briefing]
        scripts_import_kis_data[import_kis_data]
        scripts_init_database[init_database]
        scripts_init_dividend_tables[init_dividend_tables]
        scripts_init_kg[init_kg]
        scripts_init_kg_PLAN[init_kg_PLAN]
        scripts_init_kg_via_repo[init_kg_via_repo]
        scripts_init_vector_db[init_vector_db]
        scripts_migrate_dividend_aristocrats[migrate_dividend_aristocrats]
        scripts_migrate_news_to_postgres[migrate_news_to_postgres]
        scripts_monitor_free_news[monitor_free_news]
        scripts_monitor_ft[monitor_ft]
        scripts_reset_database[reset_database]
        scripts_seed_strategies[seed_strategies]
        scripts_seed_test_data[seed_test_data]
        scripts_seed_test_signals[seed_test_signals]
        scripts_test_deep_reasoning_features[test_deep_reasoning_features]
        scripts_test_phase25_4[test_phase25_4]
        scripts_test_price_verifier_flow[test_price_verifier_flow]
        scripts_test_semantic_search[test_semantic_search]
        scripts_test_structured_outputs[test_structured_outputs]
        scripts_test_tax_optimizer[test_tax_optimizer]
        scripts_test_watchtower[test_watchtower]
        scripts_verify_annual_report[verify_annual_report]
        scripts_verify_deep_reasoning[verify_deep_reasoning]
        scripts_verify_news_integration_direct[verify_news_integration_direct]
        scripts_verify_news_interpretation[verify_news_interpretation]
        scripts_verify_phase5_integrity[verify_phase5_integrity]
        scripts_verify_weekly_report[verify_weekly_report]
    end
    subgraph SERVICES [SERVICES]
        services_analytics_aggregator[analytics_aggregator]
        services_annual_report_generator[annual_report_generator]
        services_asset_service[asset_service]
        services_broker_position_sync[broker_position_sync]
        services_complete_5page_report_generator[complete_5page_report_generator]
        services_complete_korean_report_generator[complete_korean_report_generator]
        services_complete_report_generator[complete_report_generator]
        services_daily_briefing_cache_manager[daily_briefing_cache_manager]
        services_daily_briefing_service[daily_briefing_service]
        services_daily_price_sync[daily_price_sync]
        services_daily_report_scheduler[daily_report_scheduler]
        services_economic_calendar_fetcher[economic_calendar_fetcher]
        services_economic_calendar_manager[economic_calendar_manager]
        services_economic_watcher[economic_watcher]
        services_final_korean_report_generator[final_korean_report_generator]
        services_fred_economic_calendar[fred_economic_calendar]
        services_news_event_handler[news_event_handler]
        services_news_poller[news_poller]
        services_optimized_signal_pipeline[optimized_signal_pipeline]
        services_ownership_service[ownership_service]
        services_page1_generator[page1_generator]
        services_page1_generator_korean[page1_generator_korean]
        services_page2_generator_korean[page2_generator_korean]
        services_page3_generator[page3_generator]
        services_page3_generator_korean[page3_generator_korean]
        services_page5_generator_korean[page5_generator_korean]
        services_signal_pipeline[signal_pipeline]
        services_stock_price_scheduler[stock_price_scheduler]
        services_stop_loss_monitor[stop_loss_monitor]
        services_weekly_report_generator[weekly_report_generator]
        services___init__[__init__]
    end
    subgraph SKILLS [SKILLS]
        skills_skill_initializer[skill_initializer]
        skills___init__[__init__]
        skills_intelligence_claude_skill[claude_skill]
        skills_intelligence_gemini_skill[gemini_skill]
        skills_intelligence_gpt4o_skill[gpt4o_skill]
        skills_intelligence___init__[__init__]
        skills_market_data_news_skill[news_skill]
        skills_market_data___init__[__init__]
        skills_technical_backtest_skill[backtest_skill]
        skills_technical___init__[__init__]
        skills_trading_backtest_skill[backtest_skill]
        skills_trading_kis_skill[kis_skill]
        skills_trading_order_skill[order_skill]
        skills_trading_risk_skill[risk_skill]
        skills_trading___init__[__init__]
    end
    subgraph TESTS [TESTS]
        tests_conftest[conftest]
        tests_debug_glm_47_response[debug_glm_47_response]
        tests_debug_glm_response[debug_glm_response]
        tests_debug_response_text[debug_response_text]
        tests_debug_risk_analyst[debug_risk_analyst]
        tests_test_13f_validation[test_13f_validation]
        tests_test_approval_system[test_approval_system]
        tests_test_chip_war_agent[test_chip_war_agent]
        tests_test_cik_mapper[test_cik_mapper]
        tests_test_collect_sec_with_tickers[test_collect_sec_with_tickers]
        tests_test_complete_report_telegram[test_complete_report_telegram]
        tests_test_conflict_detector[test_conflict_detector]
        tests_test_data_backfill_router[test_data_backfill_router]
        tests_test_event_subscribers[test_event_subscribers]
        tests_test_fle_calculator[test_fle_calculator]
        tests_test_glm_client[test_glm_client]
        tests_test_glm_integration[test_glm_integration]
        tests_test_kill_switch_integration[test_kill_switch_integration]
        tests_test_models[test_models]
        tests_test_orders_api_conflict[test_orders_api_conflict]
        tests_test_orders_api_conflict_unit[test_orders_api_conflict_unit]
        tests_test_order_conflict_integration[test_order_conflict_integration]
        tests_test_ownership_api_pagination[test_ownership_api_pagination]
        tests_test_ownership_transfer[test_ownership_transfer]
        tests_test_portfolio_data[test_portfolio_data]
        tests_test_priority_calculator[test_priority_calculator]
        tests_test_sec_analyzer_enhanced[test_sec_analyzer_enhanced]
        tests_test_sec_with_ticker[test_sec_with_ticker]
        tests_test_strategy_repository[test_strategy_repository]
        tests_test_tax_loss_harvesting[test_tax_loss_harvesting]
        tests_test_telegram_alerts[test_telegram_alerts]
        tests_test_trading_tendency[test_trading_tendency]
        tests_test_twostage_e2e_latency[test_twostage_e2e_latency]
        tests_test_war_room_e2e[test_war_room_e2e]
        tests_test_war_room_with_sec[test_war_room_with_sec]
        tests_integration_test_end_to_end[test_end_to_end]
        tests_integration_test_event_bus_integration[test_event_bus_integration]
        tests_integration_test_paper_trading_e2e[test_paper_trading_e2e]
        tests_integration_test_strategy_repository_integration[test_strategy_repository_integration]
    end
    subgraph TRADING [TRADING]
        trading_overseas_stock[overseas_stock]
    end
    check_db_news --> database_repository
    check_db_news --> database_models
    init_news_db --> data_news_models
    main --> monitoring_metrics_collector
    main --> monitoring_alert_manager
    main --> monitoring_health_monitor
    main --> auth
    main --> events_subscribers
    main --> api_emergency_router
    run_news_crawler --> services_news_poller
    run_news_crawler --> database_models
    test_compression --> ai_compression
    test_enhanced_pipeline --> api_intelligence_router
    test_exact_glm_models --> ai_llm_providers
    test_glm_45 --> ai_llm_providers
    test_glm_4_air --> ai_llm_providers
    test_glm_all_components --> ai_llm_providers
    test_glm_all_components --> ai_intelligence_news_filter
    test_glm_all_components --> ai_intelligence_narrative_state_engine
    test_glm_api --> ai_llm_providers
    test_glm_config --> ai_glm_client
    test_glm_config --> ai_llm_providers
    test_glm_full_pipeline --> ai_llm_providers
    test_glm_full_pipeline --> ai_intelligence_news_filter
    test_glm_full_pipeline --> ai_intelligence_narrative_state_engine
    test_glm_full_pipeline --> ai_intelligence_fact_checker
    test_glm_full_pipeline --> ai_intelligence_market_confirmation
    test_glm_full_pipeline --> ai_intelligence_horizon_tagger
    test_glm_full_pipeline --> ai_intelligence_enhanced_news_pipeline
    test_glm_intelligence --> ai_llm_providers
    test_glm_intelligence --> ai_intelligence_news_filter
    test_glm_json_response --> ai_llm_providers
    test_glm_models --> ai_llm_providers
    test_news_analyzer --> database_repository
    test_news_analyzer --> database_models
    test_news_analyzer --> data_news_analyzer
    test_ollama --> ai_llm
    test_ollama --> data_processors_news_processor
    test_openai_api --> ai_llm_providers
    test_unified_processor --> database_repository
    test_unified_processor --> data_rss_crawler
    test_unified_processor --> data_processors_unified_news_processor
    test_us_market_briefing --> ai_reporters_enhanced_daily_reporter
    test_us_market_briefing --> notifications_telegram_notifier
    ai_claude_client --> config_settings
    ai_embedding_engine --> core_models_embedding_models
    ai_enhanced_analysis_cache --> config_storage_config
    ai_enhanced_trading_agent --> ai_trading_agent
    ai_enhanced_trading_agent --> models_trading_decision
    ai_enhanced_trading_agent --> services_market_scanner
    ai_enhanced_trading_agent --> services_market_scanner_massive_api_client
    ai_enhanced_trading_agent --> ai_macro
    ai_enhanced_trading_agent --> ai_learning_feedback_loop_service
    ai_enhanced_trading_agent --> ai_reasoning_skeptic_agent
    ai_enhanced_trading_agent --> ai_reasoning_macro_consistency_checker
    ai_enhanced_trading_agent --> intelligence_reporter_daily_briefing
    ai_model_utils --> ai_model_registry
    ai_news_auto_tagger --> data_news_models
    ai_news_embedder --> data_news_models
    ai_news_intelligence_analyzer --> data_news_models
    ai_news_processing_pipeline --> data_news_models
    ai_news_processing_pipeline --> ai_news_intelligence_analyzer
    ai_news_processing_pipeline --> ai_news_auto_tagger
    ai_news_processing_pipeline --> ai_news_embedder
    ai_rag_enhanced_analysis --> ai_vector_search
    ai_rag_enhanced_analysis --> ai_enhanced_analysis_cache
    ai_regime_detector --> ai_market_regime
    ai_regime_detector --> data_feature_store_store
    ai_sec_analyzer --> data_sec_client
    ai_sec_analyzer --> data_sec_parser
    ai_sec_analyzer --> core_models_sec_models
    ai_sec_analyzer --> core_models_sec_analysis_models
    ai_sec_analyzer --> ai_sec_prompts
    ai_sec_analyzer --> ai_compression
    ai_trading_agent --> config_settings
    ai_trading_agent --> ai_claude_client
    ai_trading_agent --> data_feature_store_store
    ai_trading_agent --> models_trading_decision
    ai_vector_search --> core_models_embedding_models
    ai_vector_search --> ai_embedding_engine
    ai_agents_failure_learning_agent --> database_repository
    ai_agents_failure_learning_agent --> database_models
    ai_collective___init__ --> ai_collective_ai_role_manager
    ai_consensus_consensus_engine --> schemas_base_schema
    ai_consensus_consensus_engine --> ai_consensus_consensus_models
    ai_consensus_consensus_engine --> ai_consensus_voting_rules
    ai_consensus___init__ --> ai_consensus_consensus_engine
    ai_consensus___init__ --> ai_consensus_consensus_models
    ai_consensus___init__ --> ai_consensus_voting_rules
    ai_core___init__ --> ai_core_decision_protocol
    ai_cost___init__ --> ai_cost_subscription_manager
    ai_debate_ai_debate_engine --> schemas_base_schema
    ai_debate_chip_war_agent --> ai_economics_chip_war_simulator
    ai_debate_chip_war_agent --> ai_economics_chip_war_simulator_v2
    ai_debate_chip_war_agent --> ai_economics_chip_intelligence_engine
    ai_debate_chip_war_agent --> ai_debate_chip_war_agent_helpers
    ai_debate_constitutional_debate_engine --> ai_debate_ai_debate_engine
    ai_debate_constitutional_debate_engine --> constitution
    ai_debate_constitutional_debate_engine --> backtest_shadow_trade_tracker
    ai_debate_constitutional_debate_engine --> schemas_base_schema
    ai_debate_institutional_agent --> schemas_base_schema
    ai_debate_institutional_agent --> data_collectors_smart_money_collector
    ai_debate_news_agent --> database_models
    ai_debate_news_agent --> database_repository
    ai_debate_news_agent --> ai_gemini_client
    ai_debate_skeptic_agent --> schemas_base_schema
    ai_economics_chip_efficiency_comparator --> schemas_base_schema
    ai_economics_chip_efficiency_comparator --> ai_economics_unit_economics_engine
    ai_economics_unit_economics_engine --> schemas_base_schema
    ai_intelligence_test_phase3 --> ai_intelligence_market_moving_score
    ai_learning_agent_alert_system --> database_repository
    ai_learning_agent_weight_adjuster --> database_repository
    ai_learning_daily_learning_scheduler --> ai_learning_learning_orchestrator
    ai_learning_learning_orchestrator --> ai_learning_news_agent_learning
    ai_learning_learning_orchestrator --> ai_learning_trader_agent_learning
    ai_learning_learning_orchestrator --> ai_learning_risk_agent_learning
    ai_learning_learning_orchestrator --> ai_learning_remaining_agents_learning
    ai_learning_news_agent_learning --> ai_learning_hallucination_detector
    ai_learning_news_agent_learning --> ai_learning_statistical_validators
    ai_learning_remaining_agents_learning --> ai_learning_hallucination_detector
    ai_learning_remaining_agents_learning --> ai_learning_statistical_validators
    ai_learning_risk_agent_learning --> ai_learning_hallucination_detector
    ai_learning_trader_agent_learning --> ai_learning_hallucination_detector
    ai_learning_trader_agent_learning --> ai_learning_walk_forward_validator
    ai_macro___init__ --> ai_macro_global_market_map
    ai_macro___init__ --> ai_macro_country_risk_engine
    ai_macro___init__ --> ai_macro_macro_data_collector
    ai_memory___init__ --> ai_memory_investment_journey_memory
    ai_meta___init__ --> ai_meta_debate_logger
    ai_meta___init__ --> ai_meta_agent_weight_trainer
    ai_meta___init__ --> ai_meta_strategy_refiner
    ai_monitoring_bias_monitor --> schemas_base_schema
    ai_mvp_analyst_agent_mvp --> ai_mvp_gemini_reasoning_agent_base
    ai_mvp_analyst_agent_mvp --> ai_mvp_gemini_structuring_agent
    ai_mvp_analyst_agent_mvp --> ai_schemas_war_room_schemas
    ai_mvp_data_helper --> database_models
    ai_mvp_data_helper --> database_repository
    ai_mvp_data_helper --> data_rss_crawler
    ai_mvp_data_helper --> ai_mvp_ticker_mappings
    ai_mvp_pm_agent_mvp --> ai_schemas_war_room_schemas
    ai_mvp_pm_agent_mvp --> ai_safety_leverage_guardian
    ai_mvp_pm_agent_mvp --> ai_router_persona_router
    ai_mvp_risk_agent_mvp --> ai_mvp_gemini_reasoning_agent_base
    ai_mvp_risk_agent_mvp --> ai_mvp_gemini_structuring_agent
    ai_mvp_risk_agent_mvp --> ai_schemas_war_room_schemas
    ai_mvp_test_phase4 --> ai_mvp_conflict_resolver
    ai_mvp_trader_agent_mvp --> ai_mvp_gemini_reasoning_agent_base
    ai_mvp_trader_agent_mvp --> ai_mvp_gemini_structuring_agent
    ai_mvp_trader_agent_mvp --> ai_schemas_war_room_schemas
    ai_mvp_war_room_mvp --> execution_execution_router
    ai_mvp_war_room_mvp --> execution_order_validator
    ai_mvp_war_room_mvp --> monitoring_performance_monitor
    ai_mvp_war_room_mvp --> ai_router_persona_router
    ai_mvp_deprecated_analyst_agent_mvp --> ai_schemas_war_room_schemas
    ai_mvp_deprecated_analyst_agent_mvp --> ai_debate_news_agent
    ai_mvp_deprecated_analyst_agent_mvp --> ai_reasoning_deep_reasoning_agent
    ai_mvp_deprecated_analyst_agent_mvp --> ai_mvp_stock_specific_tsla_analyzer
    ai_mvp_deprecated_analyst_agent_mvp --> ai_mvp_stock_specific_nvda_analyzer
    ai_mvp_deprecated_risk_agent_mvp --> ai_schemas_war_room_schemas
    ai_mvp_deprecated_trader_agent_mvp --> ai_schemas_war_room_schemas
    ai_mvp_deprecated_war_room_mvp --> execution_execution_router
    ai_mvp_deprecated_war_room_mvp --> execution_order_validator
    ai_mvp_deprecated_war_room_mvp --> monitoring_performance_monitor
    ai_mvp_deprecated_war_room_mvp --> ai_router_persona_router
    ai_news_news_segment_classifier --> schemas_base_schema
    ai_news_news_segment_classifier --> data_knowledge_ai_value_chain
    ai_order_execution_shadow_order_executor --> database_models
    ai_order_execution_shadow_order_executor --> brokers_kis_broker
    ai_order_execution_shadow_order_executor --> core_database
    ai_portfolio___init__ --> ai_portfolio_account_partitioning
    ai_rag_embedding_service --> database_vector_db
    ai_rag_embedding_service --> database_vector_models
    ai_rag_embedding_service --> database_models
    ai_reasoning_deep_reasoning --> config_phase14
    ai_reasoning_deep_reasoning --> ai_ai_client_factory
    ai_reasoning_deep_reasoning --> data_knowledge_graph_knowledge_graph
    ai_reasoning_deep_reasoning_agent --> ai_economics_chip_war_simulator_v2
    ai_reasoning_deep_reasoning_agent --> ai_gemini_client
    ai_reasoning_engine --> ai_reasoning_models
    ai_reasoning_engine --> ai_reasoning_prompts
    ai_reasoning_engine --> ai_reasoning_heuristics
    ai_reasoning_heuristics --> ai_reasoning_models
    ai_reasoning_rag_deep_reasoning --> ai_reasoning_deep_reasoning
    ai_reasoning_rag_deep_reasoning --> data_knowledge_graph_knowledge_graph
    ai_reporters_annual_reporter --> ai_gemini_client
    ai_reporters_annual_reporter --> ai_portfolio_account_partitioning
    ai_reporters_annual_reporter --> database_repository
    ai_reporters_annual_reporter --> database_models
    ai_reporters_enhanced_daily_reporter --> ai_gemini_client
    ai_reporters_enhanced_daily_reporter --> core_database
    ai_reporters_enhanced_daily_reporter --> database_models
    ai_reporters_monthly_reporter --> ai_gemini_client
    ai_reporters_monthly_reporter --> ai_portfolio_account_partitioning
    ai_reporters_monthly_reporter --> database_repository
    ai_reporters_monthly_reporter --> database_models
    ai_reporters_quarterly_reporter --> ai_gemini_client
    ai_reporters_quarterly_reporter --> ai_portfolio_account_partitioning
    ai_reporters_quarterly_reporter --> database_repository
    ai_reporters_quarterly_reporter --> database_models
    ai_reporters_report_orchestrator --> ai_debate_news_agent
    ai_reporters_report_orchestrator --> ai_market_regime
    ai_reporters_test_phase5 --> ai_reporters_funnel_generator
    ai_reporters_trending_news_detector --> ai_gemini_client
    ai_reporters_us_market_close_reporter --> ai_gemini_client
    ai_reporters_weekly_reporter --> ai_gemini_client
    ai_risk___init__ --> ai_risk_theme_risk_detector
    ai_router___init__ --> ai_router_persona_router
    ai_safety___init__ --> ai_safety_leverage_guardian
    ai_skills_base_agent --> ai_skills_skill_loader
    ai_skills_common_logging_decorator --> ai_skills_common_agent_logger
    ai_skills_common_test_logging --> ai_skills_common_agent_logger
    ai_skills_reporting_failure-learning-agent_failure_analyzer --> database_repository
    ai_skills_reporting_failure-learning-agent___init__ --> ai_skills_reporting_failure_learning_agent_failure_analyzer
    ai_skills_reporting_report-orchestrator-agent_report_orchestrator --> database_repository
    ai_skills_reporting_report-orchestrator-agent___init__ --> ai_skills_reporting_report_orchestrator_agent_report_orchestrator
    ai_skills_system_conflict_detector --> database_repository_multi_strategy
    ai_skills_war_room_mvp_analyst_agent_mvp_handler --> ai_mvp_analyst_agent_mvp
    ai_skills_war_room_mvp_orchestrator_mvp_handler --> ai_mvp_war_room_mvp
    ai_skills_war_room_mvp_pm_agent_mvp_handler --> ai_mvp_pm_agent_mvp
    ai_skills_war_room_mvp_risk_agent_mvp_handler --> ai_mvp_risk_agent_mvp
    ai_skills_war_room_mvp_trader_agent_mvp_handler --> ai_mvp_trader_agent_mvp
    ai_strategies_dca_strategy --> schemas_base_schema
    ai_strategies_deep_reasoning_strategy --> schemas_base_schema
    ai_strategies_global_macro_strategy --> ai_macro_global_market_map
    ai_trading_shadow_trader --> database_repository
    ai_trading_shadow_trading_agent --> database_models
    ai_video_verify_real --> ai_video_video_analyzer
    ai_war_room_shadow_trading_tracker --> data_models_shadow_trade
    alerts___init__ --> alerts_alert_system
    analysis_ceo_news_analyzer --> services_fast_polling_service
    analysis_market_gap_analyzer --> brokers_kis_broker
    analytics_performance_attribution --> core_models_analytics_models
    analytics_peri_calculator --> schemas_base_schema
    analytics_portfolio_manager --> skills_trading_risk_skill
    analytics_risk_analytics --> core_models_analytics_models
    analytics_trade_analytics --> core_models_analytics_models
    api_accountability_router --> database_repository
    api_ai_chat_router --> ai_skills_common_logging_decorator
    api_ai_quality_router --> ai_skills_common_logging_decorator
    api_ai_review_router --> ai_ai_review_models
    api_ai_signals_router --> ai_skills_common_logging_decorator
    api_approvals_router --> approval
    api_auth_router --> auth
    api_auto_trade_router --> ai_skills_common_logging_decorator
    api_backtest_router --> backtesting_signal_backtest_engine
    api_briefing_router --> services_daily_briefing_service
    api_ceo_analysis_router --> ai_sec_analyzer
    api_consensus_router --> schemas_base_schema
    api_correlation_router --> database_repository
    api_cost_monitoring --> core_database
    api_data_backfill_router --> ai_skills_common_logging_decorator
    api_dividend_router --> data_collectors_dividend_collector
    api_emergency_router --> database_repository
    api_failure_learning_router --> database_repository
    api_feedback_router --> database_models
    api_feeds_router --> data_news_models
    api_fle_router --> metrics
    api_forensics_router --> ai_skills_common_logging_decorator
    api_gemini_free_router --> ai_skills_common_logging_decorator
    api_gemini_news_router --> data_gemini_news_fetcher
    api_global_macro_router --> ai_skills_common_logging_decorator
    api_incremental_router --> core_database
    api_intelligence_router --> ai_intelligence_contrary_signal
    api_journey_router --> ai_memory_investment_journey_memory
    api_kis_integration_router --> api_phase_integration_router
    api_kis_sync_router --> database_models
    api_logs_router --> log_manager
    api_mock_router --> database_repository
    api_monitoring_router --> ai_skills_common_logging_decorator
    api_multi_asset_router --> database_repository
    api_news_analysis_router --> data_news_models
    api_news_filter --> core_database
    api_news_processing_router --> data_news_models
    api_news_router --> database_models
    api_notifications_router --> notifications_notification_manager
    api_options_flow_router --> ai_skills_common_logging_decorator
    api_orders_router --> database_models
    api_partitions_router --> ai_portfolio_account_partitioning
    api_performance_router --> database_repository
    api_persona_router --> ai_router_persona_router
    api_phase_integration_router --> ai_news_news_segment_classifier
    api_portfolio_optimization_router --> services_portfolio_optimizer
    api_portfolio_router --> brokers_kis_broker
    api_position_router --> data_position_tracker
    api_reasoning_api --> ai_reasoning_deep_reasoning
    api_reasoning_router --> ai_reasoning_engine
    api_reports_router --> core_database
    api_screener_router --> services_market_scanner
    api_sec_router --> ai_skills_common_logging_decorator
    api_sec_semantic_search --> core_database
    api_signals_router --> signals_news_signal_generator
    api_signal_consolidation_router --> database_models
    api_simple_news_router --> database_repository
    api_stock_price_router --> core_database
    api_strategy_router --> database_repository
    api_tax_routes --> tax
    api_tendency_router --> metrics_trading_tendency_analyzer
    api_thesis_router --> ai_analysis_thesis_violation_detector
    api_v2_router --> ai_enhanced_trading_agent
    api_war_room_analytics_router --> ai_war_room_debate_visualizer
    api_war_room_router --> database_models
    api_weight_adjustment_router --> ai_skills_common_logging_decorator
    approval___init__ --> approval_approval_models
    automation_accountability_scheduler --> automation_price_tracking_verifier
    automation_auto_trader --> ai_consensus_consensus_models
    automation_auto_trading_scheduler --> ai_strategies_deep_reasoning_strategy
    automation_create_accountability_tables --> database_models
    automation_create_test_interpretations --> database_repository
    automation_kis_portfolio_scheduler --> database_repository
    automation_macro_context_updater --> database_repository
    automation_ollama_scheduler --> news_rss_crawler
    automation_price_tracking_scheduler --> database_repository
    automation_price_tracking_verifier --> database_repository
    automation_scheduler --> automation_macro_context_updater
    automation_signal_to_order_converter --> schemas_base_schema
    automation___init__ --> automation_macro_context_updater
    backtest_backtest_engine --> backtest_portfolio_manager
    backtest_constitutional_backtest_engine --> constitution
    backtest_shadow_trade_tracker --> data_models_shadow_trade
    backtest_vintage_backtest --> schemas_base_schema
    backtesting_consensus_backtest --> backtesting_backtest_engine
    backtesting_constitutional_backtest_engine --> constitution_constitution
    backtesting_shadow_trade_tracker --> data_models_shadow_trade
    caching_decorators --> caching
    caching_USAGE_EXAMPLES --> caching
    config_settings --> config_secrets_manager
    contracts_strategy_contracts --> api_schemas_strategy_schemas
    core_models_analytics_models --> core_database
    core_models_embedding_models --> core_database
    core_models_news_models --> core_database
    core_models_stock_price_models --> core_database
    data_decision_store --> models_trading_decision
    data_deep_reasoning_store --> ai_reasoning_models
    data_news_analyzer --> database_models
    data_rss_crawler --> database_models
    data_rss_feed_discovery --> data_news_models
    data_sec_analysis_cache --> core_models_sec_analysis_models
    data_sec_client --> core_models_sec_models
    data_sec_file_storage --> config_storage_config
    data_sec_parser --> core_models_sec_models
    data_stock_price_storage --> core_models_stock_price_models
    data_calendar_rss_news_aggregator --> data_rss_crawler
    data_calendar_test_forex_factory_live --> data_calendar_forex_factory_scraper
    data_calendar_test_google_news --> data_calendar_google_news_collector
    data_calendar_test_realtime_news --> data_calendar_google_news_collector
    data_calendar_test_williams_speech --> config_settings
    data_collectors_finviz_collector --> database_repository
    data_collectors_free_news_monitor --> data_collectors_stealth_web_crawler
    data_collectors_smart_money_collector --> data_collectors_api_clients_yahoo_client
    data_collectors_stealth_web_crawler --> database_repository
    data_feature_store_store --> data_feature_store_cache_layer
    data_knowledge_ai_value_chain --> schemas_base_schema
    data_knowledge_memory_builder --> data_vector_store_store
    data_knowledge_graph_knowledge_graph --> database_models
    data_models_proposal --> core_models_base
    data_models_shadow_trade --> core_models_base
    data_processors_unified_news_processor --> database_models
    database_models_assets --> database_models
    database_repository --> database_models
    database_repository_multi_strategy --> database_models
    database_vector_models --> database_vector_db
    database___init__ --> database_models
    database_migrations_add_ai_trade_decisions_table --> database_repository
    database_migrations_add_v2_2_caching_fields --> database_db_service
    database_migrations_apply_migration --> database_repository
    database_migrations_check_table_structure --> config_settings
    database_migrations_create_all_tables --> database_models
    database_migrations_create_economic_events_table --> database_db_service
    database_migrations_create_rss_feeds_table --> database_models
    database_migrations_drop_and_recreate_economic_events_table --> database_db_service
    database_migrations_run_migration --> config_settings
    database_schemas_constitutional_validation_schema --> database_models
    demos_phase1_demo --> ai_compression
    events_subscribers --> events
    examples_elk_logging_example --> utils_elk_logger
    examples_tax_harvesting_example --> tax
    execution_kis_broker_adapter --> execution_executors
    execution_order_manager --> events
    execution_safety_guard --> execution_kill_switch
    execution_rl_train --> execution_rl_env
    fusion_engine --> fusion_normalizer
    fusion_gates_event_priority --> fusion_normalizer
    fusion_gates_liquidity --> fusion_normalizer
    intelligence_news_agent --> database_models
    market_data_price_scheduler --> database_repository
    monitoring_data_quality_metrics --> database_repository
    monitoring_performance_monitor --> notifications_telegram_notifier
    news_news_crawler --> database_repository
    news_rss_crawler --> ai_reasoning_deep_reasoning
    news_rss_crawler_with_db --> news_rss_crawler
    news___init__ --> news_rss_crawler
    notifications_event_subscriber --> events
    notifications_telegram_commander_bot --> data_models_proposal
    notifications_test_chatgpt_completion --> notifications_telegram_notifier
    orchestration_data_accumulation_orchestrator --> news_rss_crawler_with_db
    pipelines_news_embedding_pipeline --> ai_embedding_engine
    pipelines_sec_embedding_pipeline --> ai_embedding_engine
    reporting_pdf_renderer --> reporting_report_templates
    reporting_report_generator --> core_models_analytics_models
    reporting_shield_report_generator --> reporting_shield_metrics
    routers_kill_switch_router --> execution_kill_switch
    routers_war_room_mvp_router --> database_repository
    routing_model_selector --> routing_intent_classifier
    routing_semantic_router --> routing_intent_classifier
    routing_skill_router_integration --> skills_skill_initializer
    routing_test_semantic_router --> routing_semantic_router
    routing_tool_selector --> routing_intent_classifier
    routing___init__ --> routing_semantic_router
    runners_shadow_runner --> fusion_engine
    schedulers_chip_intelligence_updater --> ai_economics_chip_intelligence_engine
    schedulers_correlation_scheduler --> database_repository
    schedulers_failure_learning_scheduler --> database_repository
    scripts_add_new_feeds --> data_news_models
    scripts_backfill_embeddings --> core_database
    scripts_benchmark_price_storage --> core_database
    scripts_check_data_readiness --> database_repository
    scripts_check_macro_context --> database_repository
    scripts_check_model_deprecations --> ai_model_registry
    scripts_check_shadow_db --> database_connection
    scripts_create_agent_vote_tracking --> database_repository
    scripts_create_deep_reasoning_table --> database_models
    scripts_create_stock_tables --> core_database
    scripts_debug_settings --> config_settings
    scripts_fix_sqlite_tables --> data_news_models
    scripts_generate_daily_briefing --> ai_reporters_report_orchestrator
    scripts_import_kis_data --> database_models
    scripts_init_database --> database_models
    scripts_init_dividend_tables --> core_models_dividend_models
    scripts_init_kg --> data_knowledge_graph_knowledge_graph
    scripts_init_kg_PLAN --> data_knowledge_graph_knowledge_graph
    scripts_init_kg_via_repo --> data_knowledge_graph_knowledge_graph
    scripts_init_vector_db --> database_vector_db
    scripts_migrate_dividend_aristocrats --> database_models
    scripts_migrate_news_to_postgres --> core_database
    scripts_monitor_free_news --> data_collectors_free_news_monitor
    scripts_monitor_ft --> data_collectors_stealth_web_crawler
    scripts_reset_database --> database_models
    scripts_seed_strategies --> database
    scripts_seed_test_data --> database_models
    scripts_seed_test_signals --> database_models
    scripts_test_deep_reasoning_features --> ai_reasoning_deep_reasoning_agent
    scripts_test_phase25_4 --> database_repository
    scripts_test_price_verifier_flow --> database_repository
    scripts_test_semantic_search --> ai_rag_embedding_service
    scripts_test_structured_outputs --> ai_mvp_trader_agent_mvp
    scripts_test_tax_optimizer --> ai_portfolio_tax_optimizer
    scripts_test_watchtower --> ai_debate_news_agent
    scripts_verify_annual_report --> ai_reporters_annual_reporter
    scripts_verify_deep_reasoning --> ai_mvp_analyst_agent_mvp
    scripts_verify_news_integration_direct --> ai_mvp_war_room_mvp
    scripts_verify_news_interpretation --> database_repository
    scripts_verify_phase5_integrity --> database_repository
    scripts_verify_weekly_report --> ai_reporters_weekly_reporter
    services_analytics_aggregator --> core_models_analytics_models
    services_annual_report_generator --> database_repository
    services_asset_service --> database_repository
    services_broker_position_sync --> data_position_tracker
    services_complete_5page_report_generator --> services_page1_generator_korean
    services_complete_korean_report_generator --> services_page1_generator_korean
    services_complete_report_generator --> services_page1_generator
    services_daily_briefing_cache_manager --> database_models
    services_daily_briefing_service --> database_repository
    services_daily_price_sync --> core_database
    services_daily_report_scheduler --> reporting_report_generator
    services_economic_calendar_fetcher --> core_database
    services_economic_calendar_manager --> services_fred_economic_calendar
    services_economic_watcher --> services_economic_calendar_manager
    services_final_korean_report_generator --> services_page1_generator_korean
    services_fred_economic_calendar --> database_models
    services_news_event_handler --> schemas_base_schema
    services_news_poller --> data_rss_crawler
    services_optimized_signal_pipeline --> data_news_models
    services_ownership_service --> database_repository_multi_strategy
    services_page1_generator --> services_korean_font_setup
    services_page1_generator_korean --> services_korean_font_setup
    services_page2_generator_korean --> services_korean_font_setup
    services_page3_generator --> services_korean_font_setup
    services_page3_generator_korean --> services_korean_font_setup
    services_page5_generator_korean --> services_korean_font_setup
    services_signal_pipeline --> data_news_models
    services_stock_price_scheduler --> data_stock_price_storage
    services_stop_loss_monitor --> data_position_tracker
    services_weekly_report_generator --> database_repository
    services___init__ --> services_auto_trade_service
    skills_skill_initializer --> skills_base_skill
    skills___init__ --> skills_base_skill
    skills_intelligence_claude_skill --> skills_base_skill
    skills_intelligence_gemini_skill --> skills_base_skill
    skills_intelligence_gpt4o_skill --> skills_base_skill
    skills_intelligence___init__ --> skills_intelligence_gemini_skill
    skills_market_data_news_skill --> skills_base_skill
    skills_market_data___init__ --> skills_market_data_news_skill
    skills_technical_backtest_skill --> skills_base_skill
    skills_technical___init__ --> skills_technical_backtest_skill
    skills_trading_backtest_skill --> skills_base_skill
    skills_trading_kis_skill --> skills_base_skill
    skills_trading_order_skill --> skills_base_skill
    skills_trading_risk_skill --> skills_base_skill
    skills_trading___init__ --> skills_trading_kis_skill
    tests_conftest --> main
    tests_debug_glm_47_response --> ai_glm_client
    tests_debug_glm_response --> ai_glm_client
    tests_debug_response_text --> ai_glm_client
    tests_debug_risk_analyst --> ai_glm_client
    tests_test_13f_validation --> data_collectors_smart_money_collector
    tests_test_approval_system --> approval_approval_models
    tests_test_chip_war_agent --> ai_debate_chip_war_agent
    tests_test_cik_mapper --> data_sec_cik_mapper
    tests_test_collect_sec_with_tickers --> data_realtime_news_service
    tests_test_complete_report_telegram --> services_complete_report_generator
    tests_test_conflict_detector --> tests_mocks_strategy_mocks
    tests_test_data_backfill_router --> main
    tests_test_event_subscribers --> events
    tests_test_fle_calculator --> metrics_fle_calculator
    tests_test_glm_client --> ai_glm_client
    tests_test_glm_integration --> ai_glm_client
    tests_test_kill_switch_integration --> main
    tests_test_models --> ai_reasoning_models
    tests_test_orders_api_conflict --> database_repository
    tests_test_orders_api_conflict_unit --> main
    tests_test_order_conflict_integration --> database_repository
    tests_test_ownership_api_pagination --> main
    tests_test_ownership_transfer --> database_repository
    tests_test_portfolio_data --> api_main
    tests_test_priority_calculator --> ai_debate_priority_calculator
    tests_test_sec_analyzer_enhanced --> data_sec_parser
    tests_test_sec_with_ticker --> data_crawlers_sec_edgar_monitor
    tests_test_strategy_repository --> database_models
    tests_test_tax_loss_harvesting --> tax
    tests_test_telegram_alerts --> services_alert_manager
    tests_test_trading_tendency --> metrics_trading_tendency_analyzer
    tests_test_twostage_e2e_latency --> ai_mvp_trader_agent_mvp
    tests_test_war_room_e2e --> api_war_room_router
    tests_test_war_room_with_sec --> api_war_room_router
    tests_integration_test_end_to_end --> main
    tests_integration_test_event_bus_integration --> database_repository
    tests_integration_test_paper_trading_e2e --> trading_war_room_executor
    tests_integration_test_strategy_repository_integration --> database_repository
    trading_overseas_stock --> trading
```

## Note
This map is auto-generated by `backend/utils/structure_mapper.py`.
Run the script to update this file before development.
