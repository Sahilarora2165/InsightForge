import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  darkMode: boolean
  currentSessionId: string | null
  
  // Actions
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  toggleDarkMode: () => void
  setDarkMode: (dark: boolean) => void
  setCurrentSessionId: (sessionId: string | null) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  darkMode: false,
  currentSessionId: null,

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleDarkMode: () => set((state) => {
    const newDarkMode = !state.darkMode;
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', String(newDarkMode));
    return { darkMode: newDarkMode };
  }),
  setDarkMode: (dark) => {
    if (dark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', String(dark));
    return set({ darkMode: dark });
  },
  setCurrentSessionId: (sessionId) => set({ currentSessionId: sessionId }),
}))

// Initialize dark mode from localStorage or system preference
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('darkMode');
  const prefersDark = stored !== null 
    ? stored === 'true' 
    : window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  useUIStore.getState().setDarkMode(prefersDark);
}
