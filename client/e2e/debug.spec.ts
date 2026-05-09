import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const authFile = join(__dirname, '../playwright/.auth/user.json');

test('login flow', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'TestPassword123');
  await page.click('[type="submit"]');

  await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  await page.waitForTimeout(500);

  await expect(page.locator('h1')).toContainText('Agent Dashboard');
});