import { useQuery } from '@tanstack/react-query';
import apiClient from '../client';

export interface RefItem {
  id: string;
  name: string;
}

export function useAccountTypes() {
  return useQuery<RefItem[]>({
    queryKey: ['reference', 'account-types'],
    queryFn: async () => {
      const response = await apiClient.get<RefItem[]>('/reference/account-types');
      return response.data;
    },
    staleTime: 60000,
  });
}

export function useAssetTypes() {
  return useQuery<RefItem[]>({
    queryKey: ['reference', 'asset-types'],
    queryFn: async () => {
      const response = await apiClient.get<RefItem[]>('/reference/asset-types');
      return response.data;
    },
    staleTime: 60000,
  });
}

export function useLiabilityTypes() {
  return useQuery<RefItem[]>({
    queryKey: ['reference', 'liability-types'],
    queryFn: async () => {
      const response = await apiClient.get<RefItem[]>('/reference/liability-types');
      return response.data;
    },
    staleTime: 60000,
  });
}

export function useCategories() {
  return useQuery<RefItem[]>({
    queryKey: ['reference', 'categories'],
    queryFn: async () => {
      const response = await apiClient.get<RefItem[]>('/reference/categories');
      return response.data;
    },
    staleTime: 60000,
  });
}

export function useProviderTypes() {
  return useQuery<RefItem[]>({
    queryKey: ['reference', 'provider-types'],
    queryFn: async () => {
      const response = await apiClient.get<RefItem[]>('/reference/provider-types');
      return response.data;
    },
    staleTime: 60000,
  });
}
