<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideBell,
  LucidePlus,
  LucideRefreshCw,
  LucideSearch,
  LucideDownload,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, EmptyState, Skeleton, Badge, Input } from '@/components/ui'
import type { StatusVariant } from '@/types'
import { useI18n } from 'vue-i18n'

interface RecallRecord {
  name: string
  title: string
  manufacturer: string
  affected_models: string | null
  affected_years: string | null
  issue_type: string | null
  recall_start_date: string | null
  deadline: string | null
  status: string
  priority: string
  vehicles_affected: number
  vehicles_completed: number
  compliance_pct: number
  external_reference: string | null
  owner: string
  creation: string
  modified: string
}

interface RecallsData {
  records: RecallRecord[]
  total: number
}

const router = useRouter()
const { t } = useI18n()

const records = ref<RecallRecord[]>([])
const total = ref(0)
const isLoading = ref(true)
const currentPage = ref(1)
const pageSize = 20

const search = ref('')
const manufacturerFilter = ref('')
const statusFilter = ref('')
const priorityFilter = ref('')
const issueTypeFilter = ref('')

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Active: 'danger',
  'In Progress': 'warning',
  Completed: 'success',
  Cancelled: 'default',
}

const PRIORITY_VARIANTS: Record<string, StatusVariant> = {
  Low: 'default',
  Medium: 'warning',
  High: 'danger',
  Critical: 'danger',
}

const STATUS_OPTIONS = ['', 'Active', 'In Progress', 'Completed', 'Cancelled']
const PRIORITY_OPTIONS = ['', 'Low', 'Medium', 'High', 'Critical']
const ISSUE_TYPE_OPTIONS = ['', 'Safety', 'Emissions', 'Mechanical', 'Electrical', 'Software', 'Other']

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const parts = dateStr.split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    return d.toLocaleDateString()
  }
  return dateStr
}

function isOverdue(deadline: string | null, status: string): boolean {
  if (!deadline || status === 'Completed' || status === 'Cancelled') return false
  const parts = deadline.split('-')
  if (parts.length !== 3) return false
  const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
  return d < new Date()
}

function complianceColor(pct: number): string {
  if (pct >= 80) return '#22c55e'
  if (pct >= 50) return '#f59e0b'
  return '#ef4444'
}

async function loadRecalls() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: (currentPage.value - 1) * pageSize,
      limit_page_length: pageSize,
    }
    if (search.value) args.search = search.value
    if (manufacturerFilter.value) args.manufacturer = manufacturerFilter.value
    if (statusFilter.value) args.status = statusFilter.value
    if (priorityFilter.value) args.priority = priorityFilter.value

    const result = await apiCall<RecallsData>(
      'car_repair_management.api.issue.get_recalls',
      args,
    )
    records.value = result.records
    total.value = result.total
  } catch (e) {
    console.warn('Failed to load recalls', e)
    records.value = []
    total.value = 0
  } finally {
    isLoading.value = false
  }
}

function openRecall(record: RecallRecord) {
  router.push(`/issues/recalls/${record.name}`)
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function exportCsv() {
  const headers = [
    'Recall ID', 'Title', 'Manufacturer', 'Affected Models', 'Affected Years',
    'Issue Type', 'Start Date', 'Deadline', 'Status', 'Priority',
    'Vehicles Affected', 'Vehicles Completed', 'Compliance %',
  ]
  const rows = records.value.map(r => [
    r.name, r.title, r.manufacturer, r.affected_models || '', r.affected_years || '',
    r.issue_type || '', r.recall_start_date || '', r.deadline || '', r.status, r.priority,
    r.vehicles_affected, r.vehicles_completed, r.compliance_pct,
  ])
  const csv = [headers, ...rows].map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'recalls.csv'
  a.click()
  URL.revokeObjectURL(url)
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null
function onFilterChange() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    loadRecalls()
  }, 300)
}

watch([statusFilter, priorityFilter, issueTypeFilter], () => {
  currentPage.value = 1
  loadRecalls()
})

watch([search, manufacturerFilter], () => {
  onFilterChange()
})

watch(currentPage, () => {
  loadRecalls()
})

onMounted(loadRecalls)
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-page-title" style="color: var(--text-primary)">{{ $t('issues.recalls_title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">{{ $t('issues.recalls_subtitle') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <Button variant="outline" @click="exportCsv">
          <LucideDownload class="size-4" />
          {{ $t('common.export_csv') }}
        </Button>
        <Button variant="outline" @click="loadRecalls">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
        <a href="/app/vehicle-recall/new" target="_blank">
          <Button variant="primary">
            <LucidePlus class="size-4" />
            Add Recall
          </Button>
        </a>
      </div>
    </div>

    <!-- Filters -->
    <Card>
      <div class="flex flex-wrap items-end gap-3">
        <div class="flex-1 min-w-[200px]">
          <label class="text-xs font-medium mb-1 block" style="color: var(--text-muted)">{{ $t('common.search') }}</label>
          <div class="relative">
            <LucideSearch class="size-4 absolute left-3 top-1/2 -translate-y-1/2" style="color: var(--text-muted)" />
            <input
              v-model="search"
              type="text"
              placeholder="Search by title or manufacturer..."
              class="w-full h-10 pl-9 pr-3 text-sm rounded-input border bg-surface-card transition-colors text-ink placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 border-default"
            />
          </div>
        </div>
        <div class="min-w-[160px]">
          <label class="text-xs font-medium mb-1 block" style="color: var(--text-muted)">{{ $t('issues.manufacturer') }}</label>
          <input
            v-model="manufacturerFilter"
            type="text"
            placeholder="Filter manufacturer..."
            class="w-full h-10 px-3 text-sm rounded-input border bg-surface-card transition-colors text-ink placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 border-default"
          />
        </div>
        <div class="min-w-[130px]">
          <label class="text-xs font-medium mb-1 block" style="color: var(--text-muted)">{{ $t('common.status') }}</label>
          <select
            v-model="statusFilter"
            class="w-full h-10 px-3 text-sm rounded-input border bg-surface-card transition-colors text-ink focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 border-default"
          >
            <option value="">{{ $t('common.all') }}</option>
            <option v-for="s in STATUS_OPTIONS.filter(v => v)" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="min-w-[120px]">
          <label class="text-xs font-medium mb-1 block" style="color: var(--text-muted)">{{ $t('common.priority') }}</label>
          <select
            v-model="priorityFilter"
            class="w-full h-10 px-3 text-sm rounded-input border bg-surface-card transition-colors text-ink focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 border-default"
          >
            <option value="">{{ $t('common.all') }}</option>
            <option v-for="p in PRIORITY_OPTIONS.filter(v => v)" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>
        <div class="min-w-[130px]">
          <label class="text-xs font-medium mb-1 block" style="color: var(--text-muted)">{{ $t('issues.issue_type') }}</label>
          <select
            v-model="issueTypeFilter"
            class="w-full h-10 px-3 text-sm rounded-input border bg-surface-card transition-colors text-ink focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 border-default"
          >
            <option value="">{{ $t('common.all') }}</option>
            <option v-for="t in ISSUE_TYPE_OPTIONS.filter(v => v)" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
      </div>
    </Card>

    <!-- Data Table -->
    <Card padding="none">
      <div v-if="isLoading" class="p-4 space-y-3">
        <Skeleton v-for="i in 5" :key="i" height="56px" />
      </div>

      <EmptyState
        v-else-if="records.length === 0"
        :icon="LucideBell"
        :title="$t('issues.no_recalls')"
        :description="$t('issues.no_recalls_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm" style="color: var(--text-primary)">
          <thead>
            <tr class="border-b" style="border-color: var(--border-subtle)">
              <th class="text-left px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">Recall ID</th>
              <th class="text-left px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">Title</th>
              <th class="text-left px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">{{ $t('issues.manufacturer') }}</th>
              <th class="text-left px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">{{ $t('issues.affected_models') }}</th>
              <th class="text-left px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">{{ $t('issues.issue_type') }}</th>
              <th class="text-left px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">{{ $t('issues.recall_start_date') }}</th>
              <th class="text-left px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">Deadline</th>
              <th class="text-left px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">{{ $t('common.status') }}</th>
              <th class="text-right px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">{{ $t('issues.vehicles_affected') }}</th>
              <th class="text-right px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">{{ $t('issues.vehicles_completed') }}</th>
              <th class="text-left px-4 py-2.5 text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">Compliance %</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in records"
              :key="r.name"
              class="border-b cursor-pointer transition-colors"
              style="border-color: var(--border-subtle)"
              @click="openRecall(r)"
              @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
            >
              <td class="px-4 py-3 font-medium whitespace-nowrap">{{ r.name }}</td>
              <td class="px-4 py-3 max-w-[200px] truncate">{{ r.title }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.manufacturer }}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">
                {{ r.affected_models || '—' }}
                <span v-if="r.affected_years"> / {{ r.affected_years }}</span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                <Badge v-if="r.issue_type" variant="default" size="sm">{{ r.issue_type }}</Badge>
                <span v-else style="color: var(--text-muted)">—</span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">
                {{ formatDate(r.recall_start_date) }}
              </td>
              <td
                class="px-4 py-3 whitespace-nowrap font-medium"
                :style="{ color: isOverdue(r.deadline, r.status) ? '#ef4444' : 'var(--text-secondary)' }"
              >
                {{ formatDate(r.deadline) }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                <Badge :variant="STATUS_VARIANTS[r.status] || 'default'" size="sm">{{ r.status }}</Badge>
              </td>
              <td class="px-4 py-3 text-right whitespace-nowrap">{{ r.vehicles_affected }}</td>
              <td class="px-4 py-3 text-right whitespace-nowrap">{{ r.vehicles_completed }}</td>
              <td class="px-4 py-3 whitespace-nowrap min-w-[140px]">
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-2 rounded-full" style="background: var(--bg-tertiary)">
                    <div
                      class="h-2 rounded-full transition-all"
                      :style="{ width: `${Math.min(r.compliance_pct, 100)}%`, backgroundColor: complianceColor(r.compliance_pct) }"
                    />
                  </div>
                  <span
                    class="text-xs font-semibold w-10 text-right"
                    :style="{ color: complianceColor(r.compliance_pct) }"
                  >
                    {{ r.compliance_pct }}%
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div
        v-if="records.length > 0"
        class="flex items-center justify-between px-4 py-3 border-t"
        style="border-color: var(--border-subtle)"
      >
        <p class="text-xs" style="color: var(--text-muted)">
          {{ $t('common.showing') }} {{ (currentPage - 1) * pageSize + 1 }}–{{ Math.min(currentPage * pageSize, total) }} {{ $t('common.of') }} {{ total }}
        </p>
        <div class="flex items-center gap-1">
          <button
            class="px-3 py-1.5 text-xs rounded transition-colors"
            :disabled="currentPage <= 1"
            :style="{
              color: currentPage <= 1 ? 'var(--text-muted)' : 'var(--text-primary)',
              background: 'var(--bg-tertiary)',
              opacity: currentPage <= 1 ? '0.5' : '1',
              cursor: currentPage <= 1 ? 'not-allowed' : 'pointer',
            }"
            @click="goToPage(currentPage - 1)"
          >
            {{ $t('common.previous') }}
          </button>
          <span class="px-3 py-1.5 text-xs" style="color: var(--text-muted)">
            {{ $t('common.page') }} {{ currentPage }} {{ $t('common.of') }} {{ totalPages }}
          </span>
          <button
            class="px-3 py-1.5 text-xs rounded transition-colors"
            :disabled="currentPage >= totalPages"
            :style="{
              color: currentPage >= totalPages ? 'var(--text-muted)' : 'var(--text-primary)',
              background: 'var(--bg-tertiary)',
              opacity: currentPage >= totalPages ? '0.5' : '1',
              cursor: currentPage >= totalPages ? 'not-allowed' : 'pointer',
            }"
            @click="goToPage(currentPage + 1)"
          >
            {{ $t('common.next') }}
          </button>
        </div>
      </div>
    </Card>
  </div>
</template>
