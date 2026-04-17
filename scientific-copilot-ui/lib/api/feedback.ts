import { apiClient } from './client'
import type { QueuedTaskResponse } from './tasks'

export interface FeedbackResult {
  experiments_analyzed: number
  new_gaps_from_failures: number
  arbiter_examples_updated: number
  new_hypotheses_generated: number
}

export const runFeedbackLoop = async (): Promise<QueuedTaskResponse> => {
  const { data } = await apiClient.post<QueuedTaskResponse>('/feedback/run')
  return data
}

export const analyzeExperiment = async (experimentId: string): Promise<{
  status: string
  analysis: { outcome: string; result_summary: string; lessons_learned: string[] }
}> => {
  const { data } = await apiClient.post(`/feedback/analyze/${experimentId}`)
  return data
}

export const requeueFailed = async (): Promise<{
  failed_outcomes_processed: number
  new_gaps_created: number
}> => {
  const { data } = await apiClient.post('/feedback/requeue-failed')
  return data
}
