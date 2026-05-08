// client/e2e/login.spec.ts
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