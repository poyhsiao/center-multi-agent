// client/src/lib/sync.ts
import { ensureValidToken } from './auth';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const SYNC_ENDPOINT = `${API_BASE}/api/v1/sync`;

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

  if (!response.ok) {
    throw new Error(`Sync check failed: ${response.status}`);
  }

  return response.json();
}

export async function uploadSettings(settings: Record<string, unknown>): Promise<void> {
  const response = await fetch(`${SYNC_ENDPOINT}/settings`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${await ensureValidToken()}`,
    },
    body: JSON.stringify({ settings }),
  });

  if (!response.ok) {
    throw new Error(`Settings upload failed: ${response.status}`);
  }
}
