import { apiClient } from './client'
import type { Hypothesis, HypothesisStatus, PaginatedHypotheses, DebateSummary } from '@/lib/types/hypothesis'

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

export const generateHypotheses = async (): Promise<{
  gaps_found: number
  hypotheses_generated: number
  hypotheses_discarded: number
}> => {
  const { data } = await apiClient.post('/hypotheses/generate')
  return data
}

export const runExtraction = async (): Promise<{
  processed: number
  failed: number
  embedded: number
}> => {
  const { data } = await apiClient.post('/extract')
  return data
}

export const runAllDebates = async (): Promise<DebateSummary> => {
  const { data } = await apiClient.post<DebateSummary>('/debate/run-all')
  return data
}
