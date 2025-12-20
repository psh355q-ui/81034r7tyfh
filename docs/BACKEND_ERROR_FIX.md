# Backend Error Fix Summary

**문제**: `get_agent_weight_trainer` 함수 이름 불일치

## 수정 내역

### 1. Import 수정 (Line 42)
```python
# Before
from backend.ai.meta.agent_weight_trainer import get_agent_weight_trainer

# After  
from backend.ai.meta.agent_weight_trainer import get_weight_trainer
```

### 2. 함수 호출 수정 (Line 140)
```python
# Before
self.weight_trainer = get_agent_weight_trainer(
    debate_logger=self.debate_logger,
    storage_path=Path("data/agent_weights")
)

# After
self.weight_trainer = get_weight_trainer(
    storage_path=Path("data/agent_weights")
)
```

## 이유

`agent_weight_trainer.py`의 실제 함수명:
```python
def get_weight_trainer(storage_path: Optional[Path] = None) -> AgentWeightTrainer:
    """AgentWeightTrainer 싱글톤 인스턴스"""
```

- 함수명: `get_weight_trainer` (not `get_agent_weight_trainer`)
- 파라미터: `storage_path`만 필요 (`debate_logger` 없음)

## 테스트

```bash
python run_live.py
```

백엔드가 정상적으로 시작되어야 함.

---

**수정 완료**: 2025-12-16 00:48 KST
