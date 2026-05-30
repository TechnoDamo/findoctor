import { useMutation, useQuery } from '@tanstack/react-query';
import apiClient from '../client';
import { getStoredUser, useAuthStore } from '@/lib/auth/auth-store';
import { AuthResponse, LoginRequest, RegisterRequest, User } from '../types';

function toRegisterPayload(registerData: RegisterRequest) {
  return {
    email: registerData.email,
    password: registerData.password,
    phone: registerData.phone || null,
    first_name: registerData.firstName || null,
    last_name: registerData.lastName || null,
    country: registerData.country || null,
    base_currency: registerData.baseCurrency,
    timezone: registerData.timezone,
  };
}

export function useLogin() {
  const setTokens = useAuthStore((state) => state.setTokens);
  const setCredentials = useAuthStore((state) => state.setCredentials);
  const setUser = useAuthStore((state) => state.setUser);
  let submittedPassword = '';

  return useMutation<AuthResponse, Error, LoginRequest>({
    mutationFn: async (loginData) => {
      submittedPassword = loginData.password;
      const response = await apiClient.post<AuthResponse>('/auth/login', loginData);
      return response.data;
    },
    onSuccess: (session) => {
      setCredentials(session.user.email, submittedPassword);
      setTokens(session.access_token, session.refresh_token);
      setUser(session.user);
    },
  });
}

export function useRegister() {
  const setTokens = useAuthStore((state) => state.setTokens);
  const setCredentials = useAuthStore((state) => state.setCredentials);
  const setUser = useAuthStore((state) => state.setUser);
  let submittedPassword = '';

  return useMutation<AuthResponse, Error, RegisterRequest>({
    mutationFn: async (registerData) => {
      submittedPassword = registerData.password;
      const response = await apiClient.post<AuthResponse>('/auth/register', toRegisterPayload(registerData));
      return response.data;
    },
    onSuccess: (session) => {
      setCredentials(session.user.email, submittedPassword);
      setTokens(session.access_token, session.refresh_token);
      setUser(session.user);
    },
  });
}

export function useLogout() {
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return useMutation<void, Error>({
    mutationFn: async () => {
      try {
        await apiClient.post('/auth/logout');
      } catch {
        // Simple auth logout is local-only; backend logout may be a no-op/fail if no bearer session exists.
      }
    },
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
      const response = await apiClient.get<User>('/me');
      setUser(response.data || storedUser);
      return response.data || storedUser;
    },
    enabled,
    retry: false,
  });
}
