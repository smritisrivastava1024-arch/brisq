import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { apiClient, ApiError } from '../../api/client';
import { authStore } from '../../api/auth';

export function LoginPage() {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');

    if (!password.trim()) {
      setError('Password is required.');
      return;
    }

    setIsLoading(true);
    try {
      const data = await apiClient<{ token: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ password }),
      });
      authStore.setToken(data.token);
      navigate('/owner/approvals', { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError('Incorrect password. Try again.');
      } else {
        setError('Could not reach the server — try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-parchment flex items-center justify-center p-6">
      <div className="w-full max-w-sm flex flex-col gap-8">
        {/* Wordmark */}
        <div className="text-center">
          <span className="font-display font-semibold text-4xl text-ink-navy tracking-tight">
            Brisq
          </span>
          <p className="mt-2 text-sm text-[#6B6455]">Owner Ledger</p>
        </div>

        <Card className="p-8">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
            <div className="flex flex-col gap-1">
              <h1 className="font-display font-semibold text-xl text-ink-navy">
                Unlock the Ledger
              </h1>
              <p className="text-sm text-[#6B6455]">
                Enter your owner password to continue.
              </p>
            </div>

            <Input
              label="Password"
              id="owner-password"
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (error) setError('');
              }}
              error={error}
              autoFocus
              autoComplete="current-password"
              placeholder="Enter owner password"
            />

            <Button
              type="submit"
              variant="primary"
              disabled={isLoading}
              className="w-full mt-1"
            >
              {isLoading ? 'Authenticating…' : 'Unlock'}
            </Button>
          </form>
        </Card>

        <p className="text-center text-xs text-[#9AA0AE]">
          Session is memory-only — cleared when the tab closes.
        </p>
      </div>
    </div>
  );
}
