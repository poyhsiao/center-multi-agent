// client/e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('success login with correct password', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('fail login with wrong password', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'WrongPassword');
    await page.click('[type="submit"]');
    await expect(page.locator('.error')).toContainText('Invalid credentials');
  });

  test('token refresh on expiry', async ({ page }) => {
    // Simulate token expiry and verify refresh
    // This is a placeholder - real implementation would mock time
    await page.goto('/dashboard');
    // Verify dashboard loads after token refresh
    await expect(page.locator('h1')).toBeVisible();
  });
});