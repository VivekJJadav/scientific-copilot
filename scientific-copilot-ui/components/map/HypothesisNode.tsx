'use client'

import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import { StatusBadge } from '@/components/shared/StatusBadge'

export interface HypothesisNodeData {
  title: string
  status: string
  noveltyScore: number
  feasibilityScore: number
  iterationCount: number
  [key: string]: unknown
}

const STATUS_BORDER: Record<string, string> = {
  pending: '#ffb224',
  approved: '#00e5a0',
  rejected: '#ff3b5c',
  running: '#00d4ff',
  done: '#00e5a0',
}

function ScoreArc({ score, color, label }: { score: number; color: string; label: string }) {
  const radius = 14
  const strokeWidth = 2.5
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - score)

  return (
    <div className="flex flex-col items-center gap-0.5">
      <svg width="34" height="34" viewBox="0 0 34 34">
        {/* Background arc */}
        <circle
          cx="17" cy="17" r={radius}
          fill="none"
          stroke="#1a2332"
          strokeWidth={strokeWidth}
        />
        {/* Score arc */}
        <circle
          cx="17" cy="17" r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 17 17)"
          style={{
            filter: `drop-shadow(0 0 3px ${color}40)`,
            transition: 'stroke-dashoffset 0.8s ease-out',
          }}
        />
        {/* Center text */}
        <text
          x="17" y="18"
          textAnchor="middle"
          dominantBaseline="middle"
          fill={color}
          fontSize="8"
          fontFamily="var(--font-ibm-plex-mono), monospace"
          fontWeight="600"
        >
          {(score * 10).toFixed(0)}
        </text>
      </svg>
      <span className="text-[6px] font-mono uppercase tracking-widest" style={{ color: `${color}80` }}>
        {label}
      </span>
    </div>
  )
}

function HypothesisNodeComponent({ data }: NodeProps) {
  const d = data as HypothesisNodeData
  const borderColor = STATUS_BORDER[d.status] ?? '#1a2332'
  const isRunning = d.status === 'running'
  const isPending = d.status === 'pending'

  return (
    <div
      className={`cursor-pointer p-3 transition-all duration-300 hover:scale-[1.02] relative ${
        isRunning ? 'animate-border-glow' : ''
      }`}
      style={{
        width: 195,
        backgroundColor: '#0a0e14',
        border: `1.5px solid ${borderColor}60`,
        borderRadius: 8,
        boxShadow: `0 0 16px ${borderColor}12`,
      }}
    >
      <Handle type="target" position={Position.Top} className="!bg-signal-cyan !w-1.5 !h-1.5 !border-0" />
      <Handle type="source" position={Position.Bottom} className="!bg-signal-cyan !w-1.5 !h-1.5 !border-0" />
      <Handle type="target" position={Position.Left} id="feedback-in" className="!bg-signal-amber !w-1.5 !h-1.5 !border-0" />

      {/* Diamond marker */}
      <div
        className="absolute -top-1.5 -right-1.5 w-3 h-3 rotate-45"
        style={{
          backgroundColor: borderColor,
          boxShadow: `0 0 6px ${borderColor}60`,
        }}
      />

      {/* Running scan line */}
      {isRunning && <div className="scan-line-overlay" />}

      {/* Title */}
      <p className="line-clamp-2 text-[10px] font-heading font-medium text-text-primary leading-tight mb-2.5 pr-2">
        {d.title}
      </p>

      {/* Score arcs */}
      <div className="flex items-center justify-center gap-3 mb-2.5">
        <ScoreArc score={d.noveltyScore} color="#a78bfa" label="NOV" />
        <ScoreArc score={d.feasibilityScore} color="#00e5a0" label="FEA" />
      </div>

      {/* Bottom row */}
      <div className="flex items-center justify-between">
        <StatusBadge status={d.status} size="sm" />
        {d.iterationCount > 0 && (
          <span className="text-[8px] font-mono font-bold text-signal-amber flex items-center gap-0.5 tracking-wider">
            ↻<sub className="text-[6px]">{d.iterationCount}</sub>
          </span>
        )}
      </div>
    </div>
  )
}

export const HypothesisNode = memo(HypothesisNodeComponent)
