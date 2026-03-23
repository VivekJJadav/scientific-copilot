'use client'

import { useMemo, useCallback, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import dagre from 'dagre'
import { PaperNode } from './PaperNode'
import { HypothesisNode } from './HypothesisNode'
import { MapSidebar } from './MapSidebar'
import { EmptyState } from '@/components/shared/EmptyState'
import { usePapers } from '@/lib/hooks/usePapers'
import { useHypotheses } from '@/lib/hooks/useHypotheses'
import { useClusters } from '@/lib/hooks/useClusters'
import { useMapStore } from '@/lib/store/mapStore'
import type { Paper } from '@/lib/types/paper'
import type { Hypothesis } from '@/lib/types/hypothesis'
import type { PaperCluster } from '@/lib/types/cluster'

const CLUSTER_COLORS = [
  '#818cf8', '#34d399', '#fbbf24', '#f87171',
  '#22d3ee', '#a78bfa', '#fb923c', '#2dd4bf',
]

const nodeTypes: NodeTypes = {
  paper: PaperNode,
  hypothesis: HypothesisNode,
}

function getLayoutedElements(nodes: Node[], edges: Edge[]) {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: 80, ranksep: 120 })

  for (const node of nodes) {
    g.setNode(node.id, { width: node.type === 'hypothesis' ? 224 : 192, height: 100 })
  }
  for (const edge of edges) {
    g.setEdge(edge.source, edge.target)
  }

  dagre.layout(g)

  const layoutedNodes = nodes.map((node) => {
    const pos = g.node(node.id)
    return {
      ...node,
      position: { x: pos.x - (node.type === 'hypothesis' ? 112 : 96), y: pos.y - 50 },
    }
  })

  return { nodes: layoutedNodes, edges }
}

export function ResearchMap() {
  const { data: papersData } = usePapers(0, 100)
  const { data: hypothesesData } = useHypotheses({ limit: 100 })
  const { data: clustersData } = useClusters()

  const { selectedNodeId, selectedNodeType, showEdges, setSelectedNode } = useMapStore()

  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null)
  const [selectedHypothesis, setSelectedHypothesis] = useState<Hypothesis | null>(null)

  const papers = papersData?.items ?? []
  const hypotheses = hypothesesData?.items ?? []
  const clusters = clustersData?.clusters ?? []

  // Build color map for clusters
  const clusterColorMap = useMemo(() => {
    const map = new Map<string | null, string>()
    clusters.forEach((c: PaperCluster, i: number) => map.set(c.id, CLUSTER_COLORS[i % CLUSTER_COLORS.length]))
    map.set(null, '#555555')
    return map
  }, [clusters])

  // Build nodes and edges
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node[] = []
    const edges: Edge[] = []

    // Paper nodes
    for (const paper of papers) {
      nodes.push({
        id: `paper-${paper.arxiv_id}`,
        type: 'paper',
        position: { x: 0, y: 0 },
        data: {
          title: paper.title,
          arxiv_status: paper.arxiv_status,
          year: paper.published_year,
          cluster_color: clusterColorMap.get(paper.cluster_id) ?? '#555',
        },
      })
    }

    // Hypothesis nodes
    for (const h of hypotheses) {
      nodes.push({
        id: `hyp-${h.id}`,
        type: 'hypothesis',
        position: { x: 0, y: 0 },
        data: {
          title: h.title,
          status: h.status,
          novelty_score: h.novelty_score,
          feasibility_score: h.feasibility_score,
          iteration_count: h.iteration_count,
        },
      })

      // Edges: Paper → Hypothesis
      if (h.source_paper_ids) {
        for (const pid of h.source_paper_ids) {
          const paperId = `paper-${pid}`
          if (nodes.some((n) => n.id === paperId)) {
            edges.push({
              id: `edge-${pid}-${h.id}`,
              source: paperId,
              target: `hyp-${h.id}`,
              style: { stroke: '#444', strokeWidth: 1 },
              animated: false,
            })
          }
        }
      }

      // Edges: Parent Hypothesis → Child Hypothesis (feedback chain)
      if (h.parent_hypothesis_id) {
        edges.push({
          id: `feedback-${h.parent_hypothesis_id}-${h.id}`,
          source: `hyp-${h.parent_hypothesis_id}`,
          target: `hyp-${h.id}`,
          style: { stroke: '#818cf8', strokeWidth: 2 },
          animated: true,
          label: '↻ feedback',
        })
      }
    }

    return { initialNodes: nodes, initialEdges: edges }
  }, [papers, hypotheses, clusterColorMap])

  // Apply dagre layout
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(
    () => getLayoutedElements(initialNodes, initialEdges),
    [initialNodes, initialEdges]
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(showEdges ? layoutedEdges : [])

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (node.type === 'paper') {
        const arxivId = node.id.replace('paper-', '')
        const paper = papers.find((p: Paper) => p.arxiv_id === arxivId) ?? null
        setSelectedPaper(paper)
        setSelectedHypothesis(null)
        setSelectedNode(node.id, 'paper')
      } else if (node.type === 'hypothesis') {
        const hypId = node.id.replace('hyp-', '')
        const hyp = hypotheses.find((h: Hypothesis) => h.id === hypId) ?? null
        setSelectedHypothesis(hyp)
        setSelectedPaper(null)
        setSelectedNode(node.id, 'hypothesis')
      }
    },
    [papers, hypotheses, setSelectedNode]
  )

  const closeSidebar = useCallback(() => {
    setSelectedPaper(null)
    setSelectedHypothesis(null)
    setSelectedNode(null, null)
  }, [setSelectedNode])

  if (!papers.length && !hypotheses.length) {
    return <EmptyState title="No data yet" description="Ingest papers to populate the research map." />
  }

  return (
    <div className="relative h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        proOptions={{ hideAttribution: true }}
        className="bg-[#0a0a0a]"
      >
        <Background color="#222" gap={20} />
        <Controls
          className="!bg-[#111] !border-[#333] !rounded-lg [&_button]:!bg-[#111] [&_button]:!border-[#333] [&_button]:!fill-gray-400 [&_button:hover]:!bg-[#222]"
        />
        <MiniMap
          nodeColor={(n) => {
            if (n.type === 'hypothesis') return '#818cf8'
            return (n.data as { cluster_color?: string })?.cluster_color ?? '#555'
          }}
          maskColor="rgba(10, 10, 10, 0.8)"
          className="!bg-[#111] !border-[#222]"
        />
      </ReactFlow>

      <MapSidebar
        paper={selectedPaper}
        hypothesis={selectedHypothesis}
        nodeType={selectedNodeType}
        onClose={closeSidebar}
      />
    </div>
  )
}
