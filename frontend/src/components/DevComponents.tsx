import { useState } from 'react';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Input } from './ui/Input';
import { Textarea } from './ui/Textarea';
import { useToast } from './ui/Toast';
import { Skeleton } from './ui/Skeleton';
import { ApprovalStamp } from './ui/ApprovalStamp';

export function DevComponents() {
  const { toast } = useToast();
  const [stamp, setStamp] = useState<'approved' | 'rejected' | null>(null);

  return (
    <div className="p-8 max-w-4xl mx-auto flex flex-col gap-12">
      <div>
        <h2 className="font-display text-2xl mb-4">Buttons</h2>
        <div className="flex gap-4 items-center">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="ghost">Ghost</Button>
          <Button disabled>Disabled</Button>
          <Button variant="primary" size="sm">Small</Button>
        </div>
      </div>

      <div>
        <h2 className="font-display text-2xl mb-4">Badges</h2>
        <div className="flex gap-4">
          <Badge status="pending" />
          <Badge status="approved" />
          <Badge status="rejected" />
        </div>
      </div>

      <div>
        <h2 className="font-display text-2xl mb-4">Forms</h2>
        <div className="flex flex-col gap-4 max-w-md">
          <Input label="Standard Input" placeholder="Enter text..." />
          <Input label="Error Input" defaultValue="Bad value" error="This field is required." />
          <Textarea label="Message" placeholder="Type here..." />
        </div>
      </div>

      <div>
        <h2 className="font-display text-2xl mb-4">Toast Notifications</h2>
        <div className="flex gap-4">
          <Button onClick={() => toast('Standard information message')}>Info Toast</Button>
          <Button variant="primary" onClick={() => toast('Action completed successfully!', 'success')}>Success Toast</Button>
          <Button variant="danger" onClick={() => toast('Failed to update ledger.', 'error')}>Error Toast</Button>
        </div>
      </div>

      <div>
        <h2 className="font-display text-2xl mb-4">Cards & Stamps</h2>
        <Card hoverShadow className="p-6 relative max-w-md">
          <h3 className="font-display text-lg mb-2">Ledger Entry #492</h3>
          <p className="text-sm text-text-muted mb-4">Customer requested a refund for damaged goods.</p>
          <Skeleton className="h-16 w-full mb-4" />
          <div className="flex gap-2">
            <Button variant="primary" onClick={() => setStamp('approved')}>Approve</Button>
            <Button variant="danger" onClick={() => setStamp('rejected')}>Reject</Button>
            <Button variant="secondary" onClick={() => setStamp(null)}>Reset</Button>
          </div>
          
          {stamp && (
            <ApprovalStamp 
              key={stamp + Math.random()} 
              status={stamp} 
              onAnimationEnd={() => console.log('Stamp animation finished')} 
            />
          )}
        </Card>
      </div>
    </div>
  );
}
