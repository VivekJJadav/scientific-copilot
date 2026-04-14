'use client'

import { useState } from 'react'

interface ModifyFormProps {
  onSave: (updates: { method_sketch?: string; expected_outcome?: string }) => void
  onCancel: () => void
  isLoading: boolean
}

export function ModifyForm({ onSave, onCancel, isLoading }: ModifyFormProps) {
  const [methodSketch, setMethodSketch] = useState('')
  const [expectedOutcome, setExpectedOutcome] = useState('')

  const handleSave = () => {
    const updates: { method_sketch?: string; expected_outcome?: string } = {}
    if (methodSketch.trim()) updates.method_sketch = methodSketch
    if (expectedOutcome.trim()) updates.expected_outcome = expectedOutcome
    onSave(updates)
  }

  return (
    <div className="space-y-2.5 border-t border-border pt-2.5">
      <div>
        <label className="text-[7px] font-mono text-text-muted uppercase tracking-[0.15em] block mb-1">
          method sketch
        </label>
        <textarea
          value={methodSketch}
          onChange={(e) => setMethodSketch(e.target.value)}
          placeholder="updated method sketch..."
          className="w-full px-2 py-1.5 bg-void border border-border rounded text-[9px] font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-signal-cyan/30 resize-none h-16"
        />
      </div>
      <div>
        <label className="text-[7px] font-mono text-text-muted uppercase tracking-[0.15em] block mb-1">
          expected outcome
        </label>
        <textarea
          value={expectedOutcome}
          onChange={(e) => setExpectedOutcome(e.target.value)}
          placeholder="updated expected outcome..."
          className="w-full px-2 py-1.5 bg-void border border-border rounded text-[9px] font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-signal-cyan/30 resize-none h-16"
        />
      </div>
      <div className="flex gap-1.5">
        <button
          onClick={handleSave}
          disabled={isLoading || (!methodSketch.trim() && !expectedOutcome.trim())}
          className="px-2.5 py-1 bg-signal-cyan/8 text-signal-cyan text-[8px] font-mono font-medium rounded border border-signal-cyan/25 hover:bg-signal-cyan/15 disabled:opacity-40 transition-all cursor-pointer tracking-wider"
        >
          {isLoading ? '···' : '[SAVE]'}
        </button>
        <button
          onClick={onCancel}
          className="px-2.5 py-1 text-text-muted text-[8px] font-mono rounded hover:text-text-secondary cursor-pointer tracking-wider"
        >
          [CANCEL]
        </button>
      </div>
    </div>
  )
}
