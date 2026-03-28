import { Link, useLocation } from "react-router-dom";
import { useStore } from "../store/useStore";

const NAV_ITEMS = [
  { path: "/", label: "Home" },
  { path: "/history", label: "History" },
  { path: "/analytics", label: "Analytics" },
  { path: "/settings", label: "Settings" },
];

export default function Navbar() {
  const location = useLocation();
  const { auth, logout } = useStore();

  return (
    <nav className="bg-gray-900 border-b border-gray-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold">
              TL
            </div>
            <span className="text-lg font-bold tracking-tight">TruthLens</span>
          </div>

          {/* Navigation links */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  location.pathname === item.path
                    ? "bg-blue-600 text-white"
                    : "text-gray-400 hover:text-white hover:bg-gray-800"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* Auth */}
          <div className="flex items-center gap-3">
            {auth.token ? (
              <button
                onClick={logout}
                className="text-sm text-gray-400 hover:text-white transition-colors"
              >
                Logout
              </button>
            ) : (
              <span className="text-sm text-gray-500">Not logged in</span>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
