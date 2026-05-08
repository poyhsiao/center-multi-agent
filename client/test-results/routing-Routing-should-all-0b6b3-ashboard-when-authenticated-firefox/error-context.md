# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: routing.spec.ts >> Routing >> should allow access to dashboard when authenticated
- Location: e2e/routing.spec.ts:9:3

# Error details

```
Test timeout of 30000ms exceeded.
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
  3  | test.describe('Routing', () => {
  4  |   test('should redirect root to login when unauthenticated', async ({ page }) => {
  5  |     await page.goto('/');
  6  |     await expect(page).toHaveURL(/\/login/);
  7  |   });
  8  | 
  9  |   test('should allow access to dashboard when authenticated', async ({ page }) => {
  10 |     await page.goto('/login');
  11 |     await page.fill('[name="email"]', 'user@example.com');
  12 |     await page.fill('[name="password"]', 'ValidPassword123');
  13 |     await page.click('[type="submit"]');
> 14 |     await page.waitForURL(/\/dashboard/);
     |                ^ Error: page.waitForURL: Test timeout of 30000ms exceeded.
  15 |     await expect(page.locator('h1')).toContainText('Agent Dashboard');
  16 |   });
  17 | 
  18 |   test('should block direct dashboard access when unauthenticated', async ({ page }) => {
  19 |     await page.goto('/dashboard');
  20 |     await expect(page).toHaveURL(/\/login/);
  21 |   });
  22 | });
  23 | 
```