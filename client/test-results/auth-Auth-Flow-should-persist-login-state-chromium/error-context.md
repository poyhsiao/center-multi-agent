# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> Auth Flow >> should persist login state
- Location: e2e/auth.spec.ts:5:3

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /\/dashboard/
Received string:  "http://localhost:1420/login"
Timeout: 5000ms

Call log:
  - Expect "toHaveURL" with timeout 5000ms
    9 × unexpected value "http://localhost:1420/login"

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
  1  | // client/e2e/auth.spec.ts
  2  | import { test, expect } from '@playwright/test';
  3  | 
  4  | test.describe('Auth Flow', () => {
  5  |   test('should persist login state', async ({ page }) => {
  6  |     await page.goto('/login');
  7  |     await page.fill('[name="email"]', 'user@example.com');
  8  |     await page.fill('[name="password"]', 'ValidPassword123');
  9  |     await page.click('[type="submit"]');
  10 | 
  11 |     // Should redirect to dashboard
> 12 |     await expect(page).toHaveURL(/\/dashboard/);
     |                        ^ Error: expect(page).toHaveURL(expected) failed
  13 | 
  14 |     // State should persist after reload
  15 |     await page.reload();
  16 |     await expect(page).toHaveURL(/\/dashboard/);
  17 |   });
  18 | });
  19 | 
```