import { useState, FormEvent } from 'react';
import './Knowledge.css';

interface SearchResult {
  id: string;
  title: string;
  content: string;
  similarity: number;
}

interface KnowledgeSearchProps {
  onResults: (results: SearchResult[]) => void;
  onError?: (error: string) => void;
  isSearching: boolean;
}

export function KnowledgeSearch({ onResults, onError, isSearching }: KnowledgeSearchProps) {
  const [query, setQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      const authState = localStorage.getItem('auth_state');
      const token = authState ? JSON.parse(authState).accessToken : '';

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/rag/search`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ query }),
        }
      );

      if (!response.ok) throw new Error('Search failed');
      const data = await response.json();
      onResults(data.results || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Search failed';
      setError(message);
      onError?.(message);
    }
  };

  return (
    <form onSubmit={handleSearch} className="knowledge-search">
      {error && (
        <div className="knowledge-search__error" role="alert">
          {error}
          <button type="button" onClick={() => setError(null)} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search knowledge base..."
        data-testid="knowledge-search"
      />
      <button type="submit" disabled={isSearching}>
        {isSearching ? 'Searching...' : 'Search'}
      </button>
    </form>
  );
}
