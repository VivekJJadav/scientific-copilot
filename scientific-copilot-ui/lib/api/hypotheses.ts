import { apiClient } from './client'
import type { QueuedTaskResponse } from './tasks'
import type { Hypothesis, HypothesisStatus, PaginatedHypotheses } from '@/lib/types/hypothesis'

export const getHypotheses = async (params?: {
  skip?: number
  limit?: number
  status?: HypothesisStatus
}): Promise<PaginatedHypotheses> => {
  const { data } = await apiClient.get<PaginatedHypotheses>('/hypotheses', { params })
  return data
}

export const getHypothesis = async (id: string): Promise<Hypothesis> => {
  const { data } = await apiClient.get<Hypothesis>(`/hypotheses/${id}`)
  return data
}

export const generateHypotheses = async (): Promise<QueuedTaskResponse> => {
  const { data } = await apiClient.post<QueuedTaskResponse>('/hypotheses/generate')
  return data
}

export const runExtraction = async (): Promise<QueuedTaskResponse> => {
  const { data } = await apiClient.post<QueuedTaskResponse>('/extract')
  return data
}

export const runAllDebates = async (): Promise<QueuedTaskResponse> => {
  const { data } = await apiClient.post<QueuedTaskResponse>('/debate/run-all')
  return data
}
