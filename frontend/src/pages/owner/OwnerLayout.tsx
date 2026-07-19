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
    `px-4 py-3 block rounded-xl font-medium transition-all duration-200 ${
      isActive
        ? 'bg-primary/20 text-primary shadow-[inset_4px_0_0_#8B5CF6]'
        : 'text-text-muted hover:bg-white/5 hover:text-text-main'
    }`;

  return (
    <div className="min-h-screen bg-background flex text-text-main">
      {/* Sidebar - Glassmorphic */}
      <aside className="w-64 bg-surface/50 border-r border-white/10 flex flex-col backdrop-blur-xl shrink-0">
        <div className="p-6">
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
            Brisq OS
          </h1>
        </div>
        
        <nav className="flex-1 px-3 py-4 space-y-1">
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
        
        <div className="p-4 border-t border-white/10">
          <Button variant="ghost" onClick={handleLogout} className="w-full justify-start text-danger hover:text-danger hover:bg-danger/10">
            Log out
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-background/50">
        <Outlet />
      </main>
    </div>
  );
}
