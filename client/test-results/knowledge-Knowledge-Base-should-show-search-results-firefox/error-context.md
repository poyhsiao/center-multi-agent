# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: knowledge.spec.ts >> Knowledge Base >> should show search results
- Location: e2e/knowledge.spec.ts:18:3

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
  3  | test.describe('Knowledge Base', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto('/login');
  6  |     await page.fill('[name="email"]', 'user@example.com');
  7  |     await page.fill('[name="password"]', 'ValidPassword123');
  8  |     await page.click('[type="submit"]');
> 9  |     await page.waitForURL(/\/dashboard/);
     |                ^ Error: page.waitForURL: Test timeout of 30000ms exceeded.
  10 |   });
  11 | 
  12 |   test('should display search interface', async ({ page }) => {
  13 |     await page.goto('/dashboard');
  14 |     await page.click('text=Knowledge');
  15 |     await expect(page.locator('[data-testid="knowledge-search"]')).toBeVisible();
  16 |   });
  17 | 
  18 |   test('should show search results', async ({ page }) => {
  19 |     await page.goto('/dashboard');
  20 |     await page.click('text=Knowledge');
  21 |     await page.fill('[data-testid="knowledge-search"]', 'test query');
  22 |     await page.click('button[type="submit"]');
  23 |     await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
  24 |   });
  25 | });
  26 | 
```