import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const navItems = [
  { path: "/", label: "Home" },
  { path: "/resume", label: "Resume" },
  { path: "/job-match", label: "Job Match" },
  { path: "/interview", label: "Interview" },
  { path: "/improve", label: "Improve" },
  { path: "/dashboard", label: "Dashboard" },
];

/**
 * Modern, accessible SaaS navigation bar with desktop pills and mobile drawer.
 */
export function NavBar() {
  const location = useLocation();
  const { user, signOut } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Handle escape key to close mobile menu
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileMenuOpen]);

  // User display initial
  const userInitial = (user?.email || user?.userId || "U")
    .charAt(0)
    .toUpperCase();

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200/80 transition-shadow">
      <nav className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8" aria-label="Main navigation">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <Link
            to="/"
            className="flex items-center gap-2.5 font-bold text-lg text-slate-900 hover:opacity-90 transition-opacity focus-visible:ring-2 focus-visible:ring-blue-500 rounded-lg p-1"
          >
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-xs">
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="tracking-tight text-slate-900 font-extrabold">CareerPilot</span>
              <span className="text-[11px] font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200/60">
                AI
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <ul className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all duration-150 ${
                      isActive
                        ? "bg-blue-50 text-blue-700 shadow-2xs"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/60"
                    }`}
                    aria-current={isActive ? "page" : undefined}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>

          {/* Desktop User / Auth Area */}
          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-2.5">
                <Link
                  to="/settings"
                  title="Account Settings"
                  className="flex items-center gap-2 pl-2 pr-3 py-1 rounded-full border border-slate-200/80 bg-slate-50/70 hover:bg-slate-100/80 transition-colors focus-visible:ring-2 focus-visible:ring-blue-500"
                >
                  <div className="w-6 h-6 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center">
                    {userInitial}
                  </div>
                  <span className="text-xs font-semibold text-slate-700 max-w-[9rem] truncate">
                    {user.email || user.userId}
                  </span>
                </Link>

                <button
                  type="button"
                  onClick={signOut}
                  className="text-xs font-semibold text-slate-500 hover:text-slate-900 px-2.5 py-1.5 rounded-lg hover:bg-slate-100/80 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                >
                  Sign out
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="inline-flex items-center justify-center px-4 py-1.5 text-sm font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 shadow-xs transition-colors focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                Sign in
              </Link>
            )}
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden py-3 border-t border-slate-200/80 animate-in fade-in slide-in-from-top-2 duration-150">
            <ul className="space-y-1 pb-3">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      className={`flex items-center px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                        isActive
                          ? "bg-blue-50 text-blue-700 font-bold"
                          : "text-slate-700 hover:bg-slate-100"
                      }`}
                      aria-current={isActive ? "page" : undefined}
                    >
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>

            <div className="pt-3 border-t border-slate-200/80 flex items-center justify-between px-2">
              {user ? (
                <div className="flex items-center justify-between w-full">
                  <Link
                    to="/settings"
                    className="flex items-center gap-2 text-xs font-semibold text-slate-700 truncate"
                  >
                    <div className="w-7 h-7 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center">
                      {userInitial}
                    </div>
                    <span className="truncate max-w-[12rem]">{user.email || user.userId}</span>
                  </Link>
                  <button
                    type="button"
                    onClick={signOut}
                    className="text-xs font-semibold text-red-600 hover:text-red-700 px-3 py-1.5 rounded-lg bg-red-50 hover:bg-red-100"
                  >
                    Sign out
                  </button>
                </div>
              ) : (
                <Link
                  to="/login"
                  className="w-full text-center py-2.5 text-sm font-semibold rounded-xl bg-blue-600 text-white hover:bg-blue-700 shadow-xs"
                >
                  Sign in
                </Link>
              )}
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}