# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: agent.spec.ts >> Agent Operations >> submit task and receive task_id
- Location: e2e/agent.spec.ts:5:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('[data-testid="new-task"]')
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
  1  | // client/e2e/agent.spec.ts
  2  | import { test, expect } from '@playwright/test';
  3  | 
  4  | test.describe('Agent Operations', () => {
  5  |   test('submit task and receive task_id', async ({ page }) => {
  6  |     await page.goto('/dashboard');
> 7  |     await page.click('[data-testid="new-task"]');
     |                ^ Error: page.click: Test timeout of 30000ms exceeded.
  8  |     await page.fill('[name="task-input"]', 'test task');
  9  |     await page.click('[type="submit"]');
  10 |     await expect(page.locator('.task-id')).toBeVisible();
  11 |   });
  12 | 
  13 |   test('receive SSE notification on task completion', async ({ page }) => {
  14 |     // Test SSE event handling
  15 |     // Placeholder - would need real SSE endpoint
  16 |     await page.goto('/dashboard');
  17 |     await expect(page.locator('[data-testid="notification-area"]')).toBeVisible();
  18 |   });
  19 | });
```