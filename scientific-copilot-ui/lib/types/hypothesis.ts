export type HypothesisStatus = 'pending' | 'approved' | 'rejected' | 'running' | 'done'

export interface Hypothesis {
  id: string
  title: string
  motivation: string
  core_claim: string
  method_sketch: string
  expected_outcome: string
  risk_factors: string[]
  novelty_score: number
  feasibility_score: number
  hardware_requirement: string
  source_paper_ids: string[]
  gap_description: string
  status: HypothesisStatus
  iteration_count: number
  parent_hypothesis_id: string | null
  approved_at: string | null
  rejection_reason: string | null
  debate_rounds: number | null
  arbiter_notes: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedHypotheses {
  items: Hypothesis[]
  total: number
}

export interface DebateResult {
  hypothesis_id: string
  verdict: string
  rounds: number
}

export interface DebateSummary {
  debated: number
  passed: number
  failed: number
}
