import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';

// Liability interface (simplified based on what we know from OpenAPI)
export interface Liability {
  id: string;
  userId: string;
  liabilityTypeId: string;
  linkedAccountId: string | null;
  collateralAssetId: string | null;
  name: string;
  creditorInstitutionId: string | null;
  creditorName: string | null;
  originalAmount: string | null;
  currentBalance: string;
  currency: string;
  interestRate: number | null;
  interestType: string | null;
  minimumPaymentAmount: string | null;
  regularPaymentAmount: string | null;
  paymentDueDay: number | null;
  startDate: string | null;
  maturityDate: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
}

// List liabilities query
export function useLiabilities() {
  return useQuery<Liability[]>({
    queryKey: ['liabilities'],
    queryFn: async () => {
      const response = await apiClient.get<Liability[]>('/liabilities');
      return response.data;
    },
  });
}

// Create liability mutation
export function useCreateLiability() {
  const queryClient = useQueryClient();
  
  return useMutation<Liability, Error, Partial<Liability>>({
    mutationFn: async (liabilityData) => {
      const response = await apiClient.post<Liability>('/liabilities', liabilityData);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch liabilities
      queryClient.invalidateQueries({ queryKey: ['liabilities'] });
    },
  });
}

// Get liability query
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