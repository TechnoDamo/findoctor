import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';

// Transaction interface (simplified based on what we know from OpenAPI)
export interface Transaction {
  id: string;
  userId: string;
  accountId: string;
  categoryId: string | null;
  type: 'income' | 'expense' | 'transfer';
  amount: string;
  currency: string;
  transactionDatetime: string;
  description: string | null;
  merchantId: string | null;
  merchantName: string | null;
  geoLocation: string | null;
  recurringTransactionId: string | null;
  externalId: string | null;
  transferId: string | null;
  transferLeg: 'debit' | 'credit' | null;
  createdAt: string;
  tags: any[];
}

// List transactions query
export function useTransactions() {
  return useQuery<Transaction[]>({
    queryKey: ['transactions'],
    queryFn: async () => {
      const response = await apiClient.get<Transaction[]>('/transactions');
      return response.data;
    },
  });
}

// Create transaction mutation
export function useCreateTransaction() {
  const queryClient = useQueryClient();
  
  return useMutation<Transaction, Error, Partial<Transaction>>({
    mutationFn: async (transactionData) => {
      const response = await apiClient.post<Transaction>('/transactions', transactionData);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch transactions
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
}

// Get transaction query
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