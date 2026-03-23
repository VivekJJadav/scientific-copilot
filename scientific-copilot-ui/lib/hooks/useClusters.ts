import { useQuery } from '@tanstack/react-query'
import { getClusters, getDatasets } from '@/lib/api/clusters'

export function useClusters() {
  return useQuery({
    queryKey: ['clusters'],
    queryFn: getClusters,
  })
}

export function useDatasets() {
  return useQuery({
    queryKey: ['datasets'],
    queryFn: getDatasets,
  })
}
