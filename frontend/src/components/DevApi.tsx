import { useState } from 'react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card } from './ui/Card';
import { useApprovals, useAllApprovals, useApproveApproval, useRejectApproval } from '../api/useApprovals';
import { useAbandonedCarts, useGenerateDrafts } from '../api/useAbandonedCarts';
import { useSendChatMessage } from '../api/useChat';
import { authStore } from '../api/auth';
import { apiClient } from '../api/client';
import { useToast } from './ui/Toast';

export function DevApi() {
  const { toast } = useToast();
  const [password, setPassword] = useState('');
  const [chatMessage, setChatMessage] = useState('');
  
  const approvalsQuery = useApprovals();
  const allApprovalsQuery = useAllApprovals();
  const approveMutation = useApproveApproval();
  const rejectMutation = useRejectApproval();

  const cartsQuery = useAbandonedCarts();
  const generateDraftsMutation = useGenerateDrafts();

  const chatMutation = useSendChatMessage('customer');

  const handleLogin = async () => {
    try {
      const data = await apiClient<{ token: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ password })
      });
      authStore.setToken(data.token);
      toast('Logged in successfully', 'success');
      // Refetch queries that might need auth
      approvalsQuery.refetch();
      allApprovalsQuery.refetch();
      cartsQuery.refetch();
    } catch (err: any) {
      toast(`Login failed: ${err.message}`, 'error');
    }
  };

  const handleLogout = () => {
    authStore.clearToken();
    toast('Logged out', 'info');
  };

  const handleChat = () => {
    chatMutation.mutate({ message: chatMessage });
  };

  return (
    <div className="p-8 max-w-4xl mx-auto flex flex-col gap-8">
      <h1 className="font-display text-3xl">API Integration Tests</h1>

      <Card className="p-6 flex flex-col gap-4">
        <h2 className="font-display text-xl">Auth</h2>
        <div className="flex gap-4 items-end">
          <Input 
            label="Owner Password" 
            type="password" 
            value={password} 
            onChange={e => setPassword(e.target.value)} 
          />
          <Button onClick={handleLogin}>Login</Button>
          <Button variant="secondary" onClick={handleLogout}>Logout</Button>
        </div>
      </Card>

      <Card className="p-6 flex flex-col gap-4">
        <h2 className="font-display text-xl">Approvals</h2>
        <div className="flex gap-4">
          <Button onClick={() => approvalsQuery.refetch()}>Fetch Pending Approvals</Button>
          <Button onClick={() => allApprovalsQuery.refetch()}>Fetch All Approvals</Button>
        </div>
        <pre className="bg-parchment-dim p-4 rounded text-sm overflow-auto max-h-40">
          {JSON.stringify(approvalsQuery.data || approvalsQuery.error || 'No data', null, 2)}
        </pre>
        <div className="flex gap-4">
          <Button onClick={() => approveMutation.mutate(1)}>Approve ID 1</Button>
          <Button variant="danger" onClick={() => rejectMutation.mutate(1)}>Reject ID 1</Button>
        </div>
      </Card>

      <Card className="p-6 flex flex-col gap-4">
        <h2 className="font-display text-xl">Abandoned Carts</h2>
        <div className="flex gap-4">
          <Button onClick={() => cartsQuery.refetch()}>Fetch Carts</Button>
          <Button onClick={() => generateDraftsMutation.mutate('cart_123')}>Generate Drafts (cart_123)</Button>
        </div>
        <pre className="bg-parchment-dim p-4 rounded text-sm overflow-auto max-h-40">
          {JSON.stringify(cartsQuery.data || cartsQuery.error || 'No data', null, 2)}
        </pre>
      </Card>

      <Card className="p-6 flex flex-col gap-4">
        <h2 className="font-display text-xl">Chat (Customer Agent)</h2>
        <div className="flex gap-4 items-end">
          <Input 
            label="Message" 
            value={chatMessage} 
            onChange={e => setChatMessage(e.target.value)} 
          />
          <Button onClick={handleChat} disabled={chatMutation.isPending}>
            {chatMutation.isPending ? 'Sending...' : 'Send'}
          </Button>
        </div>
        <pre className="bg-parchment-dim p-4 rounded text-sm overflow-auto max-h-40">
          {JSON.stringify(chatMutation.data || chatMutation.error || 'No data', null, 2)}
        </pre>
      </Card>
    </div>
  );
}
