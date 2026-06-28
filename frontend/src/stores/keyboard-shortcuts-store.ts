import { create } from 'zustand'

interface KeyboardShortcutsState {
  open: boolean
  setOpen: (open: boolean) => void
  toggle: () => void
}

export const useKeyboardShortcutsStore = create<KeyboardShortcutsState>((set, get) => ({
  open: false,
  setOpen: (open) => set({ open }),
  toggle: () => set({ open: !get().open }),
}))