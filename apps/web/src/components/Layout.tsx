import { Link, Outlet, useLocation } from "react-router-dom";
import { LayoutDashboard, Rss, BarChart3, Search } from "lucide-react";

export function Layout() {
  const location = useLocation();

  const navItems = [
    { name: "Overview",   href: "/",          icon: LayoutDashboard },
    { name: "Live Feed",  href: "/feed",       icon: Rss },
    { name: "Analytics",  href: "/analytics",  icon: BarChart3 },
    { name: "Search",     href: "/search",     icon: Search },
  ];

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside
        className="w-[280px] flex flex-col flex-shrink-0 z-10"
        style={{
          backgroundColor: "var(--color-surface)",
          borderRight: "1px solid var(--color-border)",
          boxShadow: "1px 0 40px rgba(0,0,0,0.3)"
        }}
      >
        {/* Brand */}
        <div className="px-7 py-8 flex-shrink-0 flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <span
              className="block w-1.5 h-5 rounded-[2px] flex-shrink-0"
              style={{
                backgroundColor: "var(--color-accent)",
                boxShadow: "0 0 12px var(--color-accent)"
              }}
            />
            <span className="text-xl font-bold tracking-tight text-foreground font-display">
              FinIntel AI
            </span>
          </div>
          <span className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] font-medium pl-4 opacity-80">
            Institutional Terminal
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-2 overflow-y-auto space-y-1">
          <div className="px-3 mb-4">
            <span className="label-section opacity-70">Platform</span>
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 relative group ${
                  isActive
                    ? "bg-[rgba(91,141,239,0.08)] text-[var(--color-accent)]"
                    : "text-muted-foreground hover:bg-[rgba(255,255,255,0.04)] hover:text-foreground"
                }`}
              >
                {isActive && (
                  <div
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[55%] rounded-r"
                    style={{
                      backgroundColor: "var(--color-accent)",
                      boxShadow: "0 0 10px var(--color-accent)"
                    }}
                  />
                )}
                <Icon
                  className={`w-4 h-4 flex-shrink-0 transition-colors duration-200 ${
                    isActive ? "text-[var(--color-accent)]" : "text-muted-foreground group-hover:text-foreground"
                  }`}
                />
                <span className="tracking-[0.01em]">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* System status footer */}
        <div className="p-6 mt-auto">
          <div
            className="rounded-lg p-4 flex items-center justify-between"
            style={{
              backgroundColor: "rgba(0,0,0,0.25)",
              border: "1px solid rgba(255,255,255,0.04)"
            }}
          >
            <div className="flex flex-col gap-1.5">
              <span className="label-section">System Status</span>
              <span className="text-xs font-medium text-foreground tracking-wide opacity-90">
                Online & Synced
              </span>
            </div>
            <span className="relative flex h-2 w-2">
              <span
                className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-50"
                style={{ backgroundColor: "var(--color-positive)" }}
              />
              <span
                className="relative inline-flex rounded-full h-2 w-2"
                style={{ backgroundColor: "var(--color-positive)" }}
              />
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto p-8 relative">
        <Outlet />
      </main>
    </div>
  );
}
