<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  LucideSearch,
  LucideBell,
  LucideUser,
  LucideLogOut,
  LucideMenu,
  LucideCheck,
  LucideChevronDown,
} from 'lucide-vue-next'
import { useSessionStore } from '@/stores'
import { apiCall } from '@/api'
import { useI18n } from 'vue-i18n'
import { availableLocales } from '@/locales'

const { t, locale } = useI18n()

const emit = defineEmits<{
  'toggle-sidebar': []
}>()

const sessionStore = useSessionStore()

const searchQuery = ref('')
const showUserMenu = ref(false)
const showLangMenu = ref(false)

// Notification state
const showNotifications = ref(false)
const notifications = ref<any[]>([])
const unreadCount = ref(0)
const notifLoading = ref(false)
let pollInterval: ReturnType<typeof setInterval> | null = null

// Flag map for locales
const flagMap: Record<string, string> = {
  en: '🇬🇧',
  am: '🇪🇹',
  om: '🇪🇹',
  ti: '🇪🇹',
  ar: '🇸🇦',
  fr: '🇫🇷',
}

function getFlag(code: string): string {
  return flagMap[code] || '🌐'
}

const currentLocale = computed(() =>
  availableLocales.find(l => l.code === locale.value) || availableLocales[0]
)

function setLocale(code: string) {
  locale.value = code
  localStorage.setItem('workshop-locale', code)
  document.documentElement.dir = code === 'ar' ? 'rtl' : 'ltr'
  showLangMenu.value = false
}

function handleLogout() {
  sessionStore.logout.submit()
}

// Notification functions
async function loadNotifications() {
  notifLoading.value = true
  try {
    const data = await apiCall<any>('car_repair_management.api.notification.get_notifications')
    notifications.value = data.notifications || []
    unreadCount.value = data.unread_count || 0
  } catch {
    // silently fail
  } finally {
    notifLoading.value = false
  }
}

async function markAllRead() {
  await apiCall('car_repair_management.api.notification.mark_as_read')
  unreadCount.value = 0
  notifications.value = notifications.value.map(n => ({ ...n, read: 1 }))
}

async function markOneRead(name: string) {
  await apiCall('car_repair_management.api.notification.mark_as_read', { name })
  const n = notifications.value.find(x => x.name === name)
  if (n && !n.read) {
    n.read = 1
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }
}

function toggleNotifications() {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) {
    loadNotifications()
    showUserMenu.value = false
    showLangMenu.value = false
  }
}

function timeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  const months = Math.floor(days / 30)
  return `${months}mo ago`
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.notif-dropdown-wrapper')) {
    showNotifications.value = false
  }
  if (!target.closest('.user-menu-wrapper')) {
    showUserMenu.value = false
  }
  if (!target.closest('.lang-menu-wrapper')) {
    showLangMenu.value = false
  }
}

onMounted(() => {
  loadNotifications()
  pollInterval = setInterval(loadNotifications, 60000)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <header 
    class="h-16 flex items-center justify-between px-6 border-b"
    style="background-color: var(--bg-secondary); border-color: var(--border-color);"
  >
    <!-- Mobile menu button -->
    <button 
      class="md:hidden p-2 rounded-lg transition-colors hover:opacity-80"
      style="color: var(--text-muted);"
      @click="emit('toggle-sidebar')"
    >
      <LucideMenu class="size-5" />
    </button>

    <!-- Search -->
    <div class="flex-1 max-w-md hidden md:block">
      <div class="relative">
        <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4" style="color: var(--text-muted);" />
        <input
          v-model="searchQuery"
          type="search"
          :placeholder="t('common.search') + '...'"
          class="w-full h-10 pl-10 pr-4 rounded-lg border focus:outline-none"
          style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
        />
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-2">

      <!-- Language Switcher -->
      <div class="relative lang-menu-wrapper">
        <button
          @click.stop="showLangMenu = !showLangMenu; showNotifications = false; showUserMenu = false"
          class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg transition-colors hover:opacity-80 text-sm font-medium"
          style="color: var(--text-secondary); background-color: var(--bg-tertiary);"
          :title="currentLocale.name"
        >
          <span class="text-base leading-none">{{ getFlag(currentLocale.code) }}</span>
          <span class="hidden sm:inline text-xs">{{ currentLocale.code.toUpperCase() }}</span>
          <LucideChevronDown class="size-3.5" style="color: var(--text-muted);" />
        </button>

        <!-- Language Dropdown -->
        <div
          v-if="showLangMenu"
          class="absolute right-0 top-full mt-2 w-48 rounded-lg border shadow-lg py-1 z-50 overflow-hidden"
          style="background-color: var(--bg-elevated); border-color: var(--border-color);"
        >
          <button
            v-for="lang in availableLocales"
            :key="lang.code"
            @click="setLocale(lang.code)"
            class="w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors hover:opacity-80"
            :style="{
              backgroundColor: locale === lang.code ? 'var(--bg-tertiary)' : 'transparent',
              color: locale === lang.code ? 'var(--text-primary)' : 'var(--text-muted)',
              fontWeight: locale === lang.code ? '600' : '400',
            }"
          >
            <span class="text-base">{{ getFlag(lang.code) }}</span>
            <span>{{ lang.nativeName }}</span>
            <LucideCheck
              v-if="locale === lang.code"
              class="size-3.5 ml-auto"
              style="color: var(--accent, #3182ce);"
            />
          </button>
        </div>
      </div>

      <!-- Notifications -->
      <div class="relative notif-dropdown-wrapper">
        <button
          @click.stop="toggleNotifications"
          class="p-2 rounded-lg transition-colors hover:opacity-80 relative"
          style="color: var(--text-muted);"
          title="Notifications"
        >
          <LucideBell class="size-5" />
          <span
            v-if="unreadCount > 0"
            class="absolute top-0.5 right-0.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full text-white text-[10px] font-bold leading-none px-1"
            style="background-color: var(--accent, #e53e3e);"
          >
            {{ unreadCount > 99 ? '99+' : unreadCount }}
          </span>
        </button>

        <!-- Notification dropdown -->
        <div
          v-if="showNotifications"
          class="absolute right-0 top-full mt-2 w-80 rounded-lg border shadow-lg z-50 overflow-hidden"
          style="background-color: var(--bg-elevated); border-color: var(--border-color);"
        >
          <!-- Header -->
          <div
            class="flex items-center justify-between px-4 py-3 border-b"
            style="border-color: var(--border-color);"
          >
            <span class="text-sm font-semibold" style="color: var(--text-primary);">
              {{ t('notifications.title') }}
            </span>
            <button
              v-if="unreadCount > 0"
              @click="markAllRead"
              class="flex items-center gap-1 text-xs px-2 py-1 rounded hover:opacity-80 transition-colors"
              style="color: var(--accent, #3182ce);"
            >
              <LucideCheck class="size-3" />
              {{ t('notifications.mark_all_read') }}
            </button>
          </div>

          <!-- List -->
          <div class="max-h-80 overflow-y-auto">
            <div
              v-if="notifLoading && notifications.length === 0"
              class="px-4 py-8 text-center text-sm"
              style="color: var(--text-muted);"
            >
              {{ t('common.loading') }}
            </div>

            <div
              v-else-if="notifications.length === 0"
              class="px-4 py-8 text-center text-sm"
              style="color: var(--text-muted);"
            >
              {{ t('notifications.no_notifications') }}
            </div>

            <button
              v-for="notif in notifications"
              :key="notif.name"
              @click="markOneRead(notif.name)"
              class="w-full text-left px-4 py-3 border-b transition-colors hover:opacity-90 block"
              :style="{
                borderColor: 'var(--border-color)',
                backgroundColor: notif.read ? 'transparent' : 'var(--bg-tertiary)',
                borderLeft: notif.read ? 'none' : '3px solid var(--accent, #3182ce)',
              }"
            >
              <p
                class="text-sm leading-snug line-clamp-2"
                :style="{
                  color: 'var(--text-primary)',
                  fontWeight: notif.read ? 'normal' : '600',
                }"
              >
                {{ notif.subject }}
              </p>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-xs" style="color: var(--text-muted);">
                  {{ timeAgo(notif.creation) }}
                </span>
                <span
                  v-if="notif.document_type"
                  class="text-xs"
                  style="color: var(--text-muted);"
                >
                  · {{ notif.document_type }}
                </span>
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- User menu -->
      <div class="relative user-menu-wrapper">
        <button
          @click.stop="showUserMenu = !showUserMenu; showLangMenu = false"
          class="flex items-center gap-2 p-1.5 rounded-lg transition-colors hover:opacity-80"
        >
          <div 
            class="w-8 h-8 rounded-full flex items-center justify-center"
            style="background-color: var(--bg-tertiary);"
          >
            <LucideUser class="size-4" style="color: var(--text-secondary);" />
          </div>
        </button>

        <!-- Dropdown -->
        <div
          v-if="showUserMenu"
          class="absolute right-0 top-full mt-2 w-48 rounded-lg border shadow-lg py-1 z-50"
          style="background-color: var(--bg-elevated); border-color: var(--border-color);"
        >
          <div class="px-4 py-2 border-b" style="border-color: var(--border-color);">
            <p class="text-sm font-medium truncate" style="color: var(--text-primary);">
              {{ sessionStore.user }}
            </p>
          </div>
          <button
            @click="handleLogout"
            class="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-500 hover:opacity-80"
          >
            <LucideLogOut class="size-4" />
            {{ t('settings.logout') }}
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
