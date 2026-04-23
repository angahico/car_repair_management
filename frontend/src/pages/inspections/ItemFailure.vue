<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideAlertTriangle,
  LucideAlertCircle,
  LucideRepeat,
  LucideWrench,
  LucideClock,
  LucideSearch,
  LucideRefreshCw,
  LucideDownload,
  LucideImage,
  LucideChevronLeft,
  LucideChevronRight,
} from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Input } from '@/components/ui'

// --- Types ---
interface KPIs {
  total_failures: number
  open_failures: number
  recurring_failures: number
  most_failed_component: string
  avg_time_to_resolution: number
}

interface FailureRecord {
  name: string
  reported_date: string | null
  vehicle: string
  item_name: string
  severity: string
  inspection: string | null
  status: string
  resolution_type: string | null
  linked_work_order: string | null
  assigned_to: string | null
  evidence: string | null
  is_recurring: number
  failure_reason: string | null
  owner: string
  creation: string
  modified: string
}

interface ItemFailureData {
  kpis: KPIs
  records: FailureRecord[]
  total: number
}

// --- State ---
const router = useRouter()
const { t } = useI18n()
const isLoading = ref(true)
const data = ref<ItemFailureData | null>(null)

const searchQuery = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const selectedSeverity = ref<string | null>(null)
const selectedStatus = ref<string | null>(null)
const isRecurring = ref(false)
const currentPage = ref(0)
const PAGE_SIZE = 20

const SEVERITY_VARIANTS: Record<string, string> = {
  Low: 'default',
  Medium: 'warning',
  High: 'danger',
  Critical: 'danger',
}

const STATUS_VARIANTS: Record<string, string> = {
  Open: 'warning',
  Converted: 'info',
  Resolved: 'success',
  Ignored: 'default',
}

// --- Helpers ---
function formatDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function formatDisplayDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const parts = dateStr.split('-')
  if (parts.length !== 3) return dateStr
  const y = parseInt(parts[0], 10)
  const m = parseInt(parts[1], 10) - 1
  const day = parseInt(parts[2], 10)
  const d = new Date(y, m, day)
  return d.toLocaleDateString()
}

function setPreset(days: number) {
  const now = new Date()
  const from = new Date(now.getFullYear(), now.getMonth(), now.getDate() - days)
  dateTo.value = formatDate(now)
  dateFrom.value = formatDate(from)
  currentPage.value = 0
  loadData()
}

// --- Load ---
async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: currentPage.value * PAGE_SIZE,
      limit_page_length: PAGE_SIZE,
    }
    if (dateFrom.value) args.date_from = dateFrom.value
    if (dateTo.value) args.date_to = dateTo.value
    if (selectedSeverity.value) args.severity = selectedSeverity.value
    if (selectedStatus.value) args.status = selectedStatus.value
    if (isRecurring.value) args.is_recurring = 1
    if (searchQuery.value) args.search = searchQuery.value
    const result = await apiCall<ItemFailureData>(
      'car_repair_management.api.inspection.get_item_failures',
      args,
    )
    data.value = result
  } catch (e) {
    console.warn('Failed to load item failures', e)
  } finally {
    isLoading.value = false
  }
}

function applyFilters() {
  currentPage.value = 0
  loadData()
}

function goToPage(page: number) {
  currentPage.value = page
  loadData()
}

function navigateToDetail(name: string) {
  router.push(`/inspections/item-failures/${name}`)
}

// --- Export ---
function exportCSV() {
  if (!data.value?.records.length) return
  const headers = ['Failure ID', 'Date', 'Vehicle', 'Component', 'Severity', 'Inspection', 'Status', 'Resolution Type', 'Work Order', 'Assigned To', 'Recurring']
  const rows = data.value.records.map((r) => [
    r.name,
    r.reported_date || '',
    r.vehicle,
    r.item_name,
    r.severity,
    r.inspection || '',
    r.status,
    r.resolution_type || '',
    r.linked_work_order || '',
    r.assigned_to || '',
    r.is_recurring ? 'Yes' : 'No',
  ])
  const csv = [headers.join(','), ...rows.map((r) => r.map((c) => `"${c}"`).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `item_failures_${formatDate(new Date())}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => setPreset(90))
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div>
        <h1 class="text-page-title">{{ $t('inspections.item_failures_title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">
          {{ data?.total ?? 0 }} total failures
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="exportCSV">
          <LucideDownload class="size-4" />
        </Button>
        <Button variant="outline" @click="loadData">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
      </div>
    </div>

    <!-- Control Bar -->
    <Card>
      <div class="flex flex-wrap items-end gap-4">
        <!-- Search -->
        <div class="flex-1 min-w-[200px]">
          <label class="text-label block mb-1">{{ $t('common.search') }}</label>
          <div class="relative">
            <LucideSearch class="size-4 absolute left-3 top-1/2 -translate-y-1/2" style="color: var(--text-muted)" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Component, vehicle, inspection ID..."
              class="w-full rounded-lg border px-3 py-2 pl-9 text-sm bg-surface-bg text-ink border-default"
              @keyup.enter="applyFilters"
            />
          </div>
        </div>

        <!-- Date Range -->
        <div>
          <label class="text-label block mb-1">{{ $t('common.from') }}</label>
          <input v-model="dateFrom" type="date" class="rounded-lg border px-3 py-2 text-sm bg-surface-bg text-ink border-default" />
        </div>
        <div>
          <label class="text-label block mb-1">{{ $t('common.to') }}</label>
          <input v-model="dateTo" type="date" class="rounded-lg border px-3 py-2 text-sm bg-surface-bg text-ink border-default" />
        </div>

        <!-- Time Presets -->
        <div class="flex items-center gap-1">
          <button
            v-for="preset in [{ label: '7D', days: 7 }, { label: '30D', days: 30 }, { label: '90D', days: 90 }, { label: '1Y', days: 365 }]"
            :key="preset.days"
            class="px-3 py-2 text-xs font-medium rounded-lg border transition-colors"
            :style="{ borderColor: 'var(--border-color)', color: 'var(--text-secondary)', backgroundColor: 'var(--bg-tertiary)' }"
            @click="setPreset(preset.days)"
          >{{ preset.label }}</button>
        </div>
      </div>

      <!-- Severity + Status + Recurring row -->
      <div class="flex flex-wrap items-center gap-4 mt-4 pt-4 border-t" style="border-color: var(--border-color)">
        <!-- Severity -->
        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('inspections.severity') }}:</span>
          <button
            v-for="sev in [{ id: null, label: $t('common.all') }, { id: 'Low', label: 'Low' }, { id: 'Medium', label: 'Medium' }, { id: 'High', label: 'High' }, { id: 'Critical', label: 'Critical' }]"
            :key="sev.label"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors"
            :style="{
              borderColor: selectedSeverity === sev.id ? 'var(--accent)' : 'var(--border-color)',
              color: selectedSeverity === sev.id ? 'var(--accent-text)' : 'var(--text-secondary)',
              backgroundColor: selectedSeverity === sev.id ? 'var(--accent)' : 'transparent',
            }"
            @click="selectedSeverity = sev.id; applyFilters()"
          >{{ sev.label }}</button>
        </div>

        <!-- Status -->
        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('common.status') }}:</span>
          <button
            v-for="st in [{ id: null, label: $t('common.all') }, { id: 'Open', label: 'Open' }, { id: 'Converted', label: 'Converted' }, { id: 'Resolved', label: 'Resolved' }, { id: 'Ignored', label: 'Ignored' }]"
            :key="st.label"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors"
            :style="{
              borderColor: selectedStatus === st.id ? 'var(--accent)' : 'var(--border-color)',
              color: selectedStatus === st.id ? 'var(--accent-text)' : 'var(--text-secondary)',
              backgroundColor: selectedStatus === st.id ? 'var(--accent)' : 'transparent',
            }"
            @click="selectedStatus = st.id; applyFilters()"
          >{{ st.label }}</button>
        </div>

        <!-- Recurring Toggle -->
        <button
          class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors flex items-center gap-1.5"
          :style="{
            borderColor: isRecurring ? 'var(--accent)' : 'var(--border-color)',
            color: isRecurring ? 'var(--accent-text)' : 'var(--text-secondary)',
            backgroundColor: isRecurring ? 'var(--accent)' : 'transparent',
          }"
          @click="isRecurring = !isRecurring; applyFilters()"
        >
          <LucideRepeat class="size-3" />
          {{ $t('inspections.is_recurring') }}
        </button>

        <Button variant="primary" size="sm" @click="applyFilters">{{ $t('common.apply') }}</Button>
      </div>
    </Card>

    <!-- KPI Cards -->
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      <Card v-for="i in 5" :key="i"><Skeleton height="80px" /></Card>
    </div>
    <div v-else-if="data" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      <!-- Total Failures -->
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-red-100 dark:bg-red-500/20 flex items-center justify-center shrink-0">
            <LucideAlertTriangle class="size-5 text-red-600 dark:text-red-400" />
          </div>
          <div>
            <p class="text-label">Total Failures</p>
            <p class="text-2xl font-semibold text-ink">{{ data.kpis.total_failures }}</p>
          </div>
        </div>
      </Card>
      <!-- Open Failures -->
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center shrink-0">
            <LucideAlertCircle class="size-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <p class="text-label">Open Failures</p>
            <p class="text-2xl font-semibold text-ink">{{ data.kpis.open_failures }}</p>
          </div>
        </div>
      </Card>
      <!-- Recurring Failures -->
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-500/20 flex items-center justify-center shrink-0">
            <LucideRepeat class="size-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <p class="text-label">Recurring Failures</p>
            <p class="text-2xl font-semibold text-ink">{{ data.kpis.recurring_failures }}</p>
          </div>
        </div>
      </Card>
      <!-- Most Failed Component -->
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center shrink-0">
            <LucideWrench class="size-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <p class="text-label">Most Failed Component</p>
            <p class="text-lg font-semibold text-ink truncate">{{ data.kpis.most_failed_component || '—' }}</p>
          </div>
        </div>
      </Card>
      <!-- Avg Time to Resolution -->
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-cyan-100 dark:bg-cyan-500/20 flex items-center justify-center shrink-0">
            <LucideClock class="size-5 text-cyan-600 dark:text-cyan-400" />
          </div>
          <div>
            <p class="text-label">Avg Time to Resolution</p>
            <p class="text-2xl font-semibold text-ink">{{ data.kpis.avg_time_to_resolution }} {{ $t('common.days') }}</p>
          </div>
        </div>
      </Card>
    </div>

    <!-- Data Table -->
    <Card v-if="isLoading" padding="none">
      <div class="p-4 space-y-3">
        <Skeleton v-for="i in 5" :key="i" height="48px" />
      </div>
    </Card>

    <Card v-else-if="data" padding="none">
      <div class="p-4 border-b border-default">
        <h2 class="text-section-title">Failure Records</h2>
        <p class="text-xs text-ink-muted mt-1">{{ data.total }} total • Page {{ currentPage + 1 }} of {{ Math.max(1, Math.ceil(data.total / PAGE_SIZE)) }}</p>
      </div>

      <EmptyState
        v-if="data.records.length === 0"
        :icon="LucideAlertTriangle"
        :title="$t('inspections.no_item_failures')"
        :description="$t('inspections.no_item_failures_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-default">
              <th class="text-left text-label px-4 py-3 font-medium">Failure ID</th>
              <th class="text-left text-label px-4 py-3 font-medium">Date</th>
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('common.vehicle') }}</th>
              <th class="text-left text-label px-4 py-3 font-medium">Component</th>
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('inspections.severity') }}</th>
              <th class="text-left text-label px-4 py-3 font-medium">Inspection</th>
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('common.status') }}</th>
              <th class="text-left text-label px-4 py-3 font-medium">Resolution</th>
              <th class="text-left text-label px-4 py-3 font-medium">Work Order</th>
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('inspections.assigned_to') }}</th>
              <th class="text-center text-label px-4 py-3 font-medium">Evidence</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="record in data.records"
              :key="record.name"
              class="border-b border-default hover:bg-surface-secondary transition-colors cursor-pointer"
              @click="navigateToDetail(record.name)"
            >
              <td class="px-4 py-3 font-medium" style="color: var(--accent)">{{ record.name }}</td>
              <td class="px-4 py-3 text-ink">{{ formatDisplayDate(record.reported_date) }}</td>
              <td class="px-4 py-3 text-ink font-medium">{{ record.vehicle }}</td>
              <td class="px-4 py-3 text-ink">
                <div class="flex items-center gap-1.5">
                  {{ record.item_name }}
                  <LucideRepeat v-if="record.is_recurring" class="size-3 text-purple-500" />
                </div>
              </td>
              <td class="px-4 py-3">
                <Badge :variant="SEVERITY_VARIANTS[record.severity] || 'default'" size="sm">{{ record.severity }}</Badge>
              </td>
              <td class="px-4 py-3 text-ink-muted">{{ record.inspection || '—' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="STATUS_VARIANTS[record.status] || 'default'" size="sm">{{ record.status }}</Badge>
              </td>
              <td class="px-4 py-3 text-ink-muted">{{ record.resolution_type || '—' }}</td>
              <td class="px-4 py-3 text-ink-muted">{{ record.linked_work_order || '—' }}</td>
              <td class="px-4 py-3 text-ink-muted">{{ record.assigned_to || '—' }}</td>
              <td class="px-4 py-3 text-center">
                <LucideImage v-if="record.evidence" class="size-4 text-green-500 inline" />
                <span v-else class="text-ink-muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="data.total > PAGE_SIZE" class="flex items-center justify-between px-4 py-3 border-t border-default">
        <p class="text-xs" style="color: var(--text-muted)">
          {{ $t('common.showing') }} {{ currentPage * PAGE_SIZE + 1 }}–{{ Math.min((currentPage + 1) * PAGE_SIZE, data.total) }} {{ $t('common.of') }} {{ data.total }}
        </p>
        <div class="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            :disabled="currentPage === 0"
            @click="goToPage(currentPage - 1)"
          >
            <LucideChevronLeft class="size-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            :disabled="(currentPage + 1) * PAGE_SIZE >= data.total"
            @click="goToPage(currentPage + 1)"
          >
            <LucideChevronRight class="size-4" />
          </Button>
        </div>
      </div>
    </Card>
  </div>
</template>
