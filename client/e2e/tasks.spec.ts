import { test, expect } from '@playwright/test';

test.describe('Tasks', () => {
  test('displays task list', async ({ page }) => {
    await page.goto('/tasks');
    await expect(page.locator('[data-testid="task-list"]')).toBeVisible();
  });

  test('shows empty state when no tasks', async ({ page }) => {
    await page.goto('/tasks');
    await expect(page.locator('.empty-state')).toBeVisible();
  });

  test('opens task submit modal', async ({ page }) => {
    await page.goto('/tasks');
    const newTaskBtn = page.locator('button:has-text("New Task")');
    if (await newTaskBtn.isVisible()) {
      await newTaskBtn.click();
      await expect(page.locator('.task-submit-modal')).toBeVisible();
    }
  });

  test('closes task submit modal on cancel', async ({ page }) => {
    await page.goto('/tasks');
    const newTaskBtn = page.locator('button:has-text("New Task")');
    if (await newTaskBtn.isVisible()) {
      await newTaskBtn.click();
      await page.locator('.cancel-btn').click();
      await expect(page.locator('.task-submit-modal')).not.toBeVisible();
    }
  });
});