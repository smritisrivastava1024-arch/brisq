import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import { useToast } from '../components/ui/Toast';

export interface AbandonedCart {
  id: number;
  cart_token: string;
  customer_name: string;
  email: string;
  phone: string;
  items: string;
  cart_value: number;
  checkout_url: string;
  created_at: string;
  email_draft: string | null;
  whatsapp_draft: string | null;
  suggested_coupon: string | null;
  approved: boolean;
  sent: boolean;
}

export function useAbandonedCarts() {
  return useQuery({
    queryKey: ['abandonedCarts'],
    queryFn: () => apiClient<{ pending_carts: AbandonedCart[] }>('/abandoned-carts')
  });
}

export function useGenerateDrafts() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (cartToken: string) => apiClient(`/abandoned-carts/${cartToken}/generate-drafts`, { method: 'POST' }),
    onSuccess: () => {
      toast('Drafts generated.', 'success');
      queryClient.invalidateQueries({ queryKey: ['abandonedCarts'] });
    },
    onError: (err: Error) => {
      toast(`Couldn't reach the server — try again. (${err.message})`, 'error');
    }
  });
}
