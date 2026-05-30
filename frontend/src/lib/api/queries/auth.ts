import { useMutation, useQuery } from '@tanstack/react-query';
import apiClient from '../client';
import { useAuthStore } from '@/lib/auth/auth-store';
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

// Login mutation
export function useLogin() {
  const setTokens = useAuthStore((state) => state.setTokens);
  const setUser = useAuthStore((state) => state.setUser);

  return useMutation<AuthResponse, Error, LoginRequest>({
    mutationFn: async (loginData) => {
      const response = await apiClient.post<AuthResponse>('/auth/login', loginData);
      return response.data;
    },
    onSuccess: (session) => {
      setTokens(session.access_token, session.refresh_token);
      setUser(session.user);
    },
  });
}

// Register mutation
export function useRegister() {
  const setTokens = useAuthStore((state) => state.setTokens);
  const setUser = useAuthStore((state) => state.setUser);

  return useMutation<AuthResponse, Error, RegisterRequest>({
    mutationFn: async (registerData) => {
      const response = await apiClient.post<AuthResponse>('/auth/register', toRegisterPayload(registerData));
      return response.data;
    },
    onSuccess: (session) => {
      setTokens(session.access_token, session.refresh_token);
      setUser(session.user);
    },
  });
}

// Logout function
export function useLogout() {
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return useMutation<void, Error>({
    mutationFn: async () => {
      await apiClient.post('/auth/logout');
    },
    onSettled: () => {
      clearAuth();
    },
  });
}

// Current user query
export function useCurrentUser(enabled = true) {
  const setUser = useAuthStore((state) => state.setUser);

  return useQuery<User, Error>({
    queryKey: ['user'],
    queryFn: async () => {
      const response = await apiClient.get<User>('/me');
      setUser(response.data);
      return response.data;
    },
    enabled,
    retry: false,
  });
}
