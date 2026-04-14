'use client'

import { useMemo } from 'react'
import dagre from 'dagre'
import type { Node, Edge } from '@xyflow/react'

const PAPER_WIDTH = 148
const PAPER_HEIGHT = 80
const HYPOTHESIS_WIDTH = 188
const HYPOTHESIS_HEIGHT = 110

export function useMapLayout(nodes: Node[], edges: Edge[]) {
  return useMemo(() => {
    if (nodes.length === 0) return { nodes: [], edges }

    const g = new dagre.graphlib.Graph()
    g.setDefaultEdgeLabel(() => ({}))
    g.setGraph({ rankdir: 'TB', nodesep: 60, ranksep: 100 })

    for (const node of nodes) {
      const isHypothesis = node.type === 'hypothesisNode'
      g.setNode(node.id, {
        width: isHypothesis ? HYPOTHESIS_WIDTH : PAPER_WIDTH,
        height: isHypothesis ? HYPOTHESIS_HEIGHT : PAPER_HEIGHT,
      })
    }

    for (const edge of edges) {
      g.setEdge(edge.source, edge.target)
    }

    dagre.layout(g)

    const layoutedNodes = nodes.map((node) => {
      const pos = g.node(node.id)
      const isHypothesis = node.type === 'hypothesisNode'
      const width = isHypothesis ? HYPOTHESIS_WIDTH : PAPER_WIDTH
      const height = isHypothesis ? HYPOTHESIS_HEIGHT : PAPER_HEIGHT
      return {
        ...node,
        position: {
          x: pos.x - width / 2,
          y: pos.y - height / 2,
        },
      }
    })

    return { nodes: layoutedNodes, edges }
  }, [nodes, edges])
}
