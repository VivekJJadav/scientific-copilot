import { Loader2 } from 'lucide-react'

export function LoadingSpinner({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
      <p className="text-sm text-gray-400">{text}</p>
    </div>
  )
}
