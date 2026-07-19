import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../api/auth';
import { Button } from '../../components/ui/Button';

export function OwnerLayout() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/owner/login');
  };

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `px-4 py-2.5 block rounded-md font-medium transition-colors duration-200 text-sm ${
      isActive
        ? 'bg-surface text-primary border border-[#E8E3DA] shadow-sm'
        : 'text-text-muted hover:bg-surface-lighter hover:text-text-main border border-transparent'
    }`;

  return (
    <div className="min-h-screen bg-background flex text-text-main">
      {/* Sidebar */}
      <aside className="w-64 bg-background border-r border-[#E8E3DA] flex flex-col shrink-0">
        <div className="p-6">
          <h1 className="text-xl font-bold text-primary tracking-tight">
            Brisq OS
          </h1>
        </div>
        
        <nav className="flex-1 px-4 py-4 space-y-2">
          <NavLink to="/owner/approvals" className={navClass}>
            Approvals
          </NavLink>
          <NavLink to="/owner/chat" className={navClass}>
            Agent Chat
          </NavLink>
          <NavLink to="/owner/abandoned-carts" className={navClass}>
            Abandoned Carts
          </NavLink>
        </nav>
        
        <div className="p-4 border-t border-[#E8E3DA]">
          <Button variant="ghost" onClick={handleLogout} className="w-full justify-start text-danger hover:text-danger">
            Log out
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-background">
        <Outlet />
      </main>
    </div>
  );
}
