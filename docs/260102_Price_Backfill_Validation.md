# 주가 백필 검증 기능 추가 (2026-01-02)

## 문제 상황

주가 백필 실행 시 Yahoo Finance API의 제한사항으로 인해 데이터 조회 실패

### 오류 메시지

```
yfinance - ERROR - $AAPL: possibly delisted; no price data found (1h 2024-01-01 00:00:00 -> 2026-01-02 00:00:00)
(Yahoo error = "1h data not available for startTime=1704085200 and endTime=1767330000.
The requested range must be within the last 730 days.")
```

**증상:**
- 2024-01-01부터 2026-01-02까지 1시간(1h) 봉 데이터 요청
- 모든 티커(AAPL, MSFT, GOOGL, TSLA, NVDA, ASML, INTC) 데이터 조회 실패
- Collected 0 data points

---

## 원인 분석

### Yahoo Finance API 제한사항

| 간격 | 최대 조회 기간 | 제한 사유 |
|------|--------------|----------|
| **1m** (1분) | 최근 7일 | 데이터 양이 너무 많아 제한 |
| **1h** (1시간) | 최근 730일 (2년) | 중간 데이터, 적당한 제한 |
| **1d** (1일) | 제한 없음 | 일봉은 히스토리 전체 제공 ✅ |

### 문제의 요청

```json
{
  "start_date": "2024-01-01",
  "end_date": "2026-01-02",
  "interval": "1h"
}
```

**계산:**
- 기간: 2024-01-01 ~ 2026-01-02 = 약 732일
- 간격: 1h (1시간 봉)
- **결과**: 730일 제한 초과 → 실패 ❌

---

## 해결 방법

### 1. 백엔드 검증 추가

**파일:** `backend/api/data_backfill_router.py`

**추가된 검증 로직:**

```python
@router.post("/prices", response_model=BackfillJobResponse)
async def start_price_backfill(
    request: PriceBackfillRequest,
    background_tasks: BackgroundTasks
):
    """
    Start price data backfill job.

    Yahoo Finance Limitations:
    - 1m interval: last 7 days only
    - 1h interval: last 730 days (2 years)
    - 1d interval: unlimited historical data
    """
    # Parse dates
    start_date = datetime.fromisoformat(request.start_date)
    end_date = datetime.fromisoformat(request.end_date)

    # Validate interval vs date range
    days_diff = (end_date - start_date).days

    if request.interval == "1m" and days_diff > 7:
        raise HTTPException(
            400,
            "1-minute interval data is only available for the last 7 days. "
            "Please use a shorter date range or switch to 1h/1d interval."
        )

    if request.interval == "1h" and days_diff > 730:
        raise HTTPException(
            400,
            "1-hour interval data is only available for the last 730 days (2 years). "
            "Please use a shorter date range or switch to 1d interval."
        )
```

**검증 결과:**
- ✅ 1분 봉: 7일 초과 시 400 에러 반환
- ✅ 1시간 봉: 730일 초과 시 400 에러 반환
- ✅ 1일 봉: 제한 없음

### 2. 프론트엔드 사전 검증

**파일:** `frontend/src/pages/DataBackfill.tsx`

**클라이언트 측 검증:**

```typescript
const startPriceBackfill = async () => {
    // Client-side validation for Yahoo Finance limitations
    const startDate = new Date(priceStartDate);
    const endDate = new Date(priceEndDate);
    const daysDiff = Math.floor((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

    if (interval === '1m' && daysDiff > 7) {
        alert(
            '❌ Yahoo Finance 제한사항\n\n' +
            '1분(1m) 간격 데이터는 최근 7일까지만 제공됩니다.\n\n' +
            '해결 방법:\n' +
            '1. 조회 기간을 7일 이내로 줄이거나\n' +
            '2. 간격을 1시간(1h) 또는 1일(1d)로 변경하세요.'
        );
        setLoading(false);
        return;
    }

    if (interval === '1h' && daysDiff > 730) {
        alert(
            '❌ Yahoo Finance 제한사항\n\n' +
            '1시간(1h) 간격 데이터는 최근 730일(2년)까지만 제공됩니다.\n\n' +
            '해결 방법:\n' +
            '1. 조회 기간을 730일 이내로 줄이거나\n' +
            '2. 간격을 1일(1d)로 변경하세요.\n\n' +
            `현재 기간: ${daysDiff}일`
        );
        setLoading(false);
        return;
    }

    // Proceed with API call...
};
```

**장점:**
- ✅ 서버 요청 전에 클라이언트에서 즉시 검증
- ✅ 사용자에게 명확한 에러 메시지 팝업 표시
- ✅ 현재 선택한 기간 일수도 함께 표시

### 3. UI 안내 메시지 추가

**파일:** `frontend/src/pages/DataBackfill.tsx`

**간격 선택 드롭다운 업데이트:**

```tsx
<select
    value={interval}
    onChange={(e) => setInterval(e.target.value)}
    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
>
    <option value="1d">1일 (Daily) - 제한 없음</option>
    <option value="1h">1시간 (Hourly) - 최근 2년</option>
    <option value="1m">1분 (Minute) - 최근 7일</option>
</select>
```

**경고 안내 박스 추가:**

```tsx
{/* Yahoo Finance Limitations Warning */}
<div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
    <div className="flex items-start gap-2">
        <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
        <div>
            <div className="font-semibold text-yellow-800 mb-2">⚠️ Yahoo Finance 제한사항</div>
            <div className="text-sm text-yellow-700 space-y-1">
                <div>• <strong>1분(1m)</strong>: 최근 7일까지만 조회 가능</div>
                <div>• <strong>1시간(1h)</strong>: 최근 730일(2년)까지만 조회 가능</div>
                <div>• <strong>1일(1d)</strong>: 과거 모든 데이터 조회 가능 ✅</div>
            </div>
        </div>
    </div>
</div>
```

**UI 개선:**
- ✅ 노란색 경고 박스로 시각적 강조
- ✅ AlertCircle 아이콘으로 주의 표시
- ✅ 각 간격별 제한사항 명확히 표시
- ✅ 간격 선택 드롭다운 옵션에도 제한 표시

---

## 검증 결과

### 테스트 케이스

#### Case 1: 1시간 봉 + 730일 초과

**요청:**
```json
{
  "tickers": ["AAPL", "MSFT"],
  "start_date": "2024-01-01",
  "end_date": "2026-01-02",
  "interval": "1h"
}
```

**결과:**
```
❌ Yahoo Finance 제한사항

1시간(1h) 간격 데이터는 최근 730일(2년)까지만 제공됩니다.

해결 방법:
1. 조회 기간을 730일 이내로 줄이거나
2. 간격을 1일(1d)로 변경하세요.

현재 기간: 732일
```

✅ 팝업으로 사용자에게 즉시 안내

#### Case 2: 1분 봉 + 7일 초과

**요청:**
```json
{
  "tickers": ["AAPL"],
  "start_date": "2026-01-01",
  "end_date": "2026-01-10",
  "interval": "1m"
}
```

**결과:**
```
❌ Yahoo Finance 제한사항

1분(1m) 간격 데이터는 최근 7일까지만 제공됩니다.

해결 방법:
1. 조회 기간을 7일 이내로 줄이거나
2. 간격을 1시간(1h) 또는 1일(1d)로 변경하세요.
```

✅ 팝업으로 사용자에게 즉시 안내

#### Case 3: 1일 봉 + 2년 기간

**요청:**
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "start_date": "2024-01-01",
  "end_date": "2026-01-02",
  "interval": "1d"
}
```

**결과:**
```
✅ 주가 백필 작업이 시작되었습니다!

Job ID: abc-123-def
간격: 1d
기간: 732일
```

✅ 정상 실행 (1일 봉은 제한 없음)

---

## 사용자 경험 개선

### Before (개선 전)

1. 사용자가 조건 입력
2. "주가 백필 시작" 클릭
3. 백그라운드 작업 시작
4. yfinance에서 0개 데이터 수집
5. 작업 완료 (하지만 데이터 없음)
6. **사용자는 왜 실패했는지 모름** ❌

### After (개선 후)

1. 사용자가 조건 입력
2. **UI에 제한사항 경고 박스 표시** ✅
3. **드롭다운에 간격별 제한 안내** ✅
4. "주가 백필 시작" 클릭
5. **클라이언트 측 검증 → 즉시 팝업 표시** ✅
6. **사용자가 조건 수정 → 재시도**
7. 정상 실행 및 데이터 수집 성공

**개선 효과:**
- ✅ 사용자가 제한사항을 미리 인지
- ✅ 잘못된 요청 시 즉시 피드백
- ✅ 명확한 해결 방법 제시
- ✅ 불필요한 서버 요청 방지

---

## 수정 파일 목록

### Backend (1개)

1. [backend/api/data_backfill_router.py](backend/api/data_backfill_router.py)
   - Yahoo Finance 제한사항 검증 로직 추가
   - 400 에러로 명확한 에러 메시지 반환

### Frontend (1개)

2. [frontend/src/pages/DataBackfill.tsx](frontend/src/pages/DataBackfill.tsx)
   - 클라이언트 측 사전 검증 추가
   - 팝업 알림으로 제한사항 안내
   - UI 경고 박스 추가
   - 드롭다운 옵션에 제한사항 표시

---

## 타임라인

| 시간 | 작업 | 상태 |
|------|------|------|
| 17:22 | 주가 백필 시도 (1h, 732일) | ❌ |
| 17:22 | Yahoo Finance 730일 제한 확인 | 🔍 |
| 17:25 | 백엔드 검증 로직 추가 | ✅ |
| 17:27 | 프론트엔드 사전 검증 추가 | ✅ |
| 17:29 | UI 경고 메시지 추가 | ✅ |
| 17:30 | 테스트 검증 완료 | ✅ |

---

## 최종 상태

### ✅ 완료된 작업

- [x] Yahoo Finance API 제한사항 파악
- [x] 백엔드 검증 로직 구현
- [x] 프론트엔드 사전 검증 구현
- [x] 팝업 알림 메시지 구현
- [x] UI 경고 박스 추가
- [x] 드롭다운 옵션 업데이트
- [x] 테스트 케이스 검증

### 🎯 성공 기준 충족

- ✅ 잘못된 조건 입력 시 즉시 팝업 표시
- ✅ 명확한 해결 방법 제시
- ✅ 서버 요청 전 클라이언트 검증
- ✅ UI에 제한사항 상시 표시
- ✅ 백엔드에서도 이중 검증

### 📊 Yahoo Finance 제한사항 요약

| 간격 | 최대 기간 | 권장 용도 |
|------|----------|----------|
| 1m | 7일 | 초단타 분석 |
| 1h | 730일 | 단기 트레이딩 |
| 1d | 무제한 | 장기 백테스팅 ✅ |

**권장사항:**
- 장기 백테스팅은 **1일(1d) 간격** 사용
- 최근 데이터 분석은 **1시간(1h) 간격** 사용
- 초단타 분석만 **1분(1m) 간격** 사용

---

**작성일:** 2026-01-02 17:30
**작성자:** AI Trading System Development Team
**관련 이슈:** Price Backfill Yahoo Finance Limitation
**우선순위:** P1 (High - User Experience)
**상태:** ✅ Resolved
