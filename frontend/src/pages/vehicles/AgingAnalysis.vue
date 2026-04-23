<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  LucideClock,
  LucideRefreshCw,
  LucideAlertTriangle,
  LucideShieldAlert,
  LucideTrendingUp,
  LucideActivity,
  LucideBarChart3,
  LucideCalendarClock,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Chart } from '@/components/ui'
import type { EChartsOption } from 'echarts'

// --- Types ---
interface AgingBracket {
  label: string
  count: number
  pct: number
  vehicles: string[]
}

interface Distribution {
  brackets: AgingBracket[]
  avg_age: number
  median_age: number
  total_vehicles: number
}

interface CostBracket {
  bracket: string
  avg_cost: number
}

interface DowntimeBracket {
  bracket: string
  avg_days: number
}

interface AgingVsCost {
  maintenance_by_bracket: CostBracket[]
  downtime_by_bracket: DowntimeBracket[]
}

interface ThresholdVehicle {
  vehicle: string
  age: number
  threshold: number
}

interface LifecycleVehicle {
  vehicle: string
  age: number
}

interface RiskDashboard {
  approaching_threshold: ThresholdVehicle[]
  beyond_lifecycle: LifecycleVehicle[]
  risk_exposure_pct: number
  forecasted_replacements_12m: number
  forecasted_replacements_24m: number
}

interface AgingAnalysisResponse {
  distribution: Distribution
  aging_vs_cost: AgingVsCost
  risk_dashboard: RiskDashboard
}

const { t } = useI18n()

// --- State ---
const isLoading = ref(true)
const hasError = ref(false)
const errorMessage = ref('')
const data = ref<AgingAnalysisResponse | null>(null)

// --- Bracket colors ---
const BRACKET_COLORS = ['#10b981', '#f59e0b', '#f97316', '#ef4444']

// --- Computed ---
const distribution = computed(() => data.value?.distribution ?? null)
const agingVsCost = computed(() => data.value?.aging_vs_cost ?? null)
const risk = computed(() => data.value?.risk_dashboard ?? null)

const totalVehicles = computed(() => distribution.value?.total_vehicles ?? 0)
const avgAge = computed(() => distribution.value?.avg_age ?? 0)
const medianAge = computed(() => distribution.value?.median_age ?? 0)

const approachingCount = computed(() => risk.value?.approaching_threshold?.length ?? 0)
const beyondCount = computed(() => risk.value?.beyond_lifecycle?.length ?? 0)
const riskExposure = computed(() => risk.value?.risk_exposure_pct ?? 0)
const forecast12 = computed(() => risk.value?.forecasted_replacements_12m ?? 0)
const forecast24 = computed(() => risk.value?.forecasted_replacements_24m ?? 0)

// --- Chart Options ---
const distributionChartOption = computed<EChartsOption>(() => {
  const brackets = distribution.value?.brackets ?? []
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        const bracket = brackets[p.dataIndex]
        if (!bracket) return p.name
        return `<strong>${bracket.label}</strong><br/>Count: ${bracket.count.toLocaleString()}<br/>Share: ${bracket.pct.toFixed(1)}%`
      },
    },
    xAxis: {
      type: 'category',
      data: brackets.map((b) => b.label),
      axisLabel: { fontSize: 12 },
    },
    yAxis: {
      type: 'value',
      name: 'Vehicles',
      minInterval: 1,
    },
    series: [
      {
        type: 'bar',
        data: brackets.map((b, i) => ({
          value: b.count,
          itemStyle: { color: BRACKET_COLORS[i] ?? BRACKET_COLORS[3] },
        })),
        barMaxWidth: 60,
        label: {
          show: true,
          position: 'top',
          formatter: (p: any) => {
            const bracket = brackets[p.dataIndex]
            return bracket ? `${bracket.count} (${bracket.pct.toFixed(1)}%)` : ''
          },
          fontSize: 12,
          fontWeight: 600,
        },
      },
    ],
    grid: { top: 40, bottom: 30, left: 50, right: 20 },
  }
})

const maintenanceCostChartOption = computed<EChartsOption>(() => {
  const items = agingVsCost.value?.maintenance_by_bracket ?? []
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        return `<strong>${p.name}</strong><br/>Avg Cost: ${Number(p.value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
      },
    },
    xAxis: {
      type: 'category',
      data: items.map((d) => d.bracket),
      axisLabel: { fontSize: 12 },
    },
    yAxis: {
      type: 'value',
      name: 'Cost',
    },
    series: [
      {
        type: 'bar',
        data: items.map((d, i) => ({
          value: d.avg_cost,
          itemStyle: { color: BRACKET_COLORS[i] ?? BRACKET_COLORS[3] },
        })),
        barMaxWidth: 50,
        label: {
          show: true,
          position: 'top',
          formatter: (p: any) => Number(p.value).toLocaleString(),
          fontSize: 11,
        },
      },
    ],
    grid: { top: 40, bottom: 30, left: 60, right: 20 },
  }
})

const downtimeChartOption = computed<EChartsOption>(() => {
  const items = agingVsCost.value?.downtime_by_bracket ?? []
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        return `<strong>${p.name}</strong><br/>Avg Downtime: ${Number(p.value).toFixed(1)} days`
      },
    },
    xAxis: {
      type: 'category',
      data: items.map((d) => d.bracket),
      axisLabel: { fontSize: 12 },
    },
    yAxis: {
      type: 'value',
      name: 'Days',
    },
    series: [
      {
        type: 'bar',
        data: items.map((d, i) => ({
          value: d.avg_days,
          itemStyle: { color: BRACKET_COLORS[i] ?? BRACKET_COLORS[3] },
        })),
        barMaxWidth: 50,
        label: {
          show: true,
          position: 'top',
          formatter: (p: any) => `${Number(p.value).toFixed(1)}d`,
          fontSize: 11,
        },
      },
    ],
    grid: { top: 40, bottom: 30, left: 60, right: 20 },
  }
})

// --- Data fetching ---
async function loadData() {
  isLoading.value = true
  hasError.value = false
  errorMessage.value = ''
  try {
    const result = await apiCall<AgingAnalysisResponse>(
      'car_repair_management.api.aging_analysis.get_aging_analysis',
      {}
    )
    data.value = result ?? null
  } catch (e: any) {
    hasError.value = true
    errorMessage.value = e?.message || t('aging.failed_to_load')
    console.error('Aging analysis load failed:', e)
  } finally {
    isLoading.value = false
  }
}

function riskBadgeVariant(age: number, threshold: number): 'warning' | 'danger' {
  return age >= threshold ? 'danger' : 'warning'
}

function riskExposureColor(pct: number): string {
  if (pct >= 50) return 'text-red-600 dark:text-red-400'
  if (pct >= 25) return 'text-amber-600 dark:text-amber-400'
  return 'text-green-600 dark:text-green-400'
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div>
        <h1 class="text-page-title">{{ $t('aging.title') }}</h1>
        <p class="text-sm text-ink-muted mt-1">{{ $t('aging.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="loadData">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
      </div>
    </div>

    <!-- Error State -->
    <Card v-if="hasError && !isLoading">
      <EmptyState
        :icon="LucideAlertTriangle"
        :title="$t('aging.failed_to_load')"
        :description="errorMessage"
        :actionLabel="$t('aging.retry')"
        @action="loadData"
      />
    </Card>

    <!-- Loading Skeletons -->
    <template v-if="isLoading">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card v-for="i in 3" :key="i">
          <Skeleton height="20px" width="40%" />
          <Skeleton height="32px" width="60%" class="mt-2" />
        </Card>
      </div>
      <Card>
        <Skeleton height="20px" width="30%" />
        <Skeleton height="300px" class="mt-4" />
      </Card>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card v-for="i in 2" :key="i">
          <Skeleton height="20px" width="50%" />
          <Skeleton height="280px" class="mt-4" />
        </Card>
      </div>
    </template>

    <!-- Data Loaded -->
    <template v-else-if="data && !hasError">
      <!-- Section A: Age Stats KPIs -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center shrink-0">
              <LucideBarChart3 class="size-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p class="text-xs text-label uppercase tracking-wide">{{ $t('aging.total_vehicles') }}</p>
              <p class="text-2xl font-bold text-ink">{{ totalVehicles.toLocaleString() }}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center shrink-0">
              <LucideClock class="size-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <p class="text-xs text-label uppercase tracking-wide">{{ $t('aging.avg_fleet_age') }}</p>
              <p class="text-2xl font-bold text-ink">{{ avgAge.toFixed(1) }} <span class="text-sm font-normal text-ink-muted">{{ $t('aging.years') }}</span></p>
            </div>
          </div>
        </Card>
        <Card>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-500/20 flex items-center justify-center shrink-0">
              <LucideActivity class="size-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p class="text-xs text-label uppercase tracking-wide">{{ $t('aging.median_fleet_age') }}</p>
              <p class="text-2xl font-bold text-ink">{{ medianAge.toFixed(1) }} <span class="text-sm font-normal text-ink-muted">{{ $t('aging.years') }}</span></p>
            </div>
          </div>
        </Card>
      </div>

      <!-- Distribution Chart -->
      <Card>
        <h2 class="text-section-title mb-4">{{ $t('aging.fleet_age_dist') }}</h2>
        <template v-if="distribution && distribution.brackets.length > 0">
          <Chart :option="distributionChartOption" height="300px" :loading="isLoading" />
        </template>
        <EmptyState
          v-else
          :icon="LucideBarChart3"
          :title="$t('aging.no_dist_data')"
          :description="$t('aging.no_age_bracket_desc')"
        />
      </Card>

      <!-- Section B: Aging vs Cost Trends -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <h2 class="text-section-title mb-4">{{ $t('aging.avg_maint_cost_age') }}</h2>
          <template v-if="agingVsCost && agingVsCost.maintenance_by_bracket.length > 0">
            <Chart :option="maintenanceCostChartOption" height="280px" :loading="isLoading" />
          </template>
          <EmptyState
            v-else
            :icon="LucideTrendingUp"
            :title="$t('aging.no_cost_data')"
            :description="$t('aging.maint_cost_unavailable')"
          />
        </Card>
        <Card>
          <h2 class="text-section-title mb-4">{{ $t('aging.avg_downtime_age') }}</h2>
          <template v-if="agingVsCost && agingVsCost.downtime_by_bracket.length > 0">
            <Chart :option="downtimeChartOption" height="280px" :loading="isLoading" />
          </template>
          <EmptyState
            v-else
            :icon="LucideCalendarClock"
            :title="$t('aging.no_downtime_data')"
            :description="$t('aging.downtime_unavailable')"
          />
        </Card>
      </div>

      <!-- Section C: Risk Dashboard KPIs -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center shrink-0">
              <LucideAlertTriangle class="size-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <p class="text-xs text-label uppercase tracking-wide">{{ $t('aging.approaching_threshold') }}</p>
              <p class="text-2xl font-bold text-amber-600 dark:text-amber-400">{{ approachingCount.toLocaleString() }}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-red-100 dark:bg-red-500/20 flex items-center justify-center shrink-0">
              <LucideShieldAlert class="size-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <p class="text-xs text-label uppercase tracking-wide">{{ $t('aging.beyond_lifecycle') }}</p>
              <p class="text-2xl font-bold text-red-600 dark:text-red-400">{{ beyondCount.toLocaleString() }}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center shrink-0">
              <LucideTrendingUp class="size-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <p class="text-xs text-label uppercase tracking-wide">{{ $t('aging.risk_exposure') }}</p>
              <p class="text-2xl font-bold" :class="riskExposureColor(riskExposure)">
                {{ riskExposure.toFixed(1) }}%
              </p>
              <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
                <div
                  class="h-1.5 rounded-full transition-all"
                  :class="riskExposure >= 50 ? 'bg-red-500' : riskExposure >= 25 ? 'bg-amber-500' : 'bg-green-500'"
                  :style="{ width: `${Math.min(riskExposure, 100)}%` }"
                />
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center shrink-0">
              <LucideCalendarClock class="size-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p class="text-xs text-label uppercase tracking-wide">{{ $t('aging.forecasted_replacements') }}</p>
              <div class="flex items-baseline gap-3">
                <div>
                  <span class="text-2xl font-bold text-ink">{{ forecast12.toLocaleString() }}</span>
                  <span class="text-xs text-ink-muted ml-1">12mo</span>
                </div>
                <div class="text-ink-muted">/</div>
                <div>
                  <span class="text-xl font-semibold text-ink-muted">{{ forecast24.toLocaleString() }}</span>
                  <span class="text-xs text-ink-muted ml-1">24mo</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <!-- Risk Lists -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- Approaching Threshold Table -->
        <Card padding="none">
          <div class="p-4 border-b border-default">
            <h2 class="text-section-title flex items-center gap-2">
              <LucideAlertTriangle class="size-4 text-amber-500" />
              {{ $t('aging.approaching_threshold') }}
            </h2>
          </div>
          <div v-if="risk && risk.approaching_threshold.length > 0" class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-default bg-surface-secondary">
                  <th class="text-left px-4 py-2 text-label font-medium">{{ $t('aging.vehicle') }}</th>
                  <th class="text-right px-4 py-2 text-label font-medium">{{ $t('aging.age_yrs') }}</th>
                  <th class="text-right px-4 py-2 text-label font-medium">{{ $t('aging.threshold') }}</th>
                  <th class="text-center px-4 py-2 text-label font-medium">{{ $t('aging.status') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in risk.approaching_threshold"
                  :key="item.vehicle"
                  class="border-b border-default last:border-b-0 hover:bg-surface-secondary transition-colors"
                >
                  <td class="px-4 py-3 font-medium text-ink">{{ item.vehicle }}</td>
                  <td class="px-4 py-3 text-right text-ink">{{ item.age.toFixed(1) }}</td>
                  <td class="px-4 py-3 text-right text-ink-muted">{{ item.threshold }}</td>
                  <td class="px-4 py-3 text-center">
                    <Badge :variant="riskBadgeVariant(item.age, item.threshold)">
                      {{ item.age >= item.threshold ? $t('aging.at_threshold') : $t('aging.approaching') }}
                    </Badge>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyState
            v-else
            :icon="LucideAlertTriangle"
            :title="$t('aging.no_approaching')"
            :description="$t('aging.all_safe')"
          />
        </Card>

        <!-- Beyond Lifecycle Table -->
        <Card padding="none">
          <div class="p-4 border-b border-default">
            <h2 class="text-section-title flex items-center gap-2">
              <LucideShieldAlert class="size-4 text-red-500" />
              {{ $t('aging.beyond_optimal') }}
            </h2>
          </div>
          <div v-if="risk && risk.beyond_lifecycle.length > 0" class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-default bg-surface-secondary">
                  <th class="text-left px-4 py-2 text-label font-medium">{{ $t('aging.vehicle') }}</th>
                  <th class="text-right px-4 py-2 text-label font-medium">{{ $t('aging.age_yrs') }}</th>
                  <th class="text-center px-4 py-2 text-label font-medium">{{ $t('aging.risk') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in risk.beyond_lifecycle"
                  :key="item.vehicle"
                  class="border-b border-default last:border-b-0 hover:bg-surface-secondary transition-colors"
                >
                  <td class="px-4 py-3 font-medium text-ink">{{ item.vehicle }}</td>
                  <td class="px-4 py-3 text-right text-ink">{{ item.age.toFixed(1) }}</td>
                  <td class="px-4 py-3 text-center">
                    <Badge variant="danger">{{ $t('aging.beyond_lifecycle_badge') }}</Badge>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyState
            v-else
            :icon="LucideShieldAlert"
            :title="$t('aging.no_beyond')"
            :description="$t('aging.all_optimal')"
          />
        </Card>
      </div>
    </template>

    <!-- No data at all (not loading, no error, but data is null) -->
    <Card v-else-if="!isLoading && !hasError">
      <EmptyState
        :icon="LucideBarChart3"
        :title="$t('aging.no_aging_data')"
        :description="$t('aging.no_aging_desc')"
        :actionLabel="$t('aging.load_analysis')"
        @action="loadData"
      />
    </Card>
  </div>
</template>
