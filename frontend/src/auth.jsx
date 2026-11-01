import { createContext, useContext, useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { api } from './api';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadUser() {
    setLoading(true);
    setError('');
    if (!sessionStorage.getItem('access')) { setLoading(false); return; }
    try { setUser(await api('/auth/me')); }
    catch (err) { if (err.status !== 401) setError(err.message); }
    finally { setLoading(false); }
  }
  useEffect(() => {
    loadUser();
    const expired = () => setUser(null);
    window.addEventListener('auth-expired', expired);
    return () => window.removeEventListener('auth-expired', expired);
  }, []);

  async function login(values) {
    const result = await api('/auth/login', { method: 'POST', body: values });
    sessionStorage.setItem('access', result.access);
    setUser(result.user);
  }
  async function logout() {
    await api('/auth/logout', { method: 'POST' });
    sessionStorage.removeItem('access');
    setUser(null);
  }
  if (loading) return <div className="status" role="status">Загрузка…</div>;
  if (error) return <div className="status"><p role="alert">{error}</p><button onClick={loadUser}>Повторить</button></div>;
  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>;
}

export function ProtectedRoute({ children, admin = false }) {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) return <Navigate to="/login" state={{ from: location.pathname + location.search }} replace />;
  if (admin && user.role !== 'admin') return <div className="empty"><h1>Нет доступа</h1><p>Фильмы добавляет и редактирует администратор.</p></div>;
  return children;
}
