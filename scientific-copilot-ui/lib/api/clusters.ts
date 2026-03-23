import { apiClient } from './client'
import type { ClusterListResponse, DatasetListResponse } from '@/lib/types/cluster'

export const runClustering = async (): Promise<{
  clusters_created: number
  papers_clustered: number
  datasets_found: number
  gaps_found: number
}> => {
  const { data } = await apiClient.post('/clustering/run')
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
