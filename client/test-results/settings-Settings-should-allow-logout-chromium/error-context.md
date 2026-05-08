# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: settings.spec.ts >> Settings >> should allow logout
- Location: e2e/settings.spec.ts:24:3

# Error details

```
Test timeout of 30000ms exceeded while running "beforeEach" hook.
```

```
Error: page.waitForURL: Test timeout of 30000ms exceeded.
=========================== logs ===========================
waiting for navigation until "load"
============================================================
```

# Page snapshot

```yaml
- generic [ref=e4]:
  - heading "Sign In" [level=1] [ref=e5]
  - generic [ref=e6]:
    - generic [ref=e7]:
      - generic [ref=e8]: Email
      - textbox "Email" [ref=e9]: user@example.com
    - generic [ref=e10]:
      - generic [ref=e11]: Password
      - textbox "Password" [ref=e12]: ValidPassword123
    - generic [ref=e13]: Invalid email or password
    - button "Sign In" [ref=e14] [cursor=pointer]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Settings', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto('/login');
  6  |     await page.fill('[name="email"]', 'user@example.com');
  7  |     await page.fill('[name="password"]', 'ValidPassword123');
  8  |     await page.click('[type="submit"]');
> 9  |     await page.waitForURL(/\/dashboard/);
     |                ^ Error: page.waitForURL: Test timeout of 30000ms exceeded.
  10 |   });
  11 | 
  12 |   test('should display settings page', async ({ page }) => {
  13 |     await page.goto('/dashboard');
  14 |     await page.click('text=Settings');
  15 |     await expect(page.locator('[data-testid="settings-panel"]')).toBeVisible();
  16 |   });
  17 | 
  18 |   test('should show sync status', async ({ page }) => {
  19 |     await page.goto('/dashboard');
  20 |     await page.click('text=Settings');
  21 |     await expect(page.locator('[data-testid="sync-status"]')).toBeVisible();
  22 |   });
  23 | 
  24 |   test('should allow logout', async ({ page }) => {
  25 |     await page.goto('/dashboard');
  26 |     await page.click('text=Settings');
  27 |     await page.click('[data-testid="logout-btn"]');
  28 |     await expect(page).toHaveURL(/\/login/);
  29 |   });
  30 | });
```