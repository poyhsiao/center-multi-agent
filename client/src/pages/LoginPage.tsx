import { useAuthContext } from '../context/AuthContext';
import { saveAuth, AuthState } from '../lib/auth';

function navigate(path: string) {
  window.history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}

export function LoginPage() {
  const { logout } = useAuthContext();
  void logout; // unused but shows auth context is working

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // Mock login - save mock auth state so AuthContext recognizes authenticated
    const mockAuth: AuthState = {
      accessToken: 'mock-token-' + Date.now(),
      refreshToken: 'mock-refresh-' + Date.now(),
      expiresAt: Date.now() + 3600000,
    };
    saveAuth(mockAuth);
    // Force re-render by navigating
    navigate('/dashboard');
    window.location.reload();
  };

  return (
    <div className="container">
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <input name="email" type="email" placeholder="Email" required />
        <input name="password" type="password" placeholder="Password" required />
        <button type="submit">Login</button>
      </form>
    </div>
  );
}