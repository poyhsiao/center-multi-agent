# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.ts >> Dashboard >> should have new task button
- Location: e2e/dashboard.spec.ts:24:3

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
    - button "Sign In" [active] [ref=e14] [cursor=pointer]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Dashboard', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     // Login before each test
  6  |     await page.goto('/login');
  7  |     await page.fill('[name="email"]', 'user@example.com');
  8  |     await page.fill('[name="password"]', 'ValidPassword123');
  9  |     await page.click('[type="submit"]');
> 10 |     await page.waitForURL(/\/dashboard/);
     |                ^ Error: page.waitForURL: Test timeout of 30000ms exceeded.
  11 |   });
  12 | 
  13 |   test('should display task list', async ({ page }) => {
  14 |     await page.goto('/dashboard');
  15 |     await expect(page.locator('[data-testid="task-list"]')).toBeVisible();
  16 |   });
  17 | 
  18 |   test('should display navigation to Knowledge and Settings', async ({ page }) => {
  19 |     await page.goto('/dashboard');
  20 |     await expect(page.locator('text=Knowledge')).toBeVisible();
  21 |     await expect(page.locator('text=Settings')).toBeVisible();
  22 |   });
  23 | 
  24 |   test('should have new task button', async ({ page }) => {
  25 |     await page.goto('/dashboard');
  26 |     await expect(page.locator('[data-testid="new-task-btn"]')).toBeVisible();
  27 |   });
  28 | });
```