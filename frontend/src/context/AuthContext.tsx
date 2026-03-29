import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getCurrentUser,
  login as loginRequest,
  refreshAccessToken,
  signup as signupRequest,
} from "../api/auth";
import { setAccessToken } from "../api/http";
import type {
  Company,
  LoginRequest,
  SignupRequest,
  User,
} from "../types/auth";

const ACCESS_TOKEN_KEY = "rms_access_token";
const REFRESH_TOKEN_KEY = "rms_refresh_token";

interface AuthContextValue {
  user: User | null;
  company: Company | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  signup: (payload: SignupRequest) => Promise<void>;
  logout: () => void;
  getDefaultRoute: () => string;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  const clearSession = () => {
    setToken(null);
    setUser(null);
    setCompany(null);
    setAccessToken(null);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  };

  const persistSession = (
    accessToken: string,
    refreshToken: string,
    nextUser: User,
    nextCompany: Company,
  ) => {
    setToken(accessToken);
    setUser(nextUser);
    setCompany(nextCompany);
    setAccessToken(accessToken);
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  };

  useEffect(() => {
    const bootstrapSession = async () => {
      const storedAccessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
      const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

      if (!storedAccessToken) {
        setIsLoading(false);
        return;
      }

      setToken(storedAccessToken);
      setAccessToken(storedAccessToken);

      try {
        const me = await getCurrentUser();
        setUser(me.user);
        setCompany(me.company);
      } catch {
        if (!storedRefreshToken) {
          clearSession();
          setIsLoading(false);
          return;
        }

        try {
          const refreshed = await refreshAccessToken(storedRefreshToken);
          localStorage.setItem(ACCESS_TOKEN_KEY, refreshed.access_token);
          setToken(refreshed.access_token);
          setAccessToken(refreshed.access_token);

          const me = await getCurrentUser();
          setUser(me.user);
          setCompany(me.company);
        } catch {
          clearSession();
        }
      } finally {
        setIsLoading(false);
      }
    };

    void bootstrapSession();
  }, []);

  const login = async (payload: LoginRequest) => {
    const response = await loginRequest(payload);
    persistSession(
      response.access_token,
      response.refresh_token,
      response.user,
      response.company,
    );
  };

  const signup = async (payload: SignupRequest) => {
    const response = await signupRequest(payload);
    persistSession(
      response.access_token,
      response.refresh_token,
      response.user,
      response.company,
    );
  };

  const logout = () => {
    clearSession();
  };

  const getDefaultRoute = () => {
    if (!user) {
      return "/login";
    }

    if (user.role === "ADMIN") {
      return "/admin/claims";
    }

    return "/employee/dashboard";
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      company,
      isLoading,
      isAuthenticated: Boolean(token && user),
      login,
      signup,
      logout,
      getDefaultRoute,
    }),
    [user, company, isLoading, token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
