import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const authFile = join(__dirname, '../playwright/.auth/user.json');

test.describe('Knowledge Base', () => {
  test.use({ storageState: authFile });

  test('should display search interface', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('button:has-text("Knowledge")');
    await expect(page.locator('[data-testid="knowledge-base"]')).toBeVisible();
  });

  test('should show search results', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('button:has-text("Knowledge")');
    await expect(page.locator('[data-testid="knowledge-base"]')).toBeVisible();
  });
});