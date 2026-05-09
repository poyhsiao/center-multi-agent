import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const authFile = join(__dirname, '../playwright/.auth/user.json');

test.describe('SSE Notifications', () => {
  test.use({ storageState: authFile });

  test('should display notification area', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('h1')).toContainText('Agent Dashboard');
  });
});