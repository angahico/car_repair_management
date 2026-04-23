<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideCalendarClock,
  LucidePlus,
  LucideSearch,
  LucideRefreshCw,
  LucideDownload,
  LucideTable,
  LucideCalendar,
  LucideColumns3,
  LucideGanttChart,
  LucideConstruction,
} from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, LinkField } from '@/components/ui'
import type { PaginationState, StatusVariant } from '@/types'

type ViewMode = 'table' | 'calendar' | 'kanban' | 'gantt'

interface ScheduleRecord {
  name: string
  title: string
  vehicle: string
  form_template: string | null
  scheduled_date: string | null
  frequency: string
  assigned_to: string | null
  status: string
  last_completed: string | null
  next_due: string | null
  auto_create_inspection: number
  owner: string
  creation: string
  modified: string
}

interface ScheduleData {
  records: ScheduleRecord[]
  total: number
}

const router = useRouter()
const { t } = useI18n()

const schedules = ref<ScheduleRecord[]>([])
const isLoading = ref(true)
const searchQuery = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const statusFilter = ref('All')
const frequencyFilter = ref('All')
const viewMode = ref<ViewMode>('table')
const pagination = ref<PaginationState>({
  page: 1,
  pageSize: 20,
  total: 0,
})

const STATUS_OPTIONS = ['All', 'Active', 'Paused', 'Completed', 'Cancelled']
const FREQUENCY_OPTIONS = ['All', 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Annually', 'One-Time']
const FREQUENCY_CREATE = ['Daily', 'Weekly', 'Bi-Weekly', 'Monthly', 'Quarterly', 'Semi-Annually', 'Annually', 'One-Time']

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Active: 'success',
  Paused: 'warning',
  Completed: 'default',
  Cancelled: 'danger',
}

const VIEW_OPTIONS: { id: ViewMode; icon: any; label: string }[] = [
  { id: 'table', icon: LucideTable, label: 'Table' },
  { id: 'calendar', icon: LucideCalendar, label: 'Calendar' },
  { id: 'kanban', icon: LucideColumns3, label: 'Kanban' },
  { id: 'gantt', icon: LucideGanttChart, label: 'Gantt' },
]

const TIME_PRESETS = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
  { label: '1Y', days: 365 },
]

function parseDateSafe(dateStr: string | null | undefined): Date | null {
  if (!dateStr) return null
  const parts = dateStr.split('-')
  if (parts.length !== 3) return null
  const y = parseInt(parts[0], 10)
  const m = parseInt(parts[1], 10) - 1
  const d = parseInt(parts[2], 10)
  if (isNaN(y) || isNaN(m) || isNaN(d)) return null
  return new Date(y, m, d)
}

function formatDate(dateStr: string | null | undefined): string {
  const date = parseDateSafe(dateStr)
  if (!date) return '—'
  return date.toLocaleDateString()
}

function isOverdue(nextDue: string | null | undefined): boolean {
  const date = parseDateSafe(nextDue)
  if (!date) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date < today
}

function formatISODate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function applyTimePreset(days: number) {
  const now = new Date()
  dateFrom.value = formatISODate(now)
  const future = new Date(now)
  future.setDate(future.getDate() + days)
  dateTo.value = formatISODate(future)
  pagination.value.page = 1
  loadSchedules()
}

async function loadSchedules() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: (pagination.value.page - 1) * pagination.value.pageSize,
      limit_page_length: pagination.value.pageSize,
    }
    if (searchQuery.value) args.search = searchQuery.value
    if (dateFrom.value) args.date_from = dateFrom.value
    if (dateTo.value) args.date_to = dateTo.value
    if (statusFilter.value !== 'All') args.status = statusFilter.value
    if (frequencyFilter.value !== 'All') args.frequency = frequencyFilter.value

    const result = await apiCall<ScheduleData>(
      'car_repair_management.api.inspection.get_schedules',
      args,
    )
    schedules.value = result?.records || []
    pagination.value.total = result?.total || 0
  } catch (e) {
    console.warn('Failed to load schedules', e)
    schedules.value = []
    pagination.value.total = 0
  } finally {
    isLoading.value = false
  }
}

function handlePageChange(newPage: number) {
  pagination.value.page = newPage
  loadSchedules()
}

function handleSearch() {
  pagination.value.page = 1
  loadSchedules()
}

function handleFilterChange() {
  pagination.value.page = 1
  loadSchedules()
}

function exportCSV() {
  if (!schedules.value.length) return
  const headers = ['Schedule ID', 'Title', 'Vehicle', 'Form', 'Scheduled Date', 'Frequency', 'Assigned To', 'Status', 'Last Completed', 'Next Due']
  const rows = schedules.value.map(s => [
    s.name,
    s.title,
    s.vehicle,
    s.form_template || '',
    s.scheduled_date || '',
    s.frequency,
    s.assigned_to || '',
    s.status,
    s.last_completed || '',
    s.next_due || '',
  ])
  const csv = [headers, ...rows].map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'inspection_schedules.csv'
  a.click()
  URL.revokeObjectURL(url)
}

const showNewForm = ref(false)
const isCreating = ref(false)
const createError = ref('')
const newForm = ref({
  title: '',
  vehicle: '',
  form_template: '',
  assigned_to: '',
  status: 'Active',
  frequency: '',
  scheduled_date: '',
  auto_create_inspection: 1,
  notify_before_days: 3,
  notes: '',
})

async function createSchedule() {
  isCreating.value = true
  createError.value = ''
  try {
    const result = await apiCall<any>(
      'car_repair_management.api.inspection.create_schedule',
      { data: JSON.stringify(newForm.value) },
    )
    showNewForm.value = false
    router.push(`/inspections/schedules/${result.name}`)
  } catch (e: any) {
    createError.value = e.message || 'Failed to create schedule'
  } finally {
    isCreating.value = false
  }
}

const totalPages = computed(() => Math.ceil(pagination.value.total / pagination.value.pageSize))

watch([statusFilter, frequencyFilter], handleFilterChange)
onMounted(loadSchedules)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-page-title" style="color: var(--text-primary);">{{ $t('inspections.schedules_title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted);">
          {{ pagination.total }} scheduled inspections
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" @click="exportCSV" title="Export CSV">
          <LucideDownload class="size-4" />
        </Button>
        <Button variant="outline" size="sm" @click="loadSchedules" title="Refresh">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
        <Button variant="primary" @click="showNewForm = true">
          <LucidePlus class="size-4" />
          New Schedule
        </Button>
      </div>
    </div>

    <!-- New Schedule Form -->
    <Card v-if="showNewForm">
      <div class="space-y-4">
        <h2 class="text-lg font-semibold" style="color: var(--text-primary);">New Schedule</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- Title -->
          <div class="space-y-1">
            <label class="text-xs font-medium" style="color: var(--text-muted);">Title *</label>
            <input
              v-model="newForm.title"
              type="text"
              required
              placeholder="Schedule title"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            />
          </div>
          <!-- Vehicle -->
          <div class="space-y-1">
            <label class="text-xs font-medium" style="color: var(--text-muted);">Vehicle *</label>
            <LinkField
              v-model="newForm.vehicle"
              doctype="Vehicle"
              titleField="license_plate"
              placeholder="Select vehicle"
            />
          </div>
          <!-- Form Template -->
          <div class="space-y-1">
            <label class="text-xs font-medium" style="color: var(--text-muted);">Form Template</label>
            <LinkField
              v-model="newForm.form_template"
              doctype="Inspection Form Template"
              titleField="title"
              placeholder="Select template"
            />
          </div>
          <!-- Assigned To -->
          <div class="space-y-1">
            <label class="text-xs font-medium" style="color: var(--text-muted);">Assigned To</label>
            <LinkField
              v-model="newForm.assigned_to"
              doctype="Employee"
              titleField="employee_name"
              placeholder="Select employee"
            />
          </div>
          <!-- Frequency -->
          <div class="space-y-1">
            <label class="text-xs font-medium" style="color: var(--text-muted);">Frequency</label>
            <select
              v-model="newForm.frequency"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            >
              <option value="" disabled>Select frequency</option>
              <option v-for="f in FREQUENCY_CREATE" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <!-- Scheduled Date -->
          <div class="space-y-1">
            <label class="text-xs font-medium" style="color: var(--text-muted);">Scheduled Date *</label>
            <input
              v-model="newForm.scheduled_date"
              type="date"
              required
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            />
          </div>
          <!-- Auto Create Inspection -->
          <div class="flex items-center gap-2 self-end h-10">
            <input
              v-model="newForm.auto_create_inspection"
              type="checkbox"
              :true-value="1"
              :false-value="0"
              class="size-4 rounded border"
              style="border-color: var(--border-color);"
            />
            <label class="text-sm" style="color: var(--text-primary);">Auto Create Inspection</label>
          </div>
          <!-- Notify Before Days -->
          <div class="space-y-1">
            <label class="text-xs font-medium" style="color: var(--text-muted);">Notify Before Days</label>
            <input
              v-model.number="newForm.notify_before_days"
              type="number"
              min="0"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            />
          </div>
          <!-- Notes -->
          <div class="space-y-1 md:col-span-2 lg:col-span-3">
            <label class="text-xs font-medium" style="color: var(--text-muted);">Notes</label>
            <textarea
              v-model="newForm.notes"
              rows="3"
              placeholder="Additional notes..."
              class="w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            />
          </div>
        </div>
        <!-- Error -->
        <p v-if="createError" class="text-sm" style="color: #ef4444;">{{ createError }}</p>
        <!-- Actions -->
        <div class="flex items-center justify-end gap-2">
          <Button variant="outline" @click="showNewForm = false" :disabled="isCreating">Cancel</Button>
          <Button variant="primary" @click="createSchedule" :disabled="isCreating || !newForm.title || !newForm.vehicle || !newForm.scheduled_date">
            {{ isCreating ? 'Creating...' : 'Create' }}
          </Button>
        </div>
      </div>
    </Card>

    <!-- Control Bar -->
    <Card>
      <div class="flex flex-col gap-4">
        <!-- Row 1: Search + View Toggle -->
        <div class="flex flex-col sm:flex-row gap-3">
          <div class="relative flex-1">
            <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4" style="color: var(--text-muted);" />
            <input
              v-model="searchQuery"
              type="search"
              placeholder="Search schedules..."
              class="w-full h-10 pl-10 pr-4 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
              @keyup.enter="handleSearch"
            />
          </div>
          <!-- View Toggle -->
          <div class="flex items-center rounded-lg border overflow-hidden" style="border-color: var(--border-color);">
            <button
              v-for="opt in VIEW_OPTIONS"
              :key="opt.id"
              @click="viewMode = opt.id"
              class="flex items-center justify-center p-2 transition-colors"
              :style="{
                backgroundColor: viewMode === opt.id ? 'var(--bg-tertiary)' : 'transparent',
                color: viewMode === opt.id ? 'var(--text-primary)' : 'var(--text-muted)',
              }"
              :title="opt.label"
            >
              <component :is="opt.icon" class="size-4" />
            </button>
          </div>
        </div>

        <!-- Row 2: Date range + Time presets -->
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2">
            <label class="text-xs font-medium" style="color: var(--text-muted);">{{ $t('common.from') }}</label>
            <input
              v-model="dateFrom"
              type="date"
              class="h-8 px-2 rounded border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
              @change="handleFilterChange"
            />
          </div>
          <div class="flex items-center gap-2">
            <label class="text-xs font-medium" style="color: var(--text-muted);">{{ $t('common.to') }}</label>
            <input
              v-model="dateTo"
              type="date"
              class="h-8 px-2 rounded border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
              @change="handleFilterChange"
            />
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-for="preset in TIME_PRESETS"
              :key="preset.label"
              variant="ghost"
              size="sm"
              @click="applyTimePreset(preset.days)"
            >
              {{ preset.label }}
            </Button>
          </div>
        </div>

        <!-- Row 3: Status + Frequency filters -->
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2">
            <label class="text-xs font-medium" style="color: var(--text-muted);">{{ $t('common.status') }}</label>
            <select
              v-model="statusFilter"
              class="h-8 px-2 rounded border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            >
              <option v-for="s in STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <label class="text-xs font-medium" style="color: var(--text-muted);">{{ $t('inspections.frequency') }}</label>
            <select
              v-model="frequencyFilter"
              class="h-8 px-2 rounded border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            >
              <option v-for="f in FREQUENCY_OPTIONS" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
        </div>
      </div>
    </Card>

    <!-- Coming Soon placeholders for non-table views -->
    <Card v-if="viewMode !== 'table'">
      <EmptyState
        :icon="LucideConstruction"
        :title="`${VIEW_OPTIONS.find(v => v.id === viewMode)?.label} View`"
        :description="$t('reports.coming_soon_desc')"
      />
    </Card>

    <!-- Table View -->
    <Card v-else padding="none">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b" style="background-color: var(--bg-tertiary); border-color: var(--border-color);">
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                Schedule ID
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('common.vehicle') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                Form
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                Due Date
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                Recurrence
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('inspections.assigned_to') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('common.status') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                Last Completed
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('inspections.next_due') }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y" style="border-color: var(--border-color);">
            <!-- Loading -->
            <template v-if="isLoading">
              <tr v-for="i in 5" :key="i">
                <td class="px-4 py-4" colspan="9">
                  <Skeleton height="20px" />
                </td>
              </tr>
            </template>

            <!-- Empty -->
            <tr v-else-if="schedules.length === 0">
              <td colspan="9" class="px-4 py-8">
                <EmptyState
                  :icon="LucideCalendarClock"
                  :title="$t('inspections.no_schedules')"
                  :description="$t('inspections.no_schedules_desc')"
                />
              </td>
            </tr>

            <!-- Data -->
            <tr
              v-else
              v-for="schedule in schedules"
              :key="schedule.name"
              class="transition-colors cursor-pointer hover:opacity-80"
              :style="{ backgroundColor: 'var(--bg-secondary)' }"
              @click="router.push(`/inspections/schedules/${schedule.name}`)"
            >
              <td class="px-4 py-4">
                <span class="text-sm font-medium" style="color: var(--text-primary);">
                  {{ schedule.name }}
                </span>
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-primary);">
                {{ schedule.vehicle || '—' }}
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-primary);">
                {{ schedule.form_template || '—' }}
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-muted);">
                {{ formatDate(schedule.scheduled_date) }}
              </td>
              <td class="px-4 py-4">
                <Badge variant="default" size="sm">{{ schedule.frequency }}</Badge>
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-primary);">
                {{ schedule.assigned_to || '—' }}
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center gap-1">
                  <Badge :variant="STATUS_VARIANTS[schedule.status] || 'default'">
                    {{ schedule.status }}
                  </Badge>
                  <Badge v-if="isOverdue(schedule.next_due)" variant="danger" size="sm">
                    Overdue
                  </Badge>
                </div>
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-muted);">
                {{ formatDate(schedule.last_completed) }}
              </td>
              <td class="px-4 py-4 text-sm" :style="{ color: isOverdue(schedule.next_due) ? '#ef4444' : 'var(--text-muted)' }">
                {{ formatDate(schedule.next_due) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div
        v-if="!isLoading && schedules.length > 0"
        class="flex items-center justify-between px-4 py-3 border-t"
        style="border-color: var(--border-color);"
      >
        <p class="text-sm" style="color: var(--text-muted);">
          {{ $t('common.showing') }} {{ (pagination.page - 1) * pagination.pageSize + 1 }}
          to {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }}
          {{ $t('common.of') }} {{ pagination.total }}
        </p>
        <div class="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            :disabled="pagination.page === 1"
            @click="handlePageChange(pagination.page - 1)"
          >
            {{ $t('common.previous') }}
          </Button>
          <Button
            variant="outline"
            size="sm"
            :disabled="pagination.page >= totalPages"
            @click="handlePageChange(pagination.page + 1)"
          >
            {{ $t('common.next') }}
          </Button>
        </div>
      </div>
    </Card>
  </div>
</template>
