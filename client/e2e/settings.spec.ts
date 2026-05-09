import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const authFile = join(__dirname, '../playwright/.auth/user.json');

test.describe('Settings', () => {
  test.use({ storageState: authFile });

  test('should display settings page', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('button:has-text("Settings")');
    await expect(page.locator('[data-testid="settings-panel"]')).toBeVisible({ timeout: 10000 });
  });

  test('should show sync status', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('button:has-text("Settings")');
    await expect(page.locator('[data-testid="sync-status"]')).toBeVisible({ timeout: 10000 });
  });

  test('should allow logout', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('button:has-text("Settings")');
    await page.waitForSelector('[data-testid="logout-btn"]', { timeout: 5000 });
    await page.click('[data-testid="logout-btn"]');
    await expect(page).toHaveURL(/\/login/);
  });
});