import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';

// Financial Goal interface (simplified based on what we know from OpenAPI)
export interface FinancialGoal {
  id: string;
  userId: string;
  name: string;
  targetAmount: string;
  currentAmount: string;
  deadline: string | null;
  priority: number | null;
  createdAt: string;
  updatedAt: string;
}

// List goals query
export function useGoals() {
  return useQuery<FinancialGoal[]>({
    queryKey: ['goals'],
    queryFn: async () => {
      const response = await apiClient.get<FinancialGoal[]>('/goals');
      return response.data;
    },
  });
}

// Create goal mutation
export function useCreateGoal() {
  const queryClient = useQueryClient();
  
  return useMutation<FinancialGoal, Error, Partial<FinancialGoal>>({
    mutationFn: async (goalData) => {
      const response = await apiClient.post<FinancialGoal>('/goals', goalData);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch goals
      queryClient.invalidateQueries({ queryKey: ['goals'] });
    },
  });
}

// Get goal query
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