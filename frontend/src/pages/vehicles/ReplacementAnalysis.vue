<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  LucideRefreshCw,
  LucideTarget,
  LucideCalculator,
  LucideInfo,
  LucideBarChart3,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Chart } from '@/components/ui'
import type { EChartsOption } from 'echarts'

// --- Types ---
interface Criteria {
  age_threshold: number
  mileage_threshold: number
  cost_to_value_ratio: number
  downtime_threshold: number
  maintenance_freq_threshold: number
  weights: { age: number; mileage: number; cost_ratio: number; downtime: number; maintenance_freq: number }
}

interface Candidate {
  vehicle: string
  license_plate: string
  make: string
  model: string
  age_years: number
  total_lifetime_cost: number
  current_book_value: number
  cost_to_value_ratio: number
  downtime_days: number
  maintenance_count: number
  replacement_score: number
  recommendation: 'Keep' | 'Monitor' | 'Replace'
}

interface ScatterPoint {
  vehicle: string
  age: number
  cost: number
  downtime: number
  recommendation: string
}

interface AnalysisData {
  criteria: Criteria
  candidates: Candidate[]
  scatter_data: ScatterPoint[]
}

interface SimulationResult {
  vehicle: string
  inputs: Record<string, number>
  current_annual: { maintenance: number; fuel: number; downtime_days: number }
  keep_projection: { year: number; maintenance: number; fuel: number; total: number; cumulative: number }[]
  replace_projection: { year: number; maintenance: number; fuel: number; total: number; cumulative: number }[]
  summary: { net_savings_5y: number; breakeven_year: number | null; recommendation: string }
}

const { t } = useI18n()

// --- State ---
const isLoading = ref(true)
const data = ref<AnalysisData | null>(null)
const selectedVehicle = ref<string | null>(null)

// Simulation
const simResaleValue = ref(0)
const simAcquisitionCost = ref(0)
const simMaintReduction = ref(30)
const simDowntimeReduction = ref(50)
const simResult = ref<SimulationResult | null>(null)
const simLoading = ref(false)

// --- Helpers ---
function fmt(v: number): string {
  return v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function scoreColor(score: number): string {
  if (score <= 40) return '#10b981'
  if (score <= 70) return '#f59e0b'
  return '#ef4444'
}

function recVariant(rec: string): 'success' | 'warning' | 'danger' {
  if (rec === 'Keep') return 'success'
  if (rec === 'Monitor') return 'warning'
  return 'danger'
}

// --- Load ---
async function loadData() {
  isLoading.value = true
  try {
    const result = await apiCall<AnalysisData>(
      'car_repair_management.api.replacement_analysis.get_replacement_analysis',
      {},
    )
    data.value = result
  } catch (e) {
    console.warn('Failed to load replacement analysis', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)

function selectVehicle(vehicle: string) {
  selectedVehicle.value = vehicle
  simResult.value = null
  // Set reasonable defaults based on vehicle data
  const c = data.value?.candidates.find((x) => x.vehicle === vehicle)
  if (c) {
    simResaleValue.value = Math.round(c.current_book_value * 0.3)
    simAcquisitionCost.value = Math.round(c.current_book_value * 2)
  }
}

async function runSimulation() {
  if (!selectedVehicle.value) return
  simLoading.value = true
  try {
    const result = await apiCall<SimulationResult>(
      'car_repair_management.api.replacement_analysis.run_financial_simulation',
      {
        vehicle: selectedVehicle.value,
        resale_value: simResaleValue.value,
        acquisition_cost: simAcquisitionCost.value,
        maintenance_reduction_pct: simMaintReduction.value,
        downtime_reduction_pct: simDowntimeReduction.value,
      },
    )
    simResult.value = result
  } catch (e) {
    console.warn('Simulation failed', e)
  } finally {
    simLoading.value = false
  }
}

// --- Chart Options ---
const scatterChartOption = computed<EChartsOption>(() => {
  const pts = data.value?.scatter_data || []
  if (!pts.length) return {}

  const colorMap: Record<string, string> = { Keep: '#10b981', Monitor: '#f59e0b', Replace: '#ef4444' }
  const downtimeValues = pts.map((p) => p.downtime)
  const maxDowntime = downtimeValues.length ? Math.max(...downtimeValues, 1) : 1

  const seriesData: Record<string, unknown[][]> = { Keep: [], Monitor: [], Replace: [] }
  pts.forEach((p) => {
    const key = p.recommendation in seriesData ? p.recommendation : 'Monitor'
    seriesData[key].push([p.age, p.cost, p.downtime, p.vehicle])
  })

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const d = params.data
        return `<b>${d[3]}</b><br>Age: ${d[0]} years<br>Cost: ${fmt(d[1])}<br>Downtime: ${d[2]} days`
      },
    },
    legend: { data: ['Keep', 'Monitor', 'Replace'], bottom: 0 },
    grid: { left: 70, right: 30, top: 30, bottom: 50 },
    xAxis: { type: 'value', name: 'Age (years)', nameLocation: 'middle', nameGap: 30 },
    yAxis: { type: 'value', name: 'Lifetime Cost', axisLabel: { formatter: (v: number) => v.toLocaleString() } },
    series: Object.entries(seriesData).map(([name, d]) => ({
      name,
      type: 'scatter' as const,
      data: d,
      symbolSize: (val: number[]) => Math.max(8, (val[2] / maxDowntime) * 40),
      itemStyle: { color: colorMap[name] },
    })),
  }
})

const simChartOption = computed<EChartsOption>(() => {
  if (!simResult.value) return {}
  const keep = simResult.value.keep_projection
  const replace = simResult.value.replace_projection
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Keep (Cumulative)', 'Replace (Cumulative)'], bottom: 0 },
    grid: { left: 70, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: keep.map((k) => `Year ${k.year}`) },
    yAxis: { type: 'value', axisLabel: { formatter: (v: number) => v.toLocaleString() } },
    series: [
      { name: 'Keep (Cumulative)', type: 'line', data: keep.map((k) => k.cumulative), itemStyle: { color: '#ef4444' }, smooth: true },
      { name: 'Replace (Cumulative)', type: 'line', data: replace.map((r) => r.cumulative), itemStyle: { color: '#10b981' }, smooth: true },
    ],
  }
})

// Criteria display helpers
const criteriaItems = computed(() => {
  if (!data.value) return []
  const c = data.value.criteria
  return [
    { label: t('replacement.age_threshold'), value: `${c.age_threshold} years`, weight: c.weights.age },
    { label: t('replacement.mileage_threshold'), value: `${c.mileage_threshold.toLocaleString()} km`, weight: c.weights.mileage },
    { label: t('replacement.cost_value_ratio'), value: `${(c.cost_to_value_ratio * 100).toFixed(0)}%`, weight: c.weights.cost_ratio },
    { label: t('replacement.downtime_threshold'), value: `${c.downtime_threshold} days/year`, weight: c.weights.downtime },
    { label: t('replacement.maintenance_frequency'), value: `${c.maintenance_freq_threshold} repairs/year`, weight: c.weights.maintenance_freq },
  ]
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div>
        <h1 class="text-page-title">{{ $t('replacement.title') }}</h1>
        <p class="text-sm text-ink-muted mt-1">{{ $t('replacement.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="loadData">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
      </div>
    </div>

    <!-- Loading State -->
    <template v-if="isLoading">
      <Card><Skeleton height="120px" /></Card>
      <Card><Skeleton height="300px" /></Card>
    </template>

    <template v-else-if="data">
      <!-- Section A: Criteria Configuration -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideTarget class="size-5 text-ink-muted" />
          <h2 class="text-section-title">{{ $t('replacement.replacement_criteria') }}</h2>
          <Badge variant="default" size="sm">{{ $t('replacement.read_only') }}</Badge>
        </div>
        <p class="text-xs text-ink-muted mb-4">
          {{ $t('replacement.criteria_desc') }}
        </p>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div v-for="item in criteriaItems" :key="item.label" class="p-3 rounded-lg bg-surface-secondary">
            <p class="text-label">{{ item.label }}</p>
            <p class="text-lg font-semibold text-ink mt-1">{{ item.value }}</p>
            <div class="flex items-center gap-2 mt-2">
              <div class="flex-1 h-1.5 rounded-full overflow-hidden" style="background-color: var(--bg-tertiary);">
                <div class="h-full rounded-full bg-blue-500" :style="{ width: item.weight + '%' }" />
              </div>
              <span class="text-xs text-ink-muted">{{ item.weight }}%</span>
            </div>
          </div>
        </div>
      </Card>

      <!-- Section B: Candidates Table -->
      <Card padding="none">
        <div class="p-4 border-b border-default">
          <h2 class="text-section-title">{{ $t('replacement.replacement_candidates') }}</h2>
          <p class="text-xs text-ink-muted mt-1">{{ $t('replacement.vehicles_analyzed', { count: data.candidates.length }) }}</p>
        </div>

        <EmptyState
          v-if="data.candidates.length === 0"
          :icon="LucideBarChart3"
          :title="$t('replacement.no_vehicles_analyze')"
          :description="$t('replacement.add_vehicles_desc')"
        />

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-default">
                <th class="text-left text-label px-4 py-3 font-medium">{{ $t('replacement.vehicle') }}</th>
                <th class="text-left text-label px-4 py-3 font-medium">{{ $t('replacement.make_model') }}</th>
                <th class="text-right text-label px-4 py-3 font-medium">{{ $t('replacement.age') }}</th>
                <th class="text-right text-label px-4 py-3 font-medium">{{ $t('replacement.lifetime_cost') }}</th>
                <th class="text-right text-label px-4 py-3 font-medium">{{ $t('replacement.book_value') }}</th>
                <th class="text-right text-label px-4 py-3 font-medium">{{ $t('replacement.cost_value') }}</th>
                <th class="text-right text-label px-4 py-3 font-medium">{{ $t('replacement.downtime') }}</th>
                <th class="text-right text-label px-4 py-3 font-medium">{{ $t('replacement.repairs') }}</th>
                <th class="text-center text-label px-4 py-3 font-medium">{{ $t('replacement.score') }}</th>
                <th class="text-left text-label px-4 py-3 font-medium">{{ $t('replacement.rec') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in data.candidates"
                :key="c.vehicle"
                class="border-b border-default hover:bg-surface-secondary transition-colors cursor-pointer"
                :class="{ 'bg-surface-secondary': selectedVehicle === c.vehicle }"
                @click="selectVehicle(c.vehicle)"
              >
                <td class="px-4 py-3 text-ink font-medium">{{ c.license_plate }}</td>
                <td class="px-4 py-3 text-ink-muted">{{ c.make }} {{ c.model }}</td>
                <td class="px-4 py-3 text-ink text-right">{{ c.age_years }}y</td>
                <td class="px-4 py-3 text-ink text-right">{{ fmt(c.total_lifetime_cost) }}</td>
                <td class="px-4 py-3 text-ink text-right">{{ fmt(c.current_book_value) }}</td>
                <td class="px-4 py-3 text-ink text-right">{{ (c.cost_to_value_ratio * 100).toFixed(0) }}%</td>
                <td class="px-4 py-3 text-ink text-right">{{ c.downtime_days }}d</td>
                <td class="px-4 py-3 text-ink text-right">{{ c.maintenance_count }}</td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2 justify-center">
                    <div class="w-16 h-2.5 rounded-full overflow-hidden" style="background-color: var(--bg-tertiary);">
                      <div
                        class="h-full rounded-full transition-all"
                        :style="{ width: c.replacement_score + '%', backgroundColor: scoreColor(c.replacement_score) }"
                      />
                    </div>
                    <span class="text-xs font-semibold" :style="{ color: scoreColor(c.replacement_score) }">
                      {{ c.replacement_score }}
                    </span>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <Badge :variant="recVariant(c.recommendation)" size="sm">{{ c.recommendation }}</Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Section C: Scatter Plot -->
      <Card v-if="data.scatter_data.length > 0">
        <h2 class="text-section-title mb-1">{{ $t('replacement.comparative_viz') }}</h2>
        <p class="text-xs text-ink-muted mb-4">
          {{ $t('replacement.bubble_desc') }}
        </p>
        <Chart :option="scatterChartOption" height="400px" />
      </Card>

      <!-- Section D: Financial Simulation -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideCalculator class="size-5 text-ink-muted" />
          <h2 class="text-section-title">{{ $t('replacement.financial_simulation') }}</h2>
        </div>

        <div class="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-500/10 mb-4">
          <LucideInfo class="size-4 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
          <p class="text-xs text-amber-800 dark:text-amber-300">
            {{ $t('replacement.advisory_note') }}
          </p>
        </div>

        <div v-if="!selectedVehicle" class="text-center py-8">
          <LucideCalculator class="size-8 text-ink-muted mx-auto mb-2" />
          <p class="text-sm text-ink-muted">{{ $t('replacement.select_vehicle_sim') }}</p>
        </div>

        <template v-else>
          <p class="text-sm text-ink font-medium mb-4">
            {{ $t('replacement.simulating_for') }} <span class="text-blue-600 dark:text-blue-400">{{ selectedVehicle }}</span>
          </p>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label class="text-label block mb-1">{{ $t('replacement.est_resale_value') }}</label>
              <input
                v-model.number="simResaleValue"
                type="number"
                class="w-full rounded-lg border px-3 py-2 text-sm bg-surface-bg text-ink border-default"
              />
            </div>
            <div>
              <label class="text-label block mb-1">{{ $t('replacement.new_vehicle_cost') }}</label>
              <input
                v-model.number="simAcquisitionCost"
                type="number"
                class="w-full rounded-lg border px-3 py-2 text-sm bg-surface-bg text-ink border-default"
              />
            </div>
            <div>
              <label class="text-label block mb-1">{{ $t('replacement.maint_reduction') }}</label>
              <input
                v-model.number="simMaintReduction"
                type="number"
                min="0"
                max="100"
                class="w-full rounded-lg border px-3 py-2 text-sm bg-surface-bg text-ink border-default"
              />
            </div>
            <div>
              <label class="text-label block mb-1">{{ $t('replacement.downtime_reduction') }}</label>
              <input
                v-model.number="simDowntimeReduction"
                type="number"
                min="0"
                max="100"
                class="w-full rounded-lg border px-3 py-2 text-sm bg-surface-bg text-ink border-default"
              />
            </div>
          </div>

          <Button variant="primary" @click="runSimulation" :disabled="simLoading">
            <LucideCalculator class="size-4" />
            {{ simLoading ? $t('replacement.running') : $t('replacement.run_simulation') }}
          </Button>

          <!-- Simulation Results -->
          <div v-if="simResult" class="mt-6 space-y-4">
            <!-- Summary KPIs -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="p-4 rounded-lg bg-surface-secondary">
                <p class="text-label">{{ $t('replacement.net_5y_savings') }}</p>
                <p
                  class="text-2xl font-semibold mt-1"
                  :class="simResult.summary.net_savings_5y > 0 ? 'text-green-600' : 'text-red-600'"
                >
                  {{ fmt(Math.abs(simResult.summary.net_savings_5y)) }}
                  <span class="text-sm font-normal">{{ simResult.summary.net_savings_5y > 0 ? $t('replacement.saved') : $t('replacement.loss') }}</span>
                </p>
              </div>
              <div class="p-4 rounded-lg bg-surface-secondary">
                <p class="text-label">{{ $t('replacement.breakeven_period') }}</p>
                <p class="text-2xl font-semibold text-ink mt-1">
                  {{ simResult.summary.breakeven_year ? `Year ${simResult.summary.breakeven_year}` : 'N/A' }}
                </p>
              </div>
              <div class="p-4 rounded-lg bg-surface-secondary">
                <p class="text-label">{{ $t('replacement.recommendation') }}</p>
                <Badge
                  :variant="simResult.summary.recommendation === 'Replace' ? 'success' : 'warning'"
                  class="mt-2"
                >
                  {{ simResult.summary.recommendation }}
                </Badge>
              </div>
            </div>

            <!-- Projection Chart -->
            <div>
              <p class="text-label mb-2">{{ $t('replacement.projection_5y') }}</p>
              <Chart :option="simChartOption" height="300px" />
            </div>
          </div>
        </template>
      </Card>
    </template>
  </div>
</template>
