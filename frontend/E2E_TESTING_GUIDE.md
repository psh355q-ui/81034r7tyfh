# Playwright E2E Testing Guide

## 📋 Overview

Automated E2E tests for all frontend pages before live trading launch.

**Tests Created**:
1. `dashboard.spec.ts` - Comprehensive Dashboard testing
2. `all-pages.spec.ts` - Smoke tests for all pages
3. `api-health.spec.ts` - Backend API validation

---

## 🚀 Quick Start

### 1. Install Dependencies (Already Done)
```bash
npm install -D @playwright/test
npx playwright install chromium
```

### 2. Run All Tests
```bash
# Run all tests
npx playwright test

# Run with UI (recommended for debugging)
npx playwright test --ui

# Run specific test file
npx playwright test dashboard.spec.ts
```

### 3. View Report
```bash
npx playwright show-report
```

---

## 📊 Test Coverage

### Dashboard Tests (`dashboard.spec.ts`)
- ✅ Page loads without errors
- ✅ Summary cards display (Total Value, Daily P&L, Cash, Positions)
- ✅ Market Indicators display (S&P500, NASDAQ, VIX, US10Y, DXY)
- ✅ Currency Rates display (KRW, JPY, EUR, CNY)
- ✅ Daily Briefing loads
- ✅ Current Positions table renders
- ✅ API error handling
- ✅ Full-page screenshot

### All Pages Smoke Test (`all-pages.spec.ts`)
- ✅ Dashboard (`/dashboard`)
- ✅ Dividend Dashboard (`/dividend`)
- ✅ Trading Signals (`/signals`)
- ✅ Portfolio Analysis (`/portfolio`)

For each page:
- Console error detection
- API failure tracking
- Screenshot capture
- Basic content validation

### API Health Check (`api-health.spec.ts`)
- ✅ `/health` endpoint
- ✅ `/api/portfolio` endpoint
- ✅ `/api/market/indicators` endpoint
- ✅ `/api/briefing/latest` endpoint
- ✅ `/api/signals/latest` endpoint

---

## 🔍 Running Tests

### Basic Commands

```bash
# Run all tests (headless)
npx playwright test

# Run with browser visible
npx playwright test --headed

# Run specific test
npx playwright test dashboard.spec.ts

# Run in debug mode
npx playwright test --debug

# Run with UI mode (best for development)
npx playwright test --ui
```

### Advanced Options

```bash
# Run only Dashboard tests
npx playwright test dashboard

# Run tests matching pattern
npx playwright test api

# Run with specific browser
npx playwright test --project=chromium

# Generate trace for debugging
npx playwright test --trace on
```

---

## 📸 Screenshots & Reports

### Screenshots
Automatically captured on test failure:
- Location: `playwright-report/screenshots/`
- Full-page screenshots for all pages

### HTML Report
```bash
# View report after test run
npx playwright show-report
```

Report includes:
- Test results summary
- Failed test details
- Screenshots
- Network logs
- Console errors

---

## 🐛 Debugging Failed Tests

### Method 1: UI Mode (Recommended)
```bash
npx playwright test --ui
```
- Time-travel debugging
- Watch mode
- Network inspector
- Console viewer

### Method 2: Debug Mode
```bash
npx playwright test --debug dashboard.spec.ts
```
- Playwright Inspector
- Step-by-step execution
- Selector playground

### Method 3: Headed Mode
```bash
npx playwright test --headed --slow-mo=1000
```
- See browser in action
- Slow down execution

---

## 📝 Adding New Tests

### Template for Page Test

```typescript
import { test, expect } from '@playwright/test';

test.describe('New Page', () => {
  test('should load without errors', async ({ page }) => {
    await page.goto('/new-page');
    await expect(page.locator('text=Expected Text')).toBeVisible();
  });
});
```

### Best Practices
1. **Use `data-testid`** for stable selectors
2. **Wait for network idle** before assertions
3. **Collect console errors** to catch JS issues
4. **Take screenshots** on failure
5. **Mock API calls** for edge cases

---

## ✅ Pre-Flight Testing Workflow

### Before Live Trading

1. **Run Full Test Suite**
   ```bash
   npx playwright test
   ```

2. **Review Report**
   ```bash
   npx playwright show-report
   ```

3. **Check Screenshots**
   - Review all page screenshots in `playwright-report/screenshots/`

4. **Fix Critical Issues**
   - Any test failures must be fixed before launch

5. **Re-run Tests**
   - Ensure all tests pass

---

## 🔧 Configuration

**File**: `playwright.config.ts`

Key settings:
- **baseURL**: `http://localhost:3002`
- **timeout**: 30 seconds per test
- **retries**: 2 on CI, 0 locally
- **screenshot**: On failure
- **video**: Retain on failure
- **browsers**: Chromium, Firefox, WebKit, Mobile

---

## 📊 CI/CD Integration (Future)

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 🎯 Next Steps

1. ✅ Install Playwright - **Done**
2. ✅ Create test files - **Done**
3. ⏳ **Run tests** - `npx playwright test --ui`
4. ⏳ Fix any detected issues
5. ⏳ Add to Pre-flight Checklist

---

**Last Updated**: 2026-01-25  
**Version**: 1.0
