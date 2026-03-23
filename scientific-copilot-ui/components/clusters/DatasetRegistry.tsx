'use client'

import { useDatasets } from '@/lib/hooks/useClusters'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { EmptyState } from '@/components/shared/EmptyState'
import { Database } from 'lucide-react'

export function DatasetRegistry() {
  const { data, isLoading } = useDatasets()

  if (isLoading) return <LoadingSpinner text="Loading datasets..." />
  if (!data?.datasets.length) return <EmptyState title="No datasets found" description="Run dataset extraction to populate this list." />

  return (
    <div className="rounded-lg border border-[#222222] bg-[#111111]">
      <div className="border-b border-[#222222] px-4 py-3">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-indigo-400" />
          <h3 className="text-sm font-medium text-white">Dataset Registry</h3>
          <span className="text-xs text-gray-500">({data.total} entries)</span>
        </div>
      </div>
      <div className="divide-y divide-[#1a1a1a]">
        {data.datasets.map((ds) => (
          <div key={ds.id} className="flex items-center justify-between px-4 py-3">
            <div>
              <span className="text-sm text-gray-200">{ds.name}</span>
              <span className="ml-2 text-xs text-gray-600">{ds.paper_count} papers</span>
            </div>
            <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-xs font-medium text-indigo-400">
              ×{ds.mention_count}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
