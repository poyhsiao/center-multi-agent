// client/src/lib/sync.ts
import { ensureValidToken } from './auth';

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
