'use client'

export function LoadingPulse({ className = '', label }: { className?: string; label?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex items-center gap-1">
        <div className="h-1.5 w-1.5 rounded-full bg-signal-cyan animate-typing-dot" />
        <div className="h-1.5 w-1.5 rounded-full bg-signal-cyan animate-typing-dot [animation-delay:0.2s]" />
        <div className="h-1.5 w-1.5 rounded-full bg-signal-cyan animate-typing-dot [animation-delay:0.4s]" />
      </div>
      {label && (
        <span className="text-[9px] font-mono uppercase tracking-widest text-text-secondary">
          {label}
        </span>
      )}
    </div>
  )
}
