import { test, expect } from '@playwright/test';

test.describe('Routing', () => {
  test('should redirect root to login when unauthenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should allow access to dashboard when authenticated', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    await expect(page.locator('h1')).toContainText('Agent Dashboard');
  });

  test('should block direct dashboard access when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });
});
