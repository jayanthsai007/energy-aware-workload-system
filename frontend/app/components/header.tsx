import { Link, useLocation } from "react-router";
import { Brain, BarChart3, Gauge } from "lucide-react";

export function Header() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 font-bold text-lg">
            <Brain className="h-6 w-6 text-blue-500" />
            <span>Energy Aware</span>
          </Link>

          {/* Navigation */}
          <nav className="flex gap-1">
            <Link
              to="/"
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive("/") && location.pathname === "/"
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/50"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              <Gauge className="h-4 w-4" />
              Nodes
            </Link>

            <Link
              to="/metrics"
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive("/metrics")
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/50"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              <BarChart3 className="h-4 w-4" />
              Metrics
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
