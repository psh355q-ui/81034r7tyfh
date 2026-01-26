# API Usage Analysis Report

**Date**: 2026-01-25
**Period**: Current codebase analysis
**Phase**: Week 1-2 - War Room Legacy Investigation

---

## Executive Summary

### Key Findings

1. **War Room Legacy API is STILL ACTIVE in Frontend**
   - Legacy API file exists: `src/services/warRoomApi.legacy.ts`
   - Legacy API endpoints: `/api/war-room/debate`, `/api/war-room/sessions`, `/api/war-room/health`

2. **War Room MVP API is ALSO ACTIVE in Frontend**
   - MVP API file exists: `src/services/warRoomApi.ts`
   - MVP API endpoints: `/api/war-room-mvp/deliberate`, `/api/war-room-mvp/history`, `/api/war-room-mvp/health`

3. **War Room Legacy Router is REGISTERED in Backend**
   - File exists: `backend/api/war_room_router.py`
   - Registered in: `backend/main.py`
   - Status: Active (imported and included in app)

4. **Phase Integration Router**
   - Search returned binary file (unable to analyze)
   - Needs further investigation

---

## Detailed Analysis

### 1. Frontend Analysis

#### War Room Legacy API Usage

**File**: `src/services/warRoomApi.legacy.ts`

**Endpoints**:
- `POST /api/war-room/debate` - Start debate
- `GET /api/war-room/sessions` - Get sessions
- `GET /api/war-room/health` - Health check

**UI Components**:
- `src/components/war-room/WarRoom.tsx` - Legacy War Room component
- `src/components/war-room/WarRoom.css` - Legacy styles
- `src/components/war-room/WarRoomCard.tsx` - Legacy card component
- `src/components/war-room/WarRoomList.tsx` - Legacy list component

**Navigation**:
- `src/App.tsx`: Route `/war-room` → `<WarRoomPage />`
- `src/components/Layout/Navigation.tsx`: Link to `/war-room`
- `src/components/Layout/Sidebar.tsx`: War Room menu item

#### War Room MVP API Usage

**File**: `src/services/warRoomApi.ts`

**Endpoints**:
- `POST /api/war-room-mvp/deliberate` - Start deliberation
- `GET /api/war-room-mvp/history` - Get history
- `GET /api/war-room-mvp/health` - Health check
- `GET /api/war-room-mvp/info` - Get info

**UI Components**:
- `src/pages/WarRoomPage.tsx` - MVP War Room page
- Uses MVP API endpoints

**Observation**: Frontend has BOTH Legacy and MVP APIs active simultaneously.

### 2. Backend Analysis

#### War Room Legacy Router

**File**: `backend/api/war_room_router.py`

**Status**: 
- ✅ File exists
- ✅ Imported in `backend/main.py`
- ✅ Registered with `app.include_router(war_room_router)`

**Issues Found**:
- Multiple database schema errors in logs:
  - `debate_id` column missing from `ai_debate_sessions` table
  - `votes` column missing from `ai_debate_sessions` table
  - `duration_seconds` column missing from `ai_debate_sessions` table
  - `constitutional_valid` attribute missing from `AIDebateSession` model
  - `consensus_action` vs `consensus_action` naming inconsistency

**Error Logs**:
- `backend/ai/skills/logs/war-room/war-room-debate/errors-2025-12-25.jsonl`
- `backend/ai/skills/logs/war-room/war-room-debate/errors-2025-12-26.jsonl`
- `backend/ai/skills/logs/war-room/war-room-debate/errors-2025-12-27.jsonl`

**Error Count**: 20+ critical errors in recent logs

#### Phase Integration Router

**File**: `backend/api/phase_integration_router.py` (presumed)

**Status**: 
- ⚠️ Search returned binary file
- ⚠️ Unable to analyze content
- ⚠️ Needs manual verification

---

## API Usage Summary

| API Type | Status | Frontend Usage | Backend Registration | Active Calls |
|-----------|--------|----------------|---------------------|---------------|
| War Room Legacy | ✅ ACTIVE | `warRoomApi.legacy.ts` | `war_room_router.py` | **YES** |
| War Room MVP | ✅ ACTIVE | `warRoomApi.ts` | `war_room_mvp_router.py` | **YES** |
| Phase Integration | ❓ UNKNOWN | Not found | Binary file | ❓ UNKNOWN |

---

## Critical Issues

### 1. Database Schema Mismatch
- Legacy router expects columns that don't exist in `ai_debate_sessions` table
- This causes all legacy API calls to fail
- **Impact**: Legacy API is BROKEN, but still registered

### 2. Duplicate API Systems
- Frontend has both Legacy and MVP APIs
- Users may be calling broken Legacy API
- No clear migration path for users

### 3. No Deprecation Warnings
- Legacy API has NO deprecation warnings
- Users don't know they should migrate to MVP

---

## Recommendations

### Immediate Actions (Week 1-2)

1. **Add Deprecation Warnings**
   - Add logging to `backend/api/war_room_router.py`
   - Log all legacy API calls with deprecation notice
   - Monitor for 2 weeks

2. **Create Migration Guide**
   - Document Legacy → MVP migration
   - Update frontend to use MVP API only
   - Provide clear timeline

3. **Phase Integration Router Investigation**
   - Manually verify `phase_integration_router.py` status
   - Check if it's registered in `main.py`
   - Determine if it's still active

### Next Steps (Week 3-4)

1. **Remove Legacy Router**
   - If legacy calls = 0 for 7 days
   - Remove `war_room_router.py`
   - Remove `war_room_router` from `main.py`

2. **Remove Legacy Frontend Components**
   - Remove `src/services/warRoomApi.legacy.ts`
   - Remove legacy War Room components
   - Update navigation to use MVP only

3. **Archive Legacy Code**
   - Move `backend/ai/debate/` to archive
   - Create migration documentation
   - Tag release with archive info

---

## Monitoring Plan

### Metrics to Track

1. **Legacy API Call Count**
   - Track `/api/war-room/*` calls
   - Monitor daily/weekly trends
   - Target: 0 calls for 7 consecutive days

2. **MVP API Call Count**
   - Track `/api/war-room-mvp/*` calls
   - Verify increasing usage
   - Target: All users migrated

3. **Error Rate**
   - Monitor legacy API errors
   - Expected: 100% (due to schema mismatch)
   - Confirm: No new errors after migration

### Monitoring Duration

- **Start**: After deprecation warnings added
- **Duration**: 2 weeks (2026-01-27 ~ 2026-02-09)
- **Review**: Weekly progress reports

---

## Conclusion

### Current State
- ❌ War Room Legacy API is BROKEN (database schema mismatch)
- ✅ War Room MVP API is WORKING
- ⚠️ Frontend still has Legacy API reference
- ⚠️ No deprecation warnings in place

### Risk Assessment
- **HIGH RISK**: Users may be calling broken Legacy API
- **MEDIUM RISK**: Confusion between Legacy and MVP APIs
- **LOW RISK**: Phase Integration router status unknown

### Recommended Action
**PROCEED WITH DEPRECATION IMMEDIATELY**

1. Add deprecation warnings to Legacy API (Day 3-4)
2. Create Migration Guide (Day 5)
3. Monitor usage for 2 weeks (Week 2)
4. Remove Legacy API if usage = 0 (Week 3-4)

---

**Report Generated**: 2026-01-25
**Next Review**: 2026-02-01 (after 1 week of monitoring)
