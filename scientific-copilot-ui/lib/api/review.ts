import { apiClient } from './client'
import type { Hypothesis } from '@/lib/types/hypothesis'

export interface ReviewQueueItem {
  id: string
  title: string
  core_claim: string
  novelty_score: number
  feasibility_score: number
  risk_factors: string[]
  arbiter_notes: string | null
  source_paper_ids: string[]
}

export const getReviewQueue = async (): Promise<ReviewQueueItem[]> => {
  const { data } = await apiClient.get<ReviewQueueItem[]>('/review/queue')
  return data
}

export const approveHypothesis = async (id: string): Promise<{
  status: string
  hypothesis_id: string
  new_status: string
}> => {
  const { data } = await apiClient.post(`/review/${id}/approve`)
  return data
}

export const rejectHypothesis = async (
  id: string,
  reason: string
): Promise<{ status: string; hypothesis_id: string; new_status: string }> => {
  const { data } = await apiClient.post(`/review/${id}/reject`, { reason })
  return data
}

export const modifyHypothesis = async (
  id: string,
  updates: { method_sketch?: string; expected_outcome?: string }
): Promise<{ status: string; hypothesis_id: string; action: string }> => {
  const { data } = await apiClient.patch(`/review/${id}/modify`, updates)
  return data
}
