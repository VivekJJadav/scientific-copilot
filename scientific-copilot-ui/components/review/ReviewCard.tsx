'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { approveHypothesis, rejectHypothesis, modifyHypothesis } from '@/lib/api/review'
import type { ReviewQueueItem } from '@/lib/api/review'
import { ScoreBadge } from '@/components/shared/ScoreBadge'
import { toast } from 'sonner'
import { Check, X, Pencil, ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import { clsx } from 'clsx'
import { useMapStore } from '@/lib/store/mapStore'

interface ReviewCardProps {
  item: ReviewQueueItem
}

export function ReviewCard({ item }: ReviewCardProps) {
  const [showReject, setShowReject] = useState(false)
  const [showModify, setShowModify] = useState(false)
  const [showRisks, setShowRisks] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [methodSketch, setMethodSketch] = useState('')
  const [expectedOutcome, setExpectedOutcome] = useState('')
  const [isAnimatingOut, setIsAnimatingOut] = useState(false)

  const isRunning = useMapStore((s) => s.isRunning)
  const queryClient = useQueryClient()

  const animateOutAndInvalidate = () => {
    setIsAnimatingOut(true)
    setTimeout(() => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] })
      queryClient.invalidateQueries({ queryKey: ['hypotheses'] })
    }, 300)
  }

  const approveMutation = useMutation({
    mutationFn: () => approveHypothesis(item.id),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['review-queue'] })
      const previous = queryClient.getQueryData<ReviewQueueItem[]>(['review-queue'])
      queryClient.setQueryData<ReviewQueueItem[]>(['review-queue'], (old) =>
        old?.filter((i) => i.id !== item.id) ?? []
      )
      return { previous }
    },
    onSuccess: () => {
      toast.success(`Approved: ${item.title}`)
      animateOutAndInvalidate()
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) queryClient.setQueryData(['review-queue'], context.previous)
      toast.error('Failed to approve hypothesis')
    },
  })

  const rejectMutation = useMutation({
    mutationFn: () => rejectHypothesis(item.id, rejectReason),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['review-queue'] })
      const previous = queryClient.getQueryData<ReviewQueueItem[]>(['review-queue'])
      queryClient.setQueryData<ReviewQueueItem[]>(['review-queue'], (old) =>
        old?.filter((i) => i.id !== item.id) ?? []
      )
      return { previous }
    },
    onSuccess: () => {
      toast.success(`Rejected: ${item.title}`)
      animateOutAndInvalidate()
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) queryClient.setQueryData(['review-queue'], context.previous)
      toast.error('Failed to reject hypothesis')
    },
  })

  const modifyMutation = useMutation({
    mutationFn: () =>
      modifyHypothesis(item.id, {
        ...(methodSketch ? { method_sketch: methodSketch } : {}),
        ...(expectedOutcome ? { expected_outcome: expectedOutcome } : {}),
      }),
    onSuccess: () => {
      toast.success(`Modified: ${item.title}`)
      setShowModify(false)
      queryClient.invalidateQueries({ queryKey: ['review-queue'] })
    },
    onError: () => toast.error('Failed to modify hypothesis'),
  })

  return (
    <div
      className={clsx(
        'rounded-lg border border-[#222222] bg-[#111111] p-5 transition-all duration-300',
        isAnimatingOut && 'translate-x-full opacity-0'
      )}
    >
      <h3 className="mb-2 text-base font-medium text-white">{item.title}</h3>
      <p className="mb-4 text-sm text-gray-400">{item.core_claim}</p>

      {/* Score bars */}
      <div className="mb-4 space-y-2">
        <div>
          <div className="mb-1 flex items-center justify-between text-xs text-gray-500">
            <span>Novelty</span>
            <span>{item.novelty_score.toFixed(2)}</span>
          </div>
          <div className="h-2 rounded-full bg-[#1a1a1a]">
            <div
              className={clsx(
                'h-2 rounded-full transition-all',
                item.novelty_score >= 0.7 ? 'bg-green-500' : item.novelty_score >= 0.5 ? 'bg-amber-500' : 'bg-red-500'
              )}
              style={{ width: `${item.novelty_score * 100}%` }}
            />
          </div>
        </div>
        <div>
          <div className="mb-1 flex items-center justify-between text-xs text-gray-500">
            <span>Feasibility</span>
            <span>{item.feasibility_score.toFixed(2)}</span>
          </div>
          <div className="h-2 rounded-full bg-[#1a1a1a]">
            <div
              className={clsx(
                'h-2 rounded-full transition-all',
                item.feasibility_score >= 0.7
                  ? 'bg-green-500'
                  : item.feasibility_score >= 0.5
                  ? 'bg-amber-500'
                  : 'bg-red-500'
              )}
              style={{ width: `${item.feasibility_score * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Risk factors */}
      {item.risk_factors.length > 0 && (
        <div className="mb-4">
          <button
            onClick={() => setShowRisks(!showRisks)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300"
          >
            {showRisks ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            {item.risk_factors.length} Risk Factors
          </button>
          {showRisks && (
            <ul className="mt-2 space-y-1">
              {item.risk_factors.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-400">
                  <span className="mt-1 h-1 w-1 flex-shrink-0 rounded-full bg-amber-400" />
                  {r}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Arbiter notes */}
      {item.arbiter_notes && (
        <blockquote className="mb-4 border-l-2 border-indigo-500/30 pl-3 text-xs text-gray-500 italic">
          {item.arbiter_notes}
        </blockquote>
      )}

      {/* Source papers */}
      {item.source_paper_ids.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-1">
          {item.source_paper_ids.slice(0, 5).map((pid) => (
            <a
              key={pid}
              href={`https://arxiv.org/abs/${pid}`}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded bg-[#1a1a1a] px-2 py-0.5 text-xs text-indigo-400 hover:text-indigo-300"
            >
              {pid}
            </a>
          ))}
        </div>
      )}

      {/* Reject form */}
      {showReject && (
        <div className="mb-4 space-y-2">
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Reason for rejection..."
            className="h-20 w-full rounded-lg border border-[#333] bg-[#0a0a0a] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-red-500/50 focus:outline-none"
          />
          <div className="flex gap-2">
            <button
              onClick={() => rejectMutation.mutate()}
              disabled={!rejectReason.trim() || rejectMutation.isPending}
              className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-500 disabled:opacity-50"
            >
              {rejectMutation.isPending ? 'Rejecting...' : 'Confirm Reject'}
            </button>
            <button onClick={() => setShowReject(false)} className="text-xs text-gray-500 hover:text-gray-300">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Modify form */}
      {showModify && (
        <div className="mb-4 space-y-2">
          <textarea
            value={methodSketch}
            onChange={(e) => setMethodSketch(e.target.value)}
            placeholder="Updated method sketch..."
            className="h-16 w-full rounded-lg border border-[#333] bg-[#0a0a0a] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-indigo-500/50 focus:outline-none"
          />
          <textarea
            value={expectedOutcome}
            onChange={(e) => setExpectedOutcome(e.target.value)}
            placeholder="Updated expected outcome..."
            className="h-16 w-full rounded-lg border border-[#333] bg-[#0a0a0a] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-indigo-500/50 focus:outline-none"
          />
          <div className="flex gap-2">
            <button
              onClick={() => modifyMutation.mutate()}
              disabled={(!methodSketch.trim() && !expectedOutcome.trim()) || modifyMutation.isPending}
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {modifyMutation.isPending ? 'Saving...' : 'Save Changes'}
            </button>
            <button onClick={() => setShowModify(false)} className="text-xs text-gray-500 hover:text-gray-300">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => approveMutation.mutate()}
          disabled={isRunning || approveMutation.isPending}
          className="flex items-center gap-1.5 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-500 disabled:opacity-50"
        >
          {approveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
          Approve
        </button>
        <button
          onClick={() => { setShowReject(true); setShowModify(false) }}
          disabled={isRunning}
          className="flex items-center gap-1.5 rounded-lg bg-red-600/20 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-600/30 disabled:opacity-50"
        >
          <X className="h-4 w-4" />
          Reject
        </button>
        <button
          onClick={() => { setShowModify(true); setShowReject(false) }}
          disabled={isRunning}
          className="flex items-center gap-1.5 rounded-lg border border-[#333] px-4 py-2 text-sm font-medium text-gray-400 transition-colors hover:border-indigo-500/30 hover:text-indigo-400 disabled:opacity-50"
        >
          <Pencil className="h-4 w-4" />
          Modify
        </button>
      </div>
    </div>
  )
}
