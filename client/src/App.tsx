import { useEffect, useState, type ReactNode } from 'react';
import { AuthProvider, useAuthContext } from './context/AuthContext';
import { Login } from './components/Login/Login';
import { Dashboard } from './components/Dashboard/Dashboard';

interface RouteGuardProps {
  children: ReactNode;
  requiresAuth: boolean;
  redirectTo: string;
}

function RouteGuard({ children, requiresAuth, redirectTo }: RouteGuardProps) {
  const { isAuthenticated } = useAuthContext();
  const [hasRedirected, setHasRedirected] = useState(false);

  useEffect(() => {
    if (requiresAuth && !isAuthenticated && !hasRedirected) {
      window.location.href = redirectTo;
      setHasRedirected(true);
    } else if (!requiresAuth && isAuthenticated && !hasRedirected) {
      window.location.href = redirectTo;
      setHasRedirected(true);
    }
  }, [requiresAuth, isAuthenticated, hasRedirected, redirectTo]);

  if (hasRedirected) {
    return null;
  }

  if (requiresAuth && !isAuthenticated) {
    return null;
  }

  if (!requiresAuth && isAuthenticated) {
    return null;
  }

  return children;
}

type Pathname = '/' | '/login' | '/dashboard';

function getRoute(pathname: string): Pathname {
  if (pathname === '/dashboard') return '/dashboard';
  if (pathname === '/login') return '/login';
  return '/';
}

function AppContent() {
  const path = getRoute(window.location.pathname);

  switch (path) {
    case '/login':
      return (
        <RouteGuard requiresAuth={false} redirectTo="/dashboard">
          <Login />
        </RouteGuard>
      );
    case '/dashboard':
    case '/':
      return (
        <RouteGuard requiresAuth={true} redirectTo="/login">
          <Dashboard />
        </RouteGuard>
      );
    default:
      return (
        <RouteGuard requiresAuth={true} redirectTo="/login">
          <Dashboard />
        </RouteGuard>
      );
  }
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
