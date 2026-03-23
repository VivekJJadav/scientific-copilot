import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description?: string
  icon?: React.ReactNode
}

export function EmptyState({ title, description, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      {icon ?? <Inbox className="h-12 w-12 text-gray-600" />}
      <h3 className="text-lg font-medium text-gray-300">{title}</h3>
      {description && <p className="max-w-md text-sm text-gray-500">{description}</p>}
    </div>
  )
}
