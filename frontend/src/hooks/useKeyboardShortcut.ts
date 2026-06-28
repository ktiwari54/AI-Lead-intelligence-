'use client'

import { useEffect } from 'react'

export function useKeyboardShortcut(
  key: string,
  callback: () => void,
  options: { meta?: boolean; ctrl?: boolean; shift?: boolean; enabled?: boolean } = {}
) {
  const { meta = false, ctrl = false, shift = false, enabled = true } = options

  useEffect(() => {
    if (!enabled) return

    const handler = (e: KeyboardEvent) => {
      const metaKey = e.metaKey || e.ctrlKey
      if (meta && !metaKey) return
      if (ctrl && !e.ctrlKey) return
      if (shift && !e.shiftKey) return
      if (e.key.toLowerCase() !== key.toLowerCase()) return

      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        if (key.toLowerCase() !== 'k') return
      }

      e.preventDefault()
      callback()
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [key, callback, meta, ctrl, shift, enabled])
}