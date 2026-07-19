import { Navigate, Outlet } from 'react-router-dom';
import { useAuthToken } from '../api/auth';

export function ProtectedRoute() {
  const token = useAuthToken();

  if (!token) {
    return <Navigate to="/owner/login" replace />;
  }

  return <Outlet />;
}
