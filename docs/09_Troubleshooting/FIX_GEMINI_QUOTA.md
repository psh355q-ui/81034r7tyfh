# Gemini API Quota 해결 가이드

## 문제
```
429 You exceeded your current quota for Gemini API
```

모든 분석이 실패한 이유: **Gemini API 무료 할당량 초과**

## 현재 상황
- ✅ GOOGLE_API_KEY 로드 성공
- ❌ `gemini-1.5-flash`: 404 Not Found (v1beta에서 지원 안함)
- ❌ `gemini-2.0-flash-exp`: **429 Quota Exceeded**
- ✅ 코드 수정 완료 (content_summary 사용)

## 해결 방법

### 옵션 1: 새 API Key 생성 (권장)
1. **Google AI Studio 접속**
   https://aistudio.google.com/app/apikey

2. **새 API Key 생성**
   - "Create API Key" 클릭
   - 새 프로젝트 선택 또는 생성
   - API Key 복사

3. **.env 파일 업데이트**
   ```env
   GOOGLE_API_KEY=새로_생성한_키
   ```

4. **백엔드 재시작**

### 옵션 2: 할당량 확인
https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

- 일일 무료 한도: 1,500 requests/day
- 사용량 확인 및 리셋 대기 (UTC 기준 자정)

### 옵션 3: 다른 무료 LLM 사용
- OpenAI GPT-4o-mini (유료지만 저렴)
- Anthropic Claude (무료 티어)
- Groq (빠르고 무료)

## 테스트
새 API Key 설정 후:
```bash
python test_gemini_models.py
python test_analyzer_direct.py
```

## 다음 단계
1. 새 API Key 생성
2. .env 업데이트
3. 백엔드 재시작
4. "AI 분석 (10개)" 재시도
5. `python check_db.py` - "Analyzed articles: 10" 확인
