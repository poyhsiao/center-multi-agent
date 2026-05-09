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
  const { isAuthenticated, isLoading } = useAuthContext();
  const [hasRedirected, setHasRedirected] = useState(false);

  useEffect(() => {
    // Wait for auth state to finish loading before redirecting
    if (isLoading) return;

    if (requiresAuth && !isAuthenticated && !hasRedirected) {
      window.location.href = redirectTo;
      setHasRedirected(true);
    } else if (!requiresAuth && isAuthenticated && !hasRedirected) {
      window.location.href = redirectTo;
      setHasRedirected(true);
    }
  }, [requiresAuth, isAuthenticated, hasRedirected, redirectTo, isLoading]);

  if (isLoading || hasRedirected) {
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
