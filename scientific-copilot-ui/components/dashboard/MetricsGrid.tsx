'use client'

import { FileText, Lightbulb, CheckCircle, FlaskConical, Star, RefreshCw } from 'lucide-react'
import { clsx } from 'clsx'

interface MetricsGridProps {
  totalPapers: number
  totalHypotheses: number
  passedDebate: number
  completedExperiments: number
  avgNovelty: number
  maxIteration: number
}

interface MetricCardProps {
  label: string
  value: string | number
  icon: React.ReactNode
  color: string
}

function MetricCard({ label, value, icon, color }: MetricCardProps) {
  return (
    <div className="rounded-lg border border-[#222222] bg-[#111111] p-4">
      <div className="mb-2 flex items-center gap-2">
        <div className={clsx('flex h-8 w-8 items-center justify-center rounded-lg', color)}>{icon}</div>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )
}

export function MetricsGrid(props: MetricsGridProps) {
  const cards: MetricCardProps[] = [
    { label: 'Papers Ingested', value: props.totalPapers, icon: <FileText className="h-4 w-4 text-blue-400" />, color: 'bg-blue-500/10' },
    { label: 'Hypotheses Generated', value: props.totalHypotheses, icon: <Lightbulb className="h-4 w-4 text-amber-400" />, color: 'bg-amber-500/10' },
    { label: 'Passed Debate', value: props.passedDebate, icon: <CheckCircle className="h-4 w-4 text-green-400" />, color: 'bg-green-500/10' },
    { label: 'Experiments Completed', value: props.completedExperiments, icon: <FlaskConical className="h-4 w-4 text-purple-400" />, color: 'bg-purple-500/10' },
    { label: 'Avg Novelty Score', value: props.avgNovelty.toFixed(2), icon: <Star className="h-4 w-4 text-indigo-400" />, color: 'bg-indigo-500/10' },
    { label: 'Feedback Iterations', value: props.maxIteration, icon: <RefreshCw className="h-4 w-4 text-cyan-400" />, color: 'bg-cyan-500/10' },
  ]

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map((card) => (
        <MetricCard key={card.label} {...card} />
      ))}
    </div>
  )
}
