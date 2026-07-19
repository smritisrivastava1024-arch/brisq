
interface BadgeProps {
  status: 'pending' | 'approved' | 'rejected';
  className?: string;
}

export function Badge({ status, className = '' }: BadgeProps) {
  const styles = {
    pending: 'bg-warning/20 text-warning border-warning/30 shadow-[0_0_10px_rgba(245,158,11,0.15)]',
    approved: 'bg-success/20 text-success border-success/30 shadow-[0_0_10px_rgba(16,185,129,0.15)]',
    rejected: 'bg-danger/20 text-danger border-danger/30 shadow-[0_0_10px_rgba(239,68,68,0.15)]',
  };

  const labels = {
    pending: 'PENDING',
    approved: 'APPROVED',
    rejected: 'REJECTED',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-bold tracking-wider rounded-full border ${styles[status]} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${status === 'pending' ? 'bg-warning animate-pulse' : status === 'approved' ? 'bg-success' : 'bg-danger'}`} />
      {labels[status]}
    </span>
  );
}
