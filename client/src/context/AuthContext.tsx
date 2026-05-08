import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getStoredAuth, clearAuth, AuthState } from '../lib/auth';

export interface AuthContextType {
  auth: AuthState | null;
  isAuthenticated: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState | null>(null);

  useEffect(() => {
    // Restore auth state from localStorage on mount
    const stored = getStoredAuth();
    if (stored) {
      setAuth(stored);
    }
  }, []);

  const logout = () => {
    clearAuth();
    setAuth(null);
  };

  return (
    <AuthContext.Provider value={{ auth, isAuthenticated: !!auth?.accessToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider');
  return ctx;
}