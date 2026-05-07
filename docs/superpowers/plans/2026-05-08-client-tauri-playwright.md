# Client Agent (Tauri) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up Tauri desktop client with React frontend, API client, authentication, and Playwright E2E tests.

**Architecture:** Tauri v2 for cross-platform desktop app with React + TypeScript frontend, communicating with backend via REST API and WebSocket.

**Tech Stack:** Tauri 2.x, React 18, TypeScript, Vite, @tauri-apps/api, Playwright

---

## File Structure

```
client/
├── src/
│   ├── main.tsx              # React entry
│   ├── App.tsx               # Main app component
│   ├── lib/
│   │   ├── api.ts            # API client for backend
│   │   ├── auth.ts           # Auth state management
│   │   └── sync.ts           # Sync engine
│   └── components/           # React components
├── e2e/                      # Playwright E2E tests
│   ├── login.spec.ts
│   └── ...
├── src-tauri/
│   ├── src/
│   │   └── main.rs           # Rust entry
│   ├── Cargo.toml
│   └── tauri.conf.json
├── package.json
├── tsconfig.json
├── vite.config.ts
└── playwright.config.ts
```

---

## Task 1: Initialize Tauri Project

**Files:**
- Create: `client/` (new project)
- Modify: `client/package.json`
- Test: N/A (setup only)

- [ ] **Step 1: Create Tauri app with React template**

Run: `cd client && npm create tauri-app@latest -- --template react-ts --yes .`

This creates:
```
client/
├── src/                      # React frontend
├── src-tauri/                # Rust backend
├── package.json
└── ...config files
```

- [ ] **Step 2: Install additional dependencies**

```bash
cd client
npm install @tauri-apps/api
npm install -D @playwright/test
npx playwright install chromium firefox webkit
```

- [ ] **Step 3: Verify Tauri builds**

```bash
cd client
npm run tauri build 2>&1 | tail -20
```

Expected: Build completes without errors

- [ ] **Step 4: Commit**

```bash
cd /path/to/repo
git add client/
git commit -m "feat(client): initialize Tauri project with React"
```

---

## Task 2: API Client Library

**Files:**
- Create: `client/src/lib/api.ts`
- Modify: `client/src/lib/auth.ts`
- Test: `client/e2e/api.spec.ts`

- [ ] **Step 1: Write API client tests**

```typescript
// client/e2e/api.spec.ts
import { test, expect } from '@playwright/test';

test.describe('API Client', () => {
  test('should create login request correctly', async () => {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'TestPassword123',
        device_fingerprint: 'fp_test123',
      }),
    });
    expect(response.ok).toBeTruthy();
  });

  test('should handle auth refresh', async ({ page }) => {
    await page.goto('/login');
    // Test token refresh flow
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd client && npx playwright test e2e/api.spec.ts -v`
Expected: FAIL with connection refused (no server running)

- [ ] **Step 3: Write API client**

```typescript
// client/src/lib/api.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface LoginRequest {
  email: string;
  password: string;
  device_fingerprint: string;
  totp_code?: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export async function login(request: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Login failed: ${response.status}`);
  }

  return response.json();
}

export async function refreshToken(refreshToken: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${refreshToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Refresh failed: ${response.status}`);
  }

  return response.json();
}

export async function logout(accessToken: string): Promise<void> {
  await fetch(`${API_BASE}/api/v1/auth/logout`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
}
```

- [ ] **Step 4: Run test to verify it passes (with mock server)**

- [ ] **Step 5: Commit**

```bash
git add client/src/lib/api.ts client/e2e/api.spec.ts
git commit -m "feat(client): add API client library"
```

---

## Task 3: Auth State Management

**Files:**
- Create: `client/src/lib/auth.ts`
- Modify: `client/src/App.tsx`
- Test: `client/e2e/auth.spec.ts`

- [ ] **Step 1: Write auth state tests**

```typescript
// client/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Auth Flow', () => {
  test('should persist login state', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // State should persist after reload
    await page.reload();
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL (login page doesn't exist yet)

- [ ] **Step 3: Write auth state management**

```typescript
// client/src/lib/auth.ts
import { login as apiLogin, refreshToken, logout as apiLogout } from './api';

export interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
}

const AUTH_STORAGE_KEY = 'auth_state';

export function getStoredAuth(): AuthState | null {
  const stored = localStorage.getItem(AUTH_STORAGE_KEY);
  return stored ? JSON.parse(stored) : null;
}

export function saveAuth(auth: AuthState): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth));
}

export function clearAuth(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

export async function performLogin(
  email: string,
  password: string,
  deviceFingerprint: string
): Promise<AuthState> {
  const response = await apiLogin({
    email,
    password,
    device_fingerprint: deviceFingerprint,
  });

  const auth: AuthState = {
    accessToken: response.access_token,
    refreshToken: response.refresh_token,
    expiresAt: Date.now() + response.expires_in * 1000,
  };

  saveAuth(auth);
  return auth;
}

export async function performLogout(accessToken: string): Promise<void> {
  await apiLogout(accessToken);
  clearAuth();
}

export async function ensureValidToken(): Promise<string | null> {
  const auth = getStoredAuth();
  if (!auth) return null;

  // Check if expired
  if (Date.now() >= auth.expiresAt - 60000) {
    // Refresh needed (1 min buffer)
    try {
      const newAuth = await refreshToken(auth.refreshToken);
      const updated: AuthState = {
        accessToken: newAuth.access_token,
        refreshToken: newAuth.refresh_token,
        expiresAt: Date.now() + newAuth.expires_in * 1000,
      };
      saveAuth(updated);
      return updated.accessToken;
    } catch {
      clearAuth();
      return null;
    }
  }

  return auth.accessToken;
}
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add client/src/lib/auth.ts client/src/App.tsx client/e2e/auth.spec.ts
git commit -m "feat(client): add auth state management"
```

---

## Task 4: Sync Engine

**Files:**
- Create: `client/src/lib/sync.ts`
- Test: `client/e2e/sync.spec.ts`

- [ ] **Step 1: Write sync engine tests**

```typescript
// client/e2e/sync.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Sync Engine', () => {
  test('should detect version mismatch', async ({ page }) => {
    await page.goto('/settings');
    // Verify sync status shown
  });

  test('should sync settings across instances', async ({ browser }) => {
    const ctx1 = await browser.newContext();
    const ctx2 = await browser.newContext();

    // Update in ctx1, verify in ctx2
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Write sync engine**

```typescript
// client/src/lib/sync.ts
const SYNC_ENDPOINT = '/api/v1/sync';

interface SyncRequest {
  client_version: string;
  mcp_version: string;
  settings?: Record<string, unknown>;
}

interface SyncResponse {
  status: 'up_to_date' | 'update_required';
  updates?: {
    mcp_version: string;
    skills: Array<{ name: string; version: string }>;
  };
}

export async function checkSync(request: SyncRequest): Promise<SyncResponse> {
  const response = await fetch(`${SYNC_ENDPOINT}/check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${await ensureValidToken()}`,
    },
    body: JSON.stringify(request),
  });

  return response.json();
}

export async function uploadSettings(settings: Record<string, unknown>): Promise<void> {
  await fetch(`${SYNC_ENDPOINT}/settings`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${await ensureValidToken()}`,
    },
    body: JSON.stringify({ settings }),
  });
}
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add client/src/lib/sync.ts client/e2e/sync.spec.ts
git commit -m "feat(client): add sync engine"
```

---

## Task 5: E2E Test Suite

**Files:**
- Create: `client/e2e/login.spec.ts`
- Create: `client/e2e/agent.spec.ts`
- Create: `client/e2e/knowledge.spec.ts`
- Test: All E2E tests

- [ ] **Step 1: Write login E2E tests**

```typescript
// client/e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('success login with correct password', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('fail login with wrong password', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'WrongPassword');
    await page.click('[type="submit"]');
    await expect(page.locator('.error')).toContainText('Invalid credentials');
  });

  test('token refresh on expiry', async ({ page }) => {
    // Simulate token expiry and verify refresh
  });
});
```

- [ ] **Step 2: Write agent operation E2E tests**

```typescript
// client/e2e/agent.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Agent Operations', () => {
  test('submit task and receive task_id', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('[data-testid="new-task"]');
    await page.fill('[name="task-input"]', 'test task');
    await page.click('[type="submit"]');
    await expect(page.locator('.task-id')).toBeVisible();
  });

  test('receive SSE notification on task completion', async ({ page }) => {
    // Test SSE event handling
  });
});
```

- [ ] **Step 3: Run all E2E tests**

Run: `cd client && npx playwright test e2e/ -v`
Expected: PASS (all E2E tests green)

- [ ] **Step 4: Commit**

```bash
git add client/e2e/
git commit -m "test(e2e): add Playwright E2E test suite"
```

---

## Verification

After all tasks:

```bash
# Verify Tauri builds
cd client && npm run tauri build

# Run E2E tests
cd client && npx playwright test e2e/ --reporter=html

# Verify test results
ls client/test-results/
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Tauri Project Init | client/ (new) |
| 2 | API Client | lib/api.ts |
| 3 | Auth State | lib/auth.ts |
| 4 | Sync Engine | lib/sync.ts |
| 5 | E2E Tests | e2e/*.spec.ts |