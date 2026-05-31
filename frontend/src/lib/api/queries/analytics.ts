import { useQuery } from '@tanstack/react-query';
import apiClient from '../client';
import type { CashFlowSeries, DashboardSummary, NetWorthSeries } from '../types';

export function useDashboardSummary() {
  return useQuery<DashboardSummary>({
    queryKey: ['analytics', 'dashboard'],
    queryFn: async () => {
      const response = await apiClient.get<DashboardSummary>('/analytics/dashboard');
      return response.data;
    },
  });
}

export function useCashFlow(params?: { from?: string; to?: string; groupBy?: string }) {
  return useQuery<CashFlowSeries>({
    queryKey: ['analytics', 'cash-flow', params],
    queryFn: async () => {
      const response = await apiClient.get<CashFlowSeries>('/analytics/cash-flow', { params });
      return response.data;
    },
  });
}

export function useNetWorth(params?: { from?: string; to?: string }) {
  return useQuery<NetWorthSeries>({
    queryKey: ['analytics', 'net-worth', params],
    queryFn: async () => {
      const response = await apiClient.get<NetWorthSeries>('/analytics/net-worth', { params });
      return response.data;
    },
  });
}
