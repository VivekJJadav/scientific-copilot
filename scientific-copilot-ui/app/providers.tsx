'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000,
            retry: (failureCount, error: { response?: { status?: number } }) => {
              if (error?.response?.status === 429) {
                return false
              }
              return failureCount < 1
            },
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster
        theme="dark"
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#0a0e14',
            border: '1px solid #1a2332',
            color: '#d0d8e8',
            fontFamily: 'var(--font-ibm-plex-mono), monospace',
            fontSize: '11px',
            letterSpacing: '0.02em',
          },
        }}
      />
    </QueryClientProvider>
  )
}
