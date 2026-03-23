export interface PaperCluster {
  id: string
  label: string
  top_terms: string[]
  paper_ids: string[]
  paper_count: number
  created_at?: string
}

export interface DatasetEntry {
  id: string
  name: string
  mention_count: number
  paper_count: number
  paper_ids?: string[]
  created_at?: string
}

export interface Gap {
  id: string
  gap_description: string
  gap_type: 'untested_combination' | 'missing_benchmark' | 'scalability' | 'generalization' | 'negative_result' | 'cluster_insight'
  source_paper_ids: string[]
  cluster_id: string | null
  similarity: number
  used: boolean
  created_at: string
}

export interface ClusterListResponse {
  clusters: PaperCluster[]
  total: number
}

export interface DatasetListResponse {
  datasets: DatasetEntry[]
  total: number
}
