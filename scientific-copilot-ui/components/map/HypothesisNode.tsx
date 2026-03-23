'use client'

import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { ScoreBadge } from '@/components/shared/ScoreBadge'

export interface HypothesisNodeData {
  title: string
  status: string
  novelty_score: number
  feasibility_score: number
  iteration_count: number
  [key: string]: unknown
}

function HypothesisNodeComponent({ data }: NodeProps) {
  const nodeData = data as HypothesisNodeData
  return (
    <div className="w-56 cursor-pointer rounded-xl border border-indigo-500/30 bg-[#111111] p-3 shadow-lg transition-shadow hover:shadow-indigo-500/20">
      <Handle type="source" position={Position.Bottom} className="!bg-indigo-400" />
      <Handle type="target" position={Position.Top} className="!bg-indigo-400" />
      <div className="mb-1 flex items-center justify-between">
        <StatusBadge status={nodeData.status} size="sm" />
        {nodeData.iteration_count > 0 && (
          <span className="text-[10px] font-bold text-indigo-400">↻ {nodeData.iteration_count}</span>
        )}
      </div>
      <p className="mb-2 line-clamp-2 text-xs font-medium text-gray-200">{nodeData.title}</p>
      <div className="flex gap-1">
        <ScoreBadge score={nodeData.novelty_score} label="N" />
        <ScoreBadge score={nodeData.feasibility_score} label="F" />
      </div>
    </div>
  )
}

export const HypothesisNode = memo(HypothesisNodeComponent)
