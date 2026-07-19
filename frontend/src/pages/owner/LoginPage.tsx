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
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Dynamic Background Elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-[100px] pointer-events-none" />

      <Card className="w-full max-w-md p-8 relative z-10 border border-white/10">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-sans font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">
            Brisq Owner
          </h1>
          <p className="text-text-muted mt-2">Enter your master password</p>
        </div>
        
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <Input
            type="password"
            aria-label="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={error || undefined}
            disabled={isLoading}
          />
          
          <Button type="submit" variant="primary" disabled={isLoading} className="w-full h-12">
            {isLoading ? 'Unlocking...' : 'Unlock'}
          </Button>
        </form>
      </Card>
    </div>
  );
}
