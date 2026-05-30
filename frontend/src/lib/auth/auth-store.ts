import { create } from 'zustand';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: any | null;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: any) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
  setUser: (user) => set({ user }),
  clearAuth: () => set({ accessToken: null, refreshToken: null, user: null }),
}));