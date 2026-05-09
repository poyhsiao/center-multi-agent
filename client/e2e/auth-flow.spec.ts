import { test, expect, chromium } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const authFile = join(__dirname, '../playwright/.auth/user.json');

// Test without auth state - create isolated context
test('should show login page when unauthenticated', async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext(); // No storageState
  const page = await context.newPage();

  await page.goto('/');
  await expect(page.locator('h1')).toContainText('Sign In');

  await browser.close();
});

// Test with auth state
test.describe('Authenticated', () => {
  test.use({ storageState: authFile });

  test('should access dashboard when authenticated', async ({ page }) => {
    await page.goto('/dashboard');
    // Should see dashboard content - check for dashboard heading
    await expect(page.getByRole('heading', { name: 'Agent Dashboard' })).toBeVisible({ timeout: 10000 });
  });

  test('should show login page after logout', async ({ page }) => {
    // Go to dashboard
    await page.goto('/dashboard');

    // Click Settings to find logout button
    await page.click('button:has-text("Settings")');
    await page.waitForSelector('[data-testid="logout-btn"]', { timeout: 5000 });

    // Logout
    await page.click('[data-testid="logout-btn"]');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });
});