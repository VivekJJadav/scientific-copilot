'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { usePipelineState } from '@/lib/hooks/usePipelineState'
import { useStageRunner } from '@/components/pipeline/StageRunner'
import { useAppStore } from '@/lib/store/appStore'
import { LoadingPulse } from '@/components/shared/LoadingPulse'

function formatElapsed(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (minutes > 0) return `${minutes}m${secs.toString().padStart(2, '0')}s`
  return `${secs}s`
}

export function NextStepPrompt() {
  const { currentStage, nextAction, isRunning, counts } = usePipelineState()
  const { runStage } = useStageRunner()
  const { openDrawerWith } = useAppStore()
  const [resultMessage, setResultMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isNoOpResult, setIsNoOpResult] = useState(false)
  const [elapsedMs, setElapsedMs] = useState(0)
  const startTimeRef = useRef<number | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // For drawer-based stages, open the drawer directly
  const isDrawerStage = currentStage === 'review' || currentStage === 'feedback'

  // Elapsed timer
  useEffect(() => {
    if (isRunning) {
      if (!startTimeRef.current) startTimeRef.current = Date.now()
      intervalRef.current = setInterval(() => {
        setElapsedMs(Date.now() - (startTimeRef.current ?? Date.now()))
      }, 100)
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current)
      startTimeRef.current = null
      setElapsedMs(0)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [isRunning])

  const handleAction = useCallback(async () => {
    setErrorMessage(null)
    setResultMessage(null)

    // For stages that have dedicated drawers, open them instead of executing inline
    if (currentStage === 'feedback') {
      openDrawerWith('feedback')
      return
    }
    if (currentStage === 'review') {
      openDrawerWith('review')
      return
    }

    const result = await runStage(currentStage)

    if (result.success) {
      const elapsed = result.elapsedMs ? ` (${formatElapsed(result.elapsedMs)})` : ''
      setResultMessage(`${result.message}${elapsed}`)
      setIsNoOpResult(!!result.isNoOp)
      setTimeout(() => setResultMessage(null), 4000)
    } else {
      setErrorMessage(result.message)
    }
  }, [currentStage, runStage, openDrawerWith])

  const displayText = nextAction.text
    .replace('{n}', String(counts.pendingHypotheses || counts.approvedHypotheses || 0))

  return (
    <div className="absolute bottom-16 left-4 z-30">
      <div className="panel-glass rounded-lg px-4 py-3 shadow-2xl max-w-sm">
        {resultMessage ? (
          <div className="animate-slide-in-left">
            <div className="flex items-center gap-2 mb-0.5">
              <span className={`text-[9px] font-mono tracking-wider ${isNoOpResult ? 'text-signal-cyan' : 'text-signal-green'}`}>
                {isNoOpResult ? 'ℹ NO ACTION' : '✓ COMPLETE'}
              </span>
            </div>
            <p className={`text-[10px] font-mono leading-relaxed ${isNoOpResult ? 'text-signal-cyan/80' : 'text-signal-green/80'}`}>
              {resultMessage}
            </p>
          </div>
        ) : errorMessage ? (
          <div className="animate-shake">
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-signal-red text-[9px] font-mono tracking-wider">✕ ERROR</span>
            </div>
            <p className="text-[10px] font-mono text-signal-red/80 mb-2.5 leading-relaxed">{errorMessage}</p>
            <button
              onClick={handleAction}
              className="px-3 py-1.5 bg-signal-red/10 text-signal-red text-[9px] font-mono font-medium rounded border border-signal-red/25 hover:bg-signal-red/20 hover:border-signal-red/40 transition-all cursor-pointer tracking-wider"
            >
              [RETRY]
            </button>
          </div>
        ) : (
          <>
            {/* Terminal prompt */}
            <div className="flex items-start gap-2 mb-3">
              <span className="text-signal-cyan text-[10px] font-mono mt-0.5 shrink-0">›</span>
              <div>
                <p className="text-[10px] font-mono text-text-secondary leading-relaxed">
                  {displayText}
                  <span className="inline-block w-[5px] h-[10px] bg-signal-cyan/60 ml-0.5 animate-cursor-blink" />
                </p>
              </div>
            </div>

            {/* Action button */}
            <button
              onClick={handleAction}
              disabled={isRunning}
              className="group relative flex items-center gap-2.5 px-3.5 py-2 bg-signal-cyan/8 text-signal-cyan text-[10px] font-mono font-medium rounded border border-signal-cyan/25 hover:bg-signal-cyan/15 hover:border-signal-cyan/40 transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer tracking-wider overflow-hidden"
            >
              {isRunning ? (
                <>
                  <div className="scan-line-overlay" />
                  <LoadingPulse />
                  <span className="font-mono tabular-nums">{formatElapsed(elapsedMs)}</span>
                </>
              ) : (
                <>
                  <span>{isDrawerStage ? '[OPEN]' : '[EXECUTE]'}</span>
                  <span className="text-text-muted text-[8px]">{nextAction.action}</span>
                </>
              )}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
