# Backend Error Fix #2

**에러**: `AttributeError: 'AgentWeightTrainer' object has no attribute 'get_current_weights'`

## 문제
`ai_debate_engine.py`가 존재하지 않는 메서드 `get_current_weights()`를 호출

## 해결

`agent_weight_trainer.py`의 실제 메서드:
- ✅ `get_all_weights()` - 모든 에이전트 가중치 반환
- ✅ `get_weight(agent_name)` - 특정 에이전트 가중치
- ❌ `get_current_weights()` - 존재하지 않음

### 수정: Line 577
```python
# Before
current_weights = self.weight_trainer.get_current_weights()

# After
current_weights = self.weight_trainer.get_all_weights()
```

## 파일
`backend/ai/debate/ai_debate_engine.py`

## 다음
백엔드 재시작 후 정상 작동 예상

---

**수정 완료**: 2025-12-16 00:56 KST
