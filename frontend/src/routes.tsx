import { createBrowserRouter, Outlet } from 'react-router-dom';

function CustomerChat() {
  return (
    <div className="bg-ink-navy text-parchment font-display p-8 min-h-screen">
      <h1>Customer Chat (Placeholder)</h1>
      <p className="font-body text-parchment-dim mt-4">Tailwind theme and fonts are working!</p>
    </div>
  );
}

function DashboardLayout() {
  return (
    <div className="flex h-screen w-full">
      <nav className="w-64 bg-ink-navy text-white p-4">
        <h2 className="font-display font-semibold">Dashboard Nav</h2>
      </nav>
      <main className="flex-1 bg-parchment p-8">
        <Outlet />
      </main>
    </div>
  );
}

function Approvals() {
  return <div>Approvals View</div>;
}

function DashboardChat() {
  return <div>Owner Chat View</div>;
}

function AbandonedCarts() {
  return <div>Abandoned Carts View</div>;
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <CustomerChat />,
  },
  {
    path: '/owner',
    element: <DashboardLayout />,
    children: [
      {
        path: 'approvals',
        element: <Approvals />,
      },
      {
        path: 'chat',
        element: <DashboardChat />,
      },
      {
        path: 'abandoned-carts',
        element: <AbandonedCarts />,
      }
    ]
  }
]);
