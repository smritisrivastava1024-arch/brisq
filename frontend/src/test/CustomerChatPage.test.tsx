/**
 * Smoke test: CustomerChatPage renders without crashing and shows empty state.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CustomerChatPage } from '../pages/CustomerChatPage';
import { ToastProvider } from '../components/ui/Toast';

// useSendChatMessage relies on fetch — mock at module level
vi.mock('../api/useChat', () => ({
  useSendChatMessage: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>{ui}</MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

describe('CustomerChatPage', () => {
  it('renders without crashing', () => {
    renderWithProviders(<CustomerChatPage />);
  });

  it('shows the Brisq header', () => {
    renderWithProviders(<CustomerChatPage />);
    // "Brisq" appears as the wordmark in the header
    expect(screen.getAllByText(/Brisq/i).length).toBeGreaterThan(0);
  });

  it('shows the empty-state capability list', () => {
    renderWithProviders(<CustomerChatPage />);
    expect(screen.getByText(/order status/i)).toBeInTheDocument();
    expect(screen.getByText(/refund/i)).toBeInTheDocument();
  });

  it('renders the Send button disabled when input is empty', () => {
    renderWithProviders(<CustomerChatPage />);
    const sendBtn = screen.getByRole('button', { name: /send/i });
    expect(sendBtn).toBeDisabled();
  });
});
