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
            <button type="button" onClick={onClose} className="cancel-btn">Cancel</button>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting...' : 'Submit Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}