---
description: 파일에 표준 주석 추가
---

# Add Documentation to Python Files

이 워크플로우는 Python 파일에 데이터 소스와 의존성을 명시하는 표준 주석을 추가합니다.

## 단계

1. **파일 분석**
   - 파일의 import 문 확인
   - 함수와 클래스 목록 추출
   - API 호출 위치 파악

2. **데이터 소스 식별**
   - KIS API 호출 (`kis_broker`, `overseas_stock`)
   - Yahoo Finance 호출 (`yfinance`)
   - 데이터베이스 쿼리 (SQLAlchemy models)
   - 외부 HTTP 요청 (`requests`, `httpx`)

3. **헤더 주석 생성**
   ```python
   """
   [파일명] - [설명]
   
   📊 Data Sources:
       - [식별된 데이터 소스들]
   
   🔗 External Dependencies:
       - [라이브러리: 용도]
   
   📤 API Endpoints:
       - [엔드포인트 경로]
   """
   ```

4. **함수 Docstring 추가**
   - 각 public 함수에 데이터 소스 명시
   - Args, Returns, Raises 포함

5. **인라인 주석 개선**
   - API 호출 전: 어떤 endpoint 호출하는지
   - 데이터 변환: 어디서 어디로
   - 복잡한 로직: 비즈니스 의도

## 템플릿

### API Router 파일
```python
"""
[router_name]_router.py - [기능 설명]

📊 Data Sources:
    - KIS API: [사용하는 endpoint들]
    - Database: [테이블명들]

🔗 External Dependencies:
    - fastapi: API 라우팅
    - pydantic: 데이터 검증

📤 API Endpoints:
    - GET /api/[path]: [설명]
    - POST /api/[path]: [설명]
"""
```

### Data Source 파일
```python
"""
[source_name].py - [데이터 소스 설명]

📊 Provides:
    - [제공하는 데이터 종류]

🔗 External APIs:
    - [외부 API 이름]: [Base URL]

🔄 Used By:
    - [이 파일을 사용하는 곳들]
"""
```

## 실행 예시

```bash
# 단일 파일 업데이트
python scripts/add_docstrings.py backend/api/portfolio_router.py

# 전체 디렉토리 업데이트
python scripts/add_docstrings.py backend/api/

# 검증만 수행 (변경 없음)
python scripts/add_docstrings.py --check backend/
```

## 체크 포인트

- [ ] Data Sources 섹션이 있는가?
- [ ] 모든 외부 API 호출에 주석이 있는가?
- [ ] Public 함수에 docstring이 있는가?
- [ ] 복잡한 비즈니스 로직에 설명이 있는가?
