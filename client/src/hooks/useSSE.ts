import { useEffect, useRef, useState } from 'react';

export interface SSEvent {
  type: string;
  message: string;
  data?: Record<string, unknown>;
}

export function useSSE(url: string = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/events`) {
  const [lastEvent, setLastEvent] = useState<SSEvent | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const authState = localStorage.getItem('auth_state');
    const token = authState ? JSON.parse(authState).accessToken : null;

    if (!token) return;

    const eventSource = new EventSource(`${url}?token=${token}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => setIsConnected(true);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastEvent({ type: data.type || 'info', message: data.message || event.data });
      } catch {
        setLastEvent({ type: 'info', message: event.data });
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      eventSource.close();
    };

    return () => eventSource.close();
  }, [url]);

  return { lastEvent, isConnected };
}