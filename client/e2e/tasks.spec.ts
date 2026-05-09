import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const authFile = join(__dirname, '../playwright/.auth/user.json');

test.describe('Tasks', () => {
  test.use({ storageState: authFile });

  test('displays task list', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="task-list"]')).toBeVisible({ timeout: 10000 });
  });

  test('opens task submit modal', async ({ page }) => {
    await page.goto('/dashboard');
    const newTaskBtn = page.locator('[data-testid="new-task-btn"]');
    await newTaskBtn.click();
    await expect(page.locator('[data-testid="task-submit"]')).toBeVisible();
  });

  test('closes task submit modal on cancel', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('[data-testid="new-task-btn"]');
    await expect(page.locator('[data-testid="task-submit"]')).toBeVisible();
    await page.click('button:has-text("Close")');
    await expect(page.locator('[data-testid="task-submit"]')).not.toBeVisible();
  });
});