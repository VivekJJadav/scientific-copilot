'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '@/lib/store/appStore'
import { useReviewQueue, useApproveHypothesis, useRejectHypothesis, useModifyHypothesis } from '@/lib/hooks/useReviewQueue'
import { ReviewCard } from '@/components/review/ReviewCard'

export function ReviewDrawer() {
  const { openDrawer, closeDrawer } = useAppStore()
  const isOpen = openDrawer === 'review'

  const { data: queue, isLoading } = useReviewQueue()
  const approveMutation = useApproveHypothesis()
  const rejectMutation = useRejectHypothesis()
  const modifyMutation = useModifyHypothesis()

  const items = queue ?? []

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: 320, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 320, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed right-0 top-12 bottom-9 w-[320px] bg-surface border-l border-border z-50 flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-border shrink-0">
            <div className="flex items-center gap-2">
              <span className="text-[8px] font-mono text-signal-amber uppercase tracking-[0.15em]">◎ REVIEW QUEUE</span>
              <span className="px-1.5 py-0.5 bg-signal-amber/15 text-signal-amber text-[8px] font-mono font-medium rounded tabular-nums border border-signal-amber/20 animate-breathe">
                {items.length}
              </span>
            </div>
            <button
              onClick={closeDrawer}
              className="w-6 h-6 rounded flex items-center justify-center text-text-muted hover:text-signal-red hover:bg-signal-red/10 transition-colors cursor-pointer"
            >
              ✕
            </button>
          </div>

          {/* Queue list */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-[9px] font-mono text-text-muted tracking-wider">Loading review queue…</div>
              </div>
            ) : items.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <div className="text-[9px] font-mono text-text-muted tracking-wider">No hypotheses to review</div>
                <div className="text-[8px] font-mono text-text-muted/60 mt-1">Queue is empty</div>
              </div>
            ) : (
              items.map((item) => (
                <ReviewCard
                  key={item.id}
                  item={item}
                  onApprove={(id) => approveMutation.mutate(id)}
                  onReject={(id, reason) => rejectMutation.mutate({ id, reason })}
                  onModify={(id, updates) => modifyMutation.mutate({ id, updates })}
                  isApproving={approveMutation.isPending}
                  isRejecting={rejectMutation.isPending}
                  isModifying={modifyMutation.isPending}
                />
              ))
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
