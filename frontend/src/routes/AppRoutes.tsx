import { Navigate, Route, Routes } from "react-router";
import { RequireAuth } from "../auth/RequireAuth";
import { AppShell } from "../components/AppShell";
import { LoginPage } from "./LoginPage";
import { APP_TABS, DEFAULT_PATH } from "./tabs";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          {APP_TABS.map((tab) => (
            <Route key={tab.id} path={`${tab.path}/*`} element={tab.element} />
          ))}
          <Route path="*" element={<Navigate to={DEFAULT_PATH} replace />} />
        </Route>
      </Route>
    </Routes>
  );
}
