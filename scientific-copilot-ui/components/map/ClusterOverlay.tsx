'use client'

import { useMemo } from 'react'
import { useReactFlow } from '@xyflow/react'
import type { PaperCluster } from '@/lib/types/cluster'

interface ClusterOverlayProps {
  clusters: PaperCluster[]
  clusterColorMap: Map<string | null, string>
}

const CLUSTER_COLORS = ['#00d4ff', '#00e5a0', '#ffb224', '#a78bfa', '#ff3b5c', '#38bdf8']

export function ClusterOverlay({ clusters, clusterColorMap }: ClusterOverlayProps) {
  const { getNodes } = useReactFlow()

  const clusterRegions = useMemo(() => {
    const nodes = getNodes()
    if (nodes.length === 0) return []

    return clusters.map((cluster, index) => {
      const clusterPaperNodes = nodes.filter((n) => {
        if (n.type !== 'paperNode') return false
        const nodeData = n.data as { clusterColor?: string }
        const expectedColor = clusterColorMap.get(cluster.id)
        return nodeData.clusterColor === expectedColor
      })

      if (clusterPaperNodes.length === 0) return null

      const xs = clusterPaperNodes.map((n) => n.position.x)
      const ys = clusterPaperNodes.map((n) => n.position.y)
      const padding = 30

      const minX = Math.min(...xs) - padding
      const minY = Math.min(...ys) - padding
      const maxX = Math.max(...xs) + 155 + padding
      const maxY = Math.max(...ys) + 80 + padding

      const color = CLUSTER_COLORS[index % CLUSTER_COLORS.length]
      const label = cluster.top_terms?.slice(0, 3).join(' · ') ?? cluster.label

      return {
        id: cluster.id,
        x: minX,
        y: minY,
        width: maxX - minX,
        height: maxY - minY,
        color,
        label,
      }
    }).filter(Boolean)
  }, [clusters, clusterColorMap, getNodes])

  return (
    <>
      {clusterRegions.map((region) => {
        if (!region) return null
        return (
          <div
            key={region.id}
            className="absolute pointer-events-none"
            style={{
              left: region.x,
              top: region.y,
              width: region.width,
              height: region.height,
              backgroundColor: `${region.color}06`,
              border: `1px solid ${region.color}12`,
              borderRadius: 8,
              zIndex: -1,
            }}
          >
            <div
              className="absolute -top-4 left-2 px-2 py-0.5 rounded text-[7px] font-mono font-medium tracking-[0.1em] uppercase"
              style={{
                backgroundColor: `${region.color}10`,
                color: region.color,
                border: `0.5px solid ${region.color}20`,
              }}
            >
              {region.label}
            </div>
          </div>
        )
      })}
    </>
  )
}
