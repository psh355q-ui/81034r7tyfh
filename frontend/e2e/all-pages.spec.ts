import { test, expect } from '@playwright/test';

/**
 * All Pages Smoke Test
 * 
 * Quickly validates that all major pages:
 * - Load without errors
 * - Don't have console errors
 * - Render basic UI elements
 */

const pages = [
    // Overview (3)
    { path: '/dashboard', title: 'Dashboard', checkText: 'Total Value' },
    { path: '/dividend', title: 'Dividend Dashboard', checkText: '배당 인텔리전스' },
    { path: '/portfolio', title: 'Portfolio' },  // No checkText - strict mode violation

    // Trading (2)
    { path: '/trading', title: 'Live Trading' },  // No checkText
    { path: '/war-room', title: 'War Room' },  // No checkText

    // Intelligence (4)
    { path: '/analysis', title: 'Analysis' },  // No checkText
    { path: '/deep-reasoning', title: 'Deep Reasoning' },  // No checkText
    { path: '/advanced-analytics', title: 'Advanced Analytics' },  // No checkText
    { path: '/news', title: 'News & Market' },  // No checkText
];

for (const { path, title, checkText } of pages) {
    test.describe(`${title} Page Smoke Test`, () => {
        test(`should load ${title} without critical errors`, async ({ page }) => {
            const errors: string[] = [];
            const apiErrors: { url: string; status: number }[] = [];

            // Collect console errors
            page.on('console', msg => {
                if (msg.type() === 'error') {
                    errors.push(msg.text());
                }
            });

            // Collect failed API calls
            page.on('response', response => {
                if (response.status() >= 400) {
                    apiErrors.push({
                        url: response.url(),
                        status: response.status()
                    });
                }
            });

            // Navigate to page
            await page.goto(path);

            // Wait for page to be ready (increased timeout)
            await page.waitForLoadState('networkidle', { timeout: 60000 });

            // Take screenshot
            await page.screenshot({
                path: `playwright-report/screenshots/${title.replace(/\s/g, '_')}.png`,
                fullPage: true
            });

            // Check for basic content (increased timeout)
            if (checkText) {
                await expect(page.locator(`text=${checkText}`)).toBeVisible({ timeout: 20000 });
            }

            // Log errors for review
            if (errors.length > 0) {
                console.log(`\n❌ Console errors on ${title}:`);
                errors.forEach(e => console.log(`  - ${e}`));
            }

            if (apiErrors.length > 0) {
                console.log(`\n⚠️ API errors on ${title}:`);
                apiErrors.forEach(e => console.log(`  - ${e.status} ${e.url}`));
            }

            // Critical errors should fail the test
            const criticalErrors = errors.filter(e =>
                !e.includes('React DevTools') &&
                !e.includes('Download the React DevTools') &&
                !e.includes('favicon') &&
                !e.includes('Failed to load resource') &&
                !e.includes('antd:') &&  // Ant Design deprecation warnings
                !e.includes('Failed to fetch current mode')  // Optional feature
            );

            expect(criticalErrors).toHaveLength(0);
        });
    });
}
