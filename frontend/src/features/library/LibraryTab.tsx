import { Navigate, Route, Routes } from "react-router";
import { SetDetailPage } from "./SetDetailPage";
import { SetListPage } from "./SetListPage";

export function LibraryTab() {
  return (
    <Routes>
      <Route index element={<SetListPage />} />
      <Route path=":setId" element={<SetDetailPage />} />
      <Route path="*" element={<Navigate to="/library" replace />} />
    </Routes>
  );
}
