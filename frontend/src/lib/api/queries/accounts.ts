import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';
import type { Account, AccountList } from '../types';

export function useAccounts() {
  return useQuery<Account[]>({
    queryKey: ['accounts'],
    queryFn: async () => {
      const response = await apiClient.get<AccountList>('/accounts');
      return response.data.items;
    },
  });
}

export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation<Account, Error, Record<string, unknown>>({
    mutationFn: async (accountData) => {
      const response = await apiClient.post<Account>('/accounts', accountData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
}

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
