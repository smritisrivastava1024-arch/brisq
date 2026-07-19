import { useMutation } from '@tanstack/react-query';
import { apiClient } from './client';
import { useToast } from '../components/ui/Toast';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  agent_name: string;
  message: string;
  history?: ChatMessage[];
}

export interface ChatResponse {
  reply: string;
  agents_used?: string[];
}

export function useSendChatMessage() {
  const { toast } = useToast();

  return useMutation({
    mutationFn: (payload: ChatRequest) => {
      const { agent_name, ...bodyPayload } = payload;
      return apiClient<ChatResponse>(`/chat/${agent_name}`, {
        method: 'POST',
        body: JSON.stringify(bodyPayload)
      });
    },
    onError: (err: Error) => {
      toast(`Couldn't reach the server — try again. (${err.message})`, 'error');
    }
    // We omit onSuccess toast here because a chat reply appearing is feedback enough
  });
}
