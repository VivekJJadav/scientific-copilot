import type { Metadata } from 'next'
import { IBM_Plex_Mono, Space_Grotesk } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-ibm-plex-mono',
})

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-space-grotesk',
})

export const metadata: Metadata = {
  title: 'Scientific Copilot — Autonomous Research Terminal',
  description: 'Deep-space observatory interface for autonomous scientific research. Ingests papers, generates hypotheses, runs adversarial debates, and executes experiments.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${ibmPlexMono.variable} ${spaceGrotesk.variable} font-data bg-void text-text-primary overflow-hidden antialiased`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
