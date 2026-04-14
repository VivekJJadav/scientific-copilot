'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDiscovery, type DiscoveredHypothesis } from '@/lib/hooks/useDiscovery'

export function DiscoveryToast() {
  const { latestDiscovery } = useDiscovery()
  const [visible, setVisible] = useState(false)
  const [currentDiscovery, setCurrentDiscovery] = useState<DiscoveredHypothesis | null>(null)

  useEffect(() => {
    if (latestDiscovery && latestDiscovery.id !== currentDiscovery?.id) {
      setCurrentDiscovery(latestDiscovery)
      setVisible(true)
      const timer = setTimeout(() => setVisible(false), 5000)
      return () => clearTimeout(timer)
    }
  }, [latestDiscovery, currentDiscovery?.id])

  return (
    <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-50 pointer-events-none">
      <AnimatePresence>
        {visible && currentDiscovery && (
          <motion.div
            initial={{ opacity: 0, x: -40, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 20, scale: 0.95 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className="pointer-events-auto"
          >
            <div
              className="rounded-lg px-4 py-3 flex items-start gap-3 max-w-sm relative overflow-hidden"
              style={{
                background: '#0a0e14',
                border: '1px solid #00d4ff30',
                boxShadow: '0 0 30px #00d4ff10, 0 4px 20px rgba(0,0,0,0.5)',
              }}
            >
              {/* Scan line effect */}
              <div className="scan-line-overlay" />

              {/* Signal indicator */}
              <div className="w-5 h-5 rounded flex items-center justify-center shrink-0 mt-0.5"
                style={{ backgroundColor: '#00d4ff10', border: '1px solid #00d4ff25' }}
              >
                <div className="w-1.5 h-1.5 rounded-full bg-signal-cyan animate-signal-pulse" />
              </div>

              <div>
                <p className="text-[8px] font-mono font-semibold uppercase tracking-[0.15em] mb-1"
                  style={{
                    color: currentDiscovery.iterationCount > 0 ? '#ffb224' : '#00d4ff',
                  }}
                >
                  {currentDiscovery.iterationCount > 0
                    ? '↻ FEEDBACK LOOP — HYPOTHESIS IMPROVED'
                    : '◇ SIGNAL DETECTED — NEW HYPOTHESIS'}
                </p>
                <p className="text-[10px] font-mono text-text-primary line-clamp-1 leading-relaxed">
                  {currentDiscovery.title}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
