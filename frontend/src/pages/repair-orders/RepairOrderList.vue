<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucidePlus,
  LucideFilter,
  LucideSearch,
  LucideEye,
  LucideRefreshCw,
  LucideClipboardList,
} from 'lucide-vue-next'
import { apiList, apiGetCount } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Tabs, ViewToggle } from '@/components/ui'
import { REPAIR_ORDER_STATUSES, type PaginationState } from '@/types'

type ViewMode = 'table' | 'card'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const STATUS_TABS = computed(() => [
  { id: 'all', label: t('repair_orders.all') },
  { id: 'Draft', label: t('repair_orders.draft') },
  { id: 'In Progress', label: t('repair_orders.in_progress') },
  { id: 'Awaiting Parts', label: t('repair_orders.awaiting_parts') },
  { id: 'Ready for Handover', label: t('repair_orders.ready') },
  { id: 'Delivered', label: t('repair_orders.delivered') },
  { id: 'Closed', label: t('repair_orders.closed') },
])

const orders = ref<any[]>([])
const isLoading = ref(true)
const searchQuery = ref('')
const activeTab = ref((route.query.status as string) || 'all')
const viewMode = ref<ViewMode>('table')
const pagination = ref<PaginationState>({
  page: 1,
  pageSize: 20,
  total: 0,
})

const filters = computed(() => {
  const f: Record<string, unknown> = {}
  if (activeTab.value !== 'all') {
    f.status = activeTab.value
  }
  return f
})

async function loadOrders() {
  isLoading.value = true
  try {
    const [data, count] = await Promise.all([
      apiList({
        doctype: 'Repair Order',
        fields: ['name', 'customer', 'vehicle', 'status', 'priority', 'problem_summary', 'modified', 'creation'],
        filters: Object.keys(filters.value).length ? filters.value : undefined,
        orderBy: 'modified desc',
        limitStart: (pagination.value.page - 1) * pagination.value.pageSize,
        limitPageLength: pagination.value.pageSize,
      }),
      apiGetCount('Repair Order', filters.value),
    ])
    orders.value = data
    pagination.value.total = count
  } catch (e) {
    console.error('Failed to load orders', e)
  } finally {
    isLoading.value = false
  }
}

function handleTabChange(tabId: string) {
  activeTab.value = tabId
  pagination.value.page = 1
  router.replace({
    query: tabId === 'all' ? {} : { status: tabId },
  })
}

function handlePageChange(newPage: number) {
  pagination.value.page = newPage
  loadOrders()
}

watch([activeTab], loadOrders)
onMounted(loadOrders)

const totalPages = computed(() => Math.ceil(pagination.value.total / pagination.value.pageSize))
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-page-title text-ink">{{ $t('repair_orders.title') }}</h1>
        <p class="text-sm text-ink-muted mt-1">
          {{ $t('repair_orders.subtitle') }}
        </p>
      </div>
      <div class="flex items-center gap-3">
        <Button variant="outline" @click="loadOrders">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
        <RouterLink to="/repair-orders/new">
          <Button variant="primary">
            <LucidePlus class="size-4" />
            {{ $t('repair_orders.new_order') }}
          </Button>
        </RouterLink>
      </div>
    </div>

    <!-- Tabs -->
    <Tabs :tabs="STATUS_TABS" :model-value="activeTab" @update:model-value="handleTabChange" />

    <!-- Search, Filters & View Toggle -->
    <div class="flex flex-col sm:flex-row gap-4">
      <div class="relative flex-1">
        <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-faint" />
        <input
          v-model="searchQuery"
          type="search"
          :placeholder="$t('repair_orders.search_placeholder')"
          class="w-full h-10 pl-10 pr-4 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
          style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
        />
      </div>
      <div class="flex items-center gap-2">
        <ViewToggle v-model="viewMode" />
        <Button variant="outline">
          <LucideFilter class="size-4" />
          {{ $t('common.filters') }}
        </Button>
      </div>
    </div>

    <!-- Table View -->
    <Card v-if="viewMode === 'table'" padding="none">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b" style="background-color: var(--bg-tertiary); border-color: var(--border-color);">
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('repair_orders.order') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('common.customer') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('common.vehicle') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('common.status') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('common.priority') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('common.modified') }}
              </th>
              <th class="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">
                {{ $t('common.actions') }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y" style="border-color: var(--border-color);">
            <!-- Loading -->
            <template v-if="isLoading">
              <tr v-for="i in 5" :key="i">
                <td class="px-4 py-4" colspan="7">
                  <Skeleton height="20px" />
                </td>
              </tr>
            </template>

            <!-- Empty -->
            <tr v-else-if="orders.length === 0">
              <td colspan="7" class="px-4 py-8">
                <EmptyState
                  :title="$t('repair_orders.no_orders')"
                  :description="$t('repair_orders.no_orders_desc')"
                  :action-label="$t('repair_orders.new_order')"
                  @action="router.push('/repair-orders/new')"
                />
              </td>
            </tr>

            <!-- Data -->
            <tr
              v-else
              v-for="order in orders"
              :key="order.name"
              class="transition-colors cursor-pointer hover:opacity-80"
              :style="{ backgroundColor: 'var(--bg-secondary)' }"
              @click="router.push(`/repair-orders/${order.name}`)"
            >
              <td class="px-4 py-4">
                <span class="text-sm font-medium" style="color: var(--text-primary);">
                  {{ order.name }}
                </span>
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-primary);">
                {{ order.customer }}
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-primary);">
                {{ order.vehicle }}
              </td>
              <td class="px-4 py-4">
                <Badge :variant="REPAIR_ORDER_STATUSES[order.status]?.variant || 'default'">
                  {{ order.status }}
                </Badge>
              </td>
              <td class="px-4 py-4">
                <Badge :variant="order.priority === 'Urgent' ? 'danger' : order.priority === 'High' ? 'warning' : 'default'" size="sm">
                  {{ order.priority }}
                </Badge>
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-muted);">
                {{ new Date(order.modified).toLocaleDateString() }}
              </td>
              <td class="px-4 py-4 text-right" @click.stop>
                <RouterLink :to="`/repair-orders/${order.name}`">
                  <Button variant="ghost" size="sm">
                    <LucideEye class="size-4" />
                  </Button>
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="!isLoading && orders.length > 0" class="flex items-center justify-between px-4 py-3 border-t" style="border-color: var(--border-color);">
        <p class="text-sm" style="color: var(--text-muted);">
          {{ $t('common.showing') }} {{ (pagination.page - 1) * pagination.pageSize + 1 }} to {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} {{ $t('common.of') }} {{ pagination.total }}
        </p>
        <div class="flex gap-2">
          <Button variant="outline" size="sm" :disabled="pagination.page === 1" @click="handlePageChange(pagination.page - 1)">
            {{ $t('common.previous') }}
          </Button>
          <Button variant="outline" size="sm" :disabled="pagination.page >= totalPages" @click="handlePageChange(pagination.page + 1)">
            {{ $t('common.next') }}
          </Button>
        </div>
      </div>
    </Card>

    <!-- Card View -->
    <template v-else-if="viewMode === 'card'">
      <!-- Loading -->
      <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card v-for="i in 6" :key="i"><Skeleton height="140px" /></Card>
      </div>

      <!-- Empty -->
      <Card v-else-if="orders.length === 0">
        <EmptyState
          :title="$t('repair_orders.no_orders')"
          :description="$t('repair_orders.no_orders_desc')"
          :action-label="$t('repair_orders.new_order')"
          @action="router.push('/repair-orders/new')"
        />
      </Card>

      <!-- Cards Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <RouterLink v-for="order in orders" :key="order.name" :to="`/repair-orders/${order.name}`">
          <Card hoverable class="h-full">
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center" style="background-color: var(--bg-tertiary);">
                  <LucideClipboardList class="size-5" style="color: var(--text-secondary);" />
                </div>
                <div>
                  <p class="text-sm font-medium" style="color: var(--text-primary);">{{ order.name }}</p>
                  <p class="text-xs" style="color: var(--text-muted);">{{ new Date(order.modified).toLocaleDateString() }}</p>
                </div>
              </div>
              <Badge :variant="REPAIR_ORDER_STATUSES[order.status]?.variant || 'default'" size="sm">
                {{ order.status }}
              </Badge>
            </div>
            
            <div class="space-y-2">
              <div class="flex items-center justify-between text-sm">
                <span style="color: var(--text-muted);">{{ $t('common.customer') }}</span>
                <span style="color: var(--text-primary);">{{ order.customer }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span style="color: var(--text-muted);">{{ $t('common.vehicle') }}</span>
                <span style="color: var(--text-primary);">{{ order.vehicle }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span style="color: var(--text-muted);">{{ $t('common.priority') }}</span>
                <Badge :variant="order.priority === 'Urgent' ? 'danger' : order.priority === 'High' ? 'warning' : 'default'" size="sm">
                  {{ order.priority }}
                </Badge>
              </div>
            </div>

            <p v-if="order.problem_summary" class="mt-3 text-xs line-clamp-2" style="color: var(--text-muted);">
              {{ order.problem_summary }}
            </p>
          </Card>
        </RouterLink>
      </div>

      <!-- Pagination for Card View -->
      <div v-if="!isLoading && orders.length > 0" class="flex items-center justify-between">
        <p class="text-sm" style="color: var(--text-muted);">
          {{ $t('common.showing') }} {{ (pagination.page - 1) * pagination.pageSize + 1 }} to {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} {{ $t('common.of') }} {{ pagination.total }}
        </p>
        <div class="flex gap-2">
          <Button variant="outline" size="sm" :disabled="pagination.page === 1" @click="handlePageChange(pagination.page - 1)">
            {{ $t('common.previous') }}
          </Button>
          <Button variant="outline" size="sm" :disabled="pagination.page >= totalPages" @click="handlePageChange(pagination.page + 1)">
            {{ $t('common.next') }}
          </Button>
        </div>
      </div>
    </template>
  </div>
</template>
