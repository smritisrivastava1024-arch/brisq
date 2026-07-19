import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../api/auth';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card } from '../../components/ui/Card';

export function LoginPage() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) {
      setError('Password is required');
      return;
    }
    
    setError(null);
    setIsLoading(true);
    
    try {
      await login(password);
      navigate('/owner/approvals');
    } catch (err: any) {
      if (err.status === 401) {
        setError('Incorrect password');
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <Card className="w-full max-w-sm p-8 shadow-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-sans font-bold text-primary tracking-tight">
            Brisq Owner
          </h1>
          <p className="text-text-muted mt-2 text-sm">Log in to manage operations</p>
        </div>
        
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <Input
            type="password"
            aria-label="password"
            placeholder="Master Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={error || undefined}
            disabled={isLoading}
          />
          
          <Button type="submit" variant="primary" disabled={isLoading} className="w-full">
            {isLoading ? 'Unlocking...' : 'Unlock Dashboard'}
          </Button>
        </form>
      </Card>
    </div>
  );
}
