'use client'

import { useState } from 'react'
import { ScoreBars } from '@/components/shared/ScoreBars'
import { ModifyForm } from './ModifyForm'
import type { ReviewQueueItem } from '@/lib/api/review'

interface ReviewCardProps {
  item: ReviewQueueItem
  onApprove: (id: string) => void
  onReject: (id: string, reason: string) => void
  onModify: (id: string, updates: { method_sketch?: string; expected_outcome?: string }) => void
  isApproving: boolean
  isRejecting: boolean
  isModifying: boolean
}

export function ReviewCard({
  item,
  onApprove,
  onReject,
  onModify,
  isApproving,
  isRejecting,
  isModifying,
}: ReviewCardProps) {
  const [showRejectInput, setShowRejectInput] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [showModify, setShowModify] = useState(false)
  const [showRisks, setShowRisks] = useState(false)

  return (
    <div className="bg-panel border border-border rounded-lg p-3 space-y-2.5 hover:border-border-hover transition-colors">
      <h4 className="text-[10px] font-heading font-medium text-text-primary line-clamp-2 leading-tight">
        {item.title}
      </h4>

      <p className="text-[9px] font-mono text-text-secondary line-clamp-3 leading-relaxed">
        {item.core_claim}
      </p>

      <ScoreBars novelty={item.novelty_score} feasibility={item.feasibility_score} />

      {/* Risk factors collapsible */}
      {item.risk_factors && item.risk_factors.length > 0 && (
        <div>
          <button
            onClick={() => setShowRisks(!showRisks)}
            className="text-[8px] font-mono text-text-muted hover:text-text-secondary cursor-pointer tracking-wider uppercase"
          >
            {showRisks ? '▾' : '▸'} Risks ({item.risk_factors.length})
          </button>
          {showRisks && (
            <ul className="mt-1 space-y-0.5 pl-2">
              {item.risk_factors.map((r, i) => (
                <li key={i} className="text-[9px] font-mono text-text-secondary flex items-start gap-1.5">
                  <span className="text-signal-red mt-0.5">▸</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Arbiter notes */}
      {item.arbiter_notes && (
        <p className="text-[9px] font-mono text-text-muted italic">{item.arbiter_notes}</p>
      )}

      {/* Reject reason input */}
      {showRejectInput && (
        <div className="space-y-1.5">
          <input
            type="text"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="reason for rejection..."
            className="w-full px-2 py-1.5 bg-void border border-border rounded text-[9px] font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-signal-red/40"
          />
          <div className="flex gap-1.5">
            <button
              onClick={() => {
                onReject(item.id, rejectReason)
                setShowRejectInput(false)
              }}
              disabled={isRejecting || !rejectReason.trim()}
              className="px-2 py-1 bg-signal-red/10 text-signal-red text-[8px] font-mono rounded border border-signal-red/25 hover:bg-signal-red/20 disabled:opacity-40 cursor-pointer tracking-wider uppercase"
            >
              [CONFIRM]
            </button>
            <button
              onClick={() => setShowRejectInput(false)}
              className="px-2 py-1 text-text-muted text-[8px] font-mono rounded hover:text-text-secondary cursor-pointer tracking-wider"
            >
              [CANCEL]
            </button>
          </div>
        </div>
      )}

      {/* Modify form */}
      {showModify && (
        <ModifyForm
          onSave={(updates) => {
            onModify(item.id, updates)
            setShowModify(false)
          }}
          onCancel={() => setShowModify(false)}
          isLoading={isModifying}
        />
      )}

      {/* Action buttons */}
      {!showRejectInput && !showModify && (
        <div className="flex gap-1.5 pt-1.5 border-t border-border">
          <button
            onClick={() => onApprove(item.id)}
            disabled={isApproving}
            className="flex-1 px-2 py-1.5 bg-signal-green/8 text-signal-green text-[8px] font-mono font-medium rounded border border-signal-green/25 hover:bg-signal-green/15 disabled:opacity-40 transition-all cursor-pointer tracking-wider"
          >
            {isApproving ? '···' : '[APPROVE]'}
          </button>
          <button
            onClick={() => setShowRejectInput(true)}
            className="flex-1 px-2 py-1.5 bg-signal-red/8 text-signal-red text-[8px] font-mono font-medium rounded border border-signal-red/25 hover:bg-signal-red/15 transition-all cursor-pointer tracking-wider"
          >
            [REJECT]
          </button>
          <button
            onClick={() => setShowModify(true)}
            className="px-2 py-1.5 bg-void text-text-secondary text-[8px] font-mono font-medium rounded border border-border hover:border-border-hover hover:text-text-primary transition-all cursor-pointer tracking-wider"
          >
            [MODIFY]
          </button>
        </div>
      )}
    </div>
  )
}
