'use client'

import { useEffect, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getHypotheses } from '@/lib/api/hypotheses'
import { useAppStore } from '@/lib/store/appStore'

export interface DiscoveredHypothesis {
  id: string
  title: string
  iterationCount: number
}

export function useDiscovery() {
  const { addNewHypothesisId } = useAppStore()
  const previousIdsRef = useRef<Set<string>>(new Set())
  const isFirstRender = useRef(true)
  const discoveredRef = useRef<DiscoveredHypothesis[]>([])

  const { data } = useQuery({
    queryKey: ['hypotheses-discovery'],
    queryFn: () => getHypotheses({ limit: 100 }),
    refetchInterval: 8000,
  })

  const hypotheses = data?.items ?? []

  useEffect(() => {
    const currentIds = new Set(hypotheses.map((h) => h.id))

    if (isFirstRender.current) {
      previousIdsRef.current = currentIds
      isFirstRender.current = false
      return
    }

    const newOnes: DiscoveredHypothesis[] = []
    for (const h of hypotheses) {
      if (!previousIdsRef.current.has(h.id)) {
        newOnes.push({
          id: h.id,
          title: h.title,
          iterationCount: h.iteration_count,
        })
        addNewHypothesisId(h.id)
      }
    }

    if (newOnes.length > 0) {
      discoveredRef.current = newOnes
    }

    previousIdsRef.current = currentIds
  }, [hypotheses, addNewHypothesisId])

  const getLatestDiscovery = useCallback((): DiscoveredHypothesis | null => {
    const latest = discoveredRef.current[discoveredRef.current.length - 1] ?? null
    return latest
  }, [])

  return {
    latestDiscovery: discoveredRef.current[discoveredRef.current.length - 1] ?? null,
    discoveredHypotheses: discoveredRef.current,
    getLatestDiscovery,
  }
}
