import { Outlet, Link } from "react-router-dom";
import { NavBar } from "../components/NavBar";

/**
 * CareerPilot AI - Main Application Layout
 *
 * Provides responsive shell, sticky navigation, skip link, and unified footer.
 */
export function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-700 antialiased selection:bg-blue-100 selection:text-blue-900">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <NavBar />
      <main
        id="main-content"
        className="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12"
        role="main"
      >
        <Outlet />
      </main>

      <footer className="bg-white border-t border-slate-200/80 py-8 mt-auto">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-lg bg-blue-600 flex items-center justify-center text-white text-xs font-bold shadow-2xs">
                ⚡
              </div>
              <span className="font-extrabold text-slate-900 text-sm tracking-tight">
                CareerPilot AI
              </span>
              <span className="text-xs text-slate-400">·</span>
              <span className="text-xs text-slate-500">
                Prepare smarter. Get career-ready.
              </span>
            </div>

            <div className="flex items-center gap-5 text-xs font-semibold text-slate-500">
              <Link to="/resume" className="hover:text-blue-600 transition-colors">
                Resume
              </Link>
              <Link to="/job-match" className="hover:text-blue-600 transition-colors">
                Job Match
              </Link>
              <Link to="/interview" className="hover:text-blue-600 transition-colors">
                Interview
              </Link>
              <Link to="/dashboard" className="hover:text-blue-600 transition-colors">
                Dashboard
              </Link>
              <Link to="/settings" className="hover:text-blue-600 transition-colors">
                Privacy & Data
              </Link>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-400">
            <p>© {new Date().getFullYear()} CareerPilot AI. All rights reserved.</p>
            <p>
              AI-generated insights are for guidance only and do not guarantee hiring decisions.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}