'use client'

import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getPapers } from '@/lib/api/papers'
import { getHypotheses } from '@/lib/api/hypotheses'
import { getClusters } from '@/lib/api/clusters'
import { getExperiments } from '@/lib/api/experiments'
import { useAppStore } from '@/lib/store/appStore'

export type Stage =
  | 'ingest'
  | 'extract'
  | 'cluster'
  | 'hypothesize'
  | 'debate'
  | 'review'
  | 'run'
  | 'feedback'
  | 'done'

export type StageStatus = 'done' | 'active' | 'idle' | 'running'

export interface StageAction {
  text: string
  action: string
  endpoint?: string
  handler?: string
}

export interface PipelineState {
  currentStage: Stage
  isRunning: boolean
  runningStage: Stage | null
  stageStatus: Record<Stage, StageStatus>
  nextAction: StageAction
  counts: {
    papers: number
    processedPapers: number
    clusters: number
    hypotheses: number
    debatedHypotheses: number
    reviewableHypotheses: number
    undebatedHypotheses: number
    pendingHypotheses: number
    approvedHypotheses: number
    experiments: number
    completedExperiments: number
    maxIteration: number
  }
}

const STAGE_PROMPTS: Record<Stage, StageAction> = {
  ingest: {
    text: 'No papers yet — fetch the latest research',
    action: 'Ingest Papers',
    endpoint: 'POST /ingest/arxiv',
  },
  extract: {
    text: 'Papers ready — extract methods and limitations',
    action: 'Extract',
    endpoint: 'POST /extract',
  },
  cluster: {
    text: 'Extraction done — group papers by topic',
    action: 'Run Clustering',
    endpoint: 'POST /clustering/run',
  },
  hypothesize: {
    text: 'Clusters ready — generate research hypotheses',
    action: 'Generate Hypotheses',
    endpoint: 'POST /hypotheses/generate',
  },
  debate: {
    text: 'Hypotheses ready — run adversarial validation',
    action: 'Start Debate',
    endpoint: 'POST /debate/run-all',
  },
  review: {
    text: 'Debated hypotheses are ready for your review',
    action: 'Review →',
    handler: 'openReviewDrawer',
  },
  run: {
    text: 'Hypotheses approved — run experiments',
    action: 'Run Experiments',
    endpoint: 'POST /experiments/run',
  },
  feedback: {
    text: 'Experiments complete — close the feedback loop',
    action: 'Run Feedback',
    endpoint: 'POST /feedback/run',
  },
  done: {
    text: 'Loop complete — system is improving. Run again?',
    action: 'New Cycle',
    endpoint: 'POST /ingest/arxiv',
  },
}

const STAGES: Stage[] = ['ingest', 'extract', 'cluster', 'hypothesize', 'debate', 'review', 'run', 'feedback', 'done']

export function usePipelineState(): PipelineState {
  const { isRunning: storeIsRunning, runningStage: storeRunningStage } = useAppStore()

  const refetchInterval = storeIsRunning ? 5000 : 30000

  const { data: papersData } = useQuery({
    queryKey: ['papers', 0, 100],
    queryFn: () => getPapers({ skip: 0, limit: 100 }),
    refetchInterval,
  })

  const { data: hypothesesData } = useQuery({
    queryKey: ['hypotheses', { limit: 100 }],
    queryFn: () => getHypotheses({ limit: 100 }),
    refetchInterval,
  })

  const { data: clustersData } = useQuery({
    queryKey: ['clusters'],
    queryFn: getClusters,
    refetchInterval,
  })

  const { data: experimentsData } = useQuery({
    queryKey: ['experiments', { limit: 100 }],
    queryFn: () => getExperiments({ limit: 100 }),
    refetchInterval,
  })

  const papers = papersData?.items ?? []
  const hypotheses = hypothesesData?.items ?? []
  const clusters = clustersData?.clusters ?? []
  const experiments = experimentsData?.items ?? []

  const counts = useMemo(() => {
    const processedPapers = papers.filter(
      (p) => p.arxiv_status === 'processed' || p.arxiv_status === 'embedded'
    ).length

    const debatedHypotheses = hypotheses.filter(
      (h) => h.debate_rounds !== null && h.debate_rounds > 0
    ).length

    const reviewableHypotheses = hypotheses.filter(
      (h) => h.status === 'pending' && h.debate_rounds !== null && h.debate_rounds > 0
    ).length

    const undebatedHypotheses = hypotheses.filter(
      (h) => h.status === 'pending' && (h.debate_rounds === null || h.debate_rounds === 0)
    ).length

    const pendingHypotheses = hypotheses.filter(
      (h) => h.status === 'pending'
    ).length

    const approvedHypotheses = hypotheses.filter(
      (h) => h.status === 'approved'
    ).length

    const completedExperiments = experiments.filter(
      (e) => e.status === 'completed'
    ).length

    const maxIteration = hypotheses.reduce(
      (max, h) => Math.max(max, h.iteration_count),
      0
    )

    return {
      papers: papers.length,
      processedPapers,
      clusters: clusters.length,
      hypotheses: hypotheses.length,
      debatedHypotheses,
      reviewableHypotheses,
      undebatedHypotheses,
      pendingHypotheses,
      approvedHypotheses,
      experiments: experiments.length,
      completedExperiments,
      maxIteration,
    }
  }, [papers, hypotheses, clusters, experiments])

  const currentStage = useMemo((): Stage => {
    if (counts.papers === 0) return 'ingest'
    if (counts.processedPapers === 0) return 'extract'
    if (counts.clusters === 0) return 'cluster'
    if (counts.hypotheses === 0) return 'hypothesize'
    
    if (counts.undebatedHypotheses > 0) return 'debate'

    if (counts.reviewableHypotheses > 0) return 'review'
    
    // In 'run' stage if we have approved hypotheses but haven't finished experiments
    if (counts.approvedHypotheses > 0 && counts.completedExperiments < counts.approvedHypotheses) return 'run'
    
    // In 'feedback' stage if we have completed experiments but haven't run feedback yet
    if (counts.completedExperiments > 0 && counts.maxIteration === 0) return 'feedback'
    
    // In 'done' stage if we have hypotheses from the next iteration
    if (counts.maxIteration > 0) return 'done'
    
    return 'ingest'
  }, [counts])

  const stageStatus = useMemo(() => {
    const status: Record<Stage, StageStatus> = {
      ingest: 'idle',
      extract: 'idle',
      cluster: 'idle',
      hypothesize: 'idle',
      debate: 'idle',
      review: 'idle',
      run: 'idle',
      feedback: 'idle',
      done: 'idle',
    }

    const currentIndex = STAGES.indexOf(currentStage)
    for (let i = 0; i < STAGES.length; i++) {
      const stage = STAGES[i]
      if (i < currentIndex) {
        status[stage] = 'done'
      } else if (i === currentIndex) {
        status[stage] = storeIsRunning && storeRunningStage === stage ? 'running' : 'active'
      } else {
        status[stage] = 'idle'
      }
    }

    return status
  }, [currentStage, storeIsRunning, storeRunningStage])

  const nextAction = STAGE_PROMPTS[currentStage]

  return {
    currentStage,
    isRunning: storeIsRunning,
    runningStage: (storeRunningStage as Stage) ?? null,
    stageStatus,
    nextAction,
    counts,
  }
}
