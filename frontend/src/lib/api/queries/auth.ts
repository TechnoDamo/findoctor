import { useMutation, useQuery } from '@tanstack/react-query';
import apiClient from '../client';
import { AuthResponse, LoginRequest, RegisterRequest } from '../types';

// Login mutation
export function useLogin() {
  return useMutation<AuthResponse, Error, LoginRequest>({
    mutationFn: async (loginData) => {
      const response = await apiClient.post<AuthResponse>('/auth/login', loginData);
      return response.data;
    },
  });
}

// Register mutation
export function useRegister() {
  return useMutation<AuthResponse, Error, RegisterRequest>({
    mutationFn: async (registerData) => {
      const response = await apiClient.post<AuthResponse>('/auth/register', registerData);
      return response.data;
    },
  });
}

// Logout function
export function useLogout() {
  return useMutation<void, Error>({
    mutationFn: async () => {
      // In a real app, we'd make a call to logout endpoint here
      localStorage.removeItem('access_token');
    },
  });
}

// Current user query
export function useCurrentUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      // In a real app, we'd make a call to get current user endpoint here
      return null;
    },
    enabled: false, // We'll enable this when we have a token
  });
}