import { useState, useEffect } from 'react';
import { AuthProvider, useAuthContext } from './context/AuthContext';
import { Login } from './components/Login/Login';
import { Dashboard } from './components/Dashboard/Dashboard';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthContext();
  const [redirected, setRedirected] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      window.location.href = '/login';
      setRedirected(true);
    }
  }, [isAuthenticated]);

  if (redirected || !isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthContext();

  useEffect(() => {
    if (isAuthenticated) {
      window.location.href = '/dashboard';
    }
  }, [isAuthenticated]);

  return <>{children}</>;
}

function AppContent() {
  const { isAuthenticated } = useAuthContext();
  const path = window.location.pathname;

  if (path === '/login') {
    return <Login />;
  }

  if (path === '/dashboard' || path === '/') {
    if (!isAuthenticated) {
      window.location.href = '/login';
      return null;
    }
    return <Dashboard />;
  }

  return <Login />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
