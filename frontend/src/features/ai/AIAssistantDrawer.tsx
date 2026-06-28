'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { X, Maximize2, Pin, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAIAssistantStore } from '@/stores/ai-assistant-store'
import { AIChat } from './AIChat'
import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut'

export function AIAssistantDrawer() {
  const { drawerOpen, setDrawerOpen, toggleDrawer, pinnedChats, pinChat, clearMessages, entityContext } =
    useAIAssistantStore()

  useKeyboardShortcut('j', () => toggleDrawer(), { meta: true, shift: true })

  useEffect(() => {
    if (drawerOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [drawerOpen])

  return (
    <>
      {!drawerOpen && (
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          className="fixed bottom-20 right-6 z-overlay flex h-11 items-center gap-2 rounded-full bg-primary px-4 text-sm font-medium text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-xl lg:bottom-6"
          aria-label="Open AI Assistant"
        >
          <Sparkles className="h-4 w-4" />
          <span className="hidden sm:inline">AI Assistant</span>
        </button>
      )}

      <AnimatePresence>
        {drawerOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-overlay bg-black/40"
              onClick={() => setDrawerOpen(false)}
            />
            <motion.aside
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 28, stiffness: 320 }}
              className="fixed right-0 top-0 z-overlay flex h-full w-full max-w-md flex-col border-l border-border bg-card shadow-xl"
            >
              <div className="flex items-center justify-between border-b border-border px-4 py-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <h2 className="text-sm font-semibold text-foreground">AI Assistant</h2>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => {
                      const title = entityContext.name ?? 'Chat'
                      pinChat(title)
                    }}
                    className="rounded-md p-1.5 text-muted-foreground hover:bg-accent"
                    title="Pin chat"
                  >
                    <Pin className="h-4 w-4" />
                  </button>
                  <Link
                    href="/ai"
                    onClick={() => setDrawerOpen(false)}
                    className="rounded-md p-1.5 text-muted-foreground hover:bg-accent"
                    title="Open full page"
                  >
                    <Maximize2 className="h-4 w-4" />
                  </Link>
                  <button
                    type="button"
                    onClick={() => setDrawerOpen(false)}
                    className="rounded-md p-1.5 text-muted-foreground hover:bg-accent"
                    aria-label="Close"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <AIChat className="flex-1 min-h-0" onNavigate={() => setDrawerOpen(false)} />

              {pinnedChats.length > 0 && (
                <div className="border-t border-border px-4 py-2">
                  <p className="text-xs font-medium text-muted-foreground mb-1">Pinned</p>
                  <ul className="space-y-0.5">
                    {pinnedChats.map((c) => (
                      <li key={c.id} className="text-xs text-foreground truncate">{c.title}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="border-t border-border px-4 py-2 flex justify-between">
                <button
                  type="button"
                  onClick={clearMessages}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  New chat
                </button>
                <span className="text-xs text-muted-foreground">⌘⇧J to toggle</span>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  )
}