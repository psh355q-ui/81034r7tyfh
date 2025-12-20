# ChatGPT 고급 기능 통합 - Quick Reference

**날짜**: 2025-12-16

---

## 완료된 5개 기능

### 1. AI War 우선순위
**사용**:
```python
result = engine.debate(context)
print(result.priority_score)  # 0.85
```

### 2. 승인 워크플로우
**사용**:
```python
manager = ApprovalManager()
request = manager.create_request(
    ticker="NVDA",
    action="BUY",
    priority_score=0.85
)
# → HARD_APPROVAL 필요
```

### 3. FLE 지표
**API**:
```bash
POST /api/portfolio/fle
{
  "user_id": "user123",
  "positions": [...],
  "cash": 10000
}
```

### 4. 13F 검증
**사용**:
```python
result = collector.validate_thesis(
    ticker="OXY",
    filing_date="2024-09-30",
    filing_price=58.2,
    action="INCREASE"
)
# → "THESIS_WORKING"
```

### 5. 공감적 피드백
**사용**:
```python
feedback = logger.generate_compassionate_feedback(
    record_id="abc123",
    days_after=7
)
```

---

## API 엔드포인트

```
/api/approvals/pending
/api/approvals/{id}/approve
/api/portfolio/fle
```

---

## 다음: Frontend UI

1. 승인 대기열 페이지
2. FLE 위젯
3. 안전 모달
