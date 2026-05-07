// client/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Auth Flow', () => {
  test('should persist login state', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // State should persist after reload
    await page.reload();
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
