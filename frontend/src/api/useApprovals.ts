import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import { useToast } from '../components/ui/Toast';

export interface Approval {
  id: number;
  approval_type: string;
  reference_id: string;
  title: string;
  description: string;
  payload: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  processed_at: string | null;
}

export function useApprovals() {
  return useQuery({
    queryKey: ['approvals', 'pending'],
    queryFn: () => apiClient<{ pending_approvals: Approval[] }>('/approvals')
  });
}

export function useAllApprovals() {
  return useQuery({
    queryKey: ['approvals', 'all'],
    queryFn: () => apiClient<{ all_approvals: Approval[] }>('/approvals/all')
  });
}

export function useApproveApproval() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: number) => apiClient(`/approvals/${id}/approve`, { method: 'POST' }),
    onSuccess: () => {
      toast('Refund approved.', 'success');
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
    },
    onError: (err: Error) => {
      toast(`Couldn't reach the server — try again. (${err.message})`, 'error');
    }
  });
}

export function useRejectApproval() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: number) => apiClient(`/approvals/${id}/reject`, { method: 'POST' }),
    onSuccess: () => {
      toast('Refund rejected.', 'success');
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
    },
    onError: (err: Error) => {
      toast(`Couldn't reach the server — try again. (${err.message})`, 'error');
    }
  });
}
