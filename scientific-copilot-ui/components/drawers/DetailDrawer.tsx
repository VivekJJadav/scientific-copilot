'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '@/lib/store/appStore'
import { useQuery } from '@tanstack/react-query'
import { getPaper } from '@/lib/api/papers'
import { getHypothesis } from '@/lib/api/hypotheses'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { ScoreBars } from '@/components/shared/ScoreBars'

export function DetailDrawer() {
  const { openDrawer, selectedNode, drawerData, closeDrawer, openDrawerWith } = useAppStore()
  const isOpen = openDrawer === 'detail'

  const nodeId = selectedNode?.id ?? ''
  const nodeType = selectedNode?.type ?? 'paper'
  const dbId = nodeId.split('-').slice(1).join('-')

  const { data: paper } = useQuery({
    queryKey: ['paper-detail', dbId],
    queryFn: () => getPaper(dbId),
    enabled: isOpen && nodeType === 'paper' && !!dbId,
  })

  const { data: hypothesis } = useQuery({
    queryKey: ['hypothesis-detail', dbId],
    queryFn: () => getHypothesis(dbId),
    enabled: isOpen && nodeType === 'hypothesis' && !!dbId,
  })

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: 380, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 380, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed right-0 top-12 bottom-9 w-[380px] bg-surface border-l border-border z-50 overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-border">
            <div className="flex items-center gap-2">
              <span className="text-[8px] font-mono text-signal-cyan uppercase tracking-[0.15em]">
                {nodeType === 'paper' ? '◇ PAPER' : '△ HYPOTHESIS'}
              </span>
            </div>
            <button
              onClick={closeDrawer}
              className="w-6 h-6 rounded flex items-center justify-center text-text-muted hover:text-signal-red hover:bg-signal-red/10 transition-colors cursor-pointer"
            >
              ✕
            </button>
          </div>

          {/* Paper detail */}
          {nodeType === 'paper' && paper && (
            <div className="p-4 space-y-4">
              <h4 className="text-[13px] font-heading font-semibold text-text-primary leading-tight">
                {paper.title}
              </h4>

              <div className="flex items-center gap-2 flex-wrap">
                <StatusBadge status={paper.arxiv_status} size="md" />
                <span className="text-[9px] font-mono text-text-muted tabular-nums">{paper.published_year}</span>
              </div>

              {paper.authors && paper.authors.length > 0 && (
                <div>
                  <p className="text-[7px] font-mono uppercase text-text-muted mb-1.5 tracking-[0.15em]">AUTHORS</p>
                  <p className="text-[10px] font-mono text-text-secondary leading-relaxed">
                    {paper.authors.map((a) => a.name).join(', ')}
                  </p>
                </div>
              )}

              <div>
                <p className="text-[7px] font-mono uppercase text-text-muted mb-1.5 tracking-[0.15em]">ABSTRACT</p>
                <div className="max-h-48 overflow-y-auto rounded-lg bg-void p-3 border border-border">
                  <p className="text-[10px] font-mono text-text-secondary leading-relaxed">
                    {paper.abstract}
                  </p>
                </div>
              </div>

              <a
                href={paper.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-[9px] font-mono text-signal-cyan hover:text-signal-cyan/80 transition-colors tracking-wider uppercase"
              >
                → View on arXiv
              </a>
            </div>
          )}

          {/* Hypothesis detail */}
          {nodeType === 'hypothesis' && hypothesis && (
            <div className="p-4 space-y-4">
              <h4 className="text-[13px] font-heading font-semibold text-text-primary leading-tight">
                {hypothesis.title}
              </h4>

              <div className="flex items-center gap-2 flex-wrap">
                <StatusBadge status={hypothesis.status} size="md" />
                {hypothesis.iteration_count > 0 && (
                  <span className="text-[9px] font-mono font-bold text-signal-amber tracking-wider">
                    ↻ iteration {hypothesis.iteration_count}
                  </span>
                )}
              </div>

              <ScoreBars novelty={hypothesis.novelty_score} feasibility={hypothesis.feasibility_score} />

              {hypothesis.motivation && (
                <div>
                  <p className="text-[7px] font-mono uppercase text-text-muted mb-1.5 tracking-[0.15em]">MOTIVATION</p>
                  <p className="text-[10px] font-mono text-text-secondary leading-relaxed">{hypothesis.motivation}</p>
                </div>
              )}

              <div className="signal-box p-3">
                <p className="text-[7px] font-mono uppercase text-signal-cyan mb-1.5 tracking-[0.15em]">CORE CLAIM</p>
                <p className="text-[10px] font-mono text-text-primary leading-relaxed">{hypothesis.core_claim}</p>
              </div>

              {hypothesis.method_sketch && (
                <div>
                  <p className="text-[7px] font-mono uppercase text-text-muted mb-1.5 tracking-[0.15em]">METHOD SKETCH</p>
                  <p className="text-[10px] font-mono text-text-secondary leading-relaxed">{hypothesis.method_sketch}</p>
                </div>
              )}

              {hypothesis.expected_outcome && (
                <div>
                  <p className="text-[7px] font-mono uppercase text-text-muted mb-1.5 tracking-[0.15em]">EXPECTED OUTCOME</p>
                  <p className="text-[10px] font-mono text-text-secondary leading-relaxed">{hypothesis.expected_outcome}</p>
                </div>
              )}

              {hypothesis.risk_factors && hypothesis.risk_factors.length > 0 && (
                <div>
                  <p className="text-[7px] font-mono uppercase text-text-muted mb-1.5 tracking-[0.15em]">RISK FACTORS</p>
                  <ul className="space-y-1">
                    {hypothesis.risk_factors.map((r, i) => (
                      <li key={i} className="text-[10px] font-mono text-text-secondary flex items-start gap-1.5">
                        <span className="text-signal-red mt-0.5">▸</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {hypothesis.hardware_requirement && (
                <div>
                  <p className="text-[7px] font-mono uppercase text-text-muted mb-1.5 tracking-[0.15em]">HARDWARE</p>
                  <p className="text-[10px] font-mono text-text-secondary">{hypothesis.hardware_requirement}</p>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex gap-2 pt-2 border-t border-border">
                <button
                  onClick={() => openDrawerWith('debate', { hypothesisId: hypothesis.id })}
                  className="flex-1 px-2 py-1.5 bg-panel border border-border rounded text-[9px] font-mono font-medium text-text-primary hover:border-signal-cyan/30 hover:text-signal-cyan transition-all cursor-pointer tracking-wider"
                >
                  [DEBATE]
                </button>
                <button
                  onClick={() => openDrawerWith('experiment', { hypothesisId: hypothesis.id })}
                  className="flex-1 px-2 py-1.5 bg-panel border border-border rounded text-[9px] font-mono font-medium text-text-primary hover:border-signal-amber/30 hover:text-signal-amber transition-all cursor-pointer tracking-wider"
                >
                  [EXPERIMENTS]
                </button>
              </div>

              {hypothesis.status === 'pending' && (
                <button
                  onClick={() => openDrawerWith('review')}
                  className="w-full px-2 py-1.5 bg-signal-green/8 border border-signal-green/25 rounded text-[9px] font-mono font-medium text-signal-green hover:bg-signal-green/15 transition-all cursor-pointer tracking-wider"
                >
                  [REVIEW & APPROVE]
                </button>
              )}
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
