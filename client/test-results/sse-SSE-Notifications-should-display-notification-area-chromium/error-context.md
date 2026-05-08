# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: sse.spec.ts >> SSE Notifications >> should display notification area
- Location: e2e/sse.spec.ts:4:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="notification-area"]')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('[data-testid="notification-area"]')
    - waiting for" http://localhost:1420/login" navigation to finish...
    - navigated to "http://localhost:1420/login"

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
  1 | import { test, expect } from '@playwright/test';
  2 | 
  3 | test.describe('SSE Notifications', () => {
  4 |   test('should display notification area', async ({ page }) => {
  5 |     await page.goto('/dashboard');
  6 |     // Wait for dashboard to load
> 7 |     await expect(page.locator('[data-testid="notification-area"]')).toBeVisible();
    |                                                                     ^ Error: expect(locator).toBeVisible() failed
  8 |   });
  9 | });
```