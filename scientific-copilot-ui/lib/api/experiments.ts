import { apiClient } from './client'
import type { Experiment, PaginatedExperiments } from '@/lib/types/experiment'

export const getExperiments = async (params?: {
  skip?: number
  limit?: number
}): Promise<PaginatedExperiments> => {
  const { data } = await apiClient.get<PaginatedExperiments>('/experiments', { params })
  return data
}

export const getExperiment = async (id: string): Promise<Experiment> => {
  const { data } = await apiClient.get<Experiment>(`/experiments/${id}`)
  return data
}

export const runExperiments = async (): Promise<{
  ran: number
  completed: number
  failed: number
}> => {
  const { data } = await apiClient.post('/experiments/run')
  return data
}
