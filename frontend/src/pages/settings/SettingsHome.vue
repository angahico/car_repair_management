<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import {
  LucideUser,
  LucideLogOut,
  LucideSearch,
  LucideGlobe,
  LucideBuilding2,
  LucideCar,
  LucideClipboardList,
  LucideClipboardCheck,
  LucideAlertTriangle,
  LucideReceipt,
  LucidePackage,
  LucideUsers,
  LucideShield,
  LucideBell,
  LucidePlug,
  LucideDatabase,
  LucidePalette,
  LucideWrench,
  LucideServer,
  LucideActivity,
  LucidePlay,
  LucideTrash2,
  LucideCheckCircle,
  LucideAlertCircle,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { useSessionStore } from '@/stores'
import { Card, Button, Badge, Input, Skeleton, ConfirmModal } from '@/components/ui'
import { useI18n } from 'vue-i18n'
import { availableLocales } from '@/locales'

interface Integration {
  name: string
  type: string
  status: string
}

interface SystemInfo {
  frappe_version: string
  erpnext_version: string
  site_name: string
}

interface SettingsCategory {
  id: string
  title: string
  description: string
  icon: string
}

interface SettingsHomeData {
  system_info: SystemInfo
  scheduled_jobs_count: number
  integrations: Integration[]
  categories: SettingsCategory[]
}

const sessionStore = useSessionStore()
const { t, locale } = useI18n()

function setLocale(code: string) {
  locale.value = code
  localStorage.setItem('workshop-locale', code)
  document.documentElement.dir = code === 'ar' ? 'rtl' : 'ltr'
}

const isLoading = ref(true)
const data = ref<SettingsHomeData | null>(null)
const searchQuery = ref('')

const categoryIconMap: Record<string, any> = {
  organization: LucideBuilding2,
  vehicles: LucideCar,
  work_orders: LucideClipboardList,
  inspections: LucideClipboardCheck,
  issues: LucideAlertTriangle,
  expenses: LucideReceipt,
  inventory: LucidePackage,
  customers: LucideUsers,
  users: LucideShield,
  notifications: LucideBell,
  integrations: LucidePlug,
  data_audit: LucideDatabase,
  branding: LucidePalette,
  maintenance: LucideWrench,
}

const defaultCategories = computed<SettingsCategory[]>(() => [
  { id: 'organization', title: t('settings.organization'), description: t('settings.organization_desc'), icon: 'organization' },
  { id: 'vehicles', title: t('settings.vehicles_settings'), description: t('settings.vehicles_settings_desc'), icon: 'vehicles' },
  { id: 'work_orders', title: t('settings.work_orders_settings'), description: t('settings.work_orders_settings_desc'), icon: 'work_orders' },
  { id: 'inspections', title: t('settings.inspections_settings'), description: t('settings.inspections_settings_desc'), icon: 'inspections' },
  { id: 'issues', title: t('settings.issues_settings'), description: t('settings.issues_settings_desc'), icon: 'issues' },
  { id: 'expenses', title: t('settings.expenses_settings'), description: t('settings.expenses_settings_desc'), icon: 'expenses' },
  { id: 'inventory', title: t('settings.inventory_settings'), description: t('settings.inventory_settings_desc'), icon: 'inventory' },
  { id: 'customers', title: t('settings.customers_settings'), description: t('settings.customers_settings_desc'), icon: 'customers' },
  { id: 'users', title: t('settings.users_settings'), description: t('settings.users_settings_desc'), icon: 'users' },
  { id: 'notifications', title: t('settings.notifications_settings'), description: t('settings.notifications_settings_desc'), icon: 'notifications' },
  { id: 'integrations', title: t('settings.integrations_settings'), description: t('settings.integrations_settings_desc'), icon: 'integrations' },
  { id: 'data_audit', title: t('settings.data_audit_settings'), description: t('settings.data_audit_settings_desc'), icon: 'data_audit' },
  { id: 'branding', title: t('settings.branding_settings'), description: t('settings.branding_settings_desc'), icon: 'branding' },
  { id: 'maintenance', title: t('settings.maintenance_settings'), description: t('settings.maintenance_settings_desc'), icon: 'maintenance' },
])

const categories = computed(() => {
  return data.value?.categories?.length ? data.value.categories : defaultCategories.value
})

const filteredCategories = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return categories.value
  return categories.value.filter(
    (c) => c.title.toLowerCase().includes(q) || c.description.toLowerCase().includes(q)
  )
})

const activeIntegrationsCount = computed(() => {
  if (!data.value?.integrations) return 0
  return data.value.integrations.filter((i) => i.status === 'Active' || i.status === 'Connected').length
})

// Demo data state
interface DemoStatus {
  is_loaded: boolean
  summary: Record<string, number> | null
  total_records?: number
}

const demoStatus = ref<DemoStatus | null>(null)
const demoLoading = ref(false)
const demoMessage = ref('')
const demoError = ref('')
const showClearConfirm = ref(false)

async function loadDemoStatus() {
  try {
    demoStatus.value = await apiCall<DemoStatus>(
      'car_repair_management.api.settings.demo_status'
    )
  } catch (e) {
    console.warn('Failed to load demo status', e)
  }
}

async function seedDemo() {
  demoLoading.value = true
  demoMessage.value = ''
  demoError.value = ''
  try {
    const res = await apiCall<any>('car_repair_management.api.settings.seed_demo')
    if (res.success) {
      demoMessage.value = `Demo data seeded successfully! Created ${Object.values(res.summary || {}).reduce((a: number, b: unknown) => a + (b as number), 0)} records.`
      await loadDemoStatus()
    } else {
      demoError.value = res.message || 'Failed to seed demo data'
    }
  } catch (e: any) {
    demoError.value = e?.message || 'Failed to seed demo data'
  } finally {
    demoLoading.value = false
  }
}

function promptClearDemo() {
  showClearConfirm.value = true
}

async function clearDemo() {
  demoLoading.value = true
  demoMessage.value = ''
  demoError.value = ''
  try {
    const res = await apiCall<any>('car_repair_management.api.settings.clear_demo')
    if (res.success) {
      demoMessage.value = `Demo data cleared! Removed ${Object.values(res.cleared || {}).reduce((a: number, b: unknown) => a + (b as number), 0)} records.`
      await loadDemoStatus()
    } else {
      demoError.value = res.message || 'Failed to clear demo data'
    }
  } catch (e: any) {
    demoError.value = e?.message || 'Failed to clear demo data'
  } finally {
    demoLoading.value = false
  }
}

function handleLogout() {
  sessionStore.logout.submit()
}

async function loadData() {
  isLoading.value = true
  try {
    data.value = await apiCall<SettingsHomeData>(
      'car_repair_management.api.settings.get_settings_home'
    )
  } catch (e) {
    console.error('Failed to load settings home', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadData()
  loadDemoStatus()
})
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div>
      <h1 class="text-page-title text-ink">{{ $t('settings.title') }}</h1>
      <p class="text-sm mt-1" style="color: var(--text-muted);">
        {{ $t('settings.subtitle') }}
      </p>
    </div>

    <!-- Global Search -->
    <div class="relative max-w-md">
      <LucideSearch
        class="absolute left-3 top-1/2 -translate-y-1/2 size-4 pointer-events-none"
        style="color: var(--text-muted);"
      />
      <input
        v-model="searchQuery"
        type="search"
        :placeholder="$t('settings.search_settings')"
        class="w-full h-10 pl-10 pr-3 text-sm rounded-input border border-default bg-surface-card text-ink placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-colors"
      />
    </div>

    <!-- Environment / Status Strip -->
    <template v-if="isLoading">
      <Card>
        <Skeleton height="36px" />
      </Card>
    </template>
    <template v-else-if="data?.system_info">
      <Card padding="sm">
        <div class="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs" style="color: var(--text-muted);">
          <span class="inline-flex items-center gap-1.5">
            <LucideServer class="size-3.5" />
            Frappe {{ data.system_info.frappe_version }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <LucideActivity class="size-3.5" />
            ERPNext {{ data.system_info.erpnext_version }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            Site: <strong style="color: var(--text-secondary);">{{ data.system_info.site_name }}</strong>
          </span>
          <span>Scheduled Jobs: {{ data.scheduled_jobs_count }}</span>
          <span>Active Integrations: {{ activeIntegrationsCount }}/{{ data.integrations?.length ?? 0 }}</span>
        </div>
      </Card>
    </template>

    <!-- Account -->
    <Card>
      <h3 class="text-section-title text-ink mb-4">{{ $t('settings.account') }}</h3>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center bg-primary-100 dark:bg-primary-500/20"
          >
            <LucideUser class="size-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <p class="text-sm font-medium text-ink">{{ sessionStore.user }}</p>
            <p class="text-xs text-ink-muted">{{ $t('settings.logged_in') }}</p>
          </div>
        </div>
        <Button variant="danger" @click="handleLogout">
          <LucideLogOut class="size-4" />
          {{ $t('settings.logout') }}
        </Button>
      </div>
    </Card>

    <!-- Language -->
    <Card>
      <div class="flex items-center gap-2 mb-4">
        <LucideGlobe class="size-5" style="color: var(--accent);" />
        <h3 class="text-section-title text-ink">{{ $t('settings.language') }}</h3>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="lang in availableLocales"
          :key="lang.code"
          @click="setLocale(lang.code)"
          class="px-4 py-2.5 rounded-lg border text-sm transition-all"
          :style="{
            backgroundColor: locale === lang.code ? 'var(--bg-tertiary)' : 'transparent',
            borderColor: locale === lang.code ? 'var(--accent)' : 'var(--border-color)',
            color: locale === lang.code ? 'var(--text-primary)' : 'var(--text-muted)',
            fontWeight: locale === lang.code ? '500' : '400',
          }"
        >
          {{ lang.nativeName }}
        </button>
      </div>
    </Card>

    <!-- Demo Data -->
    <Card>
      <div class="flex items-start justify-between">
        <div>
          <h3 class="text-section-title text-ink mb-1">{{ $t('settings.demo_data') }}</h3>
          <p class="text-xs" style="color: var(--text-muted);">
            {{ $t('settings.demo_data_desc') }}
          </p>
        </div>
        <Badge v-if="demoStatus?.is_loaded" variant="success" size="sm">
          <LucideCheckCircle class="size-3 mr-1" />
          {{ $t('settings.loaded_records', { count: demoStatus.total_records }) }}
        </Badge>
        <Badge v-else variant="default" size="sm">{{ $t('settings.not_loaded') }}</Badge>
      </div>

      <!-- Summary -->
      <div
        v-if="demoStatus?.is_loaded && demoStatus.summary"
        class="mt-4 flex flex-wrap gap-2"
      >
        <span
          v-for="(count, doctype) in demoStatus.summary"
          :key="String(doctype)"
          class="text-xs px-2 py-1 rounded"
          style="background-color: var(--bg-tertiary); color: var(--text-secondary);"
        >
          {{ String(doctype) }}: {{ count }}
        </span>
      </div>

      <!-- Actions -->
      <div class="mt-4 flex items-center gap-3">
        <Button
          v-if="!demoStatus?.is_loaded"
          variant="primary"
          size="sm"
          :loading="demoLoading"
          @click="seedDemo"
        >
          <LucidePlay class="size-4" />
          {{ $t('settings.seed_demo') }}
        </Button>
        <Button
          v-if="demoStatus?.is_loaded"
          variant="danger"
          size="sm"
          :loading="demoLoading"
          @click="promptClearDemo"
        >
          <LucideTrash2 class="size-4" />
          {{ $t('settings.clear_demo') }}
        </Button>
      </div>

      <!-- Messages -->
      <div v-if="demoMessage" class="mt-3 flex items-center gap-2 text-xs px-3 py-2 rounded-lg" style="background-color: var(--bg-tertiary); color: var(--text-secondary);">
        <LucideCheckCircle class="size-3.5 shrink-0" style="color: green;" />
        {{ demoMessage }}
      </div>
      <div v-if="demoError" class="mt-3 flex items-center gap-2 text-xs px-3 py-2 rounded-lg" style="background-color: var(--bg-tertiary); color: red;">
        <LucideAlertCircle class="size-3.5 shrink-0" />
        {{ demoError }}
      </div>
    </Card>

    <ConfirmModal
      v-if="showClearConfirm"
      :title="$t('settings.clear_demo')"
      :message="$t('settings.clear_demo_confirm')"
      :confirm-label="$t('settings.clear_all_data')"
      variant="danger"
      :show-reason="true"
      reason-label="Reason (optional)"
      :loading="demoLoading"
      @confirm="clearDemo(); showClearConfirm = false"
      @cancel="showClearConfirm = false"
    />

    <!-- Category Cards Grid -->
    <div>
      <h2 class="text-section-title text-ink mb-4">{{ $t('settings.configuration') }}</h2>
      <template v-if="isLoading">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card v-for="i in 14" :key="i" class="animate-pulse">
            <Skeleton height="72px" />
          </Card>
        </div>
      </template>
      <template v-else-if="filteredCategories.length">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <RouterLink
            v-for="cat in filteredCategories"
            :key="cat.id"
            :to="`/settings/${cat.id}`"
          >
            <Card hoverable class="h-full">
              <div class="flex items-start gap-3">
                <div class="p-2.5 rounded-lg shrink-0" style="background-color: var(--bg-tertiary);">
                  <component
                    :is="categoryIconMap[cat.id] || LucideWrench"
                    class="size-5"
                    style="color: var(--accent);"
                  />
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-medium" style="color: var(--text-primary);">{{ cat.title }}</p>
                  <p class="text-xs mt-0.5 line-clamp-2" style="color: var(--text-muted);">
                    {{ cat.description }}
                  </p>
                </div>
              </div>
            </Card>
          </RouterLink>
        </div>
      </template>
      <Card v-else>
        <p class="text-sm text-center py-4" style="color: var(--text-muted);">
          {{ $t('settings.no_match', { query: searchQuery }) }}
        </p>
      </Card>
    </div>
  </div>
</template>
