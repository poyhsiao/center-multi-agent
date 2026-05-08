import { useState } from 'react';
import { Settings } from '../Settings/Settings';
import './Dashboard.css';

// Placeholder components for dependencies not yet implemented
const TaskList = () => <div data-testid="task-list">TaskList placeholder</div>;
const TaskSubmit = ({ onClose }: { onClose: () => void }) => (
  <div data-testid="task-submit">
    TaskSubmit placeholder <button onClick={onClose}>Close</button>
  </div>
);
const KnowledgeBase = () => <div data-testid="knowledge-base">KnowledgeBase placeholder</div>;

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