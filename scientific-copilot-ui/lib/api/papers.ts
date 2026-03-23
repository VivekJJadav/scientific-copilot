import { apiClient } from './client'
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

export const ingestPapers = async (): Promise<{ fetched: number; inserted: number; skipped: number }> => {
  const { data } = await apiClient.post('/ingest/arxiv')
  return data
}
