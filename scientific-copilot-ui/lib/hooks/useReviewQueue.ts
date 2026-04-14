'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getReviewQueue, approveHypothesis, rejectHypothesis, modifyHypothesis } from '@/lib/api/review'
import type { ReviewQueueItem } from '@/lib/api/review'
import { toast } from 'sonner'

export function useReviewQueue() {
  return useQuery({
    queryKey: ['review-queue'],
    queryFn: getReviewQueue,
    refetchInterval: 15000,
  })
}

export function useApproveHypothesis() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => approveHypothesis(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['review-queue'] })
      const previous = queryClient.getQueryData<ReviewQueueItem[]>(['review-queue'])
      queryClient.setQueryData<ReviewQueueItem[]>(['review-queue'], (old) =>
        old?.filter((item) => item.id !== id) ?? []
      )
      return { previous }
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['review-queue'], context.previous)
      }
      toast.error('Failed to approve hypothesis')
    },
    onSuccess: () => {
      toast.success('Hypothesis approved')
      queryClient.invalidateQueries({ queryKey: ['hypotheses'] })
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] })
    },
  })
}

export function useRejectHypothesis() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      rejectHypothesis(id, reason),
    onMutate: async ({ id }) => {
      await queryClient.cancelQueries({ queryKey: ['review-queue'] })
      const previous = queryClient.getQueryData<ReviewQueueItem[]>(['review-queue'])
      queryClient.setQueryData<ReviewQueueItem[]>(['review-queue'], (old) =>
        old?.filter((item) => item.id !== id) ?? []
      )
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['review-queue'], context.previous)
      }
      toast.error('Failed to reject hypothesis')
    },
    onSuccess: () => {
      toast.success('Hypothesis rejected')
      queryClient.invalidateQueries({ queryKey: ['hypotheses'] })
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] })
    },
  })
}

export function useModifyHypothesis() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      updates,
    }: {
      id: string
      updates: { method_sketch?: string; expected_outcome?: string }
    }) => modifyHypothesis(id, updates),
    onError: () => {
      toast.error('Failed to modify hypothesis')
    },
    onSuccess: () => {
      toast.success('Hypothesis modified')
      queryClient.invalidateQueries({ queryKey: ['review-queue'] })
      queryClient.invalidateQueries({ queryKey: ['hypotheses'] })
    },
  })
}
