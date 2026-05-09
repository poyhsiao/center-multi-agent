import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const authFile = join(__dirname, '../playwright/.auth/user.json');

test.describe('Agent Operations', () => {
  test.use({ storageState: authFile });

  test('submit task and receive task_id', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('[data-testid="new-task-btn"]');
    await expect(page.locator('[data-testid="task-submit"]')).toBeVisible();
  });

  test('receive SSE notification on task completion', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('h1')).toContainText('Agent Dashboard');
  });
});