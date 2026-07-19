/**
 * Smoke test and Integration test for AbandonedCartsPage.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { AbandonedCartsPage } from '../pages/owner/AbandonedCartsPage';
import { ToastProvider } from '../components/ui/Toast';

vi.mock('../api/useAbandonedCarts', () => {
  return {
    useAbandonedCarts: vi.fn(),
    useGenerateDrafts: vi.fn(),
  };
});

import { useAbandonedCarts, useGenerateDrafts } from '../api/useAbandonedCarts';

function renderCarts() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>
          <AbandonedCartsPage />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

const mockCart = {
  id: 1,
  cart_token: 'cart_123',
  customer_name: 'John Doe',
  email: 'john@example.com',
  phone: '',
  items: 'Shoes, Hat',
  cart_value: 150.0,
  checkout_url: 'http://store.com/checkout/123',
  created_at: new Date().toISOString(),
  email_draft: null,
  whatsapp_draft: null,
  suggested_coupon: null,
  approved: false,
  sent: false,
};

describe('AbandonedCartsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useGenerateDrafts as any).mockReturnValue({ mutate: vi.fn(), isPending: false });
  });

  it('renders without crashing and shows empty state', () => {
    (useAbandonedCarts as any).mockReturnValue({ data: { pending_carts: [] }, isLoading: false, isError: false });
    renderCarts();
    expect(screen.getByText(/Abandoned Carts/)).toBeInTheDocument();
    expect(screen.getByText(/No abandoned carts at the moment/i)).toBeInTheDocument();
  });

  it('renders carts and handles generate drafts flow', async () => {
    // Initial state: no drafts
    (useAbandonedCarts as any).mockReturnValue({ data: { pending_carts: [mockCart] }, isLoading: false, isError: false });
    
    const mockGenerateMutate = vi.fn();
    (useGenerateDrafts as any).mockReturnValue({ mutate: mockGenerateMutate, isPending: false });

    renderCarts();
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Shoes, Hat')).toBeInTheDocument();
    
    const user = userEvent.setup();
    const generateBtn = screen.getByRole('button', { name: /Generate recovery drafts/i });
    await user.click(generateBtn);

    expect(mockGenerateMutate).toHaveBeenCalledWith('cart_123');
  });

  it('shows drafts when they exist', () => {
    const cartWithDrafts = { ...mockCart, email_draft: 'Hello John', suggested_coupon: 'DISCOUNT10' };
    (useAbandonedCarts as any).mockReturnValue({ data: { pending_carts: [cartWithDrafts] }, isLoading: false, isError: false });
    
    renderCarts();
    
    expect(screen.getByText('Hello John')).toBeInTheDocument();
    expect(screen.getByText('DISCOUNT10')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Generate recovery drafts/i })).not.toBeInTheDocument();
  });
});
