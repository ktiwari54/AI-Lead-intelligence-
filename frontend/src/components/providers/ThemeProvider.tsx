'use client'

import { useEffect } from 'react'
import { applyThemeClass, resolveTheme, useThemeStore } from '@/stores/theme-store'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useThemeStore((s) => s.theme)
  const setResolvedTheme = useThemeStore((s) => s.setResolvedTheme)

  useEffect(() => {
    const resolved = resolveTheme(theme)
    applyThemeClass(resolved)
    setResolvedTheme(resolved)

    if (theme !== 'system') return

    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => {
      const next = resolveTheme('system')
      applyThemeClass(next)
      setResolvedTheme(next)
    }
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [theme, setResolvedTheme])

  return <>{children}</>
}