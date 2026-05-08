import { useState, useEffect } from 'react';
import { AuthProvider, useAuthContext } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import './App.css';

function navigate(path: string) {
  window.history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}

function AppContent() {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => setPath(window.location.pathname);
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const { isAuthenticated } = useAuthContext();

  // Auth-based redirects after mount - handled via useEffect only
  useEffect(() => {
    if (!isAuthenticated && path === '/dashboard') {
      navigate('/login');
    } else if (isAuthenticated && path === '/login') {
      navigate('/dashboard');
    }
  }, [isAuthenticated, path]);

  // Handle root path - show login if not authenticated, dashboard if authenticated
  if (path === '/' || path === '/login') {
    return <LoginPage />;
  }

  if (path === '/dashboard') {
    return <DashboardPage />;
  }

  // Unknown path - show dashboard if authenticated, login if not
  return isAuthenticated ? <DashboardPage /> : <LoginPage />;
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;