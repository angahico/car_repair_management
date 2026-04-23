<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideArrowLeft,
  LucideRefreshCw,
  LucideDownload,
  LucideFileBarChart,
  LucideBookmark,
  LucideStar,
  LucideX,
  LucideCheck,
  LucideShare2,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Chart } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface ReportMeta {
  id: string
  title: string
  category: string
  report_type: string
  description: string
  module: string
}

interface ChartData {
  labels: string[]
  values?: number[]
  pass?: number[]
  fail?: number[]
  new?: number[]
  resolved?: number[]
}

interface ReportResponse {
  report: ReportMeta
  chart_data: ChartData | null
  table_data: Record<string, unknown>[]
  kpis: Record<string, unknown>
  total: number
  date_from: string
  date_to: string
  last_refreshed: string
}

const TYPE_VARIANTS: Record<string, StatusVariant> = {
  Chart: 'info',
  Table: 'default',
  KPI: 'success',
  Pivot: 'warning',
  Dashboard: 'primary',
}

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const reportId = computed(() => route.params.id as string)

// Drilldown route mapping: for each report_id, define which column to use and where to navigate
const DRILLDOWN_MAP: Record<string, { column: string; route: (val: string) => string }> = {
  // Fleet / Vehicles
  utilization_overview: { column: 'vehicle', route: (v) => `/vehicles/${v}` },
  downtime_summary: { column: 'vehicle', route: (v) => `/vehicles/${v}` },
  mileage_by_vehicle: { column: 'vehicle', route: (v) => `/vehicles/${v}` },
  low_use_vehicles: { column: 'vehicle', route: (v) => `/vehicles/${v}` },
  fuel_vs_mileage: { column: 'vehicle', route: (v) => `/vehicles/${v}` },
  cost_per_vehicle: { column: 'vehicle', route: (v) => `/vehicles/${v}` },
  cost_per_km: { column: 'vehicle', route: (v) => `/vehicles/${v}` },
  // Work Orders
  wo_cost_variance: { column: 'name', route: (v) => `/repair-orders/${v}` },
  wo_rework_rate: { column: 'vehicle', route: (v) => `/vehicles/${v}` },
  wo_consumption: { column: 'repair_order', route: (v) => `/repair-orders/${v}` },
  // Parts
  low_stock_items: { column: 'item_code', route: (v) => `/parts/${v}` },
  fast_moving_items: { column: 'item_code', route: (v) => `/parts/${v}` },
  // Inspections
  overdue_schedules: { column: 'name', route: (v) => `/inspections/schedules/${v}` },
  inspector_productivity: { column: 'inspector', route: (v) => `/employees/${v}` },
  // Issues
  high_severity_open: { column: 'name', route: (v) => `/issues/${v}` },
  // Invoices
  invoice_aging: { column: 'name', route: (v) => `/invoices/${v}` },
  // Customers
  top_customers_revenue: { column: 'customer', route: (v) => `/customers/${v}` },
  customer_outstanding: { column: 'customer', route: (v) => `/customers/${v}` },
  // Employees
  employee_wo_completed: { column: 'employee', route: (v) => `/employees/${v}` },
  employee_avg_completion: { column: 'employee', route: (v) => `/employees/${v}` },
  employee_workload: { column: 'employee', route: (v) => `/employees/${v}` },
}

function handleRowClick(row: Record<string, unknown>) {
  const dd = DRILLDOWN_MAP[reportId.value]
  if (!dd) return
  const val = row[dd.column]
  if (val && typeof val === 'string') {
    router.push(dd.route(val))
  }
}

const isClickable = computed(() => !!DRILLDOWN_MAP[reportId.value])

const isLoading = ref(true)
const report = ref<ReportMeta | null>(null)
const chartData = ref<ChartData | null>(null)
const tableData = ref<Record<string, unknown>[]>([])
const kpis = ref<Record<string, unknown>>({})
const lastRefreshed = ref('')

// Date range — default last 30 days
const today = new Date()
const thirtyDaysAgo = new Date(today)
thirtyDaysAgo.setDate(today.getDate() - 30)

function toISODate(d: Date): string {
  return d.toISOString().split('T')[0]
}

const dateFrom = ref(toISODate(thirtyDaysAgo))
const dateTo = ref(toISODate(today))

// Pagination
const page = ref(1)
const rowsPerPage = 50

const tableColumns = computed(() => {
  if (!tableData.value.length) return []
  return Object.keys(tableData.value[0])
})

const paginatedRows = computed(() => {
  const start = (page.value - 1) * rowsPerPage
  return tableData.value.slice(start, start + rowsPerPage)
})

const totalPages = computed(() => Math.ceil(tableData.value.length / rowsPerPage))

// Chart option builder
const chartOption = computed(() => {
  if (!chartData.value) return null
  const cd = chartData.value

  const baseAxis = {
    xAxis: {
      type: 'category' as const,
      data: cd.labels,
      axisLabel: {
        rotate: cd.labels.length > 8 ? 30 : 0,
        overflow: 'truncate' as const,
        width: 80,
      },
    },
    yAxis: { type: 'value' as const },
    tooltip: { trigger: 'axis' as const },
    grid: { left: 60, right: 20, top: 40, bottom: cd.labels.length > 8 ? 60 : 40 },
  }

  // Stacked bar: pass + fail
  if (cd.pass && cd.fail) {
    return {
      ...baseAxis,
      legend: { data: ['Pass', 'Fail'] },
      series: [
        {
          name: 'Pass',
          type: 'bar',
          stack: 'total',
          data: cd.pass,
          itemStyle: { color: '#525252' },
        },
        {
          name: 'Fail',
          type: 'bar',
          stack: 'total',
          data: cd.fail,
          itemStyle: { color: '#d4d4d4' },
        },
      ],
    }
  }

  // Line chart: new + resolved
  if (cd.new && cd.resolved) {
    return {
      ...baseAxis,
      legend: { data: ['New', 'Resolved'] },
      series: [
        {
          name: 'New',
          type: 'line',
          data: cd.new,
          smooth: true,
          itemStyle: { color: '#525252' },
        },
        {
          name: 'Resolved',
          type: 'line',
          data: cd.resolved,
          smooth: true,
          itemStyle: { color: '#737373' },
        },
      ],
    }
  }

  // Default bar chart: labels + values
  if (cd.values) {
    const barColors = ['#525252', '#737373', '#a3a3a3', '#d4d4d4']
    return {
      ...baseAxis,
      series: [
        {
          type: 'bar',
          data: cd.values.map((v, i) => ({
            value: v,
            itemStyle: { color: barColors[i % barColors.length] },
          })),
        },
      ],
    }
  }

  return null
})

function parseDateStr(dateStr: string): string {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  if (parts.length < 3) return dateStr
  const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
  return d.toLocaleDateString()
}

function formatLastRefreshed(dt: string): string {
  if (!dt) return ''
  try {
    return new Date(dt).toLocaleString()
  } catch {
    return dt
  }
}

function formatCellValue(val: unknown): string {
  if (val === null || val === undefined) return '—'
  if (typeof val === 'number') return val.toLocaleString()
  return String(val)
}

function formatKpiValue(val: unknown): string {
  if (val === null || val === undefined) return '—'
  if (typeof val === 'number') return val.toLocaleString()
  return String(val)
}

function formatColumnHeader(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

// Data fetching
async function loadReport() {
  isLoading.value = true
  try {
    const data = await apiCall<ReportResponse>(
      'car_repair_management.api.reports.get_report_data',
      {
        report_id: reportId.value,
        date_from: dateFrom.value,
        date_to: dateTo.value,
      },
    )
    report.value = data.report
    chartData.value = data.chart_data
    tableData.value = data.table_data || []
    kpis.value = data.kpis || {}
    lastRefreshed.value = data.last_refreshed || ''
    page.value = 1
  } catch (e) {
    console.warn('Failed to load report data', e)
  } finally {
    isLoading.value = false
  }
}

function onDateChange() {
  loadReport()
}

// CSV Export
function exportCsv() {
  if (!tableData.value.length) return
  const cols = tableColumns.value
  const header = cols.map((c) => `"${formatColumnHeader(c)}"`).join(',')
  const rows = tableData.value.map((row) =>
    cols
      .map((c) => {
        const v = row[c]
        if (v === null || v === undefined) return ''
        const s = String(v).replace(/"/g, '""')
        return `"${s}"`
      })
      .join(','),
  )
  const csv = [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${report.value?.title || 'report'}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// Pin/Favorite
const isPinned = ref(false)
const pinLoading = ref(false)

async function loadPinStatus() {
  try {
    const res = await apiCall<{ pinned_ids: string[] }>('car_repair_management.api.reports.get_pinned_reports')
    isPinned.value = res.pinned_ids.includes(reportId.value)
  } catch {
    // ignore
  }
}

async function togglePin() {
  pinLoading.value = true
  try {
    const res = await apiCall<{ is_pinned: boolean }>('car_repair_management.api.reports.toggle_pin_report', { report_id: reportId.value })
    isPinned.value = res.is_pinned
  } catch {
    // ignore
  } finally {
    pinLoading.value = false
  }
}

// Save Report Dialog
const showSaveDialog = ref(false)
const saveTitle = ref('')
const saveDescription = ref('')
const saveLoading = ref(false)
const saveMessage = ref('')
const shareMessage = ref('')

function handleShare() {
  const url = `${window.location.origin}/workshop/reports/view/${reportId.value}`
  navigator.clipboard.writeText(url).then(() => {
    shareMessage.value = 'Report link copied to clipboard!'
    setTimeout(() => { shareMessage.value = '' }, 3000)
  }).catch(() => {
    shareMessage.value = 'Failed to copy link'
    setTimeout(() => { shareMessage.value = '' }, 3000)
  })
}

async function handleSaveReport() {
  if (!saveTitle.value.trim()) return
  saveLoading.value = true
  try {
    await apiCall('car_repair_management.api.reports.save_report', {
      title: saveTitle.value,
      report_id: reportId.value,
      date_from: dateFrom.value,
      date_to: dateTo.value,
      description: saveDescription.value,
      filters_json: '{}',
    })
    saveMessage.value = 'Report saved successfully'
    showSaveDialog.value = false
    saveTitle.value = ''
    saveDescription.value = ''
    setTimeout(() => { saveMessage.value = '' }, 3000)
  } catch {
    saveMessage.value = 'Failed to save report'
    setTimeout(() => { saveMessage.value = '' }, 3000)
  } finally {
    saveLoading.value = false
  }
}

onMounted(() => {
  loadReport()
  loadPinStatus()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Top Bar -->
    <div class="flex flex-wrap items-center gap-3">
      <RouterLink to="/reports/library">
        <Button variant="ghost" size="sm">
          <LucideArrowLeft class="size-4" />
        </Button>
      </RouterLink>

      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
          <h1 v-if="report" class="text-page-title truncate" style="color: var(--text-primary)">
            {{ report.title }}
          </h1>
          <Skeleton v-else width="200px" height="28px" />
          <Badge
            v-if="report"
            :variant="TYPE_VARIANTS[report.report_type] || 'default'"
            size="sm"
          >
            {{ report.report_type }}
          </Badge>
        </div>
        <p v-if="report" class="text-sm mt-0.5" style="color: var(--text-muted)">
          {{ report.description }}
        </p>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <div class="flex items-center gap-1.5">
          <label class="text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">{{ $t('common.from') }}</label>
          <input
            v-model="dateFrom"
            type="date"
            class="h-9 px-2.5 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @change="onDateChange"
          />
        </div>
        <div class="flex items-center gap-1.5">
          <label class="text-xs font-medium whitespace-nowrap" style="color: var(--text-muted)">{{ $t('common.to') }}</label>
          <input
            v-model="dateTo"
            type="date"
            class="h-9 px-2.5 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @change="onDateChange"
          />
        </div>

        <Button variant="outline" size="sm" :loading="isLoading" @click="loadReport">
          <LucideRefreshCw class="size-4" />
          {{ $t('common.refresh') }}
        </Button>

        <Button variant="outline" size="sm" :loading="pinLoading" @click="togglePin">
          <LucideStar class="size-4" :style="isPinned ? { color: 'var(--accent)', fill: 'var(--accent)' } : {}" />
          {{ isPinned ? 'Pinned' : 'Pin' }}
        </Button>

        <Button variant="outline" size="sm" @click="showSaveDialog = true">
          <LucideBookmark class="size-4" />
          {{ $t('common.save') }}
        </Button>

        <Button variant="outline" size="sm" @click="handleShare">
          <LucideShare2 class="size-4" />
          Share
        </Button>

        <Button
          variant="secondary"
          size="sm"
          :disabled="!tableData.length"
          @click="exportCsv"
        >
          <LucideDownload class="size-4" />
          {{ $t('common.export_csv') }}
        </Button>
      </div>
    </div>

    <!-- Save Message -->
    <div
      v-if="saveMessage || shareMessage"
      class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm"
      style="background-color: var(--bg-tertiary); color: var(--text-secondary);"
    >
      <LucideCheck class="size-4" />
      {{ saveMessage || shareMessage }}
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="space-y-4">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card v-for="i in 4" :key="i">
          <Skeleton height="14px" width="50%" />
          <Skeleton height="24px" width="70%" class="mt-2" />
        </Card>
      </div>
      <Card>
        <Skeleton height="350px" />
      </Card>
      <Card padding="none">
        <div class="p-4 space-y-3">
          <Skeleton v-for="i in 6" :key="i" height="40px" />
        </div>
      </Card>
    </div>

    <template v-else-if="report">
      <!-- KPI Cards -->
      <div v-if="kpis && Object.keys(kpis).length" class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card v-for="(value, key) in kpis" :key="String(key)">
          <p class="text-xs font-medium truncate" style="color: var(--text-muted)">
            {{ formatColumnHeader(String(key)) }}
          </p>
          <p class="text-xl font-bold mt-1" style="color: var(--text-primary)">
            {{ formatKpiValue(value) }}
          </p>
        </Card>
      </div>

      <!-- Chart Section -->
      <Card v-if="chartOption">
        <Chart :option="chartOption" height="350px" />
      </Card>

      <!-- Table Section -->
      <Card v-if="tableData.length" padding="none">
        <div class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th
                  v-for="col in tableColumns"
                  :key="col"
                  class="text-left px-4 py-3 text-xs font-medium whitespace-nowrap"
                  style="color: var(--text-muted)"
                >
                  {{ formatColumnHeader(col) }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, idx) in paginatedRows"
                :key="idx"
                class="border-b transition-colors"
                :class="{ 'cursor-pointer': isClickable }"
                :style="`border-color: var(--border-subtle)`"
                @click="handleRowClick(row)"
                @mouseenter="isClickable && (($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)')"
                @mouseleave="isClickable && (($event.currentTarget as HTMLElement).style.backgroundColor = '')"
              >
                <td
                  v-for="col in tableColumns"
                  :key="col"
                  class="px-4 py-3 whitespace-nowrap"
                >
                  {{ formatCellValue(row[col]) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="flex items-center justify-between px-4 py-3 border-t" style="border-color: var(--border-subtle)">
          <p class="text-xs" style="color: var(--text-muted)">
            {{ $t('common.showing') }} {{ (page - 1) * rowsPerPage + 1 }}–{{ Math.min(page * rowsPerPage, tableData.length) }}
            {{ $t('common.of') }} {{ tableData.length.toLocaleString() }} rows
          </p>
          <div class="flex items-center gap-1">
            <Button variant="ghost" size="sm" :disabled="page <= 1" @click="page--">
              {{ $t('common.previous') }}
            </Button>
            <span class="text-xs px-2" style="color: var(--text-muted)">{{ page }} / {{ totalPages }}</span>
            <Button variant="ghost" size="sm" :disabled="page >= totalPages" @click="page++">
              {{ $t('common.next') }}
            </Button>
          </div>
        </div>
      </Card>

      <!-- Empty state if nothing at all -->
      <EmptyState
        v-if="!Object.keys(kpis).length && !chartOption && !tableData.length"
        :icon="LucideFileBarChart"
        :title="$t('reports.no_data')"
        description="Try adjusting the date range or check back later."
      />

      <!-- Last Refreshed -->
      <p v-if="lastRefreshed" class="text-xs text-right" style="color: var(--text-muted)">
        Last refreshed: {{ formatLastRefreshed(lastRefreshed) }}
      </p>
    </template>

    <!-- Save Report Dialog -->
    <Teleport to="body">
      <div v-if="showSaveDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background: rgba(0,0,0,0.4);" @click.self="showSaveDialog = false">
        <Card class="w-full max-w-md">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-semibold" style="color: var(--text-primary);">{{ $t('reports.report_view') }}</h3>
            <button @click="showSaveDialog = false" class="p-1 rounded" style="color: var(--text-muted);">
              <LucideX class="size-4" />
            </button>
          </div>
          <div class="space-y-4">
            <div>
              <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">Title</label>
              <input
                v-model="saveTitle"
                type="text"
                :placeholder="`My ${report?.title || 'Report'}`"
                class="w-full h-10 px-3 text-sm rounded border"
                style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
              />
            </div>
            <div>
              <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">Description (optional)</label>
              <textarea
                v-model="saveDescription"
                rows="2"
                class="w-full px-3 py-2 text-sm rounded border resize-none"
                style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
              />
            </div>
            <div class="text-xs" style="color: var(--text-muted);">
              Saves current date range: {{ dateFrom }} — {{ dateTo }}
            </div>
            <div class="flex justify-end gap-2">
              <Button variant="ghost" size="sm" @click="showSaveDialog = false">{{ $t('common.cancel') }}</Button>
              <Button variant="primary" size="sm" :loading="saveLoading" :disabled="!saveTitle.trim()" @click="handleSaveReport">
                <LucideBookmark class="size-4" />
                Save
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </Teleport>
  </div>
</template>
