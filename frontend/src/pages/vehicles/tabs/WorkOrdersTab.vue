<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import {
  LucideWrench,
  LucidePlus,
  LucideFilter,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'

const props = defineProps<{ vehicleId: string }>()

const isLoading = ref(true)
const workOrdersData = ref<any>(null)
const activeFilter = ref<string | null>(null)

const filters = [
  { id: 'open', label: 'Open', color: 'bg-blue-500' },
  { id: 'in_progress', label: 'In Progress', color: 'bg-amber-500' },
  { id: 'completed', label: 'Completed', color: 'bg-green-500' },
  { id: 'emergency', label: 'Emergency', color: 'bg-red-500' },
  { id: 'over_budget', label: 'Over Budget', color: 'bg-purple-500' },
]

const statusColors: Record<string, string> = {
  'Open': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  'In Progress': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  'Completed': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  'Closed': 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
  'Delivered': 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  'Cancelled': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

async function loadWorkOrders() {
  isLoading.value = true
  try {
    workOrdersData.value = await apiCall('car_repair_management.api.vehicle.get_vehicle_work_orders_full', {
      vehicle_name: props.vehicleId,
      status_filter: activeFilter.value,
    })
  } catch (e) {
    console.error('Failed to load work orders', e)
  } finally {
    isLoading.value = false
  }
}

function setFilter(filterId: string | null) {
  activeFilter.value = activeFilter.value === filterId ? null : filterId
  loadWorkOrders()
}

function formatCurrency(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'ETB', maximumFractionDigits: 0 }).format(value)
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString()
}

onMounted(loadWorkOrders)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <template v-if="isLoading">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card v-for="i in 4" :key="i"><Skeleton height="80px" /></Card>
      </div>
      <Card><Skeleton height="300px" /></Card>
    </template>

    <template v-else-if="workOrdersData">
      <!-- Inline Metrics -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Open Orders</p>
          <p class="text-3xl font-bold" style="color: var(--text-primary);">
            {{ workOrdersData.metrics?.open_count || 0 }}
          </p>
        </Card>
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Completed</p>
          <p class="text-3xl font-bold text-green-600">
            {{ workOrdersData.metrics?.completed_count || 0 }}
          </p>
        </Card>
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Avg Resolution</p>
          <p class="text-3xl font-bold" style="color: var(--text-primary);">
            {{ workOrdersData.metrics?.avg_resolution_days || 0 }}
            <span class="text-sm font-normal" style="color: var(--text-muted);">days</span>
          </p>
        </Card>
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Total Cost</p>
          <p class="text-xl font-bold" style="color: var(--text-primary);">
            {{ formatCurrency(workOrdersData.metrics?.total_cost) }}
          </p>
        </Card>
      </div>

      <!-- Header with Actions -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <!-- Quick Filters -->
        <div class="flex flex-wrap items-center gap-2">
          <LucideFilter class="size-4" style="color: var(--text-muted);" />
          <button
            v-for="filter in filters"
            :key="filter.id"
            @click="setFilter(filter.id)"
            :class="[
              'px-3 py-1.5 text-xs font-medium rounded-full transition-colors',
              activeFilter === filter.id
                ? 'text-white ' + filter.color
                : 'hover:opacity-80'
            ]"
            :style="activeFilter !== filter.id ? {
              backgroundColor: 'var(--bg-tertiary)',
              color: 'var(--text-secondary)'
            } : {}"
          >
            {{ filter.label }}
          </button>
          <button
            v-if="activeFilter"
            @click="setFilter(null)"
            class="px-2 py-1 text-xs"
            style="color: var(--text-muted);"
          >
            Clear
          </button>
        </div>

        <!-- Primary Action -->
        <RouterLink to="/repair-orders/new">
          <Button>
            <LucidePlus class="size-4" />
            Create Work Order
          </Button>
        </RouterLink>
      </div>

      <!-- Work Orders Table -->
      <Card padding="none">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Work Order</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Status</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Priority</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Opened</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Closed</th>
                <th class="text-right px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Cost</th>
                <th class="text-right px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Downtime</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="wo in workOrdersData.items"
                :key="wo.name"
                class="border-b cursor-pointer transition-colors hover:opacity-80"
                style="border-color: var(--border-subtle);"
                @click="$router.push(`/repair-orders/${wo.name}`)"
              >
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <LucideWrench class="size-4" style="color: var(--text-muted);" />
                    <div>
                      <p class="text-sm font-medium" style="color: var(--text-primary);">{{ wo.name }}</p>
                      <p class="text-xs truncate max-w-xs" style="color: var(--text-muted);">{{ wo.problem_summary }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span :class="['px-2 py-1 rounded-full text-xs font-medium', statusColors[wo.status] || statusColors['Open']]">
                    {{ wo.status }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <Badge
                    :variant="wo.priority === 'High' ? 'danger' : wo.priority === 'Medium' ? 'warning' : 'default'"
                    size="sm"
                  >
                    {{ wo.priority || 'Normal' }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-sm" style="color: var(--text-secondary);">
                  {{ formatDate(wo.creation) }}
                </td>
                <td class="px-4 py-3 text-sm" style="color: var(--text-secondary);">
                  {{ wo.status === 'Closed' || wo.status === 'Delivered' ? formatDate(wo.modified) : '—' }}
                </td>
                <td class="px-4 py-3 text-sm text-right font-medium" style="color: var(--text-primary);">
                  {{ formatCurrency(wo.total_job_cost) }}
                </td>
                <td class="px-4 py-3 text-sm text-right" style="color: var(--text-muted);">
                  {{ wo.downtime_days || 0 }} days
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Empty State -->
        <div v-if="!workOrdersData.items?.length" class="text-center py-12">
          <LucideWrench class="size-12 mx-auto mb-4" style="color: var(--text-muted);" />
          <h3 class="text-lg font-semibold mb-2" style="color: var(--text-primary);">No Work Orders</h3>
          <p class="text-sm mb-4" style="color: var(--text-muted);">
            {{ activeFilter ? 'No work orders match the selected filter.' : 'This vehicle has no work orders yet.' }}
          </p>
          <RouterLink to="/repair-orders/new">
            <Button>
              <LucidePlus class="size-4" />
              Create Work Order
            </Button>
          </RouterLink>
        </div>
      </Card>

      <!-- Pagination Info -->
      <div v-if="workOrdersData.total > 0" class="text-center text-sm" style="color: var(--text-muted);">
        Showing {{ workOrdersData.items?.length || 0 }} of {{ workOrdersData.total }} work orders
      </div>
    </template>
  </div>
</template>
