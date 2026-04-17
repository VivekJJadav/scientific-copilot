import { apiClient } from './client'

export interface ResetDatabaseResult {
  cleared_tables: string[]
}

export const resetDatabase = async (): Promise<ResetDatabaseResult> => {
  const { data } = await apiClient.post<ResetDatabaseResult>('/admin/reset-db')
  return data
}
