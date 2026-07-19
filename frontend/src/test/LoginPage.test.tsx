/**
 * Smoke test: LoginPage renders without crashing and shows form elements.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LoginPage } from '../pages/owner/LoginPage';
import { ToastProvider } from '../components/ui/Toast';

// apiClient is called directly in LoginPage — mock the whole module
vi.mock('../api/client', () => ({
  apiClient: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, msg: string) {
      super(msg);
      this.status = status;
    }
  },
}));

// useNavigate is used post-login — prevent actual navigation
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => vi.fn() };
});

function renderLogin() {
  const qc = new QueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

describe('LoginPage', () => {
  it('renders without crashing', () => {
    renderLogin();
  });

  it('shows the password field and Unlock button', () => {
    renderLogin();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /unlock/i })).toBeInTheDocument();
  });

  it('shows inline error when submitted with empty password', async () => {
    renderLogin();
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /unlock/i }));
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it('shows inline error on 401 (wrong password)', async () => {
    const { apiClient } = await import('../api/client');
    const { ApiError } = await import('../api/client');
    vi.mocked(apiClient).mockRejectedValueOnce(new ApiError(401, 'Unauthorized'));

    renderLogin();
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/password/i), 'wrongpass');
    await user.click(screen.getByRole('button', { name: /unlock/i }));
    expect(await screen.findByText(/incorrect password/i)).toBeInTheDocument();
  });
});
