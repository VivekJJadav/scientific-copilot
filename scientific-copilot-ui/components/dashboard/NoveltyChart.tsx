'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import type { Hypothesis } from '@/lib/types/hypothesis'

interface NoveltyChartProps {
  hypotheses: Hypothesis[]
}

export function NoveltyChart({ hypotheses }: NoveltyChartProps) {
  const data = [...hypotheses]
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .map((h) => ({
      date: new Date(h.created_at).toLocaleDateString(),
      title: h.title.slice(0, 40) + '...',
      novelty: h.novelty_score,
      feasibility: h.feasibility_score,
    }))

  if (!data.length) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-[#222222] bg-[#111111] text-sm text-gray-500">
        No hypothesis data available for chart.
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-[#222222] bg-[#111111] p-4">
      <h3 className="mb-4 text-sm font-medium text-gray-400">Novelty & Feasibility Trend</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#222" />
          <XAxis dataKey="date" tick={{ fill: '#666', fontSize: 11 }} />
          <YAxis domain={[0, 1]} tick={{ fill: '#666', fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: '#111', border: '1px solid #333', borderRadius: 8 }}
            labelStyle={{ color: '#999' }}
            formatter={(value: number, name: string) => [value.toFixed(2), name]}
            labelFormatter={(_label: string, payload: Array<{ payload: { title: string } }>) =>
              payload[0]?.payload?.title ?? ''
            }
          />
          <Legend wrapperStyle={{ fontSize: 12, color: '#999' }} />
          <Line type="monotone" dataKey="novelty" stroke="#818cf8" strokeWidth={2} dot={{ r: 3 }} />
          <Line type="monotone" dataKey="feasibility" stroke="#34d399" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
