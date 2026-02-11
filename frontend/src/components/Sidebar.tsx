import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/', label: 'Stores', exact: true },
  { to: '/observability', label: 'Observability' },
  { to: '/audit-logs', label: 'Audit Logs' },
];

export function Sidebar() {
  return (
    <aside className="w-64 border-r bg-card flex flex-col">
      <div className="h-16 flex items-center px-6 border-b">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-black text-white flex items-center justify-center text-sm font-semibold">
            U
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm">Urumi Cloud</span>
            <span className="text-xs text-muted-foreground">Multi-tenant WooCommerce</span>
          </div>
        </div>
      </div>

      <div className="px-6 py-4 text-xs font-semibold text-muted-foreground tracking-wide">
        MENU
      </div>

      <nav className="flex-1 px-2 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.exact}
            className={({ isActive }) =>
              cn(
                'flex items-center px-4 py-2 text-sm rounded-md hover:bg-muted hover:text-foreground transition-colors',
                isActive && 'bg-muted text-foreground font-medium'
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

