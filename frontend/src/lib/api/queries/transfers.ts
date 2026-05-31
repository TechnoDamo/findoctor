import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';
import type { Transfer, TransferPage } from '../types';

export function useTransfers(params?: Record<string, unknown>) {
  return useQuery<TransferPage>({
    queryKey: ['transfers', params],
    queryFn: async () => {
      const response = await apiClient.get<TransferPage>('/transfers', { params });
      return response.data;
    },
  });
}

export function useCreateTransfer() {
  const queryClient = useQueryClient();

  return useMutation<Transfer, Error, Record<string, unknown>>({
    mutationFn: async (transferData) => {
      const response = await apiClient.post<Transfer>('/transfers', transferData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transfers'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
}

export function useTransfer(id: string) {
  return useQuery<Transfer>({
    queryKey: ['transfers', id],
    queryFn: async () => {
      const response = await apiClient.get<Transfer>(`/transfers/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
