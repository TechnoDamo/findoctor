import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';

// Asset interface (simplified based on what we know from OpenAPI)
export interface Asset {
  id: string;
  userId: string;
  assetTypeId: string;
  name: string;
  estimatedValue: string;
  currency: string;
  purchasePrice: string | null;
  purchaseDate: string | null;
  monthlyCost: string | null;
  createdAt: string;
  updatedAt: string;
}

// List assets query
export function useAssets() {
  return useQuery<Asset[]>({
    queryKey: ['assets'],
    queryFn: async () => {
      const response = await apiClient.get<Asset[]>('/assets');
      return response.data;
    },
  });
}

// Create asset mutation
export function useCreateAsset() {
  const queryClient = useQueryClient();
  
  return useMutation<Asset, Error, Partial<Asset>>({
    mutationFn: async (assetData) => {
      const response = await apiClient.post<Asset>('/assets', assetData);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch assets
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
  });
}

// Get asset query
export function useAsset(id: string) {
  return useQuery<Asset>({
    queryKey: ['assets', id],
    queryFn: async () => {
      const response = await apiClient.get<Asset>(`/assets/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}