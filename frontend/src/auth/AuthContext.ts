import { createContext, useContext } from "react";
import type { ApiError } from "../api/client";
import type { User } from "../types/api";

export interface AuthContextValue {
  user: User | null;
  /** True while a stored token is being checked with GET /auth/me. */
  isLoading: boolean;
  /** Set when the stored token could not be checked (e.g. server unreachable). */
  bootError: ApiError | null;
  retryBoot: () => void;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>");
  return value;
}
