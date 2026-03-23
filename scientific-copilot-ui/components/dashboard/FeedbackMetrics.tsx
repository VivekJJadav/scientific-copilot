'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { Hypothesis } from '@/lib/types/hypothesis'

interface FeedbackMetricsProps {
  hypotheses: Hypothesis[]
}

export function FeedbackMetrics({ hypotheses }: FeedbackMetricsProps) {
  // Build iteration count distribution
  const distribution = new Map<number, number>()
  for (const h of hypotheses) {
    const count = distribution.get(h.iteration_count) ?? 0
    distribution.set(h.iteration_count, count + 1)
  }

  const maxIter = Math.max(0, ...distribution.keys())
  const data = Array.from({ length: maxIter + 1 }, (_, i) => ({
    iteration: i.toString(),
    count: distribution.get(i) ?? 0,
  }))

  if (!data.length || hypotheses.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-[#222222] bg-[#111111] text-sm text-gray-500">
        No feedback loop data available.
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-[#222222] bg-[#111111] p-4">
      <h3 className="mb-4 text-sm font-medium text-gray-400">Feedback Loop — Iteration Distribution</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#222" />
          <XAxis
            dataKey="iteration"
            tick={{ fill: '#666', fontSize: 11 }}
            label={{ value: 'Iteration Count', position: 'insideBottom', offset: -2, fill: '#666', fontSize: 11 }}
          />
          <YAxis tick={{ fill: '#666', fontSize: 11 }} allowDecimals={false} />
          <Tooltip
            contentStyle={{ background: '#111', border: '1px solid #333', borderRadius: 8 }}
            labelStyle={{ color: '#999' }}
            formatter={(value: number) => [value, 'Hypotheses']}
            labelFormatter={(label: string) => `Iteration ${label}`}
          />
          <Bar dataKey="count" fill="#818cf8" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
