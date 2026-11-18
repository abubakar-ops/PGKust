import {
  createContext, useContext, useState, useEffect, useCallback,
  type ReactNode,
} from "react";
import { login as apiLogin, logout as apiLogout, getMe } from "../api/auth";
import { clearAuthTokens } from "../api/client";
import type { AuthUser } from "../types";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!localStorage.getItem("access")) { setLoading(false); return; }
    try {
      const { data } = await getMe();
      setUser(data);
    } catch {
      clearAuthTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadUser(); }, [loadUser]);

  const login = async (email: string, password: string): Promise<AuthUser> => {
    const { data } = await apiLogin(email, password);
    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);
    try {
      const me = await getMe();
      setUser(me.data);
      return me.data;
    } catch (error) {
      clearAuthTokens();
      setUser(null);
      throw error;
    }
  };

  const logout = async () => {
    try { await apiLogout(localStorage.getItem("refresh") ?? ""); } catch { /* noop */ }
    clearAuthTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, loadUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
