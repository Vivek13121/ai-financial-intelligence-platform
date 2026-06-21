import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { LayoutDashboard, Rss, BarChart3, Search, Menu, X } from "lucide-react";

export function Layout() {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { name: "Overview",   href: "/",          icon: LayoutDashboard },
    { name: "Live Feed",  href: "/feed",       icon: Rss },
    { name: "Analytics",  href: "/analytics",  icon: BarChart3 },
    { name: "Search",     href: "/search",     icon: Search },
  ];

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden flex-col lg:flex-row">
      {/* ── Mobile Header ──────────────────────────────────────────────── */}
      <header 
        className="lg:hidden flex items-center justify-between px-4 py-3 border-b z-20 flex-shrink-0" 
        style={{ borderColor: "var(--color-border)", backgroundColor: "var(--color-surface)" }}
      >
        <div className="flex items-center gap-2.5">
          <span
            className="block w-1 h-5 rounded-[2px] flex-shrink-0"
            style={{
              backgroundColor: "var(--color-accent)",
              boxShadow: "0 0 10px var(--color-accent)"
            }}
          />
          <span className="text-xl font-bold tracking-tight text-foreground font-display">
            FinIntel
          </span>
        </div>
        <button 
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} 
          className="p-1.5 text-muted-foreground hover:text-foreground focus:outline-none rounded-md"
        >
          {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </header>

      {/* ── Mobile Overlay ─────────────────────────────────────────────── */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[260px] transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 flex flex-col flex-shrink-0 ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{
          backgroundColor: "var(--color-surface)",
          borderRight: "1px solid var(--color-border)",
          boxShadow: "1px 0 40px rgba(0,0,0,0.3)"
        }}
      >
        {/* Mobile Sidebar Header */}
        <div className="flex lg:hidden px-5 py-4 items-center justify-between border-b" style={{ borderColor: "var(--color-border)" }}>
          <div className="flex items-center gap-2">
            <span className="block w-1 h-4 rounded-[2px] flex-shrink-0" style={{ backgroundColor: "var(--color-accent)", boxShadow: "0 0 10px var(--color-accent)" }} />
            <span className="text-lg font-bold tracking-tight text-foreground font-display">FinIntel</span>
          </div>
          <button onClick={() => setIsMobileMenuOpen(false)} className="text-muted-foreground hover:text-foreground p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Desktop Brand */}
        <div className="hidden lg:flex px-6 py-7 flex-shrink-0 flex-col gap-1.5">
          <div className="flex items-center gap-2.5">
            <span
              className="block w-1 h-5 rounded-[2px] flex-shrink-0"
              style={{
                backgroundColor: "var(--color-accent)",
                boxShadow: "0 0 10px var(--color-accent)"
              }}
            />
            <span className="text-xl font-bold tracking-tight text-foreground font-display">
              FinIntel
            </span>
          </div>
          <span className="text-[9px] text-muted-foreground uppercase tracking-[0.2em] font-medium pl-[14px] opacity-70">
            Institutional Terminal
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 lg:py-0 overflow-y-auto space-y-0.5">
          <div className="px-3 mb-3 mt-2 lg:mt-0">
            <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-muted-foreground opacity-60">Platform</span>
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={() => setIsMobileMenuOpen(false)}
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
        <div className="p-4 mt-auto">
          <div className="rounded-lg p-3 flex items-center justify-between bg-[rgba(255,255,255,0.02)]">
            <div className="flex flex-col gap-0.5">
              <span className="text-[9px] font-bold tracking-[0.1em] uppercase text-muted-foreground opacity-70">System Status</span>
              <span className="text-[11px] font-bold text-foreground">
                Online & Synced
              </span>
            </div>
            <span className="relative flex h-1.5 w-1.5 mr-1">
              <span
                className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-50"
                style={{ backgroundColor: "var(--color-positive)" }}
              />
              <span
                className="relative inline-flex rounded-full h-1.5 w-1.5"
                style={{ backgroundColor: "var(--color-positive)" }}
              />
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6 lg:p-8 relative w-full">
        <Outlet />
      </main>
    </div>
  );
}
