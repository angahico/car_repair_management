<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  LucideDollarSign,
  LucideFuel,
  LucideWrench,
  LucideShield,
  LucideRefreshCw,
  LucideDownload,
  LucideTrendingUp,
  LucideAlertTriangle,
  LucideBarChart3,
  LucideActivity,
  LucideReceipt,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Chart, Tabs } from '@/components/ui'
import type { EChartsOption } from 'echarts'

// --- Types ---
interface KPIs {
  total_expenses: number
  fuel_spend: number
  maintenance_spend: number
  insurance_spend: number
  avg_per_vehicle: number
  cost_per_km: number
  most_expensive: { vehicle: string; amount: number }
}

interface CategoryBreakdown { category: string; amount: number }
interface VehicleBreakdown { vehicle: string; amount: number }
interface MonthBreakdown { month: string; fuel: number; maintenance: number; other: number }

interface ExpenseRecord {
  name: string
  date: string | null
  vehicle: string
  category: string
  amount: number
  vendor: string | null
  linked_work_order: string | null
  entered_by: string
  has_receipt: boolean
  approval_status: string
}

interface FuelCostPerKm { vehicle: string; cost_per_km: number }
interface MaintenanceTrend { month: string; cost: number }
interface Anomaly { vehicle: string; type: string; description: string }

interface ExpenseData {
  kpis: KPIs
  breakdown: {
    by_category: CategoryBreakdown[]
    by_vehicle: VehicleBreakdown[]
    by_month: MonthBreakdown[]
  }
  records: ExpenseRecord[]
  efficiency: {
    fuel_cost_per_km: FuelCostPerKm[]
    maintenance_trend: MaintenanceTrend[]
    budget_warnings: unknown[]
    anomalies: Anomaly[]
  }
}

const { t } = useI18n()

// --- State ---
const isLoading = ref(true)
const data = ref<ExpenseData | null>(null)
const dateFrom = ref('')
const dateTo = ref('')
const selectedCategory = ref<string | null>(null)
const chartTab = ref('by_category')

const chartTabs = computed(() => [
  { id: 'by_category', label: t('expense_history.by_category') },
  { id: 'by_vehicle', label: t('expense_history.by_vehicle') },
  { id: 'by_month', label: t('expense_history.by_month') },
])

// --- Helpers ---
function fmt(v: number): string {
  return v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function setPreset(days: number) {
  const now = new Date()
  const from = new Date(now.getFullYear(), now.getMonth(), now.getDate() - days)
  dateTo.value = formatDate(now)
  dateFrom.value = formatDate(from)
  loadData()
}

// --- Load ---
async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {}
    if (dateFrom.value) args.date_from = dateFrom.value
    if (dateTo.value) args.date_to = dateTo.value
    if (selectedCategory.value) args.category = selectedCategory.value
    const result = await apiCall<ExpenseData>(
      'car_repair_management.api.expense_history.get_expense_history',
      args,
    )
    data.value = result
  } catch (e) {
    console.warn('Failed to load expense history', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => setPreset(90))

// --- Chart Options ---
const CHART_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

const categoryChartOption = computed<EChartsOption>(() => {
  const cats = data.value?.breakdown.by_category || []
  if (!cats.length) return {}
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, type: 'scroll' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
      data: cats.map((c, i) => ({ name: c.category, value: c.amount, itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] } })),
      label: { formatter: '{b}\n{d}%' },
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } },
    }],
  }
})

const vehicleChartOption = computed<EChartsOption>(() => {
  const vehs = (data.value?.breakdown.by_vehicle || []).slice(0, 15)
  if (!vehs.length) return {}
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 120, right: 30, top: 20, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { formatter: (v: number) => v.toLocaleString() } },
    yAxis: { type: 'category', data: vehs.map((v) => v.vehicle), inverse: true },
    series: [{
      type: 'bar',
      data: vehs.map((v, i) => ({ value: v.amount, itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] } })),
      barMaxWidth: 24,
    }],
  }
})

const monthChartOption = computed<EChartsOption>(() => {
  const months = data.value?.breakdown.by_month || []
  if (!months.length) return {}
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['Fuel', 'Maintenance', 'Other'], bottom: 0 },
    grid: { left: 60, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: months.map((m) => m.month), axisLabel: { rotate: 45 } },
    yAxis: { type: 'value', axisLabel: { formatter: (v: number) => v.toLocaleString() } },
    series: [
      { name: 'Fuel', type: 'bar', stack: 'total', data: months.map((m) => m.fuel), itemStyle: { color: '#3b82f6' } },
      { name: 'Maintenance', type: 'bar', stack: 'total', data: months.map((m) => m.maintenance), itemStyle: { color: '#f59e0b' } },
      { name: 'Other', type: 'bar', stack: 'total', data: months.map((m) => m.other), itemStyle: { color: '#10b981' } },
    ],
  }
})

const activeChartOption = computed(() => {
  if (chartTab.value === 'by_vehicle') return vehicleChartOption.value
  if (chartTab.value === 'by_month') return monthChartOption.value
  return categoryChartOption.value
})

const maintenanceTrendOption = computed<EChartsOption>(() => {
  const trend = data.value?.efficiency.maintenance_trend || []
  if (!trend.length) return {}
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 10, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: trend.map((t) => t.month), axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', axisLabel: { formatter: (v: number) => v.toLocaleString(), fontSize: 10 } },
    series: [{ type: 'line', data: trend.map((t) => t.cost), smooth: true, areaStyle: { opacity: 0.1 }, itemStyle: { color: '#f59e0b' } }],
  }
})

// --- Export ---
function exportCSV() {
  if (!data.value?.records.length) return
  const headers = [t('common.date'), t('common.vehicle'), t('expenses.category'), t('common.amount'), t('expenses.vendor'), t('expenses.work_order'), t('expenses.entered_by')]
  const rows = data.value.records.map((r) => [
    r.date || '', r.vehicle, r.category, r.amount, r.vendor || '', r.linked_work_order || '', r.entered_by,
  ])
  const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `expense_history_${formatDate(new Date())}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div>
        <h1 class="text-page-title">{{ $t('expense_history.title') }}</h1>
        <p class="text-sm text-ink-muted mt-1">{{ $t('expense_history.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="exportCSV"><LucideDownload class="size-4" /></Button>
        <Button variant="outline" @click="loadData">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
      </div>
    </div>

    <!-- Control Bar -->
    <Card>
      <div class="flex flex-wrap items-end gap-4">
        <div>
          <label class="text-label block mb-1">{{ $t('common.from') }}</label>
          <input v-model="dateFrom" type="date" class="rounded-lg border px-3 py-2 text-sm bg-surface-bg text-ink border-default" />
        </div>
        <div>
          <label class="text-label block mb-1">{{ $t('common.to') }}</label>
          <input v-model="dateTo" type="date" class="rounded-lg border px-3 py-2 text-sm bg-surface-bg text-ink border-default" />
        </div>
        <div class="flex items-center gap-1">
          <button
            v-for="preset in [{ label: '7D', days: 7 }, { label: '30D', days: 30 }, { label: '90D', days: 90 }, { label: '1Y', days: 365 }]"
            :key="preset.days"
            class="px-3 py-2 text-xs font-medium rounded-lg border transition-colors"
            :style="{ borderColor: 'var(--border-color)', color: 'var(--text-secondary)', backgroundColor: 'var(--bg-tertiary)' }"
            @click="setPreset(preset.days)"
          >{{ preset.label }}</button>
        </div>
        <div class="flex items-center gap-1">
          <button
            v-for="cat in [{ id: null, label: $t('common.all') }, { id: 'Fuel', label: $t('expense_history.fuel_spend') }, { id: 'Maintenance', label: $t('expense_history.maintenance_spend') }]"
            :key="cat.label"
            class="px-3 py-2 text-xs font-medium rounded-lg border transition-colors"
            :style="{
              borderColor: selectedCategory === cat.id ? 'var(--accent)' : 'var(--border-color)',
              color: selectedCategory === cat.id ? 'var(--accent-text)' : 'var(--text-secondary)',
              backgroundColor: selectedCategory === cat.id ? 'var(--accent)' : 'transparent',
            }"
            @click="selectedCategory = cat.id; loadData()"
          >{{ cat.label }}</button>
        </div>
        <Button variant="primary" @click="loadData">{{ $t('common.apply') }}</Button>
      </div>
    </Card>

    <!-- KPI Cards -->
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <Card v-for="i in 7" :key="i"><Skeleton height="80px" /></Card>
    </div>
    <div v-else-if="data" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center shrink-0">
            <LucideDollarSign class="size-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <p class="text-label">{{ $t('expense_history.total_fleet_expenses') }}</p>
            <p class="text-2xl font-semibold text-ink">{{ fmt(data.kpis.total_expenses) }}</p>
          </div>
        </div>
      </Card>
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-cyan-100 dark:bg-cyan-500/20 flex items-center justify-center shrink-0">
            <LucideFuel class="size-5 text-cyan-600 dark:text-cyan-400" />
          </div>
          <div>
            <p class="text-label">{{ $t('expense_history.fuel_spend') }}</p>
            <p class="text-2xl font-semibold text-ink">{{ fmt(data.kpis.fuel_spend) }}</p>
          </div>
        </div>
      </Card>
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center shrink-0">
            <LucideWrench class="size-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <p class="text-label">{{ $t('expense_history.maintenance_spend') }}</p>
            <p class="text-2xl font-semibold text-ink">{{ fmt(data.kpis.maintenance_spend) }}</p>
          </div>
        </div>
      </Card>
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-500/20 flex items-center justify-center shrink-0">
            <LucideShield class="size-5 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <p class="text-label">{{ $t('expense_history.insurance_spend') }}</p>
            <p class="text-2xl font-semibold text-ink">{{ fmt(data.kpis.insurance_spend) }}</p>
          </div>
        </div>
      </Card>
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-500/20 flex items-center justify-center shrink-0">
            <LucideActivity class="size-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <p class="text-label">{{ $t('expense_history.avg_expense_vehicle') }}</p>
            <p class="text-2xl font-semibold text-ink">{{ fmt(data.kpis.avg_per_vehicle) }}</p>
          </div>
        </div>
      </Card>
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-rose-100 dark:bg-rose-500/20 flex items-center justify-center shrink-0">
            <LucideTrendingUp class="size-5 text-rose-600 dark:text-rose-400" />
          </div>
          <div>
            <p class="text-label">{{ $t('expense_history.cost_per_km') }}</p>
            <p class="text-2xl font-semibold text-ink">{{ fmt(data.kpis.cost_per_km) }}</p>
          </div>
        </div>
      </Card>
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg bg-red-100 dark:bg-red-500/20 flex items-center justify-center shrink-0">
            <LucideBarChart3 class="size-5 text-red-600 dark:text-red-400" />
          </div>
          <div>
            <p class="text-label">{{ $t('expense_history.most_expensive_vehicle') }}</p>
            <p class="text-2xl font-semibold text-ink">{{ fmt(data.kpis.most_expensive.amount) }}</p>
            <p class="text-xs text-ink-muted">{{ data.kpis.most_expensive.vehicle }}</p>
          </div>
        </div>
      </Card>
    </div>

    <!-- Breakdown Charts -->
    <Card v-if="!isLoading && data">
      <div class="mb-4">
        <h2 class="text-section-title mb-3">{{ $t('expense_history.expense_breakdown') }}</h2>
        <Tabs :tabs="chartTabs" v-model="chartTab" />
      </div>
      <Chart :option="activeChartOption" height="350px" />
    </Card>

    <!-- Records Table -->
    <Card v-if="!isLoading && data" padding="none">
      <div class="p-4 border-b border-default">
        <h2 class="text-section-title">{{ $t('expense_history.expense_records') }}</h2>
        <p class="text-xs text-ink-muted mt-1">{{ $t('expense_history.records_count', { count: data.records.length }) }}</p>
      </div>

      <EmptyState
        v-if="data.records.length === 0"
        :icon="LucideReceipt"
        :title="$t('expense_history.no_expense_records')"
        :description="$t('expense_history.no_expenses_period')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-default">
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('common.date') }}</th>
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('common.vehicle') }}</th>
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('expenses.category') }}</th>
              <th class="text-right text-label px-4 py-3 font-medium">{{ $t('common.amount') }}</th>
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('expenses.vendor') }}</th>
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('expenses.work_order') }}</th>
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('expenses.entered_by') }}</th>
              <th class="text-center text-label px-4 py-3 font-medium">{{ $t('expenses.receipt') }}</th>
              <th class="text-left text-label px-4 py-3 font-medium">{{ $t('common.status') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="record in data.records"
              :key="record.name"
              class="border-b border-default hover:bg-surface-secondary transition-colors"
            >
              <td class="px-4 py-3 text-ink">{{ record.date || '—' }}</td>
              <td class="px-4 py-3 text-ink font-medium">{{ record.vehicle }}</td>
              <td class="px-4 py-3">
                <Badge :variant="record.category === 'Fuel' ? 'info' : 'warning'" size="sm">{{ record.category }}</Badge>
              </td>
              <td class="px-4 py-3 text-ink text-right font-medium">{{ fmt(record.amount) }}</td>
              <td class="px-4 py-3 text-ink-muted">{{ record.vendor || '—' }}</td>
              <td class="px-4 py-3 text-ink-muted">{{ record.linked_work_order || '—' }}</td>
              <td class="px-4 py-3 text-ink-muted">{{ record.entered_by }}</td>
              <td class="px-4 py-3 text-center">
                <LucideReceipt v-if="record.has_receipt" class="size-4 text-green-500 inline" />
                <span v-else class="text-ink-muted">—</span>
              </td>
              <td class="px-4 py-3">
                <Badge variant="success" size="sm">{{ record.approval_status }}</Badge>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Efficiency Panel -->
    <Card v-if="!isLoading && data">
      <div class="flex items-center gap-2 mb-4">
        <LucideActivity class="size-5 text-ink-muted" />
        <h2 class="text-section-title">{{ $t('expense_history.efficiency_insights') }}</h2>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Fuel Cost per KM -->
        <div>
          <p class="text-label mb-3">{{ $t('expense_history.fuel_cost_per_km_vehicle') }}</p>
          <div v-if="data.efficiency.fuel_cost_per_km.length === 0" class="text-sm text-ink-muted">{{ $t('expense_history.no_fuel_data') }}</div>
          <div v-else class="space-y-2">
            <div
              v-for="item in data.efficiency.fuel_cost_per_km.slice(0, 10)"
              :key="item.vehicle"
              class="flex items-center gap-3"
            >
              <span class="text-sm text-ink w-32 truncate shrink-0">{{ item.vehicle }}</span>
              <div class="flex-1 h-5 rounded-full overflow-hidden" style="background-color: var(--bg-tertiary);">
                <div
                  class="h-full rounded-full bg-blue-500"
                  :style="{
                    width: Math.min(100, (item.cost_per_km / Math.max(...data.efficiency.fuel_cost_per_km.map((f: FuelCostPerKm) => f.cost_per_km), 1)) * 100) + '%',
                  }"
                />
              </div>
              <span class="text-sm font-medium text-ink w-16 text-right shrink-0">{{ fmt(item.cost_per_km) }}</span>
            </div>
          </div>
        </div>

        <!-- Maintenance Trend -->
        <div>
          <p class="text-label mb-3">{{ $t('expense_history.maintenance_cost_trend') }}</p>
          <Chart
            v-if="data.efficiency.maintenance_trend.length > 0"
            :option="maintenanceTrendOption"
            height="200px"
          />
          <p v-else class="text-sm text-ink-muted">{{ $t('expense_history.no_maintenance_trend') }}</p>
        </div>
      </div>

      <!-- Anomalies -->
      <div v-if="data.efficiency.anomalies.length > 0" class="mt-6 border-t pt-4" style="border-color: var(--border-color);">
        <p class="text-label mb-2">{{ $t('expense_history.expense_anomalies') }}</p>
        <div class="space-y-2">
          <div
            v-for="(anomaly, idx) in data.efficiency.anomalies"
            :key="idx"
            class="flex items-start gap-2 p-3 rounded-lg bg-surface-secondary"
          >
            <LucideAlertTriangle class="size-4 text-amber-500 mt-0.5 shrink-0" />
            <div>
              <p class="text-sm font-medium text-ink">{{ anomaly.vehicle }}</p>
              <p class="text-xs text-ink-muted">{{ anomaly.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>
