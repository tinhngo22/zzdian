import { NavLink, Outlet } from "react-router";
import { useAuth } from "../auth/AuthContext";
import { APP_TABS } from "../routes/tabs";
import { Button } from "./Button";

export function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="sticky top-0 z-10 border-b border-stone-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-8 px-8 max-md:h-14 max-md:gap-4 max-md:px-4">
          <span className="font-cjk text-xl font-bold text-red-800" lang="zh-Hans">
            汉字
          </span>
          <nav aria-label="Main" className="flex h-full gap-1">
            {APP_TABS.map((tab) => (
              <NavLink
                key={tab.id}
                to={tab.path}
                className={({ isActive }) =>
                  `flex items-center border-b-2 px-3 text-sm font-medium focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-red-700 ${
                    isActive
                      ? "border-red-700 text-red-800"
                      : "border-transparent text-stone-600 hover:text-stone-900"
                  }`
                }
              >
                {tab.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-sm text-stone-600 max-md:hidden" title={user?.email}>
              {user?.email}
            </span>
            <Button variant="secondary" size="sm" onClick={logout}>
              Log out
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-8 py-8 max-md:px-4 max-md:py-5">
        <Outlet />
      </main>
    </div>
  );
}
