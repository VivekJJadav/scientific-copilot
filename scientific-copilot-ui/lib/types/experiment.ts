export type ExperimentStatus = 'queued' | 'running' | 'completed' | 'failed'

export interface Experiment {
  id: string
  hypothesis_id: string
  status: ExperimentStatus
  experiment_dir: string
  container_id: string | null
  results: Record<string, number | string> | null
  result_summary: string | null
  wandb_run_url: string | null
  mlflow_run_id: string | null
  error_log: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface ExperimentResult {
  id: string
  experiment_id: string
  hypothesis_id: string
  outcome: 'validated' | 'failed' | 'inconclusive'
  metrics: Record<string, number>
  result_summary: string
  lessons_learned: string[]
  created_at: string
}

export interface PaginatedExperiments {
  items: Experiment[]
  total: number
}
