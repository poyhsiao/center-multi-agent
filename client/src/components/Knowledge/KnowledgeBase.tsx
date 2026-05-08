import { useState } from 'react';
import { KnowledgeSearch } from './KnowledgeSearch';
import './Knowledge.css';

interface SearchResult {
  id: string;
  title: string;
  content: string;
  similarity: number;
}

export function KnowledgeBase() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  return (
    <div className="knowledge-base">
      <h2>Knowledge Base</h2>
      <KnowledgeSearch onResults={setResults} isSearching={isSearching} />
      <div className="search-results" data-testid="search-results">
        {results.length === 0 ? (
          <p className="empty-state">Enter a query to search the knowledge base.</p>
        ) : (
          <ul>
            {results.map((result) => (
              <li key={result.id} className="result-item">
                <h4>{result.title}</h4>
                <p>{result.content}</p>
                <span className="similarity">{(result.similarity * 100).toFixed(1)}% match</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
