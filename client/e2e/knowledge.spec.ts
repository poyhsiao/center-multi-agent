// client/e2e/knowledge.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Knowledge Contribution', () => {
  test('submit new knowledge', async ({ page }) => {
    await page.goto('/knowledge/new');
    await page.fill('[name="title"]', 'Test Knowledge');
    await page.fill('[name="content"]', 'Test content for knowledge base');
    await page.click('[type="submit"]');
    await expect(page.locator('.knowledge-id')).toBeVisible();
  });

  test('view knowledge list', async ({ page }) => {
    await page.goto('/knowledge');
    await expect(page.locator('.knowledge-list')).toBeVisible();
  });
});