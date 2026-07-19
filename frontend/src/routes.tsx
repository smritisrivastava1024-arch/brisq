import { createBrowserRouter, Navigate } from 'react-router-dom';
import { DevComponents } from './components/DevComponents';
import { DevApi } from './components/DevApi';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/owner/LoginPage';
import { OwnerLayout } from './pages/owner/OwnerLayout';
import { CustomerChatPage } from './pages/CustomerChatPage';
import { ApprovalsPage } from './pages/owner/ApprovalsPage';
import { OwnerChatPage } from './pages/owner/OwnerChatPage';
import { AbandonedCartsPage } from './pages/owner/AbandonedCartsPage';

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
          { path: 'approvals',       element: <ApprovalsPage /> },
          { path: 'chat',            element: <OwnerChatPage /> },
          { path: 'abandoned-carts', element: <AbandonedCartsPage /> },
        ],
      },
    ],
  },

  // Dev routes — remove before production
  { path: '/dev/components', element: <DevComponents /> },
  { path: '/dev/api',        element: <DevApi /> },
]);
