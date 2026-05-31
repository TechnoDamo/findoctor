import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';
import type { FinancialGoal, FinancialGoalList } from '../types';

export function useGoals() {
  return useQuery<FinancialGoal[]>({
    queryKey: ['goals'],
    queryFn: async () => {
      const response = await apiClient.get<FinancialGoalList>('/goals');
      return response.data.items;
    },
  });
}

export function useCreateGoal() {
  const queryClient = useQueryClient();

  return useMutation<FinancialGoal, Error, Record<string, unknown>>({
    mutationFn: async (goalData) => {
      const response = await apiClient.post<FinancialGoal>('/goals', goalData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] });
    },
  });
}

export function useGoal(id: string) {
  return useQuery<FinancialGoal>({
    queryKey: ['goals', id],
    queryFn: async () => {
      const response = await apiClient.get<FinancialGoal>(`/goals/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
