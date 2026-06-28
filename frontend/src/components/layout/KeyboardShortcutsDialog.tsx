'use client'

import { X, Keyboard } from 'lucide-react'
import { useKeyboardShortcutsStore } from '@/stores/keyboard-shortcuts-store'
import { cn } from '@/lib/utils'

const SHORTCUTS = [
  { keys: ['⌘', 'K'], description: 'Open command palette' },
  { keys: ['⌘', 'B'], description: 'Toggle sidebar' },
  { keys: ['⌘', '⇧', 'J'], description: 'Toggle AI Assistant drawer' },
  { keys: ['G', 'D'], description: 'Go to Dashboard' },
  { keys: ['G', 'S'], description: 'Go to Lead Discovery' },
  { keys: ['G', 'C'], description: 'Go to Companies' },
  { keys: ['?'], description: 'Show keyboard shortcuts' },
]

export function KeyboardShortcutsDialog() {
  const open = useKeyboardShortcutsStore((s) => s.open)
  const setOpen = useKeyboardShortcutsStore((s) => s.setOpen)

  if (!open) return null

  return (
    <div className="fixed inset-0 z-toast flex items-center justify-center bg-black/40 p-4" onClick={() => setOpen(false)}>
      <div
        className="w-full max-w-md rounded-xl border border-border bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-2">
            <Keyboard className="h-5 w-5 text-primary" />
            <h2 className="font-semibold text-foreground">Keyboard Shortcuts</h2>
          </div>
          <button type="button" onClick={() => setOpen(false)} className="rounded-md p-1.5 hover:bg-accent">
            <X className="h-4 w-4" />
          </button>
        </div>
        <ul className="divide-y divide-border px-5 py-2">
          {SHORTCUTS.map((s) => (
            <li key={s.description} className="flex items-center justify-between py-3">
              <span className="text-sm text-foreground">{s.description}</span>
              <div className="flex gap-1">
                {s.keys.map((k) => (
                  <kbd key={k} className={cn(
                    'rounded border border-border bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground min-w-[1.5rem] text-center'
                  )}>
                    {k}
                  </kbd>
                ))}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}