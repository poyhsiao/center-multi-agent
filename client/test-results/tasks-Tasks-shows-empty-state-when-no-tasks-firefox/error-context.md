# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tasks.spec.ts >> Tasks >> shows empty state when no tasks
- Location: e2e/tasks.spec.ts:9:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.empty-state')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('.empty-state')

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
  3  | test.describe('Tasks', () => {
  4  |   test('displays task list', async ({ page }) => {
  5  |     await page.goto('/tasks');
  6  |     await expect(page.locator('[data-testid="task-list"]')).toBeVisible();
  7  |   });
  8  | 
  9  |   test('shows empty state when no tasks', async ({ page }) => {
  10 |     await page.goto('/tasks');
> 11 |     await expect(page.locator('.empty-state')).toBeVisible();
     |                                                ^ Error: expect(locator).toBeVisible() failed
  12 |   });
  13 | 
  14 |   test('opens task submit modal', async ({ page }) => {
  15 |     await page.goto('/tasks');
  16 |     const newTaskBtn = page.locator('button:has-text("New Task")');
  17 |     if (await newTaskBtn.isVisible()) {
  18 |       await newTaskBtn.click();
  19 |       await expect(page.locator('.task-submit-modal')).toBeVisible();
  20 |     }
  21 |   });
  22 | 
  23 |   test('closes task submit modal on cancel', async ({ page }) => {
  24 |     await page.goto('/tasks');
  25 |     const newTaskBtn = page.locator('button:has-text("New Task")');
  26 |     if (await newTaskBtn.isVisible()) {
  27 |       await newTaskBtn.click();
  28 |       await page.locator('.cancel-btn').click();
  29 |       await expect(page.locator('.task-submit-modal')).not.toBeVisible();
  30 |     }
  31 |   });
  32 | });
```