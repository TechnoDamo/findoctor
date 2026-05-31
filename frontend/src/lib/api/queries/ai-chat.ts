import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';
import type { AiChatConversation, AiChatConversationPage } from '../types';

export function useConversations(page = 1, pageSize = 50) {
  return useQuery<AiChatConversationPage>({
    queryKey: ['conversations', { page, pageSize }],
    queryFn: async () => {
      const response = await apiClient.get<AiChatConversationPage>('/ai/chat/conversations', {
        params: { page, pageSize },
      });
      return response.data;
    },
  });
}

export function useConversation(id: string | null) {
  return useQuery<AiChatConversation>({
    queryKey: ['conversations', id],
    queryFn: async () => {
      const response = await apiClient.get<AiChatConversation>(`/ai/chat/conversations/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation<AiChatConversation, Error, string | undefined>({
    mutationFn: async (title) => {
      const response = await apiClient.post<AiChatConversation>('/ai/chat/conversations', {
        title: title || null,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await apiClient.delete(`/ai/chat/conversations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}
