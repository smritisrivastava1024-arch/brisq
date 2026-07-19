import { useState } from 'react';
import { useApprovals, useAllApprovals, useApproveApproval, useRejectApproval } from '../../api/useApprovals';
import type { Approval } from '../../api/useApprovals';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { ApprovalStamp } from '../../components/ui/ApprovalStamp';
import { Skeleton } from '../../components/ui/Skeleton';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function formatRelativeTime(dateString: string) {
  const diff = Date.now() - new Date(dateString).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function parsePayloadSafely(payloadStr: string) {
  try {
    return JSON.parse(payloadStr);
  } catch (e) {
    return { raw: payloadStr };
  }
}

// ---------------------------------------------------------------------------
// Payload Formatter Component
// ---------------------------------------------------------------------------
function PayloadFields({ payloadObj }: { payloadObj: Record<string, any> }) {
  const fields = Object.entries(payloadObj).filter(([_, v]) => v !== null && v !== undefined && v !== '');
  
  if (fields.length === 0) return null;

  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm mt-4 bg-background rounded-lg p-4 border border-[#E8E3DA]">
      {fields.map(([label, value]) => (
        <div key={label} className="contents">
          <dt className="text-text-muted font-medium whitespace-nowrap capitalize">
            {label.replace(/_/g, ' ')}
          </dt>
          <dd className="font-mono text-text-main break-all bg-surface-lighter border border-[#E8E3DA] px-2 py-0.5 rounded text-xs inline-flex items-center w-fit">
            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

// ---------------------------------------------------------------------------
// Card Component
// ---------------------------------------------------------------------------
function ApprovalCard({ 
  approval, 
  onApprove, 
  onReject,
  isProcessing
}: { 
  approval: Approval, 
  onApprove: (id: number) => void,
  onReject: (id: number) => void,
  isProcessing: boolean
}) {
  const isPending = approval.status === 'pending';
  const payloadObj = parsePayloadSafely(approval.payload);
  const showActions = isPending && !isProcessing;

  const [optimisticStatus, setOptimisticStatus] = useState<'approved' | 'rejected' | null>(null);

  const handleApprove = () => {
    setOptimisticStatus('approved');
    onApprove(approval.id);
  };

  const handleReject = () => {
    setOptimisticStatus('rejected');
    onReject(approval.id);
  };

  const displayStatus = optimisticStatus || (approval.status !== 'pending' ? approval.status : null);

  return (
    <Card className="p-6 relative bg-surface border border-[#E8E3DA]">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <Badge status={approval.status} />
            <span className="text-xs text-text-dim font-mono">{formatRelativeTime(approval.created_at)}</span>
          </div>
          <h3 className="text-lg font-bold text-text-main mb-1">{approval.title}</h3>
          <p className="text-text-muted text-sm">{approval.description}</p>
        </div>
      </div>

      <PayloadFields payloadObj={payloadObj} />

      {showActions && !optimisticStatus && (
        <div className="flex gap-3 mt-6 pt-4 border-t border-[#E8E3DA]">
          <Button variant="primary" onClick={handleApprove} className="w-full sm:w-auto">Approve</Button>
          <Button variant="secondary" onClick={handleReject} className="w-full sm:w-auto">Reject</Button>
        </div>
      )}

      {displayStatus && (
        <ApprovalStamp status={displayStatus as 'approved' | 'rejected'} />
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------
export function ApprovalsPage() {
  const [viewAll, setViewAll] = useState(false);
  
  const { data: pendingData, isLoading: loadingPending } = useApprovals();
  const { data: allData, isLoading: loadingAll } = useAllApprovals();
  
  const { mutate: approveMutate, isPending: isApproving } = useApproveApproval();
  const { mutate: rejectMutate, isPending: isRejecting } = useRejectApproval();

  const isProcessing = isApproving || isRejecting;

  const approvals = viewAll 
    ? allData?.all_approvals || [] 
    : pendingData?.pending_approvals || [];
    
  const isLoading = viewAll ? loadingAll : loadingPending;

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="px-6 py-5 border-b border-[#E8E3DA] bg-background sticky top-0 z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-primary">Approvals</h1>
          <p className="text-text-muted text-sm mt-1">Review AI-generated requests</p>
        </div>
        
        <div className="flex bg-surface-lighter border border-[#E8E3DA] rounded-md p-1 shadow-sm">
          <button
            onClick={() => setViewAll(false)}
            className={`px-4 py-1.5 text-sm font-semibold rounded transition-colors duration-200 ${!viewAll ? 'bg-surface text-primary shadow-sm border border-[#E8E3DA]' : 'text-text-muted hover:text-text-main hover:bg-[#E8E3DA]/30 border border-transparent'}`}
          >
            Pending
          </button>
          <button
            onClick={() => setViewAll(true)}
            className={`px-4 py-1.5 text-sm font-semibold rounded transition-colors duration-200 ${viewAll ? 'bg-surface text-primary shadow-sm border border-[#E8E3DA]' : 'text-text-muted hover:text-text-main hover:bg-[#E8E3DA]/30 border border-transparent'}`}
          >
            All History
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        <div className="max-w-3xl mx-auto flex flex-col gap-6">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Card key={i} className="p-6 h-40">
                <Skeleton className="w-16 h-6 rounded-md mb-4" />
                <Skeleton className="w-1/2 h-6 mb-2" />
                <Skeleton className="w-3/4 h-4" />
              </Card>
            ))
          ) : approvals.length === 0 ? (
            <div className="py-20 text-center">
              <div className="w-16 h-16 mx-auto rounded-full bg-surface-lighter flex items-center justify-center text-2xl mb-4 border border-[#E8E3DA] shadow-sm text-primary">
                ✓
              </div>
              <p className="text-lg font-bold text-text-main">Nothing waiting on you right now.</p>
              <p className="text-text-muted text-sm mt-1">The agents are handling things.</p>
            </div>
          ) : (
            approvals.map(app => (
              <ApprovalCard 
                key={app.id} 
                approval={app} 
                onApprove={approveMutate}
                onReject={rejectMutate}
                isProcessing={isProcessing}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
