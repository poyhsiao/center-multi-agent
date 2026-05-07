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
