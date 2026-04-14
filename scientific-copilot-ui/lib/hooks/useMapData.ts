'use client'

import { useMemo } from 'react'
import type { Node, Edge } from '@xyflow/react'
import { usePapers } from './usePapers'
import { useHypotheses } from './useHypotheses'
import { useClusters } from './useClusters'
import type { Paper } from '@/lib/types/paper'
import type { Hypothesis } from '@/lib/types/hypothesis'
import type { PaperCluster } from '@/lib/types/cluster'

const CLUSTER_COLORS = ['#6366f1', '#0ea5e9', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6']

export interface MapData {
  nodes: Node[]
  edges: Edge[]
  papers: Paper[]
  hypotheses: Hypothesis[]
  clusters: PaperCluster[]
  clusterColorMap: Map<string | null, string>
  isLoading: boolean
}

const EMPTY_ARRAY: any[] = []

export function useMapData(): MapData {
  const { data: papersData, isLoading: papersLoading } = usePapers(0, 100)
  const { data: hypothesesData, isLoading: hypothesesLoading } = useHypotheses({ limit: 100 })
  const { data: clustersData, isLoading: clustersLoading } = useClusters()

  const papers = papersData?.items ?? EMPTY_ARRAY
  const hypotheses = hypothesesData?.items ?? EMPTY_ARRAY
  const clusters = clustersData?.clusters ?? EMPTY_ARRAY

  const clusterColorMap = useMemo(() => {
    const map = new Map<string | null, string>()
    clusters.forEach((c: PaperCluster, i: number) =>
      map.set(c.id, CLUSTER_COLORS[i % CLUSTER_COLORS.length])
    )
    map.set(null, '#2a2a35')
    return map
  }, [clusters])

  const { nodes, edges } = useMemo(() => {
    const nodeList: Node[] = []
    const edgeList: Edge[] = []

    // Paper nodes
    for (const paper of papers) {
      nodeList.push({
        id: `paper-${paper.id}`,
        type: 'paperNode',
        position: { x: 0, y: 0 },
        data: {
          title: paper.title,
          arxivId: paper.arxiv_id,
          arxivStatus: paper.arxiv_status,
          year: paper.published_year,
          clusterColor: clusterColorMap.get(paper.cluster_id) ?? '#2a2a35',
        },
      })
    }

    // Connect papers within the same cluster
    const clusterMap = new Map<string, string[]>()
    for (const paper of papers) {
      if (paper.cluster_id) {
        if (!clusterMap.has(paper.cluster_id)) {
          clusterMap.set(paper.cluster_id, [])
        }
        clusterMap.get(paper.cluster_id)!.push(paper.id)
      }
    }

    // Create a chain of edges for papers in the same cluster
    for (const [clusterId, paperIds] of clusterMap.entries()) {
      if (paperIds.length > 1) {
        for (let i = 0; i < paperIds.length - 1; i++) {
          edgeList.push({
            id: `cluster-edge-${clusterId}-${paperIds[i]}-${paperIds[i+1]}`,
            source: `paper-${paperIds[i]}`,
            target: `paper-${paperIds[i+1]}`,
            style: { stroke: clusterColorMap.get(clusterId) ?? '#4b5563', strokeWidth: 1.5, opacity: 0.6 },
            animated: false,
          })
        }
      }
    }

    // Hypothesis nodes
    for (const h of hypotheses) {
      nodeList.push({
        id: `hyp-${h.id}`,
        type: 'hypothesisNode',
        position: { x: 0, y: 0 },
        data: {
          title: h.title,
          status: h.status,
          noveltyScore: h.novelty_score,
          feasibilityScore: h.feasibility_score,
          iterationCount: h.iteration_count,
        },
      })

      // Paper → Hypothesis edges
      if (h.source_paper_ids) {
        for (const arxivId of h.source_paper_ids) {
          // Find the paper with this arxiv_id to get its UUID
          const sourcePaper = papers.find(p => p.arxiv_id === arxivId)
          if (sourcePaper) {
            const paperNodeId = `paper-${sourcePaper.id}`
            edgeList.push({
              id: `edge-${arxivId}-${h.id}`,
              source: paperNodeId,
              target: `hyp-${h.id}`,
              style: { stroke: '#6366f1', strokeWidth: 1.5, strokeDasharray: '5 3' },
              animated: false,
            })
          }
        }
      }

      // Hypothesis → Hypothesis feedback chain
      if (h.parent_hypothesis_id) {
        edgeList.push({
          id: `feedback-${h.parent_hypothesis_id}-${h.id}`,
          source: `hyp-${h.parent_hypothesis_id}`,
          target: `hyp-${h.id}`,
          style: { stroke: '#f59e0b', strokeWidth: 2 },
          animated: true,
          markerEnd: { type: 'arrowclosed' as const, color: '#f59e0b' },
        })
      }
    }

    return { nodes: nodeList, edges: edgeList }
  }, [papers, hypotheses, clusterColorMap])

  return {
    nodes,
    edges,
    papers,
    hypotheses,
    clusters,
    clusterColorMap,
    isLoading: papersLoading || hypothesesLoading || clustersLoading,
  }
}
