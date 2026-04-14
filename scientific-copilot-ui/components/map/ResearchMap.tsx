'use client'

import { useCallback, useEffect, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  MiniMap,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  type Node,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { PaperNode } from './PaperNode'
import { HypothesisNode } from './HypothesisNode'
import { MapControls } from './MapControls'
import { useMapData } from '@/lib/hooks/useMapData'
import { useMapLayout } from '@/lib/hooks/useMapLayout'
import { useAppStore } from '@/lib/store/appStore'

const nodeTypes: NodeTypes = {
  paperNode: PaperNode,
  hypothesisNode: HypothesisNode,
}

function ResearchMapInner() {
  const { nodes: rawNodes, edges: rawEdges, clusters, clusterColorMap, isLoading } = useMapData()
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMapLayout(rawNodes, rawEdges)
  const { setSelectedNode, openDrawerWith, isRunning } = useAppStore()

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges)

  // Sync layouted nodes/edges when data changes
  useEffect(() => {
    setNodes(layoutedNodes)
    setEdges(layoutedEdges)
  }, [layoutedNodes, layoutedEdges, setNodes, setEdges])

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (node.type === 'paperNode') {
        setSelectedNode({ id: node.id, type: 'paper' })
      } else if (node.type === 'hypothesisNode') {
        setSelectedNode({ id: node.id, type: 'hypothesis' })
      }
      openDrawerWith('detail')
    },
    [setSelectedNode, openDrawerWith]
  )

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-void">
        <div className="text-center space-y-4">
          <div className="relative w-12 h-12 mx-auto">
            {/* Rotating ring */}
            <div className="absolute inset-0 rounded-full border border-signal-cyan/20 animate-glow-ring" />
            <div className="absolute inset-1 rounded-full border border-signal-cyan/10" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-signal-cyan animate-signal-pulse" />
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-mono tracking-[0.15em] text-signal-cyan uppercase">
              Scanning
            </p>
            <p className="text-[9px] font-mono text-text-muted">
              Loading research map…
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full min-h-[600px] relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        style={{ width: '100%', height: '100%' }}
        className="bg-void"
      >
        <MiniMap
          style={{ background: '#0a0e14', border: '0.5px solid #1a2332' }}
          nodeColor={(node) =>
            node.type === 'hypothesisNode' ? '#a78bfa' : '#1a2332'
          }
          position="bottom-right"
          pannable
          zoomable
        />
        <Background color="#1a2332" gap={32} size={1} />
        <MapControls />
      </ReactFlow>

      {/* Ambient scan line when system is running */}
      {isRunning && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div
            className="absolute top-0 left-0 w-full h-[1px] animate-scan-line"
            style={{
              background: 'linear-gradient(90deg, transparent, #00d4ff20, transparent)',
              animationDuration: '4s',
            }}
          />
        </div>
      )}
    </div>
  )
}

export function ResearchMap() {
  return (
    <ReactFlowProvider>
      <ResearchMapInner />
    </ReactFlowProvider>
  )
}
