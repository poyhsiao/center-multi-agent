import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await page.waitForURL(/\/dashboard/);
  });

  test('should display task list', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="task-list"]')).toBeVisible();
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