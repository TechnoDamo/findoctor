import { create } from 'zustand';

export const ACCESS_TOKEN_KEY = process.env.NEXT_PUBLIC_ACCESS_TOKEN_KEY || 'access_token';
export const REFRESH_TOKEN_KEY = process.env.NEXT_PUBLIC_REFRESH_TOKEN_KEY || 'refresh_token';

export function getStoredAccessToken() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredRefreshToken() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function storeTokens(accessToken: string, refreshToken: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearStoredAuth() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: unknown | null;
  hasHydrated: boolean;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: unknown) => void;
  hydrateFromStorage: () => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  hasHydrated: false,
  setTokens: (accessToken, refreshToken) => {
    storeTokens(accessToken, refreshToken);
    set({ accessToken, refreshToken, hasHydrated: true });
  },
  setUser: (user) => set({ user }),
  hydrateFromStorage: () =>
    set({
      accessToken: getStoredAccessToken(),
      refreshToken: getStoredRefreshToken(),
      hasHydrated: true,
    }),
  clearAuth: () => {
    clearStoredAuth();
    set({ accessToken: null, refreshToken: null, user: null, hasHydrated: true });
  },
}));
