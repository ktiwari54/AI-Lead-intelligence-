import { Inter } from 'next/font/google'
import { AppProviders } from '@/components/providers/AppProviders'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata = {
  title: 'AI Lead Intelligence',
  description: 'AI-powered lead intelligence platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} min-h-screen`} style={{ outline: '4px solid red' }}>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  )
}