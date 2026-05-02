'use client'

import { useState, useEffect } from 'react'
import { usePipelineState, type Stage, type StageStatus } from '@/lib/hooks/usePipelineState'
import { useAppStore } from '@/lib/store/appStore'

const STAGE_LABELS: Record<Stage, string> = {
  ingest: 'INGEST',
  extract: 'EXTRACT',
  cluster: 'CLUSTER',
  hypothesize: 'HYPOTHESIZE',
  debate: 'DEBATE',
  review: 'REVIEW',
  run: 'EXECUTE',
  feedback: 'FEEDBACK',
  done: 'COMPLETE',
}

const STAGE_ICONS: Record<Stage, string> = {
  ingest: '↓',
  extract: '◇',
  cluster: '⬡',
  hypothesize: '△',
  debate: '⟐',
  review: '◎',
  run: '▶',
  feedback: '↻',
  done: '✦',
}

const DISPLAY_STAGES: Stage[] = ['ingest', 'extract', 'cluster', 'hypothesize', 'debate', 'review', 'run', 'feedback']

function getStageCount(stage: Stage, counts: ReturnType<typeof usePipelineState>['counts']): string {
  switch (stage) {
    case 'ingest': return counts.papers > 0 ? `${counts.papers}` : '—'
    case 'extract': return counts.processedPapers > 0 ? `${counts.processedPapers}` : '—'
    case 'cluster': return counts.clusters > 0 ? `${counts.clusters}` : '—'
    case 'hypothesize': return counts.hypotheses > 0 ? `${counts.hypotheses}` : '—'
    case 'debate': return counts.debatedHypotheses > 0 ? `${counts.debatedHypotheses}` : '—'
    case 'review': return counts.reviewableHypotheses > 0 ? `${counts.reviewableHypotheses}` : '—'
    case 'run': return counts.experiments > 0 ? `${counts.experiments}` : '—'
    case 'feedback': return counts.maxIteration > 0 ? `${counts.maxIteration}` : '—'
    default: return '—'
  }
}

function StageIndicator({ stage, status, count, onClick }: {
  stage: Stage
  status: StageStatus
  count: string
  onClick: () => void
}) {
  const isDone = status === 'done'
  const isActive = status === 'active'
  const isRunning = status === 'running'
  const isClickable = isDone || isActive || isRunning || ['debate', 'review', 'run', 'feedback'].includes(stage)

  return (
    <button
      onClick={onClick}
      disabled={!isClickable}
      className={`relative flex items-center gap-1.5 px-2.5 py-1.5 rounded transition-all duration-300 cursor-pointer ${
        isRunning
          ? 'bg-signal-cyan/8 border border-signal-cyan/30'
          : isActive
          ? 'bg-signal-cyan/5 border border-signal-cyan/20'
          : isDone
          ? 'bg-signal-green/5 border border-signal-green/15'
          : isClickable
          ? 'bg-transparent border border-border hover:border-border-hover'
          : 'bg-transparent border border-border/50 opacity-40 !cursor-not-allowed'
      }`}
    >
      {/* Scan line overlay for running state */}
      {isRunning && <div className="scan-line-overlay" />}

      {/* Stage icon */}
      <span className={`text-[10px] ${
        isRunning ? 'text-signal-cyan animate-signal-pulse' :
        isActive ? 'text-signal-cyan' :
        isDone ? 'text-signal-green' :
        'text-text-muted'
      }`}>
        {isDone ? '✓' : STAGE_ICONS[stage]}
      </span>

      {/* Stage name */}
      <span className={`text-[9px] font-mono tracking-widest ${
        isRunning ? 'text-signal-cyan' :
        isActive ? 'text-signal-cyan' :
        isDone ? 'text-signal-green/80' :
        'text-text-muted'
      }`}>
        {STAGE_LABELS[stage]}
      </span>

      {/* Count readout */}
      {count !== '—' && (
        <span className={`text-[8px] font-mono tabular-nums ${
          isDone ? 'text-signal-green/60' :
          isActive || isRunning ? 'text-signal-cyan/60' :
          'text-text-muted/60'
        }`}>
          {count}
        </span>
      )}
    </button>
  )
}

function StageConnector({ completed }: { completed: boolean }) {
  return (
    <div className="w-4 h-[1px] mx-0.5 relative overflow-hidden">
      <div
        className="absolute inset-0 transition-all duration-500"
        style={{
          background: completed
            ? 'linear-gradient(90deg, #00e5a060, #00e5a0, #00e5a060)'
            : '#1a2332',
        }}
      />
    </div>
  )
}

function ElapsedTimer() {
  const { isRunning } = useAppStore()
  const [elapsed, setElapsed] = useState(0)
  const [startTime] = useState(() => Date.now())

  useEffect(() => {
    if (!isRunning) {
      setElapsed(0)
      return
    }
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 100)
    return () => clearInterval(interval)
  }, [isRunning, startTime])

  if (!isRunning) return null

  const minutes = Math.floor(elapsed / 60)
  const seconds = elapsed % 60
  const timeStr = minutes > 0
    ? `${minutes}m${seconds.toString().padStart(2, '0')}s`
    : `${seconds}s`

  return (
    <span className="text-[9px] font-mono tabular-nums text-signal-cyan/70">
      {timeStr}
    </span>
  )
}

export function PipelineStepper() {
  const pipelineState = usePipelineState()
  const { stageStatus, isRunning, runningStage, counts } = pipelineState
  const { openDrawerWith, taskProgress, taskMessage } = useAppStore()

  const handleStageClick = (stage: Stage) => {
    const currentIndex = DISPLAY_STAGES.indexOf(stage)
    const activeIndex = DISPLAY_STAGES.indexOf(pipelineState.currentStage)

    const isAlwaysClickable = ['debate', 'review', 'run', 'feedback'].includes(stage)

    if (currentIndex <= activeIndex || isAlwaysClickable) {
      if (stage === 'review') openDrawerWith('review')
      else if (stage === 'debate') openDrawerWith('debate')
      else if (stage === 'run') openDrawerWith('experiment')
      else if (stage === 'feedback') openDrawerWith('feedback')
    }
  }

  return (
    <div className="h-12 w-full bg-surface border-b border-border flex items-center px-4 shrink-0 z-40">
      {/* Logo */}
      <div className="flex items-center gap-1 mr-6 select-none">
        <span className="text-[11px] font-mono font-semibold text-text-primary tracking-tight">
          sci
        </span>
        <span className="w-1 h-1 rounded-full bg-signal-cyan animate-signal-pulse" />
        <span className="text-[11px] font-mono font-semibold text-text-primary tracking-tight">
          copilot
        </span>
      </div>

      {/* Stepper */}
      <div className="flex items-center flex-1 justify-center">
        {DISPLAY_STAGES.map((stage, index) => {
          const status = stageStatus[stage]
          const count = getStageCount(stage, counts)
          return (
            <div key={stage} className="flex items-center">
              <StageIndicator
                stage={stage}
                status={status}
                count={count}
                onClick={() => handleStageClick(stage)}
              />
              {index < DISPLAY_STAGES.length - 1 && (
                <StageConnector completed={status === 'done'} />
              )}
            </div>
          )
        })}
      </div>

      {/* System status readout */}
      <div className="flex items-center gap-2 ml-6">
        {isRunning ? (
          <div className="flex items-center gap-2 px-2.5 py-1 rounded border border-signal-cyan/20 bg-signal-cyan/5">
            <div className="w-1.5 h-1.5 rounded-full bg-signal-cyan animate-signal-pulse" />
            <span className="text-[9px] font-mono tracking-wider text-signal-cyan">
              {runningStage ? `${runningStage.toUpperCase()}` : 'PROCESSING'}
            </span>
            <span className="text-[9px] font-mono tracking-wider text-signal-cyan/60">
              {taskProgress}%
            </span>
            {taskMessage && (
              <span className="text-[9px] font-mono tracking-wider text-signal-cyan/60 max-w-[180px] truncate">
                {taskMessage}
              </span>
            )}
            <ElapsedTimer />
          </div>
        ) : (
          <div className="flex items-center gap-2 px-2.5 py-1 rounded border border-signal-green/20 bg-signal-green/5">
            <div className="w-1.5 h-1.5 rounded-full bg-signal-green" />
            <span className="text-[9px] font-mono tracking-wider text-signal-green">READY</span>
          </div>
        )}
      </div>
    </div>
  )
}
