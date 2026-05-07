// client/e2e/agent.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Agent Operations', () => {
  test('submit task and receive task_id', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('[data-testid="new-task"]');
    await page.fill('[name="task-input"]', 'test task');
    await page.click('[type="submit"]');
    await expect(page.locator('.task-id')).toBeVisible();
  });

  test('receive SSE notification on task completion', async ({ page }) => {
    // Test SSE event handling
    // Placeholder - would need real SSE endpoint
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="notification-area"]')).toBeVisible();
  });
});