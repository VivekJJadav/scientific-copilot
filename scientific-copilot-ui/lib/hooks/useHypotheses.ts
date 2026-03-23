import { useQuery } from '@tanstack/react-query'
import { getHypotheses, getHypothesis } from '@/lib/api/hypotheses'
import type { HypothesisStatus } from '@/lib/types/hypothesis'

export function useHypotheses(params?: { skip?: number; limit?: number; status?: HypothesisStatus }) {
  return useQuery({
    queryKey: ['hypotheses', params],
    queryFn: () => getHypotheses(params),
  })
}

export function useHypothesis(id: string) {
  return useQuery({
    queryKey: ['hypothesis', id],
    queryFn: () => getHypothesis(id),
    enabled: !!id,
  })
}

export function usePendingCount() {
  return useQuery({
    queryKey: ['hypotheses', 'pending-count'],
    queryFn: async () => {
      const data = await getHypotheses({ status: 'pending', limit: 1 })
      return data.total
    },
    refetchInterval: 30000,
  })
}
