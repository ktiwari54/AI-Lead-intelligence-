import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  suggestions?: string[]
}

export interface EntityContext {
  type: 'company' | 'contact' | null
  id: string | null
  name: string | null
  score?: number
}

interface AIAssistantState {
  drawerOpen: boolean
  pinnedChats: { id: string; title: string }[]
  messages: ChatMessage[]
  entityContext: EntityContext
  setDrawerOpen: (open: boolean) => void
  toggleDrawer: () => void
  addMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  clearMessages: () => void
  setEntityContext: (ctx: EntityContext) => void
  pinChat: (title: string) => void
}

export const useAIAssistantStore = create<AIAssistantState>()(
  persist(
    (set, get) => ({
      drawerOpen: false,
      pinnedChats: [],
      messages: [
        {
          id: 'welcome',
          role: 'assistant',
          content:
            'Welcome! I can help you discover leads, score prospects, and draft outreach. Try asking me to find companies or contacts.',
          timestamp: Date.now(),
          suggestions: [
            'Find VP of Engineering at fintech companies in NYC',
            'Score this company',
            'Find similar companies',
          ],
        },
      ],
      entityContext: { type: null, id: null, name: null },
      setDrawerOpen: (open) => set({ drawerOpen: open }),
      toggleDrawer: () => set({ drawerOpen: !get().drawerOpen }),
      addMessage: (msg) =>
        set((s) => ({
          messages: [
            ...s.messages,
            { ...msg, id: crypto.randomUUID(), timestamp: Date.now() },
          ],
        })),
      clearMessages: () =>
        set({
          messages: [
            {
              id: 'welcome',
              role: 'assistant',
              content: 'New chat started. How can I help?',
              timestamp: Date.now(),
            },
          ],
        }),
      setEntityContext: (ctx) => set({ entityContext: ctx }),
      pinChat: (title) =>
        set((s) => ({
          pinnedChats: [{ id: crypto.randomUUID(), title }, ...s.pinnedChats].slice(0, 5),
        })),
    }),
    {
      name: 'ai-assistant-store',
      partialize: (s) => ({
        pinnedChats: s.pinnedChats,
        messages: s.messages.slice(-50),
      }),
    }
  )
)