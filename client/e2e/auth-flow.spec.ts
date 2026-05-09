import { test, expect } from '@playwright/test';

test.describe('Auth Flow', () => {
  test('should show login page when unauthenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Sign In');
  });

  test('should redirect to dashboard after login', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  });

  test('should redirect to login after logout', async ({ page }) => {
    // First login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });

    // Click Settings tab to reveal logout button
    await page.click('button:has-text("Settings")');
    await page.waitForSelector('[data-testid="logout-btn"]', { timeout: 5000 });

    // Then logout
    await page.click('[data-testid="logout-btn"]');
    await expect(page).toHaveURL(/\/login/);
  });
});