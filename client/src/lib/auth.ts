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
