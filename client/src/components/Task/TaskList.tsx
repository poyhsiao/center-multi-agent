import { useTasks } from '../../hooks/useTasks';
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
              <div className="task-date">{new Date(task.created_at).toLocaleDateString()}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}