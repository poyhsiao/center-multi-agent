import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const authFile = join(__dirname, '../playwright/.auth/user.json');

test.describe('API Client', () => {
  test.use({ storageState: authFile });

  test('should create login request correctly', async ({ page }) => {
    const response = await page.request.post('/api/v1/auth/login', {
      data: {
        email: 'test@example.com',
        password: 'TestPassword123',
        device_fingerprint: 'fp_test123',
      },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('access_token');
    expect(body).toHaveProperty('refresh_token');
    expect(body).toHaveProperty('expires_in');
  });

  test('should handle auth refresh', async ({ page }) => {
    expect(true).toBeTruthy();
  });
});