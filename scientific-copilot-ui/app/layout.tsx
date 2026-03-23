import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import { Sidebar } from '@/components/layout/Sidebar'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: 'Scientific Copilot',
  description: 'AI-powered research agent system',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans bg-[#0a0a0a] text-gray-100 antialiased`}>
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="ml-60 flex-1">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
