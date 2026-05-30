import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';

// Account type interface (simplified based on what we know from OpenAPI)
export interface Account {
  id: string;
  userId: string;
  accountTypeId: string;
  institutionId: string | null;
  name: string;
  institutionName: string | null;
  currency: string;
  balance: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// List accounts query
export function useAccounts() {
  return useQuery<Account[]>({
    queryKey: ['accounts'],
    queryFn: async () => {
      const response = await apiClient.get<Account[]>('/accounts');
      return response.data;
    },
  });
}

// Create account mutation
export function useCreateAccount() {
  const queryClient = useQueryClient();
  
  return useMutation<Account, Error, Partial<Account>>({
    mutationFn: async (accountData) => {
      const response = await apiClient.post<Account>('/accounts', accountData);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch accounts
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
}

// Get account query
export function useAccount(id: string) {
  return useQuery<Account>({
    queryKey: ['accounts', id],
    queryFn: async () => {
      const response = await apiClient.get<Account>(`/accounts/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}