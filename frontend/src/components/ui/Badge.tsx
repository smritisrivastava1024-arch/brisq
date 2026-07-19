interface BadgeProps {
  status: 'pending' | 'approved' | 'rejected';
  className?: string;
}

export function Badge({ status, className = '' }: BadgeProps) {
  const styles = {
    pending: 'bg-warning/20 text-[#8c7456] border-warning/30',
    approved: 'bg-success/20 text-[#5c7264] border-success/30',
    rejected: 'bg-danger/20 text-[#825b5b] border-danger/30',
  };

  const labels = {
    pending: 'Pending',
    approved: 'Approved',
    rejected: 'Rejected',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium tracking-wide rounded-md border ${styles[status]} ${className}`}>
      {labels[status]}
    </span>
  );
}
