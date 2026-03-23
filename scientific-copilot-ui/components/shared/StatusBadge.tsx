import { clsx } from 'clsx'

const statusConfig: Record<string, { label: string; className: string }> = {
  pending: { label: 'Pending', className: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  approved: { label: 'Approved', className: 'bg-green-500/20 text-green-400 border-green-500/30' },
  rejected: { label: 'Rejected', className: 'bg-red-500/20 text-red-400 border-red-500/30' },
  running: { label: 'Running', className: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  done: { label: 'Done', className: 'bg-green-500/20 text-green-400 border-green-500/30' },
  completed: { label: 'Completed', className: 'bg-green-500/20 text-green-400 border-green-500/30' },
  failed: { label: 'Failed', className: 'bg-red-500/20 text-red-400 border-red-500/30' },
  queued: { label: 'Queued', className: 'bg-gray-500/20 text-gray-400 border-gray-500/30' },
  raw: { label: 'Raw', className: 'bg-gray-500/20 text-gray-400 border-gray-500/30' },
  processed: { label: 'Processed', className: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  embedded: { label: 'Embedded', className: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' },
  validated: { label: 'Validated', className: 'bg-green-500/20 text-green-400 border-green-500/30' },
  inconclusive: { label: 'Inconclusive', className: 'bg-gray-500/20 text-gray-400 border-gray-500/30' },
}

interface StatusBadgeProps {
  status: string
  size?: 'sm' | 'md'
}

export function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const config = statusConfig[status] ?? { label: status, className: 'bg-gray-500/20 text-gray-400 border-gray-500/30' }
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full border font-medium',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        config.className
      )}
    >
      {config.label}
    </span>
  )
}
