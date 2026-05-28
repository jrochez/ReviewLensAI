import { clsx } from 'clsx'

type Status = 'pending' | 'scraping' | 'ready' | 'error'

const config: Record<Status, { label: string; className: string; dot: string }> = {
  ready:    { label: 'Ready',    className: 'bg-success-bg text-success',  dot: 'bg-success' },
  scraping: { label: 'Scraping', className: 'bg-warning-bg text-warning',  dot: 'bg-warning animate-spin' },
  pending:  { label: 'Pending',  className: 'bg-warning-bg text-warning',  dot: 'bg-warning' },
  error:    { label: 'Error',    className: 'bg-error-bg text-error',      dot: 'bg-error' },
}

export function StatusBadge({ status }: { status: Status }) {
  const { label, className, dot } = config[status] ?? config.pending
  return (
    <span className={clsx('inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium', className)}>
      <span className={clsx('w-1.5 h-1.5 rounded-full', dot)} />
      {label}
    </span>
  )
}
