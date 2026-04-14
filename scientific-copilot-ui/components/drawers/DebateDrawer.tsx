'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '@/lib/store/appStore'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getHypothesis } from '@/lib/api/hypotheses'
import { apiClient } from '@/lib/api/client'
import { DebateThread } from '@/components/debate/DebateThread'
import { LoadingPulse } from '@/components/shared/LoadingPulse'
import { useState } from 'react'

interface DebateTranscriptEntry {
  role: string
  content: string
  round?: number
}

interface DebateData {
  transcript: DebateTranscriptEntry[]
  verdict: string
  final_novelty: number
  final_feasibility: number
  surviving_risks: string[]
  arbiter_notes: string
}

export function DebateDrawer() {
  const { openDrawer, drawerData, closeDrawer } = useAppStore()
  const isOpen = openDrawer === 'debate'
  const hypothesisId = (drawerData as { hypothesisId?: string }).hypothesisId ?? ''
  const queryClient = useQueryClient()
  const [isDebating, setIsDebating] = useState(false)

  const { data: hypothesis } = useQuery({
    queryKey: ['hypothesis-debate', hypothesisId],
    queryFn: () => getHypothesis(hypothesisId),
    enabled: isOpen && !!hypothesisId,
  })

  const { data: debateData } = useQuery({
    queryKey: ['debate-transcript', hypothesisId],
    queryFn: async (): Promise<DebateData | null> => {
      try {
        const { data } = await apiClient.get<DebateData>(`/debate/${hypothesisId}`)
        return data
      } catch {
        return null
      }
    },
    enabled: isOpen && !!hypothesisId,
  })

  const runDebate = useMutation({
    mutationFn: async () => {
      if (!hypothesisId) throw new Error('No hypothesis selected')
      setIsDebating(true)
      const { data } = await apiClient.post(`/debate/${hypothesisId}/debate`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['debate-transcript', hypothesisId] })
      queryClient.invalidateQueries({ queryKey: ['hypothesis-debate', hypothesisId] })
      queryClient.invalidateQueries({ queryKey: ['hypotheses'] })
      setIsDebating(false)
    },
    onError: () => {
      setIsDebating(false)
    },
  })

  const hasDebate = hypothesis?.debate_rounds !== null && (hypothesis?.debate_rounds ?? 0) > 0

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed right-0 top-12 bottom-9 w-[400px] bg-surface border-l border-border z-50 flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-border shrink-0">
            <div className="flex-1 min-w-0 mr-2">
              <span className="text-[8px] font-mono text-signal-cyan uppercase tracking-[0.15em] block mb-1">
                ⟐ DEBATE TRANSCRIPT
              </span>
              <h3 className="text-[11px] font-heading font-semibold text-text-primary truncate">
                {hypothesis?.title ?? 'Loading…'}
              </h3>
              {hasDebate && hypothesis && (
                <span
                  className="text-[8px] font-mono font-bold mt-0.5 inline-block tracking-wider"
                  style={{
                    color: hypothesis.arbiter_notes?.includes('PASS') || hypothesis.status === 'pending'
                      ? '#00e5a0'
                      : '#ff3b5c',
                  }}
                >
                  {hypothesis.debate_rounds} ROUNDS
                </span>
              )}
            </div>
            <button
              onClick={closeDrawer}
              className="w-6 h-6 rounded flex items-center justify-center text-text-muted hover:text-signal-red hover:bg-signal-red/10 transition-colors shrink-0 cursor-pointer"
            >
              ✕
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-3">
            {isDebating ? (
              <div className="flex flex-col items-center justify-center py-16 space-y-4">
                <div className="relative w-10 h-10">
                  <div className="absolute inset-0 rounded-full border border-signal-cyan/20 animate-glow-ring" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-2 h-2 rounded-full bg-signal-cyan animate-signal-pulse" />
                  </div>
                </div>
                <div className="text-center space-y-1">
                  <p className="text-[9px] font-mono text-signal-cyan uppercase tracking-[0.15em]">
                    Adversarial debate in progress
                  </p>
                  <LoadingPulse label="transmitting" />
                </div>
              </div>
            ) : hasDebate && debateData ? (
              <DebateThread
                transcript={debateData.transcript ?? []}
                arbiterVerdict={{
                  verdict: debateData.verdict ?? 'UNKNOWN',
                  final_novelty: debateData.final_novelty ?? hypothesis?.novelty_score ?? 0,
                  final_feasibility: debateData.final_feasibility ?? hypothesis?.feasibility_score ?? 0,
                  surviving_risks: debateData.surviving_risks ?? [],
                  notes: debateData.arbiter_notes ?? '',
                }}
              />
            ) : (
              <div className="flex flex-col items-center justify-center py-16 space-y-4">
                <p className="text-[9px] font-mono text-text-muted tracking-wider">No debate transcript yet</p>
                <button
                  onClick={() => runDebate.mutate()}
                  className="px-4 py-2 bg-signal-cyan/8 text-signal-cyan text-[9px] font-mono font-medium rounded border border-signal-cyan/25 hover:bg-signal-cyan/15 transition-all cursor-pointer tracking-wider"
                >
                  [START DEBATE]
                </button>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
