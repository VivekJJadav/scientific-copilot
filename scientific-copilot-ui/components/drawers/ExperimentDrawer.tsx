'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '@/lib/store/appStore'
import { useQuery } from '@tanstack/react-query'
import { getExperiments } from '@/lib/api/experiments'
import type { Experiment } from '@/lib/types/experiment'
import { useStageRunner } from '@/components/pipeline/StageRunner'

function ExperimentStatusIndicator({ status }: { status: string }) {
  switch (status) {
    case 'queued':
      return <div className="w-3 h-3 rounded-full bg-text-muted animate-breathe" />
    case 'running':
      return (
        <div className="w-3 h-3 rounded-full border-2 border-signal-cyan border-t-transparent animate-spin" />
      )
    case 'completed':
      return (
        <div className="w-3 h-3 rounded-full bg-signal-green flex items-center justify-center">
          <svg width="7" height="7" viewBox="0 0 7 7" fill="none">
            <path d="M1 3.5L2.5 5L6 1.5" stroke="white" strokeWidth="1.2" strokeLinecap="round" />
          </svg>
        </div>
      )
    case 'failed':
      return (
        <div className="w-3 h-3 rounded-full bg-signal-red flex items-center justify-center">
          <span className="text-white text-[6px] font-bold">✕</span>
        </div>
      )
    default:
      return <div className="w-3 h-3 rounded-full bg-text-muted" />
  }
}

export function ExperimentDrawer() {
  const { openDrawer, drawerData, closeDrawer } = useAppStore()
  const isOpen = openDrawer === 'experiment'
  const hypothesisId = (drawerData as { hypothesisId?: string }).hypothesisId ?? ''

  const { runStage } = useStageRunner()

  const { data: experimentsData } = useQuery({
    queryKey: ['experiments', { limit: 100 }],
    queryFn: () => getExperiments({ limit: 100 }),
    enabled: isOpen,
  })

  const experiments = (experimentsData?.items ?? []).filter(
    (e: Experiment) => !hypothesisId || e.hypothesis_id === hypothesisId
  )

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: 360, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 360, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed right-0 top-12 bottom-9 w-[360px] bg-surface border-l border-border z-50 flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-border shrink-0">
            <span className="text-[8px] font-mono text-signal-amber uppercase tracking-[0.15em]">▶ EXPERIMENTS</span>
            <button
              onClick={closeDrawer}
              className="w-6 h-6 rounded flex items-center justify-center text-text-muted hover:text-signal-red hover:bg-signal-red/10 transition-colors cursor-pointer"
            >
              ✕
            </button>
          </div>

          {/* Experiments */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3 relative">
            {experiments.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 space-y-4">
                <p className="text-[9px] font-mono text-text-muted tracking-wider">No experiments found</p>
                <button
                  onClick={() => runStage('run')}
                  className="px-4 py-2 bg-signal-amber/8 text-signal-amber text-[9px] font-mono font-medium rounded border border-signal-amber/25 hover:bg-signal-amber/15 transition-all cursor-pointer tracking-wider"
                >
                  [RUN EXPERIMENTS]
                </button>
              </div>
            ) : (
              experiments.map((exp: Experiment) => (
                <div key={exp.id} className="bg-panel border border-border rounded-lg p-3 space-y-2.5 hover:border-border-hover transition-colors">
                  {/* Status header */}
                  <div className="flex items-center gap-2">
                    <ExperimentStatusIndicator status={exp.status} />
                    <span className="text-[9px] font-mono font-medium text-text-primary uppercase tracking-wider">
                      {exp.status}
                    </span>
                    {exp.completed_at && (
                      <span className="text-[8px] font-mono text-text-muted ml-auto tabular-nums">
                        {new Date(exp.completed_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>

                  {/* Results */}
                  {exp.status === 'completed' && exp.results && (
                    <div className="space-y-2">
                      <div className="grid grid-cols-2 gap-1.5">
                        {Object.entries(exp.results).map(([key, value]) => (
                          <div key={key} className="bg-void rounded px-2 py-1.5 border border-border">
                            <p className="text-[7px] font-mono text-text-muted uppercase tracking-[0.1em]">{key}</p>
                            <p className="text-[10px] font-mono text-text-primary font-medium tabular-nums">
                              {typeof value === 'number' ? value.toFixed(4) : String(value)}
                            </p>
                          </div>
                        ))}
                      </div>

                      {exp.result_summary && (
                        <div className="border-l-2 border-signal-cyan/20 pl-2.5">
                          <p className="text-[9px] font-mono text-text-secondary italic leading-relaxed">{exp.result_summary}</p>
                        </div>
                      )}

                      {exp.wandb_run_url && (
                        <a
                          href={exp.wandb_run_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[9px] font-mono text-signal-cyan hover:text-signal-cyan/80 transition-colors tracking-wider"
                        >
                          → View W&B Run
                        </a>
                      )}
                    </div>
                  )}

                  {/* Error log */}
                  {exp.status === 'failed' && exp.error_log && (
                    <div
                      className="max-h-32 overflow-y-auto rounded p-2.5 font-mono text-[8px] text-signal-red/70 leading-relaxed"
                      style={{
                        backgroundColor: '#ff3b5c06',
                        border: '0.5px solid #ff3b5c15',
                      }}
                    >
                      {exp.error_log}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
