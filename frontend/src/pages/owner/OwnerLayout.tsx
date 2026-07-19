import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { authStore } from '../../api/auth';
import { Button } from '../../components/ui/Button';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    to: '/owner/approvals',
    label: 'Approvals',
    icon: (
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    to: '/owner/chat',
    label: 'Chat',
    icon: (
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
  },
  {
    to: '/owner/abandoned-carts',
    label: 'Abandoned Carts',
    icon: (
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
];

export function OwnerLayout() {
  const navigate = useNavigate();

  function handleLogout() {
    authStore.clearToken();
    navigate('/owner/login', { replace: true });
  }

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Sidebar */}
      <nav className="flex flex-col w-64 shrink-0 bg-ink-navy border-r border-white/10">
        {/* Logo area */}
        <div className="px-6 py-6 border-b border-white/10">
          <span className="font-display font-semibold text-xl text-[#F3EFE4] tracking-tight">
            Brisq Ledger
          </span>
          <p className="text-xs text-[#9AA0AE] mt-1">Owner Dashboard</p>
        </div>

        {/* Nav links */}
        <div className="flex-1 px-3 py-4 flex flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-ledger text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-gold ${
                  isActive
                    ? 'bg-white/10 text-[#F3EFE4]'
                    : 'text-[#9AA0AE] hover:bg-white/5 hover:text-[#F3EFE4]'
                }`
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </div>

        {/* Logout pinned at bottom */}
        <div className="px-3 py-4 border-t border-white/10">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="w-full justify-start gap-3 text-[#9AA0AE] hover:text-[#F3EFE4] hover:bg-white/5"
          >
            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Log out
          </Button>
        </div>
      </nav>

      {/* Main content area */}
      <main className="flex-1 bg-parchment overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
