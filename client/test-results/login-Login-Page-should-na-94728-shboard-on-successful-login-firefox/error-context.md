# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> Login Page >> should navigate to dashboard on successful login
- Location: e2e/login.spec.ts:20:3

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /\/dashboard/
Received string:  "http://localhost:1420/login"
Timeout: 5000ms

Call log:
  - Expect "toHaveURL" with timeout 5000ms
    8 × unexpected value "http://localhost:1420/login"

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
  1  | // client/e2e/login.spec.ts
  2  | import { test, expect } from '@playwright/test';
  3  | 
  4  | test.describe('Login Page', () => {
  5  |   test('should render login form with email and password fields', async ({ page }) => {
  6  |     await page.goto('/login');
  7  |     await expect(page.locator('input[name="email"]')).toBeVisible();
  8  |     await expect(page.locator('input[name="password"]')).toBeVisible();
  9  |     await expect(page.locator('button[type="submit"]')).toBeVisible();
  10 |   });
  11 | 
  12 |   test('should show error on invalid credentials', async ({ page }) => {
  13 |     await page.goto('/login');
  14 |     await page.fill('[name="email"]', 'wrong@example.com');
  15 |     await page.fill('[name="password"]', 'WrongPassword');
  16 |     await page.click('[type="submit"]');
  17 |     await expect(page.locator('.error-message')).toBeVisible();
  18 |   });
  19 | 
  20 |   test('should navigate to dashboard on successful login', async ({ page }) => {
  21 |     await page.goto('/login');
  22 |     await page.fill('[name="email"]', 'user@example.com');
  23 |     await page.fill('[name="password"]', 'ValidPassword123');
  24 |     await page.click('[type="submit"]');
> 25 |     await expect(page).toHaveURL(/\/dashboard/);
     |                        ^ Error: expect(page).toHaveURL(expected) failed
  26 |   });
  27 | });
```