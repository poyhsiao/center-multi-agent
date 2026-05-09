import { test as setup, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const authFile = join(__dirname, '../playwright/.auth/user.json');

setup('authenticate via UI', async ({ page }) => {
  console.log('Starting authentication setup...');

  // Navigate to login page
  await page.goto('/login');
  console.log('Navigated to login page');

  // Fill in credentials
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'TestPassword123');
  console.log('Filled credentials');

  await page.click('[type="submit"]');
  console.log('Clicked submit');

  // Wait for redirect to dashboard
  await page.waitForURL(/\/dashboard/, { timeout: 15000 });
  console.log('Redirected to dashboard');

  // Verify we're logged in - check localStorage
  const authState = await page.evaluate(() => localStorage.getItem('auth_state'));
  console.log('Auth state in localStorage:', authState ? 'exists' : 'missing');

  // Verify page loaded
  await expect(page.locator('body')).toBeVisible();
  console.log('Page body visible');

  // Save storage state (cookies + localStorage)
  await page.context().storageState({ path: authFile });
  console.log('Storage state saved to:', authFile);
});