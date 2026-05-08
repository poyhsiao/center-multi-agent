import { useState, useEffect } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import { checkSync } from '../../lib/sync';
import './Settings.css';

export function Settings() {
  const { logout } = useAuthContext();
  const [syncStatus, setSyncStatus] = useState<'checking' | 'up_to_date' | 'update_required'>('checking');
  const [clientVersion] = useState('0.1.0');

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
        <button className="logout-btn" onClick={logout} data-testid="logout-btn">
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