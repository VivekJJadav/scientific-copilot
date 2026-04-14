'use client'

interface DebateRound {
  role: string
  content: string
  round?: number
}

interface ArbiterVerdict {
  verdict: string
  final_novelty: number
  final_feasibility: number
  surviving_risks: string[]
  notes: string
}

interface DebateThreadProps {
  transcript: DebateRound[]
  arbiterVerdict: ArbiterVerdict | null
}

function RoleBadge({ role }: { role: string }) {
  const isProposer = role.toLowerCase() === 'proposer'
  const isCritic = role.toLowerCase() === 'critic'
  const color = isProposer ? '#00d4ff' : isCritic ? '#ffb224' : '#00e5a0'

  return (
    <span
      className="text-[7px] font-mono font-semibold uppercase tracking-[0.15em] px-1.5 py-0.5 rounded"
      style={{
        color,
        backgroundColor: `${color}10`,
        border: `0.5px solid ${color}20`,
      }}
    >
      {role}
    </span>
  )
}

export function DebateThread({ transcript, arbiterVerdict }: DebateThreadProps) {
  return (
    <div className="space-y-3">
      {transcript.map((round, index) => {
        const isProposer = round.role.toLowerCase() === 'proposer'
        const isCritic = round.role.toLowerCase() === 'critic'
        const color = isProposer ? '#00d4ff' : isCritic ? '#ffb224' : '#00e5a0'

        return (
          <div
            key={index}
            className={`flex flex-col ${isCritic ? 'items-end' : 'items-start'}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <RoleBadge role={round.role} />
              {round.round && (
                <span className="text-[7px] font-mono text-text-muted tracking-wider">
                  RND {round.round}
                </span>
              )}
            </div>
            <div
              className="max-w-[85%] rounded px-3 py-2 text-[10px] font-mono text-text-primary leading-relaxed"
              style={{
                backgroundColor: `${color}08`,
                borderLeft: `2px solid ${color}40`,
              }}
            >
              {round.content}
            </div>
          </div>
        )
      })}

      {/* Arbiter Verdict */}
      {arbiterVerdict && (
        <div className="mt-5">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="flex-1 h-[0.5px]" style={{ background: 'linear-gradient(90deg, transparent, #1a2332, transparent)' }} />
            <span className="text-[8px] font-mono font-semibold text-text-muted uppercase tracking-[0.2em]">
              ARBITER VERDICT
            </span>
            <div className="flex-1 h-[0.5px]" style={{ background: 'linear-gradient(90deg, transparent, #1a2332, transparent)' }} />
          </div>

          <div
            className="rounded-lg p-3 space-y-2.5"
            style={{
              backgroundColor: arbiterVerdict.verdict === 'PASS' ? '#00e5a006' : '#ff3b5c06',
              border: `1px solid ${arbiterVerdict.verdict === 'PASS' ? '#00e5a025' : '#ff3b5c25'}`,
            }}
          >
            <div className="flex items-center gap-2">
              <span
                className="text-sm font-heading font-bold"
                style={{
                  color: arbiterVerdict.verdict === 'PASS' ? '#00e5a0' : '#ff3b5c',
                  textShadow: `0 0 8px ${arbiterVerdict.verdict === 'PASS' ? '#00e5a030' : '#ff3b5c30'}`,
                }}
              >
                {arbiterVerdict.verdict}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="flex items-center gap-2">
                <span className="text-[8px] font-mono text-text-muted uppercase tracking-wider">NOVELTY</span>
                <span className="text-[10px] font-mono font-semibold text-signal-violet tabular-nums">{arbiterVerdict.final_novelty.toFixed(2)}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[8px] font-mono text-text-muted uppercase tracking-wider">FEASIB</span>
                <span className="text-[10px] font-mono font-semibold text-signal-green tabular-nums">{arbiterVerdict.final_feasibility.toFixed(2)}</span>
              </div>
            </div>

            {arbiterVerdict.surviving_risks.length > 0 && (
              <div>
                <p className="text-[8px] font-mono text-text-muted uppercase tracking-wider mb-1">SURVIVING RISKS</p>
                <ul className="space-y-0.5">
                  {arbiterVerdict.surviving_risks.map((risk, i) => (
                    <li key={i} className="text-[10px] font-mono text-text-secondary flex items-start gap-1.5">
                      <span className="text-signal-amber mt-0.5">▸</span>
                      <span>{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {arbiterVerdict.notes && (
              <p className="text-[9px] font-mono text-text-muted italic border-t border-border pt-2 mt-2">
                {arbiterVerdict.notes}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
