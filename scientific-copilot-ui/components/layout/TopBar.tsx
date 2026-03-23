'use client'

interface TopBarProps {
  title: string
  children?: React.ReactNode
}

export function TopBar({ title, children }: TopBarProps) {
  return (
    <header className="flex h-16 items-center justify-between border-b border-[#222222] bg-[#0a0a0a] px-6">
      <h1 className="text-lg font-semibold text-white">{title}</h1>
      <div className="flex items-center gap-3">{children}</div>
    </header>
  )
}
