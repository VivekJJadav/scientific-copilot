import { apiClient } from './client'
import type { QueuedTaskResponse } from './tasks'
import type { ClusterListResponse, DatasetListResponse } from '@/lib/types/cluster'

export const runClustering = async (): Promise<QueuedTaskResponse> => {
  const { data } = await apiClient.post<QueuedTaskResponse>('/clustering/run')
  return data
}

export const getClusters = async (): Promise<ClusterListResponse> => {
  const { data } = await apiClient.get<ClusterListResponse>('/clustering/clusters')
  return data
}

export const extractDatasets = async (): Promise<{
  datasets_found: number
  new_entries: number
  updated_entries: number
}> => {
  const { data } = await apiClient.post('/clustering/extract-datasets')
  return data
}

export const getDatasets = async (): Promise<DatasetListResponse> => {
  const { data } = await apiClient.get<DatasetListResponse>('/clustering/datasets')
  return data
}
