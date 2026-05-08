import { useState, useEffect } from 'react';

export interface Task {
  id: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async () => {
    setIsLoading(true);
    try {
      const stored = localStorage.getItem('auth_state');
      const token = stored ? JSON.parse(stored).accessToken : '';

      const response = await fetch(`${API_BASE}/api/v1/tasks`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch tasks');
      const data = await response.json();
      setTasks(data.tasks || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const submitTask = async (description: string) => {
    const stored = localStorage.getItem('auth_state');
    const token = stored ? JSON.parse(stored).accessToken : '';

    const response = await fetch(`${API_BASE}/api/v1/tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ description }),
    });
    if (!response.ok) throw new Error('Failed to submit task');
    return response.json();
  };

  useEffect(() => { fetchTasks(); }, []);

  return { tasks, isLoading, error, fetchTasks, submitTask };
}