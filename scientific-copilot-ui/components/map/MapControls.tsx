'use client'

import { useReactFlow } from '@xyflow/react'

export function MapControls() {
  const { zoomIn, zoomOut, fitView } = useReactFlow()

  const buttonClass = "w-8 h-8 bg-surface border border-border rounded flex items-center justify-center text-text-secondary hover:text-signal-cyan hover:border-signal-cyan/30 transition-all cursor-pointer"

  return (
    <div className="absolute bottom-14 left-4 z-20 flex flex-col gap-1">
      <button
        onClick={() => zoomIn({ duration: 300 })}
        className={buttonClass}
        title="Zoom In"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 3V11M3 7H11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
      <button
        onClick={() => zoomOut({ duration: 300 })}
        className={buttonClass}
        title="Zoom Out"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M3 7H11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
      <button
        onClick={() => fitView({ padding: 0.2, duration: 400 })}
        className={buttonClass}
        title="Fit View"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M2 5V2H5M9 2H12V5M12 9V12H9M5 12H2V9" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    </div>
  )
}
