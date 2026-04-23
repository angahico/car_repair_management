<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import {
  LucideArrowLeft,
  LucideCalendarClock,
  LucideSearch,
  LucidePlus,
  LucideTrash2,
  LucidePlay,
  LucideX,
} from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, ConfirmModal } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface ScheduledReport {
  name: string
  title: string
  report_id: string
  report_title: string
  frequency: string
  delivery_method: string
  export_format: string
  recipients: string
  enabled: boolean
  last_sent: string | null
  next_run: string | null
  last_status: string | null
  delivery_time: string | null
  owner: string
  creation: string
  modified: string
}

interface ScheduledReportsResponse {
  reports: ScheduledReport[]
  total: number
}

const STANDARD_REPORT_OPTIONS = [
  { id: 'fleet_health_score', title: 'Fleet Health Score' },
  { id: 'age_distribution', title: 'Age Distribution' },
  { id: 'utilization_overview', title: 'Utilization Overview' },
  { id: 'downtime_summary', title: 'Downtime Summary' },
  { id: 'mileage_by_vehicle', title: 'Mileage by Vehicle' },
  { id: 'low_use_vehicles', title: 'Low-Use Vehicles' },
  { id: 'fuel_vs_mileage', title: 'Fuel vs Mileage Efficiency' },
  { id: 'wo_volume_trend', title: 'Work Order Volume Trend' },
  { id: 'wo_avg_resolution', title: 'Average Resolution Time' },
  { id: 'wo_backlog_status', title: 'Backlog by Status' },
  { id: 'wo_cost_variance', title: 'Cost vs Estimate Variance' },
  { id: 'wo_rework_rate', title: 'Repeat Repairs / Rework' },
  { id: 'low_stock_items', title: 'Low Stock / Out of Stock' },
  { id: 'fast_moving_items', title: 'Fast-Moving Items' },
  { id: 'wo_consumption', title: 'Work Order Consumption' },
  { id: 'inspection_pass_fail', title: 'Pass/Fail Trends' },
  { id: 'overdue_schedules', title: 'Overdue Schedules' },
  { id: 'failure_hotspots', title: 'Failure Hotspots' },
  { id: 'inspector_productivity', title: 'Inspector Productivity' },
  { id: 'issues_new_vs_resolved', title: 'New vs Resolved Trend' },
  { id: 'issues_mttr', title: 'Mean Time to Resolve' },
  { id: 'top_fault_codes', title: 'Top Fault Codes' },
  { id: 'high_severity_open', title: 'High Severity Open Issues' },
  { id: 'expenses_by_category', title: 'Expenses by Category' },
  { id: 'cost_per_vehicle', title: 'Cost per Vehicle' },
  { id: 'cost_per_km', title: 'Cost per KM' },
  { id: 'invoice_aging', title: 'Invoice Aging' },
  { id: 'top_customers_revenue', title: 'Top Customers by Revenue' },
  { id: 'customer_outstanding', title: 'Outstanding Balance' },
  { id: 'employee_wo_completed', title: 'Work Orders Completed' },
  { id: 'employee_avg_completion', title: 'Avg Completion Time' },
  { id: 'employee_workload', title: 'Workload Distribution' },
]

const FREQUENCY_OPTIONS = ['Daily', 'Weekly', 'Monthly']
const DELIVERY_METHOD_OPTIONS = ['Email', 'In-App', 'Download Link']
const EXPORT_FORMAT_OPTIONS = ['CSV', 'PDF', 'Excel']

const isLoading = ref(true)
const reports = ref<ScheduledReport[]>([])
const total = ref(0)
const search = ref('')
const showCreateModal = ref(false)
const isCreating = ref(false)
const deletingName = ref<string | null>(null)
const runningName = ref<string | null>(null)
const togglingName = ref<string | null>(null)
const showDeleteConfirm = ref(false)
const deleteTarget = ref<ScheduledReport | null>(null)
const deleteLoading = ref(false)

const { t } = useI18n()

const form = ref({
  title: '',
  report_id: '',
  frequency: 'Daily',
  delivery_method: 'Email',
  export_format: 'PDF',
  recipients: '',
  delivery_time: '08:00',
})

let searchTimeout: ReturnType<typeof setTimeout> | null = null

function formatDate(value: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatDateTime(value: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function truncate(text: string, max: number): string {
  if (!text) return '—'
  return text.length > max ? text.slice(0, max) + '…' : text
}

function frequencyVariant(freq: string): StatusVariant {
  if (freq === 'Daily') return 'info'
  if (freq === 'Weekly') return 'primary'
  if (freq === 'Monthly') return 'warning'
  return 'default'
}

function statusVariant(status: string | null): StatusVariant {
  if (!status) return 'default'
  if (status === 'Sent' || status === 'Success') return 'success'
  if (status === 'Failed' || status === 'Error') return 'danger'
  if (status === 'Pending') return 'warning'
  return 'default'
}

async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: 0,
      limit_page_length: 100,
    }
    if (search.value) args.search = search.value

    const data = await apiCall<ScheduledReportsResponse>(
      'car_repair_management.api.reports.get_scheduled_reports',
      args,
    )
    reports.value = data.reports
    total.value = data.total
  } catch (e) {
    console.warn('Failed to load scheduled reports', e)
  } finally {
    isLoading.value = false
  }
}

async function toggleEnabled(report: ScheduledReport) {
  togglingName.value = report.name
  try {
    await apiCall('car_repair_management.api.reports.toggle_report_schedule', {
      name: report.name,
      enabled: !report.enabled,
    })
    report.enabled = !report.enabled
  } catch (e) {
    console.warn('Failed to toggle schedule', e)
  } finally {
    togglingName.value = null
  }
}

function promptDeleteSchedule(report: ScheduledReport) {
  deleteTarget.value = report
  showDeleteConfirm.value = true
}

async function deleteSchedule(reason: string) {
  if (!deleteTarget.value) return
  deleteLoading.value = true
  try {
    await apiCall('car_repair_management.api.reports.delete_report_schedule', {
      name: deleteTarget.value.name,
    })
    reports.value = reports.value.filter((r) => r.name !== deleteTarget.value!.name)
    total.value = Math.max(0, total.value - 1)
    showDeleteConfirm.value = false
    deleteTarget.value = null
  } catch (e) {
    console.warn('Failed to delete schedule', e)
  } finally {
    deleteLoading.value = false
  }
}

async function runNow(report: ScheduledReport) {
  runningName.value = report.name
  try {
    const res = await apiCall<{ success: boolean; status?: string; last_sent?: string }>(
      'car_repair_management.api.reports.run_report_now',
      { name: report.name },
    )
    if (res.success) {
      report.last_status = res.status || 'Sent'
      report.last_sent = res.last_sent || null
    }
    await loadData()
  } catch (e) {
    console.warn('Failed to run report', e)
  } finally {
    runningName.value = null
  }
}

function resetForm() {
  form.value = {
    title: '',
    report_id: '',
    frequency: 'Daily',
    delivery_method: 'Email',
    export_format: 'PDF',
    recipients: '',
    delivery_time: '08:00',
  }
}

function openCreateModal() {
  resetForm()
  showCreateModal.value = true
}

async function createSchedule() {
  if (!form.value.title || !form.value.report_id) return
  isCreating.value = true
  try {
    await apiCall('car_repair_management.api.reports.create_report_schedule', {
      title: form.value.title,
      report_id: form.value.report_id,
      frequency: form.value.frequency,
      delivery_method: form.value.delivery_method,
      export_format: form.value.export_format,
      recipients: form.value.recipients,
      delivery_time: form.value.delivery_time,
    })
    showCreateModal.value = false
    await loadData()
  } catch (e) {
    console.warn('Failed to create schedule', e)
  } finally {
    isCreating.value = false
  }
}

watch(search, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(loadData, 300)
})

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div class="flex items-center gap-3">
        <RouterLink to="/reports">
          <Button variant="ghost" size="sm">
            <LucideArrowLeft class="size-4" />
          </Button>
        </RouterLink>
        <div>
          <h1 class="text-page-title" style="color: var(--text-primary)">{{ $t('reports.scheduled') }}</h1>
          <p class="text-sm mt-1" style="color: var(--text-muted)">
            {{ $t('reports.schedule_delivery') }}
          </p>
        </div>
      </div>
      <Button variant="primary" @click="openCreateModal">
        <LucidePlus class="size-4" />
        New Schedule
      </Button>
    </div>

    <!-- Search -->
    <div class="relative">
      <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4" style="color: var(--text-muted)" />
      <input
        v-model="search"
        type="search"
        placeholder="Search schedules..."
        class="w-full h-10 pl-10 pr-4 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
        style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
      />
    </div>

    <!-- Table -->
    <Card padding="none">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr
              class="border-b"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color)"
            >
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">Schedule Name</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">Report</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">{{ $t('inspections.frequency') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">Recipients</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">Format</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">Delivery Time</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">Last Sent</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">Next Run</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">{{ $t('common.status') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">Enabled</th>
              <th class="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider whitespace-nowrap" style="color: var(--text-muted)">{{ $t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y" style="border-color: var(--border-color)">
            <!-- Loading -->
            <template v-if="isLoading">
              <tr v-for="i in 5" :key="i">
                <td class="px-4 py-4" colspan="11">
                  <Skeleton height="20px" />
                </td>
              </tr>
            </template>

            <!-- Empty -->
            <tr v-else-if="reports.length === 0">
              <td colspan="11" class="px-4 py-8">
                <EmptyState
                  :icon="LucideCalendarClock"
                  title="No Scheduled Reports"
                  description="Automate report delivery via email on daily, weekly, or monthly schedules."
                >
                  <template #action>
                    <Button variant="primary" class="mt-3" @click="openCreateModal">
                      <LucidePlus class="size-4" />
                      Create Schedule
                    </Button>
                  </template>
                </EmptyState>
              </td>
            </tr>

            <!-- Data rows -->
            <tr
              v-else
              v-for="report in reports"
              :key="report.name"
              class="transition-colors"
              style="background-color: var(--bg-secondary)"
            >
              <!-- Schedule Name -->
              <td class="px-4 py-4">
                <span class="text-sm font-medium" style="color: var(--text-primary)">
                  {{ report.title || report.name }}
                </span>
              </td>

              <!-- Report -->
              <td class="px-4 py-4 text-sm" style="color: var(--text-primary)">
                {{ report.report_title || report.report_id || '—' }}
              </td>

              <!-- Frequency -->
              <td class="px-4 py-4">
                <Badge :variant="frequencyVariant(report.frequency)" size="sm">
                  {{ report.frequency }}
                </Badge>
              </td>

              <!-- Recipients -->
              <td class="px-4 py-4 text-sm" style="color: var(--text-muted)">
                {{ truncate(report.recipients, 30) }}
              </td>

              <!-- Format -->
              <td class="px-4 py-4 text-sm" style="color: var(--text-primary)">
                {{ report.export_format || '—' }}
              </td>

              <!-- Delivery Time -->
              <td class="px-4 py-4 text-sm" style="color: var(--text-primary)">
                {{ report.delivery_time || '—' }}
              </td>

              <!-- Last Sent -->
              <td class="px-4 py-4 text-sm whitespace-nowrap" style="color: var(--text-muted)">
                {{ formatDateTime(report.last_sent) }}
              </td>

              <!-- Next Run -->
              <td class="px-4 py-4 text-sm whitespace-nowrap" style="color: var(--text-muted)">
                {{ formatDateTime(report.next_run) }}
              </td>

              <!-- Status -->
              <td class="px-4 py-4">
                <Badge v-if="report.last_status" :variant="statusVariant(report.last_status)" size="sm">
                  {{ report.last_status }}
                </Badge>
                <span v-else class="text-sm" style="color: var(--text-muted)">—</span>
              </td>

              <!-- Enabled toggle -->
              <td class="px-4 py-4">
                <button
                  class="px-2.5 py-1 text-xs font-medium rounded-full transition-colors cursor-pointer border-none"
                  :style="{
                    backgroundColor: report.enabled ? 'var(--accent)' : 'var(--bg-tertiary)',
                    color: report.enabled ? 'var(--accent-text)' : 'var(--text-muted)',
                    opacity: togglingName === report.name ? 0.5 : 1,
                  }"
                  :disabled="togglingName === report.name"
                  @click="toggleEnabled(report)"
                >
                  {{ report.enabled ? 'Active' : 'Paused' }}
                </button>
              </td>

              <!-- Actions -->
              <td class="px-4 py-4 text-right">
                <div class="inline-flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    title="Run Now"
                    :disabled="runningName === report.name"
                    @click="runNow(report)"
                  >
                    <LucidePlay class="size-4" :style="{ color: runningName === report.name ? 'var(--text-muted)' : 'var(--accent)' }" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    title="Delete"
                    :disabled="deletingName === report.name"
                    @click="promptDeleteSchedule(report)"
                  >
                    <LucideTrash2 class="size-4" style="color: var(--text-muted)" />
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Summary -->
      <div
        v-if="!isLoading && reports.length > 0"
        class="flex items-center px-4 py-3 border-t"
        style="border-color: var(--border-color)"
      >
        <p class="text-sm" style="color: var(--text-muted)">
          {{ total }} scheduled report{{ total === 1 ? '' : 's' }}
        </p>
      </div>
    </Card>

    <ConfirmModal
      v-if="showDeleteConfirm"
      :title="$t('reports.delete_schedule')"
      :message="`Delete schedule &quot;${deleteTarget?.title}&quot;? This cannot be undone.`"
      confirm-label="Delete"
      variant="danger"
      :loading="deleteLoading"
      @confirm="deleteSchedule"
      @cancel="showDeleteConfirm = false; deleteTarget = null"
    />

    <!-- Create Modal -->
    <Teleport to="body">
      <div
        v-if="showCreateModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0"
          style="background-color: rgba(0, 0, 0, 0.5)"
          @click="showCreateModal = false"
        />

        <!-- Dialog -->
        <Card class="relative z-10 w-full max-w-lg max-h-[90vh] overflow-y-auto">
          <!-- Modal header -->
          <div class="flex items-center justify-between mb-6">
            <div>
              <h2 class="text-lg font-semibold" style="color: var(--text-primary)">
                New Scheduled Report
              </h2>
              <p class="text-sm mt-1" style="color: var(--text-muted)">
                Configure automated report delivery
              </p>
            </div>
            <Button variant="ghost" size="sm" @click="showCreateModal = false">
              <LucideX class="size-4" />
            </Button>
          </div>

          <form class="space-y-4" @submit.prevent="createSchedule">
            <!-- Title -->
            <div class="space-y-1">
              <label class="block text-sm font-medium" style="color: var(--text-secondary)">
                Schedule Title
              </label>
              <input
                v-model="form.title"
                type="text"
                required
                placeholder="e.g., Weekly Fleet Summary"
                class="w-full h-10 px-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
                style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
              />
            </div>

            <!-- Report -->
            <div class="space-y-1">
              <label class="block text-sm font-medium" style="color: var(--text-secondary)">
                Report
              </label>
              <select
                v-model="form.report_id"
                required
                class="w-full h-10 px-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
                style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
              >
                <option value="" disabled>Select a report…</option>
                <option
                  v-for="opt in STANDARD_REPORT_OPTIONS"
                  :key="opt.id"
                  :value="opt.id"
                >
                  {{ opt.title }}
                </option>
              </select>
            </div>

            <!-- Frequency + Delivery Method row -->
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <label class="block text-sm font-medium" style="color: var(--text-secondary)">
                  Frequency
                </label>
                <select
                  v-model="form.frequency"
                  class="w-full h-10 px-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
                  style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
                >
                  <option v-for="f in FREQUENCY_OPTIONS" :key="f" :value="f">{{ f }}</option>
                </select>
              </div>
              <div class="space-y-1">
                <label class="block text-sm font-medium" style="color: var(--text-secondary)">
                  Delivery Method
                </label>
                <select
                  v-model="form.delivery_method"
                  class="w-full h-10 px-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
                  style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
                >
                  <option v-for="m in DELIVERY_METHOD_OPTIONS" :key="m" :value="m">{{ m }}</option>
                </select>
              </div>
            </div>

            <!-- Export Format + Delivery Time row -->
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <label class="block text-sm font-medium" style="color: var(--text-secondary)">
                  Export Format
                </label>
                <select
                  v-model="form.export_format"
                  class="w-full h-10 px-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
                  style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
                >
                  <option v-for="f in EXPORT_FORMAT_OPTIONS" :key="f" :value="f">{{ f }}</option>
                </select>
              </div>
              <div class="space-y-1">
                <label class="block text-sm font-medium" style="color: var(--text-secondary)">
                  Delivery Time
                </label>
                <input
                  v-model="form.delivery_time"
                  type="time"
                  class="w-full h-10 px-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
                  style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
                />
              </div>
            </div>

            <!-- Recipients -->
            <div class="space-y-1">
              <label class="block text-sm font-medium" style="color: var(--text-secondary)">
                Recipients
              </label>
              <textarea
                v-model="form.recipients"
                rows="3"
                placeholder="Comma-separated emails, e.g., alice@co.com, bob@co.com"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none"
                style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
              />
            </div>

            <!-- Actions -->
            <div class="flex items-center justify-end gap-3 pt-2">
              <Button variant="outline" type="button" @click="showCreateModal = false">
                {{ $t('common.cancel') }}
              </Button>
              <Button
                variant="primary"
                type="submit"
                :disabled="isCreating || !form.title || !form.report_id"
              >
                {{ isCreating ? 'Creating…' : 'Create Schedule' }}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </Teleport>
  </div>
</template>
