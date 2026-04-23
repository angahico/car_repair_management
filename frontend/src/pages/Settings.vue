<script setup lang="ts">
import { LucideSun, LucideMoon, LucideMonitor, LucideUser, LucideLogOut } from 'lucide-vue-next'
import { useThemeStore, useSessionStore } from '@/stores'
import { Card, Button } from '@/components/ui'

const themeStore = useThemeStore()
const sessionStore = useSessionStore()

const themeOptions = [
  { id: 'light', label: 'Light', icon: LucideSun },
  { id: 'dark', label: 'Dark', icon: LucideMoon },
  { id: 'system', label: 'System', icon: LucideMonitor },
] as const

function handleLogout() {
  sessionStore.logout.submit()
}
</script>

<template>
  <div class="space-y-6 max-w-2xl">
    <div>
      <h1 class="text-page-title text-ink">Settings</h1>
      <p class="text-sm text-ink-muted mt-1">Preferences and account</p>
    </div>

    <Card>
      <h3 class="text-section-title text-ink mb-4">Appearance</h3>
      <div class="flex gap-3">
        <button
          v-for="option in themeOptions"
          :key="option.id"
          @click="themeStore.setTheme(option.id)"
          :class="[
            'flex-1 flex flex-col items-center gap-2 p-4 rounded-lg border transition-all',
            themeStore.mode === option.id
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10'
              : 'border-default hover:border-gray-300 dark:hover:border-gray-600',
          ]"
        >
          <component :is="option.icon" :class="['size-6', themeStore.mode === option.id ? 'text-primary-500' : 'text-ink-muted']" />
          <span :class="['text-sm font-medium', themeStore.mode === option.id ? 'text-primary-600 dark:text-primary-400' : 'text-ink']">
            {{ option.label }}
          </span>
        </button>
      </div>
    </Card>

    <Card>
      <h3 class="text-section-title text-ink mb-4">Account</h3>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center">
            <LucideUser class="size-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <p class="text-sm font-medium text-ink">{{ sessionStore.user }}</p>
            <p class="text-xs text-ink-muted">Logged in</p>
          </div>
        </div>
        <Button variant="danger" @click="handleLogout">
          <LucideLogOut class="size-4" />
          Logout
        </Button>
      </div>
    </Card>
  </div>
</template>
