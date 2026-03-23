import { useQuery } from '@tanstack/react-query'
import { getExperiments, getExperiment } from '@/lib/api/experiments'

export function useExperiments(skip = 0, limit = 50) {
  return useQuery({
    queryKey: ['experiments', skip, limit],
    queryFn: () => getExperiments({ skip, limit }),
  })
}

export function useExperiment(id: string) {
  return useQuery({
    queryKey: ['experiment', id],
    queryFn: () => getExperiment(id),
    enabled: !!id,
  })
}
