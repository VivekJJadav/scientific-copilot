'use client'

import { useClusters } from '@/lib/hooks/useClusters'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { EmptyState } from '@/components/shared/EmptyState'
import { Network } from 'lucide-react'

const CLUSTER_COLORS = [
  'border-indigo-500/30 bg-indigo-500/5',
  'border-emerald-500/30 bg-emerald-500/5',
  'border-amber-500/30 bg-amber-500/5',
  'border-rose-500/30 bg-rose-500/5',
  'border-cyan-500/30 bg-cyan-500/5',
  'border-purple-500/30 bg-purple-500/5',
  'border-orange-500/30 bg-orange-500/5',
  'border-teal-500/30 bg-teal-500/5',
]

export function ClusterList() {
  const { data, isLoading } = useClusters()

  if (isLoading) return <LoadingSpinner text="Loading clusters..." />
  if (!data?.clusters.length) return <EmptyState title="No clusters yet" description="Run clustering to group papers by topic." />

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data.clusters.map((cluster, idx) => (
        <div
          key={cluster.id}
          className={`rounded-lg border p-4 ${CLUSTER_COLORS[idx % CLUSTER_COLORS.length]}`}
        >
          <div className="mb-2 flex items-center gap-2">
            <Network className="h-4 w-4 text-gray-400" />
            <span className="text-xs text-gray-500">{cluster.paper_count} papers</span>
          </div>
          <h3 className="mb-2 text-sm font-medium text-white">{cluster.label}</h3>
          <div className="flex flex-wrap gap-1">
            {cluster.top_terms.map((term) => (
              <span key={term} className="rounded bg-[#1a1a1a] px-2 py-0.5 text-xs text-gray-400">
                {term}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
