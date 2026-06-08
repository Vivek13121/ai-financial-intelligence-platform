import { Link, Outlet, useLocation } from "react-router-dom";
import { LayoutDashboard, Rss, BarChart3, LineChart, Search } from "lucide-react";

export function Layout() {
  const location = useLocation();

  const navItems = [
    { name: "Overview", href: "/", icon: LayoutDashboard },
    { name: "Live Feed", href: "/feed", icon: Rss },
    { name: "Analytics", href: "/analytics", icon: BarChart3 },
    { name: "Forecasts", href: "/forecasts", icon: LineChart },
    { name: "Search", href: "/search", icon: Search },
  ];

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 glass border-r flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            FinIntel AI
          </h1>
          <p className="text-xs text-muted-foreground mt-1">Platform Dashboard</p>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  isActive 
                    ? "bg-primary/10 text-primary font-medium" 
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8 relative">
        <Outlet />
      </main>
    </div>
  );
}
