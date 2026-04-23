import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'workshop-theme'

function getSystemTheme(): 'light' | 'dark' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(theme: 'light' | 'dark') {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

export const useThemeStore = defineStore('workshop-theme', () => {
  const storedTheme = localStorage.getItem(STORAGE_KEY) as ThemeMode | null
  const mode = ref<ThemeMode>(storedTheme || 'system')

  function getEffectiveTheme(): 'light' | 'dark' {
    return mode.value === 'system' ? getSystemTheme() : mode.value
  }

  function setTheme(newMode: ThemeMode) {
    mode.value = newMode
    localStorage.setItem(STORAGE_KEY, newMode)
    applyTheme(getEffectiveTheme())
  }

  // Initialize theme
  applyTheme(getEffectiveTheme())

  // Watch for system theme changes
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', () => {
    if (mode.value === 'system') {
      applyTheme(getEffectiveTheme())
    }
  })

  return {
    mode,
    setTheme,
    getEffectiveTheme,
  }
})
