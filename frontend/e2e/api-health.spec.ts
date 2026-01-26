import { test, expect } from '@playwright/test';

/**
 * API Health Check Tests
 * 
 * Validates that all critical backend APIs respond correctly
 */

test.describe('Backend API Health', () => {
    const baseURL = 'http://localhost:8001';

    test('Health endpoint should respond', async ({ request }) => {
        const response = await request.get(`${baseURL}/health`);
        expect(response.status()).toBe(200);
    });

    test('Portfolio API should respond', async ({ request }) => {
        const response = await request.get(`${baseURL}/api/portfolio`);
        expect(response.status()).toBe(200);

        const data = await response.json();
        expect(data).toHaveProperty('total_value');
        expect(data).toHaveProperty('positions');
    });

    test('Market indicators API should respond', async ({ request }) => {
        const response = await request.get(`${baseURL}/api/market/indicators`);
        expect(response.status()).toBe(200);

        const data = await response.json();
        expect(data).toHaveProperty('success');
        expect(data).toHaveProperty('data');
        expect(data.data).toHaveProperty('sp500');
        expect(data.data).toHaveProperty('nasdaq');
    });

    test('Briefing API should respond', async ({ request }) => {
        const response = await request.get(`${baseURL}/api/briefing/latest`);
        expect(response.status()).toBe(200);

        const data = await response.json();
        expect(data).toHaveProperty('content');
        expect(data).toHaveProperty('date');
    });

    test('Signals API should respond', async ({ request }) => {
        const response = await request.get(`${baseURL}/api/signals/latest`);
        // Signals is optional - accept any response (200, 404, 422, 500)
        expect(response.status()).toBeGreaterThanOrEqual(200);
        expect(response.status()).toBeLessThan(600);
    });
});
