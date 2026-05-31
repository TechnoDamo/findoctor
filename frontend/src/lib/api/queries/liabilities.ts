import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';
import type { Liability, LiabilityList } from '../types';

export function useLiabilities() {
  return useQuery<Liability[]>({
    queryKey: ['liabilities'],
    queryFn: async () => {
      const response = await apiClient.get<LiabilityList>('/liabilities');
      return response.data.items;
    },
  });
}

export function useCreateLiability() {
  const queryClient = useQueryClient();

  return useMutation<Liability, Error, Record<string, unknown>>({
    mutationFn: async (liabilityData) => {
      const response = await apiClient.post<Liability>('/liabilities', liabilityData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['liabilities'] });
    },
  });
}

export function useLiability(id: string) {
  return useQuery<Liability>({
    queryKey: ['liabilities', id],
    queryFn: async () => {
      const response = await apiClient.get<Liability>(`/liabilities/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
