<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideClipboardList,
  LucideAlertCircle,
  LucideDollarSign,
  LucideFileText,
  LucideActivity,
  LucideCar,
  LucideGauge,
  LucidePackage,
  LucideClipboardCheck,
  LucideAlertTriangle,
  LucideUsers,
  LucideUserCog,
  LucideLibrary,
  LucideBarChart3,
  LucideStar,
  LucideBookmark,
  LucideCalendarClock,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Skeleton, EmptyState } from '@/components/ui'

interface KpiData {
  open_work_orders: number
  overdue_inspections: number
  total_expenses_30d: number
  outstanding_invoices: number
  fleet_utilization: number
}

interface TopCostVehicle {
  vehicle: string
  total_cost: number
}

interface RecurringFailure {
  item_name: string
  failure_count: number
}

interface WorstDowntime {
  vehicle: string
  wo_count: number
  total_days: number
}

interface OverdueReminder {
  name: string
  vehicle: string
  title: string
  next_due: string
}

interface InsightsData {
  top_cost_vehicles: TopCostVehicle[]
  recurring_failures: RecurringFailure[]
  worst_downtime: WorstDowntime[]
  overdue_reminders: OverdueReminder[]
}

interface ReportsHomeData {
  kpis: KpiData
  insights: InsightsData
  categories: string[]
}

interface PinnedReport {
  id: string
  title: string
  category: string
  report_type: string
  description: string
  module: string
}

const { t } = useI18n()

const isLoading = ref(true)
const data = ref<ReportsHomeData | null>(null)
const pinnedReports = ref<PinnedReport[]>([])

const categoryIconMap: Record<string, any> = {
  'Fleet Overview': LucideCar,
  'Utilization & Meter': LucideGauge,
  'Work Orders & Repairs': LucideClipboardList,
  'Parts & Inventory': LucidePackage,
  'Inspections': LucideClipboardCheck,
  'Issues & Faults': LucideAlertTriangle,
  'Financials': LucideDollarSign,
  'Customers': LucideUsers,
  'Employees': LucideUserCog,
}

const kpiCards = computed(() => {
  if (!data.value) return []
  const k = data.value.kpis
  return [
    {
      label: t('dashboard.open_work_orders'),
      value: k.open_work_orders,
      formatted: String(k.open_work_orders),
      icon: LucideClipboardList,
      route: '/repair-orders',
    },
    {
      label: t('dashboard.overdue_inspections'),
      value: k.overdue_inspections,
      formatted: String(k.overdue_inspections),
      icon: LucideAlertCircle,
      route: '/inspections/schedules',
    },
    {
      label: t('dashboard.total_expenses'),
      value: k.total_expenses_30d,
      formatted: k.total_expenses_30d.toLocaleString(undefined, { style: 'currency', currency: 'ETB' }),
      icon: LucideDollarSign,
      route: '',
    },
    {
      label: t('dashboard.outstanding_invoices'),
      value: k.outstanding_invoices,
      formatted: k.outstanding_invoices.toLocaleString(undefined, { style: 'currency', currency: 'ETB' }),
      icon: LucideFileText,
      route: '',
    },
    {
      label: t('dashboard.fleet_utilization'),
      value: k.fleet_utilization,
      formatted: `${k.fleet_utilization.toFixed(1)}%`,
      icon: LucideActivity,
      route: '',
    },
  ]
})

function formatDueDate(dateStr: string): string {
  if (!dateStr) return '—'
  const parts = dateStr.split('-')
  if (parts.length !== 3) return dateStr
  const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

async function loadData() {
  isLoading.value = true
  try {
    data.value = await apiCall<ReportsHomeData>(
      'car_repair_management.api.reports.get_reports_home'
    )
  } catch (e) {
    console.error('Failed to load reports home', e)
  } finally {
    isLoading.value = false
  }
}

async function loadPinned() {
  try {
    const res = await apiCall<{ reports: PinnedReport[] }>(
      'car_repair_management.api.reports.get_pinned_reports'
    )
    pinnedReports.value = res.reports
  } catch {
    // ignore
  }
}

onMounted(() => {
  loadData()
  loadPinned()
})
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-page-title text-ink">{{ $t('reports.title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted);">
          {{ $t('reports.subtitle') }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <RouterLink to="/reports/saved">
          <Button variant="ghost" size="sm">
            <LucideBookmark class="size-4" />
            {{ $t('reports.saved') }}
          </Button>
        </RouterLink>
        <RouterLink to="/reports/scheduled">
          <Button variant="ghost" size="sm">
            <LucideCalendarClock class="size-4" />
            {{ $t('reports.scheduled') }}
          </Button>
        </RouterLink>
        <RouterLink to="/reports/library">
          <Button variant="outline">
            <LucideLibrary class="size-4" />
            {{ $t('reports.library') }}
          </Button>
        </RouterLink>
      </div>
    </div>

    <!-- KPI Strip -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      <template v-if="isLoading">
        <Card v-for="i in 5" :key="i" class="animate-pulse">
          <Skeleton height="80px" />
        </Card>
      </template>
      <template v-else-if="data">
        <component
          :is="kpi.route ? RouterLink : 'div'"
          v-for="kpi in kpiCards"
          :key="kpi.label"
          :to="kpi.route || undefined"
        >
          <Card :hoverable="!!kpi.route" class="h-full">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-xs" style="color: var(--text-muted);">{{ kpi.label }}</p>
                <p class="text-2xl font-semibold mt-1" style="color: var(--text-primary);">
                  {{ kpi.formatted }}
                </p>
              </div>
              <div class="p-2 rounded-lg" style="background-color: var(--bg-tertiary);">
                <component :is="kpi.icon" class="size-5" style="color: var(--text-muted);" />
              </div>
            </div>
          </Card>
        </component>
      </template>
    </div>

    <!-- Pinned Reports -->
    <div v-if="pinnedReports.length">
      <h2 class="text-section-title text-ink mb-4">
        <LucideStar class="size-4 inline-block mr-1" style="color: var(--accent);" />
        Pinned Reports
      </h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <RouterLink
          v-for="pr in pinnedReports"
          :key="pr.id"
          :to="`/reports/view/${pr.id}`"
        >
          <Card hoverable class="h-full">
            <p class="text-sm font-medium truncate" style="color: var(--text-primary);">{{ pr.title }}</p>
            <p class="text-xs mt-1 truncate" style="color: var(--text-muted);">{{ pr.category }}</p>
          </Card>
        </RouterLink>
      </div>
    </div>

    <!-- Insight Tiles -->
    <div>
      <h2 class="text-section-title text-ink mb-4">Insights</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <template v-if="isLoading">
          <Card v-for="i in 4" :key="i" class="animate-pulse">
            <Skeleton height="160px" />
          </Card>
        </template>
        <template v-else-if="data">
          <!-- Top Cost Vehicles -->
          <Card>
            <h3 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">
              {{ $t('reports.top_cost_vehicles') }}
            </h3>
            <div v-if="data.insights.top_cost_vehicles.length" class="space-y-2">
              <div
                v-for="item in data.insights.top_cost_vehicles"
                :key="item.vehicle"
                class="flex items-center justify-between text-sm"
              >
                <span class="truncate" style="color: var(--text-secondary);">{{ item.vehicle }}</span>
                <span class="font-medium tabular-nums" style="color: var(--text-primary);">
                  {{ item.total_cost.toLocaleString(undefined, { style: 'currency', currency: 'ETB' }) }}
                </span>
              </div>
            </div>
            <p v-else class="text-sm" style="color: var(--text-muted);">{{ $t('reports.no_data') }}</p>
          </Card>

          <!-- Recurring Failures -->
          <Card>
            <h3 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">
              {{ $t('reports.recurring_failures') }}
            </h3>
            <div v-if="data.insights.recurring_failures.length" class="space-y-2">
              <div
                v-for="item in data.insights.recurring_failures"
                :key="item.item_name"
                class="flex items-center justify-between text-sm"
              >
                <span class="truncate" style="color: var(--text-secondary);">{{ item.item_name }}</span>
                <span class="font-medium tabular-nums" style="color: var(--text-primary);">
                  {{ item.failure_count }}
                </span>
              </div>
            </div>
            <p v-else class="text-sm" style="color: var(--text-muted);">{{ $t('reports.no_data') }}</p>
          </Card>

          <!-- Worst Downtime Vehicles -->
          <Card>
            <h3 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">
              {{ $t('reports.worst_downtime') }}
            </h3>
            <div v-if="data.insights.worst_downtime.length" class="space-y-2">
              <div
                v-for="item in data.insights.worst_downtime"
                :key="item.vehicle"
                class="flex items-center justify-between text-sm"
              >
                <span class="truncate" style="color: var(--text-secondary);">{{ item.vehicle }}</span>
                <span class="font-medium tabular-nums" style="color: var(--text-primary);">
                  {{ item.total_days }}d
                </span>
              </div>
            </div>
            <p v-else class="text-sm" style="color: var(--text-muted);">{{ $t('reports.no_data') }}</p>
          </Card>

          <!-- Overdue Service Reminders -->
          <Card>
            <h3 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">
              Overdue Service Reminders
            </h3>
            <div v-if="data.insights.overdue_reminders.length" class="space-y-2">
              <div
                v-for="item in data.insights.overdue_reminders"
                :key="item.name"
                class="text-sm"
              >
                <div class="flex items-center justify-between">
                  <span class="truncate font-medium" style="color: var(--text-secondary);">{{ item.vehicle }}</span>
                </div>
                <div class="flex items-center justify-between text-xs" style="color: var(--text-muted);">
                  <span>{{ item.title }}</span>
                  <span>{{ formatDueDate(item.next_due) }}</span>
                </div>
              </div>
            </div>
            <p v-else class="text-sm" style="color: var(--text-muted);">{{ $t('reports.no_data') }}</p>
          </Card>
        </template>
      </div>
    </div>

    <!-- Report Categories -->
    <div>
      <h2 class="text-section-title text-ink mb-4">Report Categories</h2>
      <template v-if="isLoading">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card v-for="i in 9" :key="i" class="animate-pulse">
            <Skeleton height="60px" />
          </Card>
        </div>
      </template>
      <template v-else-if="data && data.categories.length">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <RouterLink
            v-for="cat in data.categories"
            :key="cat"
            :to="`/reports/library?category=${encodeURIComponent(cat)}`"
          >
            <Card hoverable class="h-full">
              <div class="flex items-center gap-3">
                <div class="p-2.5 rounded-lg" style="background-color: var(--bg-tertiary);">
                  <component
                    :is="categoryIconMap[cat] || LucideBarChart3"
                    class="size-5"
                    style="color: var(--accent);"
                  />
                </div>
                <span class="text-sm font-medium" style="color: var(--text-primary);">{{ cat }}</span>
              </div>
            </Card>
          </RouterLink>
        </div>
      </template>
      <EmptyState
        v-else
        title="No report categories"
        description="Report categories will appear here once configured."
        :icon="LucideBarChart3"
      />
    </div>
  </div>
</template>
