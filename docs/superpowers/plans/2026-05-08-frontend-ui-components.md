# Frontend UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the React UI components for the Tauri agent client - login, dashboard, task management, knowledge base, settings, and real-time notifications.

**Architecture:** React 19 + TypeScript frontend with Tauri v2 desktop integration. UI state managed via React hooks, server state via fetch to backend API, real-time updates via SSE.

**Tech Stack:** React 19, TypeScript, Vite, @tauri-apps/api, CSS Modules

---

## File Structure

```
client/src/
├── main.tsx                    # React entry (exists)
├── App.tsx                     # Main app with routing (exists, to replace)
├── lib/
│   ├── api.ts                  # API client (exists)
│   ├── auth.ts                 # Auth state (exists)
│   └── sync.ts                 # Sync engine (exists)
├── components/
│   ├── Login/
│   │   ├── Login.tsx           # Login form
│   │   └── Login.css           # Login styles
│   ├── Dashboard/
│   │   ├── Dashboard.tsx       # Main dashboard
│   │   └── Dashboard.css       # Dashboard styles
│   ├── Task/
│   │   ├── TaskList.tsx        # Task list view
│   │   ├── TaskDetail.tsx      # Task detail panel
│   │   ├── TaskSubmit.tsx      # Task submission form
│   │   └── Task.css            # Task styles
│   ├── Knowledge/
│   │   ├── KnowledgeBase.tsx   # Knowledge base browser
│   │   ├── KnowledgeSearch.tsx  # Search interface
│   │   └── Knowledge.css       # Knowledge styles
│   ├── Settings/
│   │   ├── Settings.tsx        # Settings panel
│   │   └── Settings.css        # Settings styles
│   └── Notification/
│       ├── NotificationToast.tsx  # Toast notifications
│       └── Notification.css       # Notification styles
├── hooks/
│   ├── useAuth.ts              # Auth context hook
│   ├── useSSE.ts               # SSE connection hook
│   └── useTasks.ts             # Task management hook
├── context/
│   └── AuthContext.tsx         # Auth provider context
└── types/
    └── index.ts                # TypeScript types
```

---

## Task 1: Auth Context & Protected Routes

**Files:**
- Create: `client/src/context/AuthContext.tsx`
- Create: `client/src/hooks/useAuth.ts`
- Modify: `client/src/App.tsx` (replace default template)
- Test: `client/e2e/auth-flow.spec.ts`

- [ ] **Step 1: Write AuthContext tests**

```typescript
// client/e2e/auth-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Auth Flow', () => {
  test('should show login page when unauthenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Login');
  });

  test('should redirect to dashboard after login', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should redirect to login after logout', async ({ page }) => {
    // First login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    // Then logout
    await page.click('[data-testid="logout-btn"]');
    await expect(page).toHaveURL(/\/login/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd client && npx playwright test e2e/auth-flow.spec.ts -v`
Expected: FAIL - login page doesn't exist yet

- [ ] **Step 3: Write AuthContext**

```typescript
// client/src/context/AuthContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getStoredAuth, clearAuth, AuthState } from '../lib/auth';

interface AuthContextType {
  auth: AuthState | null;
  isAuthenticated: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState | null>(null);

  useEffect(() => {
    // Restore auth state from localStorage on mount
    const stored = getStoredAuth();
    if (stored) {
      setAuth(stored);
    }
  }, []);

  const logout = () => {
    clearAuth();
    setAuth(null);
  };

  return (
    <AuthContext.Provider value={{ auth, isAuthenticated: !!auth?.accessToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider');
  return ctx;
}
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add client/src/context/AuthContext.tsx client/e2e/auth-flow.spec.ts
git commit -m "feat(client): add AuthContext and protected routes"
```

---

## Task 2: Login Page Component

**Files:**
- Create: `client/src/components/Login/Login.tsx`
- Create: `client/src/components/Login/Login.css`
- Modify: `client/src/App.tsx`
- Test: `client/e2e/login.spec.ts` (exists, update)

- [ ] **Step 1: Write Login component tests**

```typescript
// client/e2e/login.spec.ts (update existing placeholder)
import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('should render login form with email and password fields', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show error on invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'wrong@example.com');
    await page.fill('[name="password"]', 'WrongPassword');
    await page.click('[type="submit"]');
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should navigate to dashboard on successful login', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - Login component doesn't exist

- [ ] **Step 3: Write Login component**

```typescript
// client/src/components/Login/Login.tsx
import { useState, FormEvent } from 'react';
import { performLogin } from '../../lib/auth';
import { useAuthContext } from '../../context/AuthContext';
import './Login.css';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { logout } = useAuthContext();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // Generate a simple device fingerprint
      const fingerprint = navigator.userAgent + screen.width + screen.height;
      await performLogin(email, password, fingerprint);
      // Auth context will update, App.tsx will redirect
      window.location.href = '/dashboard';
    } catch (err) {
      setError('Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Sign In</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Write Login CSS**

```css
/* client/src/components/Login/Login.css */
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: 400px;
}

.login-card h1 {
  margin-bottom: 1.5rem;
  color: #333;
  font-size: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
  font-size: 0.875rem;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.error-message {
  color: #dc3545;
  font-size: 0.875rem;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background: #f8d7da;
  border-radius: 4px;
}

button[type="submit"] {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

button[type="submit"]:hover:not(:disabled) {
  background: #5568d3;
}

button[type="submit"]:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
```

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit**

```bash
git add client/src/components/Login/Login.tsx client/src/components/Login/Login.css
git commit -m "feat(client): add Login page component"
```

---

## Task 3: Dashboard Component

**Files:**
- Create: `client/src/components/Dashboard/Dashboard.tsx`
- Create: `client/src/components/Dashboard/Dashboard.css`
- Modify: `client/src/App.tsx`
- Test: `client/e2e/dashboard.spec.ts`

- [ ] **Step 1: Write Dashboard tests**

```typescript
// client/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await page.waitForURL(/\/dashboard/);
  });

  test('should display task list', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="task-list"]')).toBeVisible();
  });

  test('should display navigation to Knowledge and Settings', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=Knowledge')).toBeVisible();
    await expect(page.locator('text=Settings')).toBeVisible();
  });

  test('should have new task button', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="new-task-btn"]')).toBeVisible();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - Dashboard doesn't exist

- [ ] **Step 3: Write Dashboard component**

```typescript
// client/src/components/Dashboard/Dashboard.tsx
import { useState, useEffect } from 'react';
import { TaskList } from '../Task/TaskList';
import { TaskSubmit } from '../Task/TaskSubmit';
import { KnowledgeBase } from '../Knowledge/KnowledgeBase';
import { Settings } from '../Settings/Settings';
import { useSSE } from '../../hooks/useSSE';
import './Dashboard.css';

type Tab = 'tasks' | 'knowledge' | 'settings';

export function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('tasks');
  const [showTaskSubmit, setShowTaskSubmit] = useState(false);
  const { lastEvent } = useSSE();

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Agent Dashboard</h1>
        <nav className="dashboard-nav">
          <button
            className={activeTab === 'tasks' ? 'active' : ''}
            onClick={() => setActiveTab('tasks')}
          >
            Tasks
          </button>
          <button
            className={activeTab === 'knowledge' ? 'active' : ''}
            onClick={() => setActiveTab('knowledge')}
          >
            Knowledge
          </button>
          <button
            className={activeTab === 'settings' ? 'active' : ''}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
        </nav>
      </header>

      <main className="dashboard-content">
        {lastEvent && (
          <div className="notification-toast" data-testid="notification-area">
            {lastEvent.type}: {lastEvent.message}
          </div>
        )}

        {activeTab === 'tasks' && (
          <>
            <button
              className="new-task-btn"
              onClick={() => setShowTaskSubmit(true)}
              data-testid="new-task-btn"
            >
              + New Task
            </button>
            <TaskList />
            {showTaskSubmit && (
              <TaskSubmit onClose={() => setShowTaskSubmit(false)} />
            )}
          </>
        )}

        {activeTab === 'knowledge' && <KnowledgeBase />}

        {activeTab === 'settings' && <Settings />}
      </main>
    </div>
  );
}
```

- [ ] **Step 4: Write Dashboard CSS**

```css
/* client/src/components/Dashboard/Dashboard.css */
.dashboard {
  min-height: 100vh;
  background: #f5f5f5;
}

.dashboard-header {
  background: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  font-size: 1.25rem;
  color: #333;
  margin: 0;
}

.dashboard-nav {
  display: flex;
  gap: 0.5rem;
}

.dashboard-nav button {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.dashboard-nav button:hover {
  background: #f0f0f0;
}

.dashboard-nav button.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.dashboard-content {
  padding: 2rem;
}

.new-task-btn {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.new-task-btn:hover {
  background: #5568d3;
}

.notification-toast {
  padding: 1rem;
  background: #e7f3ff;
  border: 1px solid #667eea;
  border-radius: 4px;
  margin-bottom: 1rem;
}
```

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit**

```bash
git add client/src/components/Dashboard/Dashboard.tsx client/src/components/Dashboard/Dashboard.css
git commit -m "feat(client): add Dashboard component with tab navigation"
```

---

## Task 4: Task List & Task Submit Components

**Files:**
- Create: `client/src/components/Task/TaskList.tsx`
- Create: `client/src/components/Task/TaskSubmit.tsx`
- Create: `client/src/components/Task/Task.css`
- Create: `client/src/hooks/useTasks.ts`
- Test: `client/e2e/tasks.spec.ts`

- [ ] **Step 1: Write useTasks hook**

```typescript
// client/src/hooks/useTasks.ts
import { useState, useEffect } from 'react';

export interface Task {
  id: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/tasks`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_state') ? JSON.parse(localStorage.getItem('auth_state') || '{}').accessToken : ''}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch tasks');
      const data = await response.json();
      setTasks(data.tasks || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const submitTask = async (description: string) => {
    const response = await fetch(`${API_BASE}/api/v1/tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_state') ? JSON.parse(localStorage.getItem('auth_state') || '{}').accessToken : ''}`,
      },
      body: JSON.stringify({ description }),
    });
    if (!response.ok) throw new Error('Failed to submit task');
    return response.json();
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  return { tasks, isLoading, error, fetchTasks, submitTask };
}
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - TaskList component doesn't exist

- [ ] **Step 3: Write TaskList component**

```typescript
// client/src/components/Task/TaskList.tsx
import { useTasks, Task } from '../../hooks/useTasks';
import './Task.css';

export function TaskList() {
  const { tasks, isLoading, error } = useTasks();

  if (isLoading) return <div className="loading">Loading tasks...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="task-list" data-testid="task-list">
      <h2>Tasks</h2>
      {tasks.length === 0 ? (
        <p className="empty-state">No tasks yet. Create one to get started.</p>
      ) : (
        <ul>
          {tasks.map((task) => (
            <li key={task.id} className={`task-item status-${task.status}`}>
              <div className="task-id">{task.id}</div>
              <div className="task-description">{task.description}</div>
              <div className="task-status">{task.status}</div>
              <div className="task-date">
                {new Date(task.created_at).toLocaleDateString()}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Write TaskSubmit component**

```typescript
// client/src/components/Task/TaskSubmit.tsx
import { useState, FormEvent } from 'react';
import { useTasks } from '../../hooks/useTasks';
import './Task.css';

interface TaskSubmitProps {
  onClose: () => void;
}

export function TaskSubmit({ onClose }: TaskSubmitProps) {
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const { submitTask } = useTasks();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await submitTask(description);
      onClose();
    } catch (err) {
      setError('Failed to submit task');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="task-submit-overlay">
      <div className="task-submit-modal">
        <h3>New Task</h3>
        <form onSubmit={handleSubmit}>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the task..."
            rows={4}
            required
          />
          {error && <div className="error-message">{error}</div>}
          <div className="button-group">
            <button type="button" onClick={onClose} className="cancel-btn">
              Cancel
            </button>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting...' : 'Submit Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Write Task CSS**

```css
/* client/src/components/Task/Task.css */
.task-list {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.task-list h2 {
  font-size: 1rem;
  color: #333;
  margin-bottom: 1rem;
}

.task-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.task-item {
  padding: 1rem;
  border-bottom: 1px solid #eee;
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  gap: 1rem;
  align-items: center;
}

.task-item:last-child {
  border-bottom: none;
}

.task-id {
  font-family: monospace;
  font-size: 0.75rem;
  color: #666;
  background: #f5f5f5;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.task-description {
  color: #333;
}

.task-status {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
}

.status-pending .task-status {
  background: #fff3cd;
  color: #856404;
}

.status-running .task-status {
  background: #cce5ff;
  color: #004085;
}

.status-completed .task-status {
  background: #d4edda;
  color: #155724;
}

.status-failed .task-status {
  background: #f8d7da;
  color: #721c24;
}

.empty-state {
  color: #666;
  text-align: center;
  padding: 2rem;
}

/* Task Submit Modal */
.task-submit-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.task-submit-modal {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  width: 100%;
  max-width: 500px;
}

.task-submit-modal h3 {
  margin-bottom: 1rem;
  color: #333;
}

.task-submit-modal textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;
}

.button-group {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.button-group button {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.button-group button[type="submit"] {
  background: #667eea;
  color: white;
  border: none;
}

.button-group button[type="submit"]:disabled {
  opacity: 0.7;
}

.cancel-btn {
  background: transparent;
  border: 1px solid #ddd;
}
```

- [ ] **Step 6: Run test to verify it passes**

- [ ] **Step 7: Commit**

```bash
git add client/src/components/Task/TaskList.tsx client/src/components/Task/TaskSubmit.tsx client/src/components/Task/Task.css client/src/hooks/useTasks.ts
git commit -m "feat(client): add Task list and submit components"
```

---

## Task 5: SSE Hook for Real-time Notifications

**Files:**
- Create: `client/src/hooks/useSSE.ts`
- Test: `client/e2e/sse.spec.ts`

- [ ] **Step 1: Write useSSE tests**

```typescript
// client/e2e/sse.spec.ts
import { test, expect } from '@playwright/test';

test.describe('SSE Notifications', () => {
  test('should display notification when task completes', async ({ page }) => {
    // This test requires a running backend with SSE
    await page.goto('/dashboard');
    // Wait for SSE connection
    await page.waitForTimeout(1000);
    // Notification area should exist
    await expect(page.locator('[data-testid="notification-area"]')).toBeVisible();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - useSSE doesn't exist

- [ ] **Step 3: Write useSSE hook**

```typescript
// client/src/hooks/useSSE.ts
import { useEffect, useRef, useState } from 'react';

export interface SSEvent {
  type: string;
  message: string;
  data?: Record<string, unknown>;
}

export function useSSE(url: string = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/events`) {
  const [lastEvent, setLastEvent] = useState<SSEvent | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Get auth token
    const authState = localStorage.getItem('auth_state');
    const token = authState ? JSON.parse(authState).accessToken : null;

    if (!token) return;

    const eventSource = new EventSource(`${url}?token=${token}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastEvent({ type: data.type || 'info', message: data.message || event.data });
      } catch {
        setLastEvent({ type: 'info', message: event.data });
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [url]);

  return { lastEvent, isConnected };
}
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add client/src/hooks/useSSE.ts client/e2e/sse.spec.ts
git commit -m "feat(client): add SSE hook for real-time notifications"
```

---

## Task 6: Knowledge Base Component

**Files:**
- Create: `client/src/components/Knowledge/KnowledgeBase.tsx`
- Create: `client/src/components/Knowledge/KnowledgeSearch.tsx`
- Create: `client/src/components/Knowledge/Knowledge.css`
- Test: `client/e2e/knowledge.spec.ts`

- [ ] **Step 1: Write KnowledgeBase tests**

```typescript
// client/e2e/knowledge.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Knowledge Base', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await page.waitForURL(/\/dashboard/);
  });

  test('should display search interface', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('text=Knowledge');
    await expect(page.locator('[data-testid="knowledge-search"]')).toBeVisible();
  });

  test('should show search results', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('text=Knowledge');
    await page.fill('[data-testid="knowledge-search"]', 'test query');
    await page.click('button[type="submit"]');
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - KnowledgeBase doesn't exist

- [ ] **Step 3: Write KnowledgeSearch component**

```typescript
// client/src/components/Knowledge/KnowledgeSearch.tsx
import { useState, FormEvent } from 'react';
import './Knowledge.css';

interface SearchResult {
  id: string;
  title: string;
  content: string;
  similarity: number;
}

interface KnowledgeSearchProps {
  onResults: (results: SearchResult[]) => void;
  isSearching: boolean;
}

export function KnowledgeSearch({ onResults, isSearching }: KnowledgeSearchProps) {
  const [query, setQuery] = useState('');

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      const authState = localStorage.getItem('auth_state');
      const token = authState ? JSON.parse(authState).accessToken : '';

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/rag/search`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ query }),
        }
      );

      if (!response.ok) throw new Error('Search failed');
      const data = await response.json();
      onResults(data.results || []);
    } catch (err) {
      console.error('Search error:', err);
    }
  };

  return (
    <form onSubmit={handleSearch} className="knowledge-search">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search knowledge base..."
        data-testid="knowledge-search"
      />
      <button type="submit" disabled={isSearching}>
        {isSearching ? 'Searching...' : 'Search'}
      </button>
    </form>
  );
}
```

- [ ] **Step 4: Write KnowledgeBase component**

```typescript
// client/src/components/Knowledge/KnowledgeBase.tsx
import { useState } from 'react';
import { KnowledgeSearch } from './KnowledgeSearch';
import './Knowledge.css';

interface SearchResult {
  id: string;
  title: string;
  content: string;
  similarity: number;
}

export function KnowledgeBase() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  return (
    <div className="knowledge-base">
      <h2>Knowledge Base</h2>
      <KnowledgeSearch onResults={setResults} isSearching={isSearching} />
      <div className="search-results" data-testid="search-results">
        {results.length === 0 ? (
          <p className="empty-state">Enter a query to search the knowledge base.</p>
        ) : (
          <ul>
            {results.map((result) => (
              <li key={result.id} className="result-item">
                <h4>{result.title}</h4>
                <p>{result.content}</p>
                <span className="similarity">{(result.similarity * 100).toFixed(1)}% match</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Write Knowledge CSS**

```css
/* client/src/components/Knowledge/Knowledge.css */
.knowledge-base {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.knowledge-base h2 {
  font-size: 1rem;
  color: #333;
  margin-bottom: 1rem;
}

.knowledge-search {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.knowledge-search input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.knowledge-search button {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.knowledge-search button:disabled {
  opacity: 0.7;
}

.search-results ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.result-item {
  padding: 1rem;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 0.75rem;
}

.result-item h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.result-item p {
  margin: 0 0 0.5rem 0;
  color: #666;
  font-size: 0.875rem;
}

.similarity {
  font-size: 0.75rem;
  color: #667eea;
}

.empty-state {
  color: #666;
  text-align: center;
  padding: 2rem;
}
```

- [ ] **Step 6: Run test to verify it passes**

- [ ] **Step 7: Commit**

```bash
git add client/src/components/Knowledge/KnowledgeBase.tsx client/src/components/Knowledge/KnowledgeSearch.tsx client/src/components/Knowledge/Knowledge.css
git commit -m "feat(client): add Knowledge base search component"
```

---

## Task 7: Settings Component

**Files:**
- Create: `client/src/components/Settings/Settings.tsx`
- Create: `client/src/components/Settings/Settings.css`
- Modify: `client/src/App.tsx`
- Test: `client/e2e/settings.spec.ts`

- [ ] **Step 1: Write Settings tests**

```typescript
// client/e2e/settings.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await page.waitForURL(/\/dashboard/);
  });

  test('should display settings page', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('text=Settings');
    await expect(page.locator('[data-testid="settings-panel"]')).toBeVisible();
  });

  test('should show sync status', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('text=Settings');
    await expect(page.locator('[data-testid="sync-status"]')).toBeVisible();
  });

  test('should allow logout', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('text=Settings');
    await page.click('[data-testid="logout-btn"]');
    await expect(page).toHaveURL(/\/login/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - Settings doesn't exist

- [ ] **Step 3: Write Settings component**

```typescript
// client/src/components/Settings/Settings.tsx
import { useState, useEffect } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import { checkSync } from '../../lib/sync';
import './Settings.css';

export function Settings() {
  const { logout } = useAuthContext();
  const [syncStatus, setSyncStatus] = useState<'checking' | 'up_to_date' | 'update_required'>('checking');
  const [clientVersion, setClientVersion] = useState('0.1.0');

  useEffect(() => {
    const checkSyncStatus = async () => {
      try {
        const result = await checkSync({
          client_version: clientVersion,
          mcp_version: '1.0.0',
        });
        setSyncStatus(result.status);
      } catch {
        setSyncStatus('up_to_date');
      }
    };
    checkSyncStatus();
  }, []);

  return (
    <div className="settings" data-testid="settings-panel">
      <h2>Settings</h2>

      <div className="settings-section">
        <h3>Sync Status</h3>
        <div className="sync-status" data-testid="sync-status">
          {syncStatus === 'checking' && <span>Checking...</span>}
          {syncStatus === 'up_to_date' && <span className="status-ok">Up to date</span>}
          {syncStatus === 'update_required' && <span className="status-warning">Update available</span>}
        </div>
      </div>

      <div className="settings-section">
        <h3>Account</h3>
        <button
          className="logout-btn"
          onClick={logout}
          data-testid="logout-btn"
        >
          Sign Out
        </button>
      </div>

      <div className="settings-section">
        <h3>About</h3>
        <p>Version: {clientVersion}</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Write Settings CSS**

```css
/* client/src/components/Settings/Settings.css */
.settings {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.settings h2 {
  font-size: 1rem;
  color: #333;
  margin-bottom: 1.5rem;
}

.settings-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #eee;
}

.settings-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.settings-section h3 {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.75rem;
}

.sync-status {
  display: flex;
  align-items: center;
}

.sync-status .status-ok {
  color: #28a745;
}

.sync-status .status-warning {
  color: #ffc107;
}

.logout-btn {
  padding: 0.5rem 1rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.logout-btn:hover {
  background: #c82333;
}

.settings-section p {
  color: #666;
  margin: 0;
}
```

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit**

```bash
git add client/src/components/Settings/Settings.tsx client/src/components/Settings/Settings.css
git commit -m "feat(client): add Settings component"
```

---

## Task 8: App.tsx with Routing Integration

**Files:**
- Modify: `client/src/App.tsx`
- Test: `client/e2e/routing.spec.ts`

- [ ] **Step 1: Write routing tests**

```typescript
// client/e2e/routing.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Routing', () => {
  test('should redirect root to login when unauthenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should allow access to dashboard when authenticated', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'ValidPassword123');
    await page.click('[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    await expect(page.locator('h1')).toContainText('Agent Dashboard');
  });

  test('should block direct dashboard access when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - App.tsx hasn't been updated yet

- [ ] **Step 3: Write App.tsx with routing**

```typescript
// client/src/App.tsx
import { useState, useEffect } from 'react';
import { AuthProvider, useAuthContext } from './context/AuthContext';
import { Login } from './components/Login/Login';
import { Dashboard } from './components/Dashboard/Dashboard';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthContext();
  const [redirected, setRedirected] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      window.location.href = '/login';
      setRedirected(true);
    }
  }, [isAuthenticated]);

  if (redirected || !isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthContext();

  useEffect(() => {
    if (isAuthenticated) {
      window.location.href = '/dashboard';
    }
  }, [isAuthenticated]);

  return <>{children}</>;
}

function AppContent() {
  const { isAuthenticated } = useAuthContext();
  const path = window.location.pathname;

  // Simple client-side routing
  if (path === '/login') {
    return <Login />;
  }

  if (path === '/dashboard' || path === '/') {
    if (!isAuthenticated) {
      window.location.href = '/login';
      return null;
    }
    return <Dashboard />;
  }

  // Fallback to login
  return <Login />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add client/src/App.tsx
git commit -m "feat(client): integrate routing with AuthContext"
```

---

## Verification

After all tasks:

```bash
# Run all E2E tests
cd client && npx playwright test e2e/ --reporter=html

# Verify test results
ls client/test-results/

# Build verification
cd client && npm run build
```

---

## Summary

- **Task 1:** AuthContext + useAuth hook for authentication state
- **Task 2:** Login page with form validation
- **Task 3:** Dashboard with tab navigation (Tasks, Knowledge, Settings)
- **Task 4:** TaskList + TaskSubmit with useTasks hook
- **Task 5:** useSSE hook for real-time notifications
- **Task 6:** KnowledgeBase + KnowledgeSearch with RAG integration
- **Task 7:** Settings page with sync status and logout
- **Task 8:** App.tsx with client-side routing and protected routes