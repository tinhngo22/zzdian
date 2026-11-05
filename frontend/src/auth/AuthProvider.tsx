import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router";
import { ApiError, setUnauthorizedHandler } from "../api/client";
import { getMe, login as apiLogin } from "../api/endpoints";
import { queryKeys } from "../api/queryKeys";
import { AuthContext, type AuthContextValue } from "./AuthContext";
import { clearToken, getToken, setToken } from "./tokenStorage";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const [token, setTokenState] = useState<string | null>(getToken);

  const meQuery = useQuery({
    queryKey: queryKeys.me,
    queryFn: getMe,
    enabled: token !== null,
    staleTime: Infinity,
  });

  const signOut = useCallback(() => {
    clearToken();
    setTokenState(null);
    queryClient.clear();
  }, [queryClient]);

  const locationRef = useRef(location);
  useEffect(() => {
    locationRef.current = location;
  }, [location]);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      signOut();
      const from = locationRef.current;
      if (from.pathname !== "/login") {
        navigate("/login", { replace: true, state: { from } });
      }
    });
    return () => setUnauthorizedHandler(null);
  }, [signOut, navigate]);

  const login = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await apiLogin(email, password);
      setToken(access_token);
      queryClient.clear();
      const user = await queryClient.fetchQuery({
        queryKey: queryKeys.me,
        queryFn: getMe,
        staleTime: Infinity,
      });
      setTokenState(access_token);
      return user;
    },
    [queryClient],
  );

  const logout = useCallback(() => {
    signOut();
    navigate("/login", { replace: true });
  }, [signOut, navigate]);

  const bootError =
    token !== null && meQuery.error instanceof ApiError && meQuery.error.status !== 401
      ? meQuery.error
      : null;

  const value = useMemo<AuthContextValue>(
    () => ({
      user: token ? (meQuery.data ?? null) : null,
      isLoading: token !== null && meQuery.isPending && !meQuery.isError,
      bootError,
      retryBoot: () => void meQuery.refetch(),
      login,
      logout,
    }),
    [token, meQuery, bootError, login, logout],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}
