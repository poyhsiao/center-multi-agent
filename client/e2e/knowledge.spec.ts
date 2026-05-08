import { test, expect } from '@playwright/test';

test.describe('Knowledge Base', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await page.waitForURL(/\/dashboard/);
  });

  test('should display search interface', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('text=Knowledge');
    await expect(page.locator('[data-testid="knowledge-search"]')).toBeVisible();
  });

  test('should show search results', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('text=Knowledge');
    await page.fill('[data-testid="knowledge-search"]', 'test query');
    await page.click('button[type="submit"]');
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
  });
});
