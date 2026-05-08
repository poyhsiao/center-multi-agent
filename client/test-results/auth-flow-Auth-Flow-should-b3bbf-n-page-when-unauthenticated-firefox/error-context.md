# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-flow.spec.ts >> Auth Flow >> should show login page when unauthenticated
- Location: e2e/auth-flow.spec.ts:4:3

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('h1')
Expected substring: "Login"
Received string:    "Sign In"
Timeout: 5000ms

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('h1')
    9 × locator resolved to <h1>Sign In</h1>
      - unexpected value "Sign In"

```

# Page snapshot

```yaml
- generic [ref=e4]:
  - heading "Sign In" [level=1] [ref=e5]
  - generic [ref=e6]:
    - generic [ref=e7]:
      - generic [ref=e8]: Email
      - textbox "Email" [ref=e9]
    - generic [ref=e10]:
      - generic [ref=e11]: Password
      - textbox "Password" [ref=e12]
    - button "Sign In" [ref=e13] [cursor=pointer]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Auth Flow', () => {
  4  |   test('should show login page when unauthenticated', async ({ page }) => {
  5  |     await page.goto('/');
> 6  |     await expect(page.locator('h1')).toContainText('Login');
     |                                      ^ Error: expect(locator).toContainText(expected) failed
  7  |   });
  8  | 
  9  |   test('should redirect to dashboard after login', async ({ page }) => {
  10 |     await page.goto('/login');
  11 |     await page.fill('[name="email"]', 'test@example.com');
  12 |     await page.fill('[name="password"]', 'ValidPassword123');
  13 |     await page.click('[type="submit"]');
  14 |     await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  15 |   });
  16 | 
  17 |   test('should redirect to login after logout', async ({ page }) => {
  18 |     // First login
  19 |     await page.goto('/login');
  20 |     await page.fill('[name="email"]', 'test@example.com');
  21 |     await page.fill('[name="password"]', 'ValidPassword123');
  22 |     await page.click('[type="submit"]');
  23 |     // Then logout
  24 |     await page.click('[data-testid="logout-btn"]');
  25 |     await expect(page).toHaveURL(/\/login/);
  26 |   });
  27 | });
```