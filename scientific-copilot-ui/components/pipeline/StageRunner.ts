'use client'

import { useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAppStore } from '@/lib/store/appStore'
import { getApiErrorMessage } from '@/lib/api/errors'
import { ingestPapers } from '@/lib/api/papers'
import { runExtraction } from '@/lib/api/hypotheses'
import { runClustering } from '@/lib/api/clusters'
import { generateHypotheses, runAllDebates } from '@/lib/api/hypotheses'
import { runExperiments } from '@/lib/api/experiments'
import { runFeedbackLoop } from '@/lib/api/feedback'
import { API_KEY } from '@/lib/api/client'
import type { QueuedTaskResponse } from '@/lib/api/tasks'
import type { Stage } from '@/lib/hooks/usePipelineState'

interface StageResult {
  success: boolean
  message: string
  elapsedMs?: number
  isNoOp?: boolean
}

interface IngestTaskResult {
  fetched: number
  inserted: number
  skipped: number
}

interface ExtractTaskResult {
  processed: number
  failed: number
  embedded: number
}

interface ClusterTaskResult {
  clusters_created: number
  papers_clustered: number
  datasets_found: number
  gaps_found: number
}

interface HypothesizeTaskResult {
  gaps_found: number
  hypotheses_generated: number
  hypotheses_discarded: number
}

interface DebateTaskResult {
  debated: number
  passed: number
  failed: number
}

interface ExperimentTaskResult {
  ran: number
  completed: number
  failed: number
}

interface FeedbackTaskResult {
  experiments_analyzed: number
  new_gaps_from_failures: number
  arbiter_examples_updated: number
  new_hypotheses_generated: number
}

type CompletedStageResult =
  | IngestTaskResult
  | ExtractTaskResult
  | ClusterTaskResult
  | HypothesizeTaskResult
  | DebateTaskResult
  | ExperimentTaskResult
  | FeedbackTaskResult
  | { success: true; message: string; isNoOp: true }

async function streamTask(
  taskId: string,
  onProgress: (progress: number, message?: string) => void
): Promise<unknown> {
  return await new Promise((resolve, reject) => {
    const url = new URL('/backend/pipeline/stream', window.location.origin)
    url.searchParams.set('task_id', taskId)
    url.searchParams.set('api_key', API_KEY)

    const source = new EventSource(url.toString())

    source.addEventListener('task', (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data)
        onProgress(payload.progress ?? 0, payload.message)
        if (payload.status === 'done') {
          source.close()
          resolve(payload.result)
        } else if (payload.status === 'failed') {
          source.close()
          reject(new Error(payload.error || 'Task failed'))
        }
      } catch (error) {
        source.close()
        reject(error)
      }
    })

    source.onerror = () => {
      source.close()
      reject(new Error('Pipeline stream disconnected'))
    }
  })
}

async function startStage(stage: Stage, ingestLimit: number): Promise<QueuedTaskResponse | CompletedStageResult | null> {
  switch (stage) {
    case 'ingest':
    case 'done': {
      return await ingestPapers(ingestLimit)
    }
    case 'extract': {
      return await runExtraction()
    }
    case 'cluster': {
      return await runClustering()
    }
    case 'hypothesize': {
      return await generateHypotheses()
    }
    case 'debate': {
      return await runAllDebates()
    }
    case 'run': {
      return await runExperiments()
    }
    case 'feedback': {
      return await runFeedbackLoop()
    }
    case 'review':
      return { success: true, message: 'Opening review drawer', isNoOp: true }
    default:
      return null
  }
}

function isQueuedTaskResponse(result: unknown): result is QueuedTaskResponse {
  return !!result && typeof result === 'object' && 'task_id' in result
}

function describeStageResult(stage: Stage, result: unknown): Omit<StageResult, 'elapsedMs'> {
  switch (stage) {
    case 'ingest':
    case 'done': {
      const typedResult = result as IngestTaskResult
      return {
        success: true,
        message: `Fetched ${typedResult.fetched} papers, inserted ${typedResult.inserted}`,
        isNoOp: typedResult.inserted === 0 && typedResult.fetched === 0,
      }
    }
    case 'extract': {
      const typedResult = result as ExtractTaskResult
      return {
        success: true,
        message: `Processed ${typedResult.processed}, failed ${typedResult.failed}, embedded ${typedResult.embedded}`,
        isNoOp: typedResult.processed === 0 && typedResult.failed === 0 && typedResult.embedded === 0,
      }
    }
    case 'cluster': {
      const typedResult = result as ClusterTaskResult
      return {
        success: true,
        message: `Created ${typedResult.clusters_created} clusters, found ${typedResult.gaps_found} gaps`,
        isNoOp: typedResult.clusters_created === 0 && typedResult.gaps_found === 0,
      }
    }
    case 'hypothesize': {
      const typedResult = result as HypothesizeTaskResult
      return {
        success: true,
        message: `Generated ${typedResult.hypotheses_generated} hypotheses from ${typedResult.gaps_found} gaps`,
        isNoOp: typedResult.hypotheses_generated === 0,
      }
    }
    case 'debate': {
      const typedResult = result as DebateTaskResult
      return {
        success: true,
        message: `Debated ${typedResult.debated}, ${typedResult.passed} passed, ${typedResult.failed} failed`,
        isNoOp: typedResult.debated === 0,
      }
    }
    case 'run': {
      const typedResult = result as ExperimentTaskResult
      return {
        success: true,
        message: `Ran ${typedResult.ran} experiments, ${typedResult.completed} completed`,
        isNoOp: typedResult.ran === 0,
      }
    }
    case 'feedback': {
      const typedResult = result as FeedbackTaskResult
      return {
        success: true,
        message: `Analyzed ${typedResult.experiments_analyzed}, generated ${typedResult.new_hypotheses_generated} new hypotheses`,
        isNoOp: typedResult.experiments_analyzed === 0,
      }
    }
    default:
      return { success: false, message: 'Unknown stage' }
  }
}

export function useStageRunner() {
  const { setRunning, setTaskProgress, openDrawerWith, isRunning, ingestLimit } = useAppStore()
  const queryClient = useQueryClient()
  const startTimeRef = useRef<number | null>(null)
  const runLockRef = useRef(false)

  const getElapsedMs = useCallback((): number => {
    if (!startTimeRef.current) return 0
    return Date.now() - startTimeRef.current
  }, [])

  const getStartTime = useCallback((): number | null => {
    return startTimeRef.current
  }, [])

  const runStage = useCallback(
    async (stage: Stage): Promise<StageResult> => {
      if (runLockRef.current || useAppStore.getState().isRunning) {
        return { success: false, message: 'A stage is already running' }
      }

      if (stage === 'review') {
        openDrawerWith('review')
        return { success: true, message: 'Opening review drawer' }
      }

      runLockRef.current = true
      startTimeRef.current = Date.now()
      setRunning(true, stage)
      setTaskProgress(0, 'Queued')

      try {
        const taskObj = await startStage(stage, ingestLimit)

        if (!isQueuedTaskResponse(taskObj)) {
          const result = describeStageResult(stage, taskObj)
          const elapsedMs = Date.now() - (startTimeRef.current ?? Date.now())
          await queryClient.invalidateQueries()
          return { ...result, elapsedMs }
        }

        const result = await streamTask(taskObj.task_id, (progress, message) => {
          setTaskProgress(progress, message)
        })
        const stageResult = describeStageResult(stage, result)
        const elapsedMs = Date.now() - (startTimeRef.current ?? Date.now())
        // Invalidate all queries to refresh data
        await queryClient.invalidateQueries()
        return { ...stageResult, elapsedMs }
      } catch (error) {
        const message = getApiErrorMessage(error)
        return { success: false, message }
      } finally {
        runLockRef.current = false
        startTimeRef.current = null
        setRunning(false)
        setTaskProgress(0, null)
      }
    },
    [ingestLimit, setRunning, setTaskProgress, openDrawerWith, queryClient]
  )

  return { runStage, isRunning, getElapsedMs, getStartTime }
}
