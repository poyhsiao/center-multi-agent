import { test, expect } from '@playwright/test';

test('login flow', async ({ page }) => {
  await page.goto('http://localhost:1420/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'ValidPassword123');
  await page.click('[type="submit"]');
  
  // Wait for dashboard URL
  await page.waitForURL('**/dashboard**', { timeout: 10000 });
  
  // Wait a moment for React to render
  await page.waitForTimeout(500);
  
  // Check page content
  const h1 = await page.locator('h1').first().textContent();
  console.log('H1 content:', h1);
  
  await expect(page.locator('h1')).toContainText('Agent Dashboard');
});
