'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '@/lib/store/appStore'
import { usePipelineState } from '@/lib/hooks/usePipelineState'
import { useStageRunner } from '@/components/pipeline/StageRunner'
import { LoadingPulse } from '@/components/shared/LoadingPulse'

interface FeedbackResult {
  experiments_analyzed: number
  new_gaps_from_failures: number
  arbiter_examples_updated: number
  new_hypotheses_generated: number
}

function StatCell({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-void border border-border rounded-lg p-3 text-center">
      <p
        className="text-2xl font-mono font-bold tabular-nums"
        style={{ color, textShadow: `0 0 10px ${color}40` }}
      >
        {value}
      </p>
      <p className="text-[7px] font-mono text-text-muted uppercase tracking-[0.12em] mt-1">
        {label}
      </p>
    </div>
  )
}

export function FeedbackDrawer() {
  const { openDrawer, closeDrawer } = useAppStore()
  const isOpen = openDrawer === 'feedback'
  const { counts, isRunning: pipelineRunning } = usePipelineState()
  const { runStage, isRunning } = useStageRunner()

  const [result, setResult] = useState<FeedbackResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [hasRun, setHasRun] = useState(false)

  const canRun = counts.completedExperiments > 0
  const hasApprovedWithNoExperiments = counts.approvedHypotheses > 0 && counts.experiments === 0

  const handleRunFeedback = async () => {
    setError(null)
    setResult(null)
    setHasRun(false)

    const stageResult = await runStage('feedback')

    if (stageResult.success) {
      setHasRun(true)
      // Parse the message to extract numbers — or rely on the next query invalidation
      // The result message format: "Analyzed N, generated M new hypotheses"
      // We'll just show the message + trigger a re-read via invalidation (already done in runStage)
    } else {
      setError(stageResult.message)
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: 380, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 380, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed right-0 top-12 bottom-9 w-[380px] bg-surface border-l border-border z-50 flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-border shrink-0">
            <div className="flex items-center gap-2">
              <span className="text-[8px] font-mono text-signal-cyan uppercase tracking-[0.15em]">
                ↻ FEEDBACK LOOP
              </span>
              {counts.maxIteration > 0 && (
                <span className="px-1.5 py-0.5 bg-signal-cyan/15 text-signal-cyan text-[8px] font-mono rounded border border-signal-cyan/20 tabular-nums">
                  CYCLE {counts.maxIteration}
                </span>
              )}
            </div>
            <button
              onClick={closeDrawer}
              className="w-6 h-6 rounded flex items-center justify-center text-text-muted hover:text-signal-red hover:bg-signal-red/10 transition-colors cursor-pointer"
            >
              ✕
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Current pipeline state context */}
            <div className="space-y-1.5">
              <p className="text-[7px] font-mono text-text-muted uppercase tracking-[0.12em]">
                Pipeline State
              </p>
              <div className="grid grid-cols-2 gap-1.5">
                <div className="bg-panel border border-border rounded px-3 py-2 flex items-center justify-between">
                  <span className="text-[8px] font-mono text-text-muted">Approved</span>
                  <span
                    className="text-[11px] font-mono font-bold tabular-nums"
                    style={{ color: counts.approvedHypotheses > 0 ? '#00e5a0' : '#344055' }}
                  >
                    {counts.approvedHypotheses}
                  </span>
                </div>
                <div className="bg-panel border border-border rounded px-3 py-2 flex items-center justify-between">
                  <span className="text-[8px] font-mono text-text-muted">Experiments</span>
                  <span
                    className="text-[11px] font-mono font-bold tabular-nums"
                    style={{ color: counts.experiments > 0 ? '#ffb224' : '#344055' }}
                  >
                    {counts.experiments}
                  </span>
                </div>
                <div className="bg-panel border border-border rounded px-3 py-2 flex items-center justify-between">
                  <span className="text-[8px] font-mono text-text-muted">Completed</span>
                  <span
                    className="text-[11px] font-mono font-bold tabular-nums"
                    style={{ color: counts.completedExperiments > 0 ? '#00e5a0' : '#344055' }}
                  >
                    {counts.completedExperiments}
                  </span>
                </div>
                <div className="bg-panel border border-border rounded px-3 py-2 flex items-center justify-between">
                  <span className="text-[8px] font-mono text-text-muted">Cycle</span>
                  <span
                    className="text-[11px] font-mono font-bold tabular-nums"
                    style={{ color: counts.maxIteration > 0 ? '#00d4ff' : '#344055' }}
                  >
                    {counts.maxIteration > 0 ? counts.maxIteration : '—'}
                  </span>
                </div>
              </div>
            </div>

            {/* Prereq warning */}
            {!canRun && !hasApprovedWithNoExperiments && (
              <div
                className="rounded-lg p-3 space-y-1"
                style={{
                  backgroundColor: '#ffb22408',
                  border: '0.5px solid #ffb22430',
                }}
              >
                <p className="text-[9px] font-mono text-signal-amber uppercase tracking-wider">
                  ⚠ Prerequisites not met
                </p>
                <p className="text-[8px] font-mono text-text-muted leading-relaxed">
                  You need at least one <span className="text-signal-amber">completed experiment</span> to
                  run the feedback loop. Run experiments first.
                </p>
              </div>
            )}

            {hasApprovedWithNoExperiments && !canRun && (
              <div
                className="rounded-lg p-3 space-y-1"
                style={{
                  backgroundColor: '#00d4ff08',
                  border: '0.5px solid #00d4ff20',
                }}
              >
                <p className="text-[9px] font-mono text-signal-cyan uppercase tracking-wider">
                  → Run Experiments First
                </p>
                <p className="text-[8px] font-mono text-text-muted leading-relaxed">
                  {counts.approvedHypotheses} approved hypothesis
                  {counts.approvedHypotheses !== 1 ? 'es' : ''} ready. Execute experiments
                  before closing the feedback loop.
                </p>
              </div>
            )}

            {/* Run button */}
            <div className="space-y-2">
              <p className="text-[7px] font-mono text-text-muted uppercase tracking-[0.12em]">
                Action
              </p>
              <button
                onClick={handleRunFeedback}
                disabled={isRunning || pipelineRunning}
                className={`w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg font-mono text-[10px] font-medium tracking-wider border transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed relative overflow-hidden ${
                  canRun
                    ? 'bg-signal-cyan/8 text-signal-cyan border-signal-cyan/25 hover:bg-signal-cyan/15 hover:border-signal-cyan/40'
                    : 'bg-text-muted/5 text-text-muted border-border hover:border-border-hover'
                }`}
              >
                {isRunning ? (
                  <>
                    <div className="scan-line-overlay" />
                    <LoadingPulse />
                    <span>Running feedback loop…</span>
                  </>
                ) : (
                  <>
                    <span className="text-[13px]">↻</span>
                    <span>[RUN FEEDBACK LOOP]</span>
                  </>
                )}
              </button>

              {!canRun && (
                <p className="text-[8px] font-mono text-text-muted/60 text-center">
                  Requires completed experiments
                </p>
              )}
            </div>

            {/* Error */}
            {error && (
              <div
                className="rounded-lg p-3 animate-shake"
                style={{
                  backgroundColor: '#ff3b5c08',
                  border: '0.5px solid #ff3b5c30',
                }}
              >
                <p className="text-[9px] font-mono text-signal-red uppercase tracking-wider mb-1">
                  ✕ Error
                </p>
                <p className="text-[8px] font-mono text-signal-red/70 leading-relaxed">{error}</p>
              </div>
            )}

            {/* Success result */}
            {hasRun && !error && !isRunning && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-2"
              >
                <p className="text-[7px] font-mono text-signal-green uppercase tracking-[0.12em]">
                  ✓ Feedback loop complete
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <StatCell label="Experiments Analyzed" value={counts.completedExperiments} color="#00e5a0" />
                  <StatCell label="New Cycle" value={counts.maxIteration} color="#00d4ff" />
                </div>
                <div
                  className="rounded-lg p-3"
                  style={{
                    backgroundColor: '#00e5a008',
                    border: '0.5px solid #00e5a020',
                  }}
                >
                  <p className="text-[8px] font-mono text-text-secondary leading-relaxed">
                    The system has analyzed experiment results, extracted lessons from failures,
                    and seeded new hypotheses for the next research cycle.
                  </p>
                </div>
              </motion.div>
            )}

            {/* What happens section */}
            <div className="space-y-2 pt-2 border-t border-border">
              <p className="text-[7px] font-mono text-text-muted uppercase tracking-[0.12em]">
                What the feedback loop does
              </p>
              {[
                { icon: '①', label: 'Analyze experiments', desc: 'Assess outcomes of completed experiments' },
                { icon: '②', label: 'Extract lessons', desc: 'Identify gaps from failures and negative results' },
                { icon: '③', label: 'Update arbiter', desc: 'Strengthen debate few-shot examples' },
                { icon: '④', label: 'Generate hypotheses', desc: 'Spawn next-iteration hypotheses from gaps' },
              ].map((step) => (
                <div key={step.icon} className="flex items-start gap-2.5">
                  <span className="text-[9px] font-mono text-signal-cyan/60 mt-0.5 shrink-0">{step.icon}</span>
                  <div>
                    <p className="text-[8px] font-mono text-text-secondary">{step.label}</p>
                    <p className="text-[7px] font-mono text-text-muted/70 mt-0.5">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
