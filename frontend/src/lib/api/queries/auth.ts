import { useMutation, useQuery } from '@tanstack/react-query';
import { StoredUser, getStoredUser, useAuthStore } from '@/lib/auth/auth-store';
import { AuthResponse, LoginRequest, RegisterRequest, User } from '../types';

function localSession(user: StoredUser): AuthResponse {
  return {
    access_token: `local-access-${Date.now()}`,
    refresh_token: `local-refresh-${Date.now()}`,
    token_type: 'Bearer',
    expires_in: 86400,
    user,
  };
}

export function useLogin() {
  const setTokens = useAuthStore((state) => state.setTokens);
  const setUser = useAuthStore((state) => state.setUser);

  return useMutation<AuthResponse, Error, LoginRequest>({
    mutationFn: async (loginData) => {
      const now = new Date().toISOString();
      return localSession({
        id: 'local-user',
        email: loginData.email,
        first_name: null,
        last_name: null,
        phone: null,
        country: process.env.NEXT_PUBLIC_DEFAULT_COUNTRY || 'RU',
        base_currency: process.env.NEXT_PUBLIC_DEFAULT_CURRENCY || 'RUB',
        timezone: process.env.NEXT_PUBLIC_DEFAULT_TIMEZONE || 'Europe/Moscow',
        created_at: now,
        updated_at: now,
      });
    },
    onSuccess: (session) => {
      setTokens(session.access_token, session.refresh_token);
      setUser(session.user);
    },
  });
}

export function useRegister() {
  const setTokens = useAuthStore((state) => state.setTokens);
  const setUser = useAuthStore((state) => state.setUser);

  return useMutation<AuthResponse, Error, RegisterRequest>({
    mutationFn: async (registerData) => {
      const now = new Date().toISOString();
      return localSession({
        id: 'local-user',
        email: registerData.email,
        first_name: registerData.firstName || null,
        last_name: registerData.lastName || null,
        phone: registerData.phone || null,
        country: registerData.country || process.env.NEXT_PUBLIC_DEFAULT_COUNTRY || 'RU',
        base_currency: registerData.baseCurrency,
        timezone: registerData.timezone,
        created_at: now,
        updated_at: now,
      });
    },
    onSuccess: (session) => {
      setTokens(session.access_token, session.refresh_token);
      setUser(session.user);
    },
  });
}

export function useLogout() {
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return useMutation<void, Error>({
    mutationFn: async () => undefined,
    onSettled: () => {
      clearAuth();
    },
  });
}

export function useCurrentUser(enabled = true) {
  const setUser = useAuthStore((state) => state.setUser);
  const user = useAuthStore((state) => state.user);

  return useQuery<User, Error>({
    queryKey: ['user'],
    queryFn: async () => {
      const storedUser = user || getStoredUser();
      if (!storedUser) throw new Error('No local user');
      setUser(storedUser);
      return storedUser;
    },
    enabled,
    retry: false,
  });
}
