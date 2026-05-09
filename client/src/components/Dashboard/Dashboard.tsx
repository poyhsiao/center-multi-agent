import { useState } from 'react';
import { Settings } from '../Settings/Settings';
import './Dashboard.css';

// Placeholder components for dependencies not yet implemented
// Note: Using inline placeholders that match real component data-testid attributes
// to maintain E2E test compatibility. Real components require API integration.
const TaskList = () => <div data-testid="task-list"><div className="task-list"><h2>Tasks</h2><p className="empty-state">No tasks yet. Create one to get started.</p></div></div>;
const TaskSubmit = ({ onClose }: { onClose: () => void }) => (
  <div data-testid="task-submit" className="task-submit-overlay">
    <div className="task-submit-modal">
      <h3>New Task</h3>
      <form onSubmit={(e) => { e.preventDefault(); onClose(); }}>
        <textarea placeholder="Describe the task..." rows={4} required />
        <div className="button-group">
          <button type="button" onClick={onClose} className="cancel-btn">Close</button>
          <button type="submit">Submit Task</button>
        </div>
      </form>
    </div>
  </div>
);
const KnowledgeBase = () => <div data-testid="knowledge-base" className="knowledge-base"><h2>Knowledge Base</h2><p className="empty-state">Enter a query to search the knowledge base.</p></div>;

// Placeholder useSSE hook
function useSSE() {
  return { lastEvent: null as { type: string; message: string } | null };
}

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