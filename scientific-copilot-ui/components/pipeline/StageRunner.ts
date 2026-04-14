'use client'

import { useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAppStore } from '@/lib/store/appStore'
import { ingestPapers } from '@/lib/api/papers'
import { runExtraction } from '@/lib/api/hypotheses'
import { runClustering } from '@/lib/api/clusters'
import { generateHypotheses, runAllDebates } from '@/lib/api/hypotheses'
import { runExperiments } from '@/lib/api/experiments'
import { runFeedbackLoop } from '@/lib/api/feedback'
import type { Stage } from '@/lib/hooks/usePipelineState'

interface StageResult {
  success: boolean
  message: string
  elapsedMs?: number
  isNoOp?: boolean
}

async function executeStage(stage: Stage): Promise<Omit<StageResult, 'elapsedMs'>> {
  switch (stage) {
    case 'ingest':
    case 'done': {
      const result = await ingestPapers(20)
      return {
        success: true,
        message: `Fetched ${result.fetched} papers, inserted ${result.inserted}`,
        isNoOp: result.inserted === 0 && result.fetched === 0,
      }
    }
    case 'extract': {
      const result = await runExtraction()
      return {
        success: true,
        message: `Processed ${result.processed}, failed ${result.failed}, embedded ${result.embedded}`,
        isNoOp: result.processed === 0 && result.failed === 0 && result.embedded === 0,
      }
    }
    case 'cluster': {
      const result = await runClustering()
      return {
        success: true,
        message: `Created ${result.clusters_created} clusters, found ${result.gaps_found} gaps`,
        isNoOp: result.clusters_created === 0 && result.gaps_found === 0,
      }
    }
    case 'hypothesize': {
      const result = await generateHypotheses()
      return {
        success: true,
        message: `Generated ${result.hypotheses_generated} hypotheses from ${result.gaps_found} gaps`,
        isNoOp: result.hypotheses_generated === 0,
      }
    }
    case 'debate': {
      const result = await runAllDebates()
      return {
        success: true,
        message: `Debated ${result.debated}, ${result.passed} passed, ${result.failed} failed`,
        isNoOp: result.debated === 0,
      }
    }
    case 'run': {
      const result = await runExperiments()
      return {
        success: true,
        message: `Ran ${result.ran} experiments, ${result.completed} completed`,
        isNoOp: result.ran === 0,
      }
    }
    case 'feedback': {
      const result = await runFeedbackLoop()
      return {
        success: true,
        message: `Analyzed ${result.experiments_analyzed}, generated ${result.new_hypotheses_generated} new hypotheses`,
        isNoOp: result.experiments_analyzed === 0,
      }
    }
    case 'review':
      return { success: true, message: 'Opening review drawer', isNoOp: true }
    default:
      return { success: false, message: 'Unknown stage' }
  }
}

export function useStageRunner() {
  const { setRunning, openDrawerWith, isRunning } = useAppStore()
  const queryClient = useQueryClient()
  const startTimeRef = useRef<number | null>(null)

  const getElapsedMs = useCallback((): number => {
    if (!startTimeRef.current) return 0
    return Date.now() - startTimeRef.current
  }, [])

  const getStartTime = useCallback((): number | null => {
    return startTimeRef.current
  }, [])

  const runStage = useCallback(
    async (stage: Stage): Promise<StageResult> => {
      if (isRunning) {
        return { success: false, message: 'A stage is already running' }
      }

      if (stage === 'review') {
        openDrawerWith('review')
        return { success: true, message: 'Opening review drawer' }
      }

      startTimeRef.current = Date.now()
      setRunning(true, stage)

      try {
        const result = await executeStage(stage)
        const elapsedMs = Date.now() - (startTimeRef.current ?? Date.now())
        // Invalidate all queries to refresh data
        await queryClient.invalidateQueries()
        return { ...result, elapsedMs }
      } catch (error) {
        const message =
          error instanceof Error ? error.message : 'An unknown error occurred'
        return { success: false, message }
      } finally {
        startTimeRef.current = null
        setRunning(false)
      }
    },
    [isRunning, setRunning, openDrawerWith, queryClient]
  )

  return { runStage, isRunning, getElapsedMs, getStartTime }
}
