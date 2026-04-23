<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  LucideGauge,
  LucideRefreshCw,
  LucideDownload,
  LucideAlertTriangle,
  LucideChevronDown,
  LucideChevronUp,
  LucideTrendingUp,
  LucideTrendingDown,
  LucideActivity,
  LucideShieldAlert,
  LucideFilter,
  LucideX,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Chart } from '@/components/ui'
import type { EChartsOption } from 'echarts'

const { t } = useI18n()

// --- Types ---
interface KPIs {
  total_fleet_mileage: number
  avg_km_per_vehicle: number
  highest_usage: { vehicle: string; km: number }
  lowest_usage: { vehicle: string; km: number }
  sensor_pct: number
  missing_reading_alerts: number
}

interface TrendPoint {
  date: string
  total_km: number
  vehicle_data: Record<string, number>
}

interface MeterRecord {
  name: string
  date: string | null
  vehicle: string
  reading: number
  reading_delta: number
  source: string
  recorded_by: string
  anomaly: { type: string; description: string } | null
  notes: string
}

interface IntegrityData {
  inconsistent_vehicles: string[]
  missing_readings: { vehicle: string; last_reading_date: string | null; days_since: number }[]
  manual_override_pct: number
  total_vehicles: number
  vehicles_with_readings: number
}

interface MeterHistoryData {
  kpis: KPIs
  trend: TrendPoint[]
  records: MeterRecord[]
  integrity: IntegrityData
}

// --- State ---
const isLoading = ref(true)
const data = ref<MeterHistoryData | null>(null)
const dateFrom = ref('')
const dateTo = ref('')
const selectedVehicles = ref<string[]>([])
const allVehicles = ref<any[]>([])
const chartView = ref<'fleet' | 'vehicle'>('fleet')
const expandedRows = ref<Set<string>>(new Set())
const showVehicleFilter = ref(false)

const chartViewTabs = computed(() => [
  { id: 'fleet' as const, label: t('meter_history.fleet_total') },
  { id: 'vehicle' as const, label: t('meter_history.per_vehicle') },
])

// --- Presets ---
function setPreset(days: number) {
  const now = new Date()
  const from = new Date(now.getFullYear(), now.getMonth(), now.getDate() - days)
  dateTo.value = formatDate(now)
  dateFrom.value = formatDate(from)
  loadData()
}

function formatDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

// --- Load ---
async function fetchVehicles() {
  try {
    const res = await apiCall('frappe.client.get_list', {
      doctype: 'Vehicle',
      fields: ['name', 'license_plate'],
      limit: 100,
    })
    allVehicles.value = res
  } catch (e) {
    console.warn('Failed to fetch vehicles', e)
  }
}

async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {}
    if (dateFrom.value) args.date_from = dateFrom.value
    if (dateTo.value) args.date_to = dateTo.value
    if (selectedVehicles.value.length > 0) {
      args.vehicles = JSON.stringify(selectedVehicles.value)
    }
    const result = await apiCall<MeterHistoryData>(
      'car_repair_management.api.meter_history.get_meter_history',
      args,
    )
    data.value = result
  } catch (e) {
    console.warn('Failed to load meter history', e)
  } finally {
    isLoading.value = false
  }
}

function toggleVehicleSelection(vehicle: string) {
  const idx = selectedVehicles.value.indexOf(vehicle)
  if (idx > -1) {
    selectedVehicles.value.splice(idx, 1)
  } else {
    selectedVehicles.value.push(vehicle)
  }
}

function clearVehicleFilter() {
  selectedVehicles.value = []
  loadData()
}

onMounted(() => {
  fetchVehicles()
  setPreset(90)
})

// --- Chart Options ---
const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

const trendChartOption = computed<EChartsOption>(() => {
  if (!data.value?.trend.length) {
    return { graphic: { type: 'text', left: 'center', top: 'middle', style: { text: 'No trend data', fontSize: 14 } } }
  }

  const trend = data.value.trend

  if (chartView.value === 'fleet') {
    return {
      tooltip: { trigger: 'axis' },
      grid: { left: 60, right: 20, top: 40, bottom: 40 },
      xAxis: {
        type: 'category',
        data: trend.map((t) => t.date),
        axisLabel: { rotate: 45, fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        name: 'KM',
        axisLabel: { formatter: (v: number) => v.toLocaleString() },
      },
      series: [
        {
          name: 'Fleet Total KM',
          type: 'line',
          data: trend.map((t) => t.total_km),
          smooth: true,
          areaStyle: { opacity: 0.15 },
          itemStyle: { color: '#3b82f6' },
        },
      ],
    }
  }

  // Per vehicle view
  const vehicleSet = new Set<string>()
  trend.forEach((t) => Object.keys(t.vehicle_data).forEach((v) => vehicleSet.add(v)))
  const vehicles = Array.from(vehicleSet)

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: vehicles, bottom: 0, type: 'scroll' },
    grid: { left: 60, right: 20, top: 40, bottom: 60 },
    xAxis: {
      type: 'category',
      data: trend.map((t) => t.date),
      axisLabel: { rotate: 45, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: 'KM',
      axisLabel: { formatter: (v: number) => v.toLocaleString() },
    },
    series: vehicles.map((v, i) => ({
      name: v,
      type: 'line' as const,
      data: trend.map((t) => t.vehicle_data[v] || 0),
      smooth: true,
      itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    })),
  }
})

// --- Anomaly helpers ---
function toggleRow(name: string) {
  if (expandedRows.value.has(name)) {
    expandedRows.value.delete(name)
  } else {
    expandedRows.value.add(name)
  }
}

function anomalyBorderColor(anomaly: MeterRecord['anomaly']): string {
  if (!anomaly) return ''
  return anomaly.type === 'negative_delta' ? 'border-l-4 border-l-red-500' : 'border-l-4 border-l-amber-500'
}

function anomalyVariant(type: string): 'danger' | 'warning' {
  return type === 'negative_delta' ? 'danger' : 'warning'
}

// --- Export ---
function exportCSV() {
  if (!data.value?.records.length) return
  const headers = [t('common.date'), t('common.vehicle'), 'Reading', t('meter_history.delta'), t('meter_history.source'), t('meter_history.recorded_by'), t('meter_history.anomaly')]
  const rows = data.value.records.map((r) => [
    r.date || '',
    r.vehicle,
    r.reading,
    r.reading_delta,
    r.source,
    r.recorded_by,
    r.anomaly ? r.anomaly.type : '',
  ])
  const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `meter_history_${formatDate(new Date())}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="space-y-6 pb-12">
    <!-- Page Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div>
        <h1 class="text-3xl font-bold" style="color: var(--text-primary);">{{ $t('meter_history.title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted);">{{ $t('meter_history.subtitle') }}</p>
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

    <!-- Multi-Filter Bar -->
    <Card class="relative z-20">
      <div class="flex flex-wrap items-end gap-6">
        <!-- Vehicle Multi-select Filter -->
        <div class="relative min-w-[240px]">
          <label class="text-xs font-bold uppercase tracking-wider mb-2 block" style="color: var(--text-muted);">
            {{ $t('common.vehicle') }}
          </label>
          <div 
            @click="showVehicleFilter = !showVehicleFilter"
            class="flex items-center justify-between px-3 py-2 rounded-lg border cursor-pointer transition-all hover:border-accent"
            style="background-color: var(--bg-tertiary); border-color: var(--border-color);"
          >
            <div class="flex flex-wrap gap-1 max-w-[200px] overflow-hidden">
              <span v-if="selectedVehicles.length === 0" class="text-sm" style="color: var(--text-muted);">All Vehicles</span>
              <Badge v-for="v in selectedVehicles" :key="v" variant="info" size="sm" class="shrink-0">
                {{ v }}
              </Badge>
            </div>
            <LucideFilter class="size-4 opacity-50" />
          </div>

          <!-- Dropdown -->
          <div 
            v-if="showVehicleFilter" 
            class="absolute top-full left-0 mt-2 w-full max-h-60 overflow-y-auto z-50 rounded-xl shadow-2xl border animate-in fade-in slide-in-from-top-2 duration-200"
            style="background-color: var(--bg-primary); border-color: var(--border-color);"
          >
            <div class="p-2 space-y-1">
              <div 
                v-for="v in allVehicles" 
                :key="v.name"
                @click="toggleVehicleSelection(v.name)"
                class="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors hover:bg-surface-secondary"
                :class="{ 'bg-accent/10 border-accent': selectedVehicles.includes(v.name) }"
              >
                <div class="flex flex-col">
                  <span class="text-sm font-medium">{{ v.license_plate }}</span>
                  <span class="text-[10px] opacity-60">{{ v.name }}</span>
                </div>
                <div v-if="selectedVehicles.includes(v.name)" class="size-2 rounded-full bg-accent"></div>
              </div>
            </div>
          </div>
        </div>

        <div>
          <label class="text-xs font-bold uppercase tracking-wider mb-2 block" style="color: var(--text-muted);">{{ $t('common.from') }}</label>
          <input
            v-model="dateFrom"
            type="date"
            class="rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
            style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
          />
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider mb-2 block" style="color: var(--text-muted);">{{ $t('common.to') }}</label>
          <input
            v-model="dateTo"
            type="date"
            class="rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
            style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
          />
        </div>
        
        <div class="flex items-center gap-2">
          <Button variant="outline" class="h-10 px-4" @click="clearVehicleFilter">
            <LucideX class="size-4 mr-2" />
            Clear
          </Button>
          <Button variant="primary" class="h-10 px-6 font-bold" @click="loadData">{{ $t('common.apply') }}</Button>
        </div>
      </div>
    </Card>

    <!-- KPI Cards -->
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card v-for="i in 6" :key="i"><Skeleton height="100px" /></Card>
    </div>
    <div v-else-if="data" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card class="hover:shadow-lg transition-all border-l-4 border-l-blue-500">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-xl bg-blue-500/10 text-blue-500 shrink-0">
            <LucideGauge class="size-6" />
          </div>
          <div>
            <p class="text-xs font-bold uppercase tracking-widest text-ink-muted">{{ $t('meter_history.total_fleet_mileage') }}</p>
            <p class="text-2xl font-black mt-1" style="color: var(--text-primary);">{{ data.kpis.total_fleet_mileage.toLocaleString() }} <span class="text-sm font-normal text-ink-muted">km</span></p>
          </div>
        </div>
      </Card>

      <Card class="hover:shadow-lg transition-all border-l-4 border-l-green-500">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-xl bg-green-500/10 text-green-500 shrink-0">
            <LucideActivity class="size-6" />
          </div>
          <div>
            <p class="text-xs font-bold uppercase tracking-widest text-ink-muted">{{ $t('meter_history.avg_km_per_vehicle') }}</p>
            <p class="text-2xl font-black mt-1" style="color: var(--text-primary);">{{ data.kpis.avg_km_per_vehicle.toLocaleString() }} <span class="text-sm font-normal text-ink-muted">km</span></p>
          </div>
        </div>
      </Card>

      <Card class="hover:shadow-lg transition-all border-l-4 border-l-amber-500">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-xl bg-amber-500/10 text-amber-500 shrink-0">
            <LucideAlertTriangle class="size-6" />
          </div>
          <div>
            <p class="text-xs font-bold uppercase tracking-widest text-ink-muted font-bold">{{ $t('meter_history.missing_reading_alerts') }}</p>
            <p class="text-2xl font-black mt-1" style="color: var(--text-primary);">{{ data.kpis.missing_reading_alerts }}</p>
            <p class="text-[10px] text-ink-muted">{{ $t('meter_history.vehicles_no_readings_30d') }}</p>
          </div>
        </div>
      </Card>
    </div>

    <!-- Trend Chart -->
    <Card v-if="!isLoading && data" class="p-6">
      <div class="flex items-center justify-between mb-8">
        <div>
          <h2 class="text-xl font-bold">{{ $t('meter_history.mileage_trend') }}</h2>
          <p class="text-xs text-ink-muted">Visualizing distance covered over time</p>
        </div>
        <div class="flex p-1 rounded-xl bg-surface-tertiary">
          <button
            v-for="view in chartViewTabs"
            :key="view.id"
            class="px-4 py-2 text-xs font-bold rounded-lg transition-all"
            :class="chartView === view.id ? 'bg-white shadow-sm text-ink' : 'text-ink-muted hover:text-ink'"
            @click="chartView = view.id"
          >
            {{ view.label }}
          </button>
        </div>
      </div>
      <Chart :option="trendChartOption" height="400px" />
    </Card>

    <!-- Records Table -->
    <Card v-if="!isLoading && data" padding="none" class="overflow-hidden">
      <div class="p-6 border-b flex items-center justify-between" style="border-color: var(--border-color);">
        <div>
          <h2 class="text-xl font-bold">{{ $t('meter_history.odometer_records') }}</h2>
          <p class="text-xs text-ink-muted mt-1">{{ $t('meter_history.records_count', { count: data.records.length }) }}</p>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left py-4 px-6 uppercase tracking-wider text-[10px] font-black" style="background-color: var(--bg-tertiary); color: var(--text-muted);">
              <th class="px-6 py-4">{{ $t('common.date') }}</th>
              <th class="px-6 py-4">{{ $t('common.vehicle') }}</th>
              <th class="px-6 py-4 text-right">Reading</th>
              <th class="px-6 py-4 text-right">{{ $t('meter_history.delta') }}</th>
              <th class="px-6 py-4">{{ $t('meter_history.source') }}</th>
              <th class="px-6 py-4">{{ $t('meter_history.recorded_by') }}</th>
              <th class="px-6 py-4">{{ $t('meter_history.anomaly') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y" style="border-color: var(--border-subtle);">
            <template v-for="record in data.records" :key="record.name">
              <tr
                class="hover:bg-surface-secondary/50 transition-colors group cursor-pointer"
                :class="anomalyBorderColor(record.anomaly)"
                @click="record.anomaly && toggleRow(record.name)"
              >
                <td class="px-6 py-4 font-medium">{{ record.date || '—' }}</td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <div class="size-8 rounded-lg bg-surface-tertiary flex items-center justify-center font-bold text-[10px]">
                      {{ record.vehicle.slice(0, 2) }}
                    </div>
                    <span class="font-bold">{{ record.vehicle }}</span>
                  </div>
                </td>
                <td class="px-6 py-4 text-right font-black">{{ record.reading.toLocaleString() }} <span class="text-[10px] font-normal opacity-60">km</span></td>
                <td class="px-6 py-4 text-right">
                  <span 
                    class="px-2 py-1 rounded-full text-xs font-bold"
                    :class="record.reading_delta < 0 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'"
                  >
                    {{ record.reading_delta >= 0 ? '+' : '' }}{{ record.reading_delta.toLocaleString() }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <Badge variant="outline" class="font-bold">{{ record.source }}</Badge>
                </td>
                <td class="px-6 py-4 text-ink-muted text-xs">{{ record.recorded_by }}</td>
                <td class="px-6 py-4 text-right">
                  <div v-if="record.anomaly" class="flex items-center justify-end gap-2">
                    <Badge :variant="anomalyVariant(record.anomaly.type)" size="sm" class="animate-pulse">
                      {{ record.anomaly.type === 'negative_delta' ? $t('meter_history.negative') : $t('meter_history.jump') }}
                    </Badge>
                    <component
                      :is="expandedRows.has(record.name) ? LucideChevronUp : LucideChevronDown"
                      class="size-4 text-ink-muted"
                    />
                  </div>
                  <span v-else class="text-ink-muted opacity-40">—</span>
                </td>
              </tr>
              <!-- Expanded anomaly detail -->
              <tr v-if="record.anomaly && expandedRows.has(record.name)" class="bg-surface-tertiary">
                <td colspan="7" class="px-8 py-4">
                  <div class="flex items-center gap-4 p-4 rounded-xl border border-default bg-white/50">
                    <div class="p-2 rounded-lg bg-amber-500/10 text-amber-500">
                      <LucideShieldAlert class="size-5" />
                    </div>
                    <div>
                      <p class="text-xs font-black uppercase text-amber-600 tracking-widest">Integrity Violation</p>
                      <p class="text-sm font-medium">{{ record.anomaly.description }}</p>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>

<style scoped>
.text-label {
  color: var(--text-muted);
}
</style>
