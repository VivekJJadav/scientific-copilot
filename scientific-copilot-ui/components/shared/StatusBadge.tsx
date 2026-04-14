'use client'

type BadgeStatus = string

const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string; animate?: string }> = {
  raw:               { bg: '#344055', text: '#6b7a90', dot: '#6b7a90' },
  processed:         { bg: '#00d4ff15', text: '#00d4ff', dot: '#00d4ff' },
  embedded:          { bg: '#a78bfa15', text: '#a78bfa', dot: '#a78bfa' },
  extraction_failed: { bg: '#ff3b5c15', text: '#ff3b5c', dot: '#ff3b5c' },
  pending:           { bg: '#ffb22415', text: '#ffb224', dot: '#ffb224', animate: 'animate-breathe' },
  approved:          { bg: '#00e5a015', text: '#00e5a0', dot: '#00e5a0' },
  rejected:          { bg: '#ff3b5c15', text: '#ff3b5c', dot: '#ff3b5c' },
  running:           { bg: '#00d4ff15', text: '#00d4ff', dot: '#00d4ff', animate: 'animate-signal-pulse' },
  done:              { bg: '#00e5a015', text: '#00e5a0', dot: '#00e5a0' },
  queued:            { bg: '#34405520', text: '#6b7a90', dot: '#6b7a90', animate: 'animate-breathe' },
  completed:         { bg: '#00e5a015', text: '#00e5a0', dot: '#00e5a0' },
  failed:            { bg: '#ff3b5c15', text: '#ff3b5c', dot: '#ff3b5c' },
}

interface StatusBadgeProps {
  status: BadgeStatus
  size?: 'sm' | 'md'
}

export function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const styles = STATUS_STYLES[status] ?? STATUS_STYLES.raw

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded font-mono uppercase tracking-widest ${
        size === 'sm' ? 'px-1.5 py-0.5 text-[7px]' : 'px-2 py-0.5 text-[9px]'
      }`}
      style={{ backgroundColor: styles.bg, color: styles.text }}
    >
      <span
        className={`inline-block rounded-full ${styles.animate ?? ''}`}
        style={{
          width: size === 'sm' ? 4 : 5,
          height: size === 'sm' ? 4 : 5,
          backgroundColor: styles.dot,
        }}
      />
      {status}
    </span>
  )
}
