import { Navigate, Outlet, useLocation } from 'react-router';
import { Spinner } from '@/components/ui';
import { useAuth, type Peran } from './authContext';

function LayarMemuatSesi() {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-canvas px-4">
      <div className="flex flex-col items-center gap-3 text-center">
        <Spinner size="lg" label="Memuat…" className="text-brand" />
        <p className="text-sm font-medium text-ink-secondary">Memuat…</p>
      </div>
    </main>
  );
}

export function ProtectedRoute() {
  const { isAuthenticated, isInitializing } = useAuth();
  const location = useLocation();

  if (isInitializing) {
    return <LayarMemuatSesi />;
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
    return <LayarMemuatSesi />;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!allowedRoles.includes(user.peran)) {
    return <Navigate to="/403" replace />;
  }

  return <Outlet />;
}
