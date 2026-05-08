# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: agent.spec.ts >> Agent Operations >> submit task and receive task_id
- Location: e2e/agent.spec.ts:5:3

# Error details

```
Error: Channel closed
```

```
Error: page.click: Target page, context or browser has been closed
Call log:
  - waiting for locator('[data-testid="new-task"]')

```

```
Error: browserContext.close: Test ended.
Browser logs:

<launching> /Users/kimhsiao/Library/Caches/ms-playwright/webkit-2272/pw_run.sh --inspector-pipe --headless --no-startup-window
<launched> pid=45722
[pid=45722] <gracefully close start>
```