import type { ReactNode } from "react";
import { LibraryTab } from "../features/library/LibraryTab";

export interface AppTab {
  id: string;
  label: string;
  /** Top-level path; the tab owns every route below it (e.g. /library/:setId). */
  path: string;
  element: ReactNode;
}

// Adding a tab = adding one entry here plus its page component.
export const APP_TABS: AppTab[] = [
  { id: "library", label: "Library", path: "/library", element: <LibraryTab /> },
];

export const DEFAULT_PATH = APP_TABS[0].path;
