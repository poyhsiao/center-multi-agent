import { useAuthContext } from '../context/AuthContext';

function navigate(path: string) {
  window.history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}

export function DashboardPage() {
  const { auth, logout } = useAuthContext();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="container">
      <h1>Dashboard</h1>
      <p>Welcome! You are authenticated.</p>
      {auth?.accessToken && <p>Token: {auth.accessToken.substring(0, 20)}...</p>}
      <button data-testid="logout-btn" onClick={handleLogout}>Logout</button>
    </div>
  );
}