<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import {
  LucideClipboardList,
  LucideWrench,
  LucideClock,
  LucideCheckCircle,
  LucidePlus,
  LucideCar,
  LucidePackage,
  LucideFileText,
  LucideClipboardCheck,
  LucideAlertCircle,
  LucideBarChart3,
  LucideUsers,
  LucideArrowRight,
  LucideTrendingUp,
  LucideLoader2,
} from 'lucide-vue-next'
import { apiGetCount, apiList } from '@/api'
import { Card, Skeleton, Badge, Button } from '@/components/ui'
import { REPAIR_ORDER_STATUSES } from '@/types'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// ─── State ────────────────────────────────────────────────────────────────
const isLoading = ref(true)

// KPI counts
const counts = ref({
  totalOrders: 0,
  inProgress: 0,
  awaitingParts: 0,
  readyForHandover: 0,
  outstandingInvoices: 0,
  overdueInspections: 0,
})

// Status breakdown
const statusBreakdown = ref<{ status: string; count: number; color: string }[]>([])

// Recent orders
const recentOrders = ref<any[]>([])

// Fleet
const fleetCounts = ref({ total: 0, inService: 0 })

// ─── Status colour palette ─────────────────────────────────────────────────
const STATUS_COLORS: Record<string, string> = {
  'Draft':              '#94a3b8',
  'Scheduled':          '#3b82f6',
  'In Progress':        '#8b5cf6',
  'Awaiting Parts':     '#f59e0b',
  'Ready for Handover': '#10b981',
  'Delivered':          '#06b6d4',
  'Closed':             '#6b7280',
  'On Hold':            '#f97316',
  'Cancelled':          '#ef4444',
}

const ALL_STATUSES = [
  'Draft', 'Scheduled', 'In Progress', 'Awaiting Parts',
  'Ready for Handover', 'Delivered', 'Closed', 'On Hold', 'Cancelled',
]

// ─── Data loading ──────────────────────────────────────────────────────────
async function loadDashboard() {
  isLoading.value = true

  try {
    const [
      total,
      inProgress,
      awaitingParts,
      readyForHandover,
      scheduled,
      draft,
      delivered,
      closed,
      onHold,
      cancelled,
      vehicles,
      vehiclesInService,
    ] = await Promise.all([
      apiGetCount('Repair Order'),
      apiGetCount('Repair Order', { status: 'In Progress' }),
      apiGetCount('Repair Order', { status: 'Awaiting Parts' }),
      apiGetCount('Repair Order', { status: 'Ready for Handover' }),
      apiGetCount('Repair Order', { status: 'Scheduled' }),
      apiGetCount('Repair Order', { status: 'Draft' }),
      apiGetCount('Repair Order', { status: 'Delivered' }),
      apiGetCount('Repair Order', { status: 'Closed' }),
      apiGetCount('Repair Order', { status: 'On Hold' }),
      apiGetCount('Repair Order', { status: 'Cancelled' }),
      apiGetCount('Vehicle'),
      apiGetCount('Repair Order', { status: ['in', ['Scheduled', 'In Progress', 'Awaiting Parts', 'Ready for Handover']] }),
    ])

    counts.value = {
      totalOrders: total,
      inProgress,
      awaitingParts,
      readyForHandover,
      // These APIs may not exist — fall back to 0 gracefully
      outstandingInvoices: 0,
      overdueInspections: 0,
    }

    // Try to get invoice and inspection counts (non-critical)
    try {
      const [invoiceCount, inspectionCount] = await Promise.all([
        apiGetCount('Sales Invoice', { outstanding_amount: ['>', 0], docstatus: 1 }),
        apiGetCount('Vehicle Inspection', { result: 'Fail' }),
      ])
      counts.value.outstandingInvoices = invoiceCount
      counts.value.overdueInspections = inspectionCount
    } catch {
      // silently ignore
    }

    fleetCounts.value = { total: vehicles, inService: vehiclesInService }

    const rawBreakdown = [
      { status: 'Draft',              count: draft },
      { status: 'Scheduled',          count: scheduled },
      { status: 'In Progress',        count: inProgress },
      { status: 'Awaiting Parts',     count: awaitingParts },
      { status: 'Ready for Handover', count: readyForHandover },
      { status: 'Delivered',          count: delivered },
      { status: 'Closed',             count: closed },
      { status: 'On Hold',            count: onHold },
      { status: 'Cancelled',          count: cancelled },
    ]
    statusBreakdown.value = rawBreakdown
      .filter(s => s.count > 0)
      .map(s => ({ ...s, color: STATUS_COLORS[s.status] || '#94a3b8' }))

    recentOrders.value = await apiList({
      doctype: 'Repair Order',
      fields: ['name', 'customer', 'vehicle', 'status', 'priority', 'modified'],
      orderBy: 'modified desc',
      limitPageLength: 10,
    })
  } catch (e) {
    console.error('Failed to load dashboard', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(loadDashboard)

// ─── KPI card definitions ─────────────────────────────────────────────────
const kpiCards = computed(() => [
  {
    label: t('dashboard.total_orders'),
    value: counts.value.totalOrders,
    icon: LucideClipboardList,
    iconBg: 'rgba(99,102,241,0.12)',
    iconColor: '#6366f1',
    route: '/repair-orders',
  },
  {
    label: t('dashboard.in_progress'),
    value: counts.value.inProgress,
    icon: LucideWrench,
    iconBg: 'rgba(139,92,246,0.12)',
    iconColor: '#8b5cf6',
    route: '/repair-orders',
  },
  {
    label: t('dashboard.awaiting_parts'),
    value: counts.value.awaitingParts,
    icon: LucidePackage,
    iconBg: 'rgba(245,158,11,0.12)',
    iconColor: '#f59e0b',
    route: '/repair-orders',
  },
  {
    label: t('dashboard.ready_for_handover'),
    value: counts.value.readyForHandover,
    icon: LucideCheckCircle,
    iconBg: 'rgba(16,185,129,0.12)',
    iconColor: '#10b981',
    route: '/repair-orders',
  },
  {
    label: t('dashboard.outstanding_invoices'),
    value: counts.value.outstandingInvoices,
    icon: LucideFileText,
    iconBg: 'rgba(239,68,68,0.12)',
    iconColor: '#ef4444',
    route: '/invoices',
  },
  {
    label: t('dashboard.overdue_inspections'),
    value: counts.value.overdueInspections,
    icon: LucideClipboardCheck,
    iconBg: 'rgba(249,115,22,0.12)',
    iconColor: '#f97316',
    route: '/inspections',
  },
])

// ─── Status bar max for percentage ───────────────────────────────────────
const maxStatusCount = computed(() =>
  Math.max(1, ...statusBreakdown.value.map(s => s.count))
)

// ─── Quick actions ────────────────────────────────────────────────────────
const quickActions = [
  { label: 'New Repair Order', route: '/repair-orders/new', icon: LucideClipboardList, color: '#6366f1' },
  { label: 'New Vehicle',      route: '/vehicles/new',      icon: LucideCar,          color: '#0ea5e9' },
  { label: 'Customers',        route: '/customers',         icon: LucideUsers,        color: '#10b981' },
  { label: 'Reports',          route: '/reports',           icon: LucideBarChart3,    color: '#f59e0b' },
]

// ─── Priority badge colour ─────────────────────────────────────────────────
function priorityColor(p: string): string {
  const map: Record<string, string> = {
    Urgent: '#ef4444',
    High:   '#f59e0b',
    Normal: '#6366f1',
    Low:    '#94a3b8',
  }
  return map[p] || '#94a3b8'
}

// ─── Time helper ──────────────────────────────────────────────────────────
function timeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
</script>

<template>
  <div class="space-y-6">

    <!-- ── Header ────────────────────────────────────────────────────── -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-page-title text-ink">{{ $t('dashboard.title') }}</h1>
        <p class="text-sm text-ink-muted mt-1">{{ $t('dashboard.subtitle') }}</p>
      </div>
      <RouterLink to="/repair-orders/new">
        <Button variant="primary">
          <LucidePlus class="size-4" />
          {{ $t('dashboard.new_repair_order') }}
        </Button>
      </RouterLink>
    </div>

    <!-- ── KPI Cards (6) ──────────────────────────────────────────────── -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      <template v-if="isLoading">
        <Card v-for="i in 6" :key="i" class="animate-pulse">
          <Skeleton height="72px" />
        </Card>
      </template>
      <template v-else>
        <RouterLink
          v-for="kpi in kpiCards"
          :key="kpi.label"
          :to="kpi.route"
          class="block"
        >
          <Card hoverable class="group h-full">
            <div class="flex flex-col gap-2">
              <div
                class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                :style="{ backgroundColor: kpi.iconBg }"
              >
                <component :is="kpi.icon" class="size-5" :style="{ color: kpi.iconColor }" />
              </div>
              <div>
                <p class="text-2xl font-bold text-ink leading-none">{{ kpi.value }}</p>
                <p class="text-xs text-ink-muted mt-1 leading-snug">{{ kpi.label }}</p>
              </div>
            </div>
          </Card>
        </RouterLink>
      </template>
    </div>

    <!-- ── Middle row: Status Breakdown + Quick Actions ───────────────── -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Status Breakdown (2/3 width) -->
      <Card class="lg:col-span-2">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-section-title text-ink flex items-center gap-2">
            <LucideTrendingUp class="size-4" style="color: var(--text-muted);" />
            Work Order Status Breakdown
          </h2>
          <RouterLink
            to="/repair-orders"
            class="flex items-center gap-1 text-xs hover:opacity-70 transition-opacity"
            style="color: var(--accent, #6366f1);"
          >
            View all <LucideArrowRight class="size-3" />
          </RouterLink>
        </div>

        <div v-if="isLoading" class="space-y-3">
          <Skeleton v-for="i in 5" :key="i" height="32px" />
        </div>
        <div v-else-if="statusBreakdown.length === 0" class="py-6 text-center text-sm text-ink-muted">
          No repair orders yet
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="item in statusBreakdown"
            :key="item.status"
            class="flex items-center gap-3"
          >
            <span class="text-xs text-ink-muted w-32 flex-shrink-0 truncate">{{ item.status }}</span>
            <div
              class="flex-1 h-5 rounded-full overflow-hidden"
              style="background-color: var(--bg-tertiary);"
            >
              <div
                class="h-full rounded-full transition-all duration-500"
                :style="{
                  width: `${Math.round((item.count / maxStatusCount) * 100)}%`,
                  backgroundColor: item.color,
                  opacity: 0.85,
                }"
              />
            </div>
            <span
              class="text-xs font-semibold w-6 text-right flex-shrink-0"
              :style="{ color: item.color }"
            >{{ item.count }}</span>
          </div>
        </div>
      </Card>

      <!-- Quick Actions + Fleet Summary (1/3 width) -->
      <div class="space-y-4">
        <!-- Quick Actions -->
        <Card>
          <h2 class="text-section-title text-ink mb-3">Quick Actions</h2>
          <div class="grid grid-cols-2 gap-2">
            <RouterLink
              v-for="action in quickActions"
              :key="action.label"
              :to="action.route"
              class="flex flex-col items-center gap-2 py-3 px-2 rounded-lg text-center transition-all hover:opacity-80 active:scale-95"
              style="background-color: var(--bg-tertiary);"
            >
              <div
                class="w-8 h-8 rounded-lg flex items-center justify-center"
                :style="{ backgroundColor: action.color + '20' }"
              >
                <component :is="action.icon" class="size-4" :style="{ color: action.color }" />
              </div>
              <span class="text-[11px] font-medium leading-tight" style="color: var(--text-secondary);">
                {{ action.label }}
              </span>
            </RouterLink>
          </div>
        </Card>

        <!-- Fleet Summary -->
        <Card>
          <h2 class="text-section-title text-ink mb-3 flex items-center gap-2">
            <LucideCar class="size-4" style="color: var(--text-muted);" />
            Fleet Summary
          </h2>
          <div v-if="isLoading">
            <Skeleton height="60px" />
          </div>
          <div v-else class="space-y-3">
            <RouterLink to="/vehicles" class="flex items-center justify-between group">
              <span class="text-sm text-ink-muted">Total Vehicles</span>
              <span class="text-lg font-bold text-ink group-hover:opacity-70 transition-opacity">
                {{ fleetCounts.total }}
              </span>
            </RouterLink>
            <div class="h-px" style="background-color: var(--border-color);" />
            <div class="flex items-center justify-between">
              <span class="text-sm text-ink-muted">Currently in Service</span>
              <span
                class="text-sm font-semibold px-2 py-0.5 rounded-full"
                style="background-color: rgba(16,185,129,0.12); color: #10b981;"
              >
                {{ fleetCounts.inService }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-ink-muted">Available</span>
              <span
                class="text-sm font-semibold px-2 py-0.5 rounded-full"
                style="background-color: rgba(99,102,241,0.12); color: #6366f1;"
              >
                {{ Math.max(0, fleetCounts.total - fleetCounts.inService) }}
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>

    <!-- ── Recent Repair Orders ───────────────────────────────────────── -->
    <Card>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-section-title text-ink">{{ $t('dashboard.recent_repair_orders') }}</h2>
        <RouterLink
          to="/repair-orders"
          class="flex items-center gap-1 text-xs hover:opacity-70 transition-opacity"
          style="color: var(--accent, #6366f1);"
        >
          {{ $t('common.view_all') }} <LucideArrowRight class="size-3" />
        </RouterLink>
      </div>

      <div v-if="isLoading" class="space-y-3">
        <Skeleton v-for="i in 5" :key="i" height="52px" />
      </div>

      <div v-else-if="recentOrders.length === 0" class="py-8 text-center text-ink-muted">
        {{ $t('dashboard.no_repair_orders') }}
      </div>

      <div v-else class="divide-y divide-border-light dark:divide-border-dark">
        <RouterLink
          v-for="order in recentOrders"
          :key="order.name"
          :to="`/repair-orders/${order.name}`"
          class="flex items-center justify-between py-3 hover:opacity-80 -mx-4 px-4 transition-opacity"
        >
          <!-- Left: icon + info -->
          <div class="flex items-center gap-3 min-w-0">
            <div
              class="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center"
              style="background-color: rgba(99,102,241,0.1);"
            >
              <LucideClipboardList class="size-4" style="color: #6366f1;" />
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-ink truncate">{{ order.name }}</p>
              <p class="text-xs text-ink-muted truncate">
                {{ order.customer }}
                <span v-if="order.vehicle"> · {{ order.vehicle }}</span>
              </p>
            </div>
          </div>

          <!-- Right: priority dot + status badge + time -->
          <div class="flex items-center gap-2 flex-shrink-0 ml-3">
            <span
              v-if="order.priority && order.priority !== 'Normal'"
              class="w-2 h-2 rounded-full flex-shrink-0"
              :style="{ backgroundColor: priorityColor(order.priority) }"
              :title="order.priority"
            />
            <Badge :variant="REPAIR_ORDER_STATUSES[order.status]?.variant || 'default'">
              {{ order.status }}
            </Badge>
            <span class="text-xs text-ink-muted hidden sm:block whitespace-nowrap">
              {{ timeAgo(order.modified) }}
            </span>
          </div>
        </RouterLink>
      </div>
    </Card>

  </div>
</template>
