import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';
import type { Transaction, TransactionPage } from '../types';

export function useTransactions(params?: Record<string, unknown>) {
  return useQuery<TransactionPage>({
    queryKey: ['transactions', params],
    queryFn: async () => {
      const response = await apiClient.get<TransactionPage>('/transactions', { params });
      return response.data;
    },
  });
}

export function useCreateTransaction() {
  const queryClient = useQueryClient();

  return useMutation<Transaction, Error, Record<string, unknown>>({
    mutationFn: async (transactionData) => {
      const response = await apiClient.post<Transaction>('/transactions', transactionData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
}

export function useTransaction(id: string) {
  return useQuery<Transaction>({
    queryKey: ['transactions', id],
    queryFn: async () => {
      const response = await apiClient.get<Transaction>(`/transactions/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
