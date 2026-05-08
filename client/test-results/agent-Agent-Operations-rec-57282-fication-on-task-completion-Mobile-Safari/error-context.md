# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: agent.spec.ts >> Agent Operations >> receive SSE notification on task completion
- Location: e2e/agent.spec.ts:13:3

# Error details

```
Error: Channel closed
```

```
Error: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="notification-area"]')
Expected: visible
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('[data-testid="notification-area"]')

```

```
Error: browserContext.close: Test ended.
Browser logs:

<launching> /Users/kimhsiao/Library/Caches/ms-playwright/webkit-2272/pw_run.sh --inspector-pipe --headless --no-startup-window
<launched> pid=45741
[pid=45741] <gracefully close start>
```