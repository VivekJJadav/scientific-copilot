'use client'

import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '@/lib/store/appStore'
import { usePipelineState } from '@/lib/hooks/usePipelineState'
import { useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { getHypotheses } from '@/lib/api/hypotheses'
import { resetDatabase } from '@/lib/api/admin'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

export function DashboardDrawer() {
  const { openDrawer, closeDrawer, ingestLimit, setIngestLimit, isRunning } = useAppStore()
  const isOpen = openDrawer === 'dashboard'
  const { counts } = usePipelineState()
  const queryClient = useQueryClient()
  const [isResetting, setIsResetting] = useState(false)
  const fetchLimitOptions = useMemo(() => [2, 5, 10, 20], [])

  const { data: hypothesesData } = useQuery({
    queryKey: ['hypotheses', { limit: 100 }],
    queryFn: () => getHypotheses({ limit: 100 }),
    enabled: isOpen,
  })

  const hypotheses = hypothesesData?.items ?? []

  const avgNovelty =
    hypotheses.length > 0
      ? hypotheses.reduce((sum, h) => sum + h.novelty_score, 0) / hypotheses.length
      : 0

  const passedDebate = hypotheses.filter(
    (h) => h.debate_rounds !== null && h.debate_rounds > 0
  ).length

  const chartData = hypotheses
    .map((h) => ({
      date: new Date(h.created_at).toLocaleDateString(),
      novelty: h.novelty_score,
      status: h.status,
    }))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())

  const stats = [
    { label: 'PAPERS', value: counts.papers, color: '#00d4ff' },
    { label: 'HYPOTHESES', value: counts.hypotheses, color: '#a78bfa' },
    { label: 'DEBATED', value: passedDebate, color: '#00e5a0' },
    { label: 'EXPERIMENTS', value: counts.experiments, color: '#ffb224' },
    { label: 'AVG NOV', value: avgNovelty.toFixed(2), color: '#a78bfa' },
    { label: 'CYCLE', value: counts.maxIteration, color: '#00d4ff' },
  ]

  useEffect(() => {
    const savedLimit = window.localStorage.getItem('dashboard.ingestLimit')
    if (!savedLimit) return

    const parsedLimit = Number(savedLimit)
    if (Number.isFinite(parsedLimit) && parsedLimit > 0 && parsedLimit !== ingestLimit) {
      setIngestLimit(parsedLimit)
    }
  }, [ingestLimit, setIngestLimit])

  const cycleFetchLimit = () => {
    const currentIndex = fetchLimitOptions.indexOf(ingestLimit)
    const nextLimit = fetchLimitOptions[(currentIndex + 1) % fetchLimitOptions.length]
    setIngestLimit(nextLimit)
    window.localStorage.setItem('dashboard.ingestLimit', String(nextLimit))
  }

  const handleClearDb = async () => {
    const confirmed = window.confirm(
      'Clear all papers, hypotheses, experiments, clusters, gaps, and datasets from the database?'
    )
    if (!confirmed) return

    setIsResetting(true)
    try {
      await resetDatabase()
      await queryClient.invalidateQueries()
    } finally {
      setIsResetting(false)
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ y: 340, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 340, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed left-0 right-0 bottom-9 h-[340px] bg-surface border-t border-border z-50 flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border shrink-0">
            <span className="text-[8px] font-mono text-signal-cyan uppercase tracking-[0.15em]">✦ MISSION DASHBOARD</span>
            <div className="flex items-center gap-2">
              <button
                onClick={cycleFetchLimit}
                disabled={isRunning || isResetting}
                className="rounded-md border border-signal-cyan/30 bg-signal-cyan/8 px-2.5 py-1 text-[8px] font-mono uppercase tracking-[0.14em] text-signal-cyan transition-colors hover:border-signal-cyan/60 hover:bg-signal-cyan/12 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Fetch Limit: {ingestLimit}
              </button>
              <button
                onClick={handleClearDb}
                disabled={isRunning || isResetting}
                className="rounded-md border border-signal-red/30 bg-signal-red/8 px-2.5 py-1 text-[8px] font-mono uppercase tracking-[0.14em] text-signal-red transition-colors hover:border-signal-red/60 hover:bg-signal-red/12 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isResetting ? 'Clearing...' : 'Clear DB'}
              </button>
              <button
                onClick={closeDrawer}
                className="w-6 h-6 rounded flex items-center justify-center text-text-muted hover:text-signal-red hover:bg-signal-red/10 transition-colors cursor-pointer"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden px-4 py-3">
            {/* Stat cards */}
            <div className="grid grid-cols-6 gap-2 mb-3">
              {stats.map((stat) => (
                <div
                  key={stat.label}
                  className="bg-panel border border-border rounded-lg p-2.5 text-center hover:border-border-hover transition-colors"
                >
                  <p
                    className="text-lg font-mono font-bold tabular-nums"
                    style={{ color: stat.color, textShadow: `0 0 8px ${stat.color}20` }}
                  >
                    {stat.value}
                  </p>
                  <p className="text-[7px] font-mono text-text-muted uppercase tracking-[0.12em] mt-0.5">
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-3 mb-3">
              <button
                onClick={cycleFetchLimit}
                disabled={isRunning || isResetting}
                className="flex min-h-[64px] flex-col items-start justify-center rounded-xl border border-signal-cyan/35 bg-signal-cyan/10 px-3 py-2 text-left transition-colors hover:border-signal-cyan/70 hover:bg-signal-cyan/15 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span className="text-[9px] font-mono uppercase tracking-[0.16em] text-signal-cyan">
                  Fetch Papers
                </span>
                <span className="mt-1 text-xl font-mono font-bold text-signal-cyan">
                  {ingestLimit}
                </span>
                <span className="text-[8px] font-mono uppercase tracking-[0.1em] text-text-muted">
                  tap to cycle 2 / 5 / 10 / 20
                </span>
              </button>

              <button
                onClick={handleClearDb}
                disabled={isRunning || isResetting}
                className="flex min-h-[64px] flex-col items-start justify-center rounded-xl border border-signal-red/35 bg-signal-red/10 px-3 py-2 text-left transition-colors hover:border-signal-red/70 hover:bg-signal-red/15 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span className="text-[9px] font-mono uppercase tracking-[0.16em] text-signal-red">
                  Clear Database
                </span>
                <span className="mt-1 text-sm font-mono font-bold text-signal-red">
                  {isResetting ? 'clearing now' : 'truncate all app tables'}
                </span>
                <span className="text-[8px] font-mono uppercase tracking-[0.1em] text-text-muted">
                  papers, hypotheses, experiments, gaps
                </span>
              </button>
            </div>

            {/* Charts row */}
            <div className="grid grid-cols-2 gap-3 h-[170px]">
              {/* Novelty trend */}
              <div className="bg-panel border border-border rounded-lg p-2.5">
                <p className="text-[7px] font-mono text-text-muted uppercase tracking-[0.12em] mb-1.5">
                  NOVELTY TREND
                </p>
                <ResponsiveContainer width="100%" height="85%">
                  <LineChart data={chartData}>
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 7, fill: '#344055', fontFamily: 'var(--font-ibm-plex-mono)' }}
                      stroke="#1a2332"
                    />
                    <YAxis
                      domain={[0, 1]}
                      tick={{ fontSize: 7, fill: '#344055', fontFamily: 'var(--font-ibm-plex-mono)' }}
                      stroke="#1a2332"
                      width={25}
                    />
                    <Tooltip
                      contentStyle={{
                        background: '#0a0e14',
                        border: '0.5px solid #1a2332',
                        borderRadius: 4,
                        fontSize: 9,
                        fontFamily: 'var(--font-ibm-plex-mono), monospace',
                        color: '#d0d8e8',
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="novelty"
                      stroke="#a78bfa"
                      strokeWidth={1.5}
                      dot={{ r: 2, fill: '#a78bfa' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Pipeline status bars */}
              <div className="bg-panel border border-border rounded-lg p-2.5">
                <p className="text-[7px] font-mono text-text-muted uppercase tracking-[0.12em] mb-2.5">
                  PIPELINE STATUS
                </p>
                <div className="space-y-3">
                  <PipelineBar
                    label="PAPERS"
                    segments={[
                      { value: counts.processedPapers, color: '#00d4ff', label: 'processed' },
                      { value: counts.papers - counts.processedPapers, color: '#344055', label: 'raw' },
                    ]}
                    total={counts.papers}
                  />
                  <PipelineBar
                    label="HYPOTHESES"
                    segments={[
                      { value: hypotheses.filter((h) => h.status === 'approved').length, color: '#00e5a0', label: 'approved' },
                      { value: hypotheses.filter((h) => h.status === 'pending').length, color: '#ffb224', label: 'pending' },
                      { value: hypotheses.filter((h) => h.status === 'rejected').length, color: '#ff3b5c', label: 'rejected' },
                    ]}
                    total={counts.hypotheses}
                  />
                  <PipelineBar
                    label="EXPERIMENTS"
                    segments={[
                      { value: counts.completedExperiments, color: '#00e5a0', label: 'completed' },
                      { value: counts.experiments - counts.completedExperiments, color: '#344055', label: 'other' },
                    ]}
                    total={counts.experiments}
                  />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

interface PipelineBarProps {
  label: string
  segments: { value: number; color: string; label: string }[]
  total: number
}

function PipelineBar({ label, segments, total }: PipelineBarProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[8px] font-mono text-text-secondary tracking-wider">{label}</span>
        <span className="text-[8px] font-mono text-text-muted tabular-nums">{total}</span>
      </div>
      <div className="h-2 bg-void rounded-full overflow-hidden flex">
        {segments.map((seg, i) =>
          seg.value > 0 ? (
            <div
              key={i}
              className="h-full transition-all duration-500 animate-fill-bar"
              style={{
                width: total > 0 ? `${(seg.value / total) * 100}%` : '0%',
                backgroundColor: seg.color,
                boxShadow: `0 0 4px ${seg.color}30`,
              }}
              title={`${seg.label}: ${seg.value}`}
            />
          ) : null
        )}
      </div>
    </div>
  )
}
