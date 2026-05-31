import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';
import type { Asset, AssetList } from '../types';

export function useAssets() {
  return useQuery<Asset[]>({
    queryKey: ['assets'],
    queryFn: async () => {
      const response = await apiClient.get<AssetList>('/assets');
      return response.data.items;
    },
  });
}

export function useCreateAsset() {
  const queryClient = useQueryClient();

  return useMutation<Asset, Error, Record<string, unknown>>({
    mutationFn: async (assetData) => {
      const response = await apiClient.post<Asset>('/assets', assetData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
  });
}

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
