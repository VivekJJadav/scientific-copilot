'use client'

import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import { StatusBadge } from '@/components/shared/StatusBadge'

export interface PaperNodeData {
  title: string
  arxivId: string
  arxivStatus: string
  year: number
  clusterColor: string
  [key: string]: unknown
}

const STATUS_GLOW: Record<string, { border: string; shadow: string }> = {
  raw:               { border: '#344055', shadow: 'none' },
  processed:         { border: '#00d4ff40', shadow: '0 0 12px #00d4ff15' },
  embedded:          { border: '#a78bfa40', shadow: '0 0 12px #a78bfa15' },
  extraction_failed: { border: '#ff3b5c40', shadow: '0 0 12px #ff3b5c15' },
}

function HexIndicator({ status }: { status: string }) {
  const color = status === 'processed' ? '#00d4ff'
    : status === 'embedded' ? '#a78bfa'
    : status === 'extraction_failed' ? '#ff3b5c'
    : '#344055'

  return (
    <svg width="10" height="12" viewBox="0 0 10 12" className="shrink-0">
      <polygon
        points="5,0 10,3 10,9 5,12 0,9 0,3"
        fill={`${color}30`}
        stroke={color}
        strokeWidth="0.8"
      />
    </svg>
  )
}

function PaperNodeComponent({ data }: NodeProps) {
  const d = data as PaperNodeData
  const glow = STATUS_GLOW[d.arxivStatus] ?? STATUS_GLOW.raw
  const isProcessing = d.arxivStatus === 'processed' || d.arxivStatus === 'embedded'

  return (
    <div
      className="group cursor-pointer rounded-md p-2.5 transition-all duration-300 hover:scale-[1.02]"
      style={{
        width: 155,
        backgroundColor: '#0f1520',
        border: `1px solid ${glow.border}`,
        boxShadow: glow.shadow,
        borderRadius: 6,
      }}
    >
      <Handle type="target" position={Position.Top} className="!bg-text-muted !w-1.5 !h-1.5 !border-0" />
      <Handle type="source" position={Position.Bottom} className="!bg-text-muted !w-1.5 !h-1.5 !border-0" />

      {/* Cluster accent bar */}
      <div
        className="absolute top-0 left-2 right-2 h-[2px] rounded-b"
        style={{ backgroundColor: d.clusterColor ?? '#1a2332' }}
      />

      {/* Header row */}
      <div className="flex items-start gap-1.5 mb-1.5">
        <HexIndicator status={d.arxivStatus} />
        <p className="line-clamp-2 text-[10px] font-mono font-medium text-text-primary leading-tight flex-1">
          {d.title}
        </p>
      </div>

      {/* Meta row */}
      <div className="flex items-center justify-between">
        <span className="text-[8px] font-mono text-text-muted tracking-wider">
          arx:{d.arxivId?.slice(0, 10)}
        </span>
        <span className="text-[8px] font-mono text-text-muted tabular-nums">{d.year}</span>
      </div>

      {/* Status */}
      <div className="mt-1.5">
        <StatusBadge status={d.arxivStatus} size="sm" />
      </div>
    </div>
  )
}

export const PaperNode = memo(PaperNodeComponent)
