import { useState } from 'react';
import {
  useApprovals,
  useAllApprovals,
  useApproveApproval,
  useRejectApproval,
} from '../../api/useApprovals';
import type { Approval } from '../../api/useApprovals';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { ApprovalStamp } from '../../components/ui/ApprovalStamp';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function relativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  return `${Math.floor(diffHr / 24)}d ago`;
}

// Parse the JSON payload and return a list of [label, value] pairs,
// avoiding a raw JSON dump.
function parsePayloadFields(raw: string): [string, string][] {
  try {
    const obj = JSON.parse(raw || '{}');
    return Object.entries(obj).map(([k, v]) => {
      const label = k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
      const value = typeof v === 'object' ? JSON.stringify(v) : String(v);
      return [label, value];
    });
  } catch {
    return [['Details', raw]];
  }
}



// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function PayloadFields({ raw }: { raw: string }) {
  const fields = parsePayloadFields(raw);
  if (fields.length === 0) return null;
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm mt-3">
      {fields.map(([label, value]) => (
        <>
          <dt key={`dt-${label}`} className="text-[#6B6455] font-semibold whitespace-nowrap">
            {label}
          </dt>
          <dd key={`dd-${label}`} className="font-mono text-ink-navy break-all">
            {value}
          </dd>
        </>
      ))}
    </dl>
  );
}

function CardSkeleton() {
  return (
    <div className="flex flex-col gap-3 p-6 bg-white border border-parchment-dim rounded-ledger">
      <Skeleton className="h-5 w-1/3" />
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-16 w-full" />
    </div>
  );
}

// "Decision" tracks per-card stamp state independently from the mutation lifecycle,
// so the stamp stays rendered even after the query re-fetches and removes the card.
type Decision = 'approved' | 'rejected';

interface ApprovalCardProps {
  approval: Approval;
  readonly?: boolean; // historical view — no action buttons
}

function ApprovalCard({ approval, readonly = false }: ApprovalCardProps) {
  const approveMutation = useApproveApproval();
  const rejectMutation = useRejectApproval();

  // Local stamp state — once set, it never clears (the card stays "stamped")
  const [decision, setDecision] = useState<Decision | null>(
    // Pre-populate stamp for historical cards
    approval.status === 'approved' ? 'approved'
    : approval.status === 'rejected' ? 'rejected'
    : null
  );

  const isMutating =
    (approveMutation.isPending && approveMutation.variables === approval.id) ||
    (rejectMutation.isPending && rejectMutation.variables === approval.id);

  const isSettled = decision !== null;

  function handleApprove() {
    setDecision('approved'); // stamp shows immediately on click
    approveMutation.mutate(approval.id);
  }

  function handleReject() {
    setDecision('rejected');
    rejectMutation.mutate(approval.id);
  }

  return (
    <Card
      hoverShadow={!isSettled}
      className={`relative p-6 transition-opacity bg-white duration-300 ${
        isSettled ? 'opacity-60' : ''
      }`}
    >
      {/* Status badge + timestamp row */}
      <div className="flex items-center justify-between mb-3">
        <Badge status={approval.status === 'pending' ? 'pending' : (approval.status as Decision)} />
        <time
          dateTime={approval.created_at}
          className="font-mono text-xs text-[#9AA0AE]"
          title={new Date(approval.created_at).toLocaleString()}
        >
          {relativeTime(approval.created_at)}
        </time>
      </div>

      {/* Type label */}
      <p className="text-[10px] font-semibold tracking-widest uppercase text-[#9AA0AE] mb-1 font-body">
        {approval.approval_type.replace(/_/g, ' ')}
      </p>

      {/* Title */}
      <h2 className="font-display font-semibold text-xl text-ink-navy leading-snug">
        {approval.title}
      </h2>

      {/* Description */}
      {approval.description && (
        <p className="text-sm text-[#6B6455] mt-2 leading-relaxed">
          {approval.description}
        </p>
      )}

      {/* Payload fields */}
      {approval.payload && <PayloadFields raw={approval.payload} />}

      {/* Action buttons — hidden once settled or in readonly mode */}
      {!isSettled && !readonly && (
        <div className="flex gap-3 mt-5 pt-4 border-t border-parchment-dim">
          <Button
            variant="primary"
            size="sm"
            disabled={isMutating}
            onClick={handleApprove}
          >
            {isMutating && decision === null ? 'Approving…' : 'Approve'}
          </Button>
          <Button
            variant="danger"
            size="sm"
            disabled={isMutating}
            onClick={handleReject}
          >
            {isMutating && decision === null ? 'Rejecting…' : 'Reject'}
          </Button>
        </div>
      )}

      {/* Stamp — renders immediately on decision, stays after mutation settles */}
      {decision && (
        <ApprovalStamp
          key={decision} // re-key if somehow status changes (shouldn't happen)
          status={decision}
        />
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Empty states
// ---------------------------------------------------------------------------

function PendingEmpty() {
  return (
    <div className="flex flex-col items-start pt-16 pb-8">
      <span className="text-3xl mb-4">✓</span>
      <p className="font-display font-semibold text-xl text-ink-navy">
        Nothing waiting on you right now.
      </p>
      <p className="text-sm text-[#6B6455] mt-2">
        All approvals are up to date. Check back when new refund or cart
        requests come in.
      </p>
    </div>
  );
}

function HistoryEmpty() {
  return (
    <div className="flex flex-col items-start pt-16">
      <p className="text-sm text-[#6B6455]">No processed approvals yet.</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type Tab = 'pending' | 'all';

export function ApprovalsPage() {
  const [tab, setTab] = useState<Tab>('pending');

  const pendingQuery = useApprovals();
  const allQuery = useAllApprovals();

  const isLoading = tab === 'pending' ? pendingQuery.isLoading : allQuery.isLoading;
  const isError   = tab === 'pending' ? pendingQuery.isError   : allQuery.isError;

  const items: Approval[] =
    tab === 'pending'
      ? (pendingQuery.data?.pending_approvals ?? [])
      : (allQuery.data?.all_approvals ?? []);

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">

      {/* Page header */}
      <div className="mb-8">
        <h1 className="font-display font-semibold text-3xl text-ink-navy">
          Approvals
        </h1>
        <p className="text-sm text-[#6B6455] mt-1">
          Review and act on pending refund and cart requests.
        </p>
      </div>

      {/* Tab toggle */}
      <div className="flex gap-1 mb-6 bg-parchment-dim rounded-ledger p-1 w-fit">
        {(['pending', 'all'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`
              px-4 py-1.5 text-sm font-semibold rounded-[4px] transition-colors
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-gold
              ${tab === t
                ? 'bg-white text-ink-navy shadow-[0_1px_3px_rgba(20,27,46,0.08)]'
                : 'text-[#6B6455] hover:text-ink-navy'
              }
            `}
          >
            {t === 'pending' ? 'Pending' : 'All approvals'}
          </button>
        ))}
      </div>

      {/* Content */}
      {isError && (
        <p className="text-sm text-rust">
          Could not load approvals — check that the API is running.
        </p>
      )}

      {isLoading && (
        <div className="flex flex-col gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      )}

      {!isLoading && !isError && items.length === 0 && (
        tab === 'pending' ? <PendingEmpty /> : <HistoryEmpty />
      )}

      {!isLoading && !isError && items.length > 0 && (
        <div className="flex flex-col gap-4">
          {items.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              readonly={tab === 'all'}
            />
          ))}
        </div>
      )}

    </div>
  );
}
