import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const authFile = join(__dirname, '../playwright/.auth/user.json');

test.describe('Dashboard', () => {
  test.use({ storageState: authFile });

  test('should display task list', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="task-list"]')).toBeVisible({ timeout: 10000 });
  });

  test('should display navigation to Knowledge and Settings', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=Knowledge')).toBeVisible();
    await expect(page.locator('text=Settings')).toBeVisible();
  });

  test('should have new task button', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="new-task-btn"]')).toBeVisible();
  });
});