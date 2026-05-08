import { test, expect } from '@playwright/test';

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await page.waitForURL(/\/dashboard/);
  });

  test('should display settings page', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('text=Settings');
    await expect(page.locator('[data-testid="settings-panel"]')).toBeVisible();
  });

  test('should show sync status', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('text=Settings');
    await expect(page.locator('[data-testid="sync-status"]')).toBeVisible();
  });

  test('should allow logout', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('text=Settings');
    await page.click('[data-testid="logout-btn"]');
    await expect(page).toHaveURL(/\/login/);
  });
});