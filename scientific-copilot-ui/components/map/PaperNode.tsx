'use client'

import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import { StatusBadge } from '@/components/shared/StatusBadge'

export interface PaperNodeData {
  title: string
  arxiv_status: string
  year: number
  cluster_color: string
  [key: string]: unknown
}

function PaperNodeComponent({ data }: NodeProps) {
  const nodeData = data as PaperNodeData
  return (
    <div
      className="w-48 cursor-pointer rounded-lg border bg-[#111111] p-3 shadow-lg transition-shadow hover:shadow-indigo-500/10"
      style={{ borderColor: nodeData.cluster_color + '40' }}
    >
      <Handle type="source" position={Position.Bottom} className="!bg-gray-500" />
      <Handle type="target" position={Position.Top} className="!bg-gray-500" />
      <div className="mb-1 flex items-center justify-between">
        <StatusBadge status={nodeData.arxiv_status} size="sm" />
        <span className="text-[10px] text-gray-600">{nodeData.year}</span>
      </div>
      <p className="line-clamp-2 text-xs font-medium text-gray-200">{nodeData.title}</p>
    </div>
  )
}

export const PaperNode = memo(PaperNodeComponent)
