import { createBrowserRouter, Navigate } from 'react-router-dom';
import { DevComponents } from './components/DevComponents';
import { DevApi } from './components/DevApi';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/owner/LoginPage';
import { OwnerLayout } from './pages/owner/OwnerLayout';
import { CustomerChatPage } from './pages/CustomerChatPage';
import { ApprovalsPage } from './pages/owner/ApprovalsPage';

// ---------------------------------------------------------------------------
// Placeholder pages for owner sub-routes
// ---------------------------------------------------------------------------
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="p-10">
      <h1 className="font-display font-semibold text-3xl text-ink-navy">{title}</h1>
      <p className="mt-3 text-sm text-[#6B6455]">This page is under construction.</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------
export const router = createBrowserRouter([
  // Customer-facing chat
  {
    path: '/',
    element: <CustomerChatPage />,
  },

  // Owner login — public
  {
    path: '/owner/login',
    element: <LoginPage />,
  },

  // Protected owner shell
  {
    path: '/owner',
    element: <ProtectedRoute />,
    children: [
      {
        element: <OwnerLayout />,
        children: [
          // Default redirect: /owner → /owner/approvals
          { index: true, element: <Navigate to="approvals" replace /> },
          { path: 'approvals',      element: <ApprovalsPage /> },
          { path: 'chat',           element: <PlaceholderPage title="Chat" /> },
          { path: 'abandoned-carts', element: <PlaceholderPage title="Abandoned Carts" /> },
        ],
      },
    ],
  },

  // Dev routes — remove before production
  { path: '/dev/components', element: <DevComponents /> },
  { path: '/dev/api',        element: <DevApi /> },
]);
