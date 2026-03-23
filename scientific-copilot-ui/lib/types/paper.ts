export type ArxivStatus = 'raw' | 'processed' | 'embedded' | 'extraction_failed'

export interface Paper {
  id: string
  arxiv_id: string
  title: string
  abstract: string
  authors: { name: string }[]
  published_year: number
  pdf_url: string
  embedding: number[] | null
  arxiv_status: ArxivStatus
  cluster_id: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedPapers {
  items: Paper[]
  total: number
}
