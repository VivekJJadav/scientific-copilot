import { apiClient } from './client'
import type { QueuedTaskResponse } from './tasks'
import type { Paper, PaginatedPapers } from '@/lib/types/paper'

export const getPapers = async (params?: {
  skip?: number
  limit?: number
}): Promise<PaginatedPapers> => {
  const { data } = await apiClient.get<PaginatedPapers>('/papers', { params })
  return data
}

export const getPaper = async (id: string): Promise<Paper> => {
  const { data } = await apiClient.get<Paper>(`/papers/${id}`)
  return data
}

export const ingestPapers = async (limit: number = 2): Promise<QueuedTaskResponse> => {
  const response = await apiClient.post<QueuedTaskResponse>('/ingest/arxiv', null, { params: { limit } })
  return response.data
}
