import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth, type Peran } from './authContext';

export function ProtectedRoute() {
  const { isAuthenticated, isInitializing } = useAuth();
  const location = useLocation();

  if (isInitializing) {
    return (
      <main>
        <p role="status">Memuat sesi…</p>
      </main>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

export interface RoleRouteProps {
  allowedRoles: readonly Peran[];
}

export function RoleRoute({ allowedRoles }: RoleRouteProps) {
  const { user, isInitializing } = useAuth();
  const location = useLocation();

  if (isInitializing) {
    return (
      <main>
        <p role="status">Memuat sesi…</p>
      </main>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!allowedRoles.includes(user.peran)) {
    return <Navigate to="/403" replace />;
  }

  return <Outlet />;
}
