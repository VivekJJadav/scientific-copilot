import { useQuery } from '@tanstack/react-query'
import { getPapers } from '@/lib/api/papers'
import { getHypotheses } from '@/lib/api/hypotheses'
import { getExperiments } from '@/lib/api/experiments'

export function useDashboardMetrics() {
  const papers = useQuery({ queryKey: ['dashboard', 'papers'], queryFn: () => getPapers({ limit: 100 }) })
  const hypotheses = useQuery({ queryKey: ['dashboard', 'hypotheses'], queryFn: () => getHypotheses({ limit: 100 }) })
  const experiments = useQuery({ queryKey: ['dashboard', 'experiments'], queryFn: () => getExperiments({ limit: 100 }) })

  const isLoading = papers.isLoading || hypotheses.isLoading || experiments.isLoading

  const metrics = {
    totalPapers: papers.data?.total ?? 0,
    totalHypotheses: hypotheses.data?.total ?? 0,
    passedDebate: hypotheses.data?.items.filter((h) => h.status === 'approved' || h.status === 'done').length ?? 0,
    completedExperiments: experiments.data?.items.filter((e) => e.status === 'completed').length ?? 0,
    avgNovelty: hypotheses.data?.items.length
      ? hypotheses.data.items.reduce((s, h) => s + h.novelty_score, 0) / hypotheses.data.items.length
      : 0,
    maxIteration: hypotheses.data?.items.reduce((max, h) => Math.max(max, h.iteration_count), 0) ?? 0,
    papersByStatus: {
      raw: papers.data?.items.filter((p) => p.arxiv_status === 'raw').length ?? 0,
      processed: papers.data?.items.filter((p) => p.arxiv_status === 'processed').length ?? 0,
      embedded: papers.data?.items.filter((p) => p.arxiv_status === 'embedded').length ?? 0,
    },
    hypothesesByStatus: {
      pending: hypotheses.data?.items.filter((h) => h.status === 'pending').length ?? 0,
      approved: hypotheses.data?.items.filter((h) => h.status === 'approved').length ?? 0,
      rejected: hypotheses.data?.items.filter((h) => h.status === 'rejected').length ?? 0,
    },
    experimentsByStatus: {
      queued: experiments.data?.items.filter((e) => e.status === 'queued').length ?? 0,
      running: experiments.data?.items.filter((e) => e.status === 'running').length ?? 0,
      completed: experiments.data?.items.filter((e) => e.status === 'completed').length ?? 0,
      failed: experiments.data?.items.filter((e) => e.status === 'failed').length ?? 0,
    },
    hypotheses: hypotheses.data?.items ?? [],
  }

  return { metrics, isLoading }
}
