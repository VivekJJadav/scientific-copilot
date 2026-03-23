'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { clsx } from 'clsx'
import { Map, Lightbulb, ClipboardCheck, FlaskConical, Network, LayoutDashboard } from 'lucide-react'
import { usePendingCount } from '@/lib/hooks/useHypotheses'

const navItems = [
  { href: '/map', label: 'Research Map', icon: Map },
  { href: '/hypotheses', label: 'Hypotheses', icon: Lightbulb },
  { href: '/review', label: 'Review Queue', icon: ClipboardCheck, showBadge: true },
  { href: '/experiments', label: 'Experiments', icon: FlaskConical },
  { href: '/clusters', label: 'Clusters', icon: Network },
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
]

export function Sidebar() {
  const pathname = usePathname()
  const { data: pendingCount } = usePendingCount()

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r border-[#222222] bg-[#0a0a0a]">
      <div className="flex h-16 items-center gap-3 border-b border-[#222222] px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/20">
          <FlaskConical className="h-4 w-4 text-indigo-400" />
        </div>
        <span className="text-sm font-semibold text-white">Scientific Copilot</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href)
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-indigo-500/10 text-indigo-400'
                  : 'text-gray-400 hover:bg-[#111111] hover:text-gray-200'
              )}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span className="flex-1">{item.label}</span>
              {item.showBadge && pendingCount !== undefined && pendingCount > 0 && (
                <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-amber-500/20 px-1.5 text-xs font-bold text-amber-400">
                  {pendingCount}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-[#222222] p-4">
        <p className="text-xs text-gray-600">v0.4.0 · Phase 5</p>
      </div>
    </aside>
  )
}
