import { create } from 'zustand';

export const ACCESS_TOKEN_KEY = process.env.NEXT_PUBLIC_ACCESS_TOKEN_KEY || 'access_token';
export const REFRESH_TOKEN_KEY = process.env.NEXT_PUBLIC_REFRESH_TOKEN_KEY || 'refresh_token';
export const USER_KEY = process.env.NEXT_PUBLIC_USER_KEY || 'findoctor_user';
export const EMAIL_KEY = process.env.NEXT_PUBLIC_EMAIL_KEY || 'findoctor_email';
export const PASSWORD_KEY = process.env.NEXT_PUBLIC_PASSWORD_KEY || 'findoctor_password';

export type StoredUser = {
  id: string;
  email: string;
  phone?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  country?: string | null;
  base_currency: string;
  timezone: string;
  created_at: string;
  updated_at: string;
};

export function getStoredAccessToken() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredRefreshToken() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getStoredEmail() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(EMAIL_KEY);
}

export function getStoredPassword() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(PASSWORD_KEY);
}

export function getStoredUser() {
  if (typeof window === 'undefined') return null;
  const value = localStorage.getItem(USER_KEY);
  if (!value) return null;

  try {
    return JSON.parse(value) as StoredUser;
  } catch {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

export function storeTokens(accessToken: string, refreshToken: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function storeUser(user: StoredUser) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function storeCredentials(email: string, password: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(EMAIL_KEY, email);
  localStorage.setItem(PASSWORD_KEY, password);
}

export function clearStoredAuth() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(EMAIL_KEY);
  localStorage.removeItem(PASSWORD_KEY);
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  email: string | null;
  password: string | null;
  user: StoredUser | null;
  hasHydrated: boolean;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setCredentials: (email: string, password: string) => void;
  setUser: (user: StoredUser | null) => void;
  hydrateFromStorage: () => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  accessToken: null,
  refreshToken: null,
  email: null,
  password: null,
  user: null,
  hasHydrated: false,
  setTokens: (accessToken, refreshToken) => {
    storeTokens(accessToken, refreshToken);
    set({ accessToken, refreshToken, hasHydrated: true });
  },
  setCredentials: (email, password) => {
    storeCredentials(email, password);
    set({ email, password, hasHydrated: true });
  },
  setUser: (user) => {
    if (user) storeUser(user);
    set({ user });
  },
  hydrateFromStorage: () =>
    set({
      accessToken: getStoredAccessToken(),
      refreshToken: getStoredRefreshToken(),
      email: getStoredEmail(),
      password: getStoredPassword(),
      user: getStoredUser(),
      hasHydrated: true,
    }),
  clearAuth: () => {
    clearStoredAuth();
    set({
      accessToken: null,
      refreshToken: null,
      email: null,
      password: null,
      user: null,
      hasHydrated: true,
    });
  },
}));
