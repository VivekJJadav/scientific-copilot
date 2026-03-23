import { useQuery } from '@tanstack/react-query'
import { getPapers, getPaper } from '@/lib/api/papers'

export function usePapers(skip = 0, limit = 50) {
  return useQuery({
    queryKey: ['papers', skip, limit],
    queryFn: () => getPapers({ skip, limit }),
  })
}

export function usePaper(id: string) {
  return useQuery({
    queryKey: ['paper', id],
    queryFn: () => getPaper(id),
    enabled: !!id,
  })
}
