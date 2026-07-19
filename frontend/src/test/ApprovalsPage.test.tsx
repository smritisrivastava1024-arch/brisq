/**
 * Smoke test and Integration test for ApprovalsPage.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApprovalsPage } from '../pages/owner/ApprovalsPage';
import { ToastProvider } from '../components/ui/Toast';

// Mock the API hooks
vi.mock('../api/useApprovals', () => {
  return {
    useApprovals: vi.fn(),
    useAllApprovals: vi.fn(),
    useApproveApproval: vi.fn(),
    useRejectApproval: vi.fn(),
  };
});

import { useApprovals, useAllApprovals, useApproveApproval, useRejectApproval } from '../api/useApprovals';

function renderApprovals() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <ApprovalsPage />
      </ToastProvider>
    </QueryClientProvider>
  );
}

const mockApproval = {
  id: 1,
  approval_type: 'refund',
  reference_id: 'order_123',
  title: 'Refund Request',
  description: 'Customer requested a refund.',
  payload: JSON.stringify({ amount: 50.0 }),
  status: 'pending',
  created_at: new Date().toISOString(),
  processed_at: null,
};

describe('ApprovalsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useAllApprovals as any).mockReturnValue({ data: { all_approvals: [] }, isLoading: false, isError: false });
    (useApproveApproval as any).mockReturnValue({ mutate: vi.fn(), isPending: false });
    (useRejectApproval as any).mockReturnValue({ mutate: vi.fn(), isPending: false });
  });

  it('renders without crashing and shows empty state', () => {
    (useApprovals as any).mockReturnValue({ data: { pending_approvals: [] }, isLoading: false, isError: false });
    renderApprovals();
    expect(screen.getByText(/Approvals/)).toBeInTheDocument();
    expect(screen.getByText(/Nothing waiting on you right now/i)).toBeInTheDocument();
  });

  it('renders pending approvals and handles approve flow', async () => {
    (useApprovals as any).mockReturnValue({ data: { pending_approvals: [mockApproval] }, isLoading: false, isError: false });
    
    const mockApproveMutate = vi.fn();
    (useApproveApproval as any).mockReturnValue({ mutate: mockApproveMutate, isPending: false });

    renderApprovals();
    
    // Check card renders
    expect(screen.getByText('Refund Request')).toBeInTheDocument();
    expect(screen.getByText('Customer requested a refund.')).toBeInTheDocument();
    
    // Click approve
    const user = userEvent.setup();
    const approveBtn = screen.getByRole('button', { name: /Approve/i });
    await user.click(approveBtn);

    // Verify mutation was called
    expect(mockApproveMutate).toHaveBeenCalledWith(1);
    
    // Check stamp appears (status changed to approved locally)
    await waitFor(() => {
      expect(screen.getByText(/approved/i)).toBeInTheDocument();
    });
  });
});
