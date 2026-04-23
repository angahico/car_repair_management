<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucidePackage,
  LucideRefreshCw,
  LucideDownload,
  LucideToggleLeft,
  LucideToggleRight,
  LucidePlus,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, EmptyState, Skeleton, Badge } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface PartRecord {
  name: string
  item_code: string
  item_name: string
  item_group: string | null
  stock_uom: string
  current_qty: number
  reorder_level: number
  stock_status: string
  standard_rate: number
  modified: string
}

interface PartKPIs {
  total_items: number
  in_stock: number
  low_stock: number
  out_of_stock: number
}

interface PartListData {
  kpis: PartKPIs
  records: PartRecord[]
  total: number
}

const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const records = ref<PartRecord[]>([])
const kpis = ref<PartKPIs>({
  total_items: 0,
  in_stock: 0,
  low_stock: 0,
  out_of_stock: 0,
})
const total = ref(0)
const page = ref(0)
const pageSize = 20

const searchQuery = ref('')
const itemGroupFilter = ref('')
const stockStatusFilter = ref<string | null>(null)
const isStockItem = ref(false)

const STOCK_STATUS_OPTIONS = ['In Stock', 'Low', 'Out of Stock']

const STOCK_STATUS_VARIANTS: Record<string, StatusVariant> = {
  'In Stock': 'success',
  Low: 'warning',
  'Out of Stock': 'danger',
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const hasPrev = computed(() => page.value > 0)
const hasNext = computed(() => (page.value + 1) * pageSize < total.value)

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—'
  const [datePart, timePart] = dateStr.split(' ')
  const parts = datePart.split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    const formatted = d.toLocaleDateString()
    return timePart ? `${formatted} ${timePart.substring(0, 5)}` : formatted
  }
  return dateStr
}

function formatCurrency(value: number): string {
  return 'ETB ' + (value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00')
}

function setStockStatusFilter(val: string | null) {
  stockStatusFilter.value = val
  page.value = 0
  loadData()
}

function toggleIsStockItem() {
  isStockItem.value = !isStockItem.value
  page.value = 0
  loadData()
}

function prevPage() {
  if (hasPrev.value) {
    page.value--
    loadData()
  }
}

function nextPage() {
  if (hasNext.value) {
    page.value++
    loadData()
  }
}

function openDetail(record: PartRecord) {
  router.push(`/parts/${record.name}`)
}

function addItem() {
  window.open('/app/item/new', '_blank')
}

async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: page.value * pageSize,
      limit_page_length: pageSize,
    }
    if (searchQuery.value) args.search = searchQuery.value
    if (itemGroupFilter.value) args.item_group = itemGroupFilter.value
    if (stockStatusFilter.value) args.stock_status = stockStatusFilter.value
    if (isStockItem.value) args.is_stock_item = 1

    const data = await apiCall<PartListData>(
      'car_repair_management.api.parts.get_parts',
      args,
    )
    kpis.value = data.kpis
    records.value = data.records
    total.value = data.total
  } catch (e) {
    console.warn('Failed to load parts', e)
  } finally {
    isLoading.value = false
  }
}

function exportCSV() {
  const headers = [
    'Item Code', 'Item Name', 'Item Group', 'Stock UOM',
    'Current Qty', 'Reorder Level', 'Stock Status', 'Standard Rate', 'Last Updated',
  ]
  const rows = records.value.map((r) => [
    r.item_code,
    r.item_name,
    r.item_group || '',
    r.stock_uom,
    r.current_qty,
    r.reorder_level,
    r.stock_status,
    r.standard_rate,
    r.modified || '',
  ])
  const csv = [headers, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `parts_inventory_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-page-title">{{ $t('parts.title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">
          {{ $t('common.items_found', { count: total }) }}
        </p>
      </div>
      <Button variant="primary" @click="addItem">
        <LucidePlus class="size-4" />
        {{ $t('parts.add_item') }}
      </Button>
    </div>

    <!-- Control Bar -->
    <Card>
      <!-- Row 1: Search + Item Group + Stock Status -->
      <div class="flex flex-wrap items-end gap-3 pb-4 border-b" style="border-color: var(--border-subtle)">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('common.search') }}</label>
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="$t('parts.search_placeholder')"
            class="w-full h-9 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @keyup.enter="() => { page = 0; loadData() }"
          />
        </div>
        <div class="min-w-[160px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('parts.item_group') }}</label>
          <input
            v-model="itemGroupFilter"
            type="text"
            placeholder="Filter by group..."
            class="w-full h-9 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @keyup.enter="() => { page = 0; loadData() }"
          />
        </div>
        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('parts.stock') }}:</span>
          <Button
            :variant="stockStatusFilter === null ? 'secondary' : 'ghost'"
            size="sm"
            @click="setStockStatusFilter(null)"
          >
            {{ $t('common.all') }}
          </Button>
          <Button
            v-for="opt in STOCK_STATUS_OPTIONS"
            :key="opt"
            :variant="stockStatusFilter === opt ? 'secondary' : 'ghost'"
            size="sm"
            @click="setStockStatusFilter(opt)"
          >
            {{ opt }}
          </Button>
        </div>
      </div>

      <!-- Row 2: Toggle + Actions -->
      <div class="flex flex-wrap items-center gap-3 pt-4">
        <!-- Is Stock Item Toggle -->
        <button
          class="flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded"
          :style="{
            color: isStockItem ? 'var(--accent)' : 'var(--text-muted)',
            background: isStockItem ? 'var(--bg-tertiary)' : 'transparent',
          }"
          @click="toggleIsStockItem"
        >
          <component :is="isStockItem ? LucideToggleRight : LucideToggleLeft" class="size-4" />
          {{ $t('parts.is_stock_item') }}
        </button>

        <div class="flex-1" />

        <!-- Export + Refresh -->
        <Button variant="outline" size="sm" @click="exportCSV">
          <LucideDownload class="size-3.5" />
          {{ $t('common.export_csv') }}
        </Button>
        <Button variant="ghost" size="sm" @click="loadData">
          <LucideRefreshCw class="size-3.5" />
        </Button>
      </div>
    </Card>

    <!-- KPI Row -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.total_items') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ kpis.total_items }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.in_stock') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ kpis.in_stock }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.low_stock') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p
          v-else
          class="text-2xl font-bold mt-1"
          :style="{ color: kpis.low_stock > 0 ? '#f59e0b' : 'var(--text-primary)' }"
        >
          {{ kpis.low_stock }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.out_of_stock') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p
          v-else
          class="text-2xl font-bold mt-1"
          :style="{ color: kpis.out_of_stock > 0 ? '#ef4444' : 'var(--text-primary)' }"
        >
          {{ kpis.out_of_stock }}
        </p>
      </Card>
    </div>

    <!-- Data Table -->
    <Card padding="none">
      <div v-if="isLoading" class="p-4 space-y-3">
        <Skeleton v-for="i in 8" :key="i" height="48px" />
      </div>

      <EmptyState
        v-else-if="records.length === 0"
        :icon="LucidePackage"
        :title="$t('parts.no_items')"
        :description="$t('parts.no_items_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm" style="color: var(--text-primary)">
          <thead>
            <tr class="border-b" style="border-color: var(--border-subtle)">
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.item_code') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.item_name') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.item_group') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.stock_uom') }}</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.current_qty') }}</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.reorder_level') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.stock_status') }}</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('parts.standard_rate') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.last_updated') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in records"
              :key="r.name"
              class="border-b cursor-pointer transition-colors"
              style="border-color: var(--border-subtle)"
              @click="openDetail(r)"
              @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
            >
              <td class="px-4 py-3 font-medium whitespace-nowrap">{{ r.item_code }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.item_name }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.item_group || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.stock_uom }}</td>
              <td class="px-4 py-3 text-right">{{ r.current_qty }}</td>
              <td class="px-4 py-3 text-right">{{ r.reorder_level }}</td>
              <td class="px-4 py-3">
                <Badge :variant="STOCK_STATUS_VARIANTS[r.stock_status] || 'default'">
                  {{ r.stock_status }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right whitespace-nowrap">{{ formatCurrency(r.standard_rate) }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ formatDateTime(r.modified) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div
        v-if="!isLoading && records.length > 0"
        class="flex items-center justify-between px-4 py-3 border-t"
        style="border-color: var(--border-subtle)"
      >
        <p class="text-xs" style="color: var(--text-muted)">
          {{ $t('common.showing') }} {{ page * pageSize + 1 }}–{{ Math.min((page + 1) * pageSize, total) }} {{ $t('common.of') }} {{ total }}
        </p>
        <div class="flex items-center gap-2">
          <Button variant="outline" size="sm" :disabled="!hasPrev" @click="prevPage">{{ $t('common.prev') }}</Button>
          <span class="text-xs" style="color: var(--text-muted)">
            {{ $t('common.page') }} {{ page + 1 }} {{ $t('common.of') }} {{ totalPages }}
          </span>
          <Button variant="outline" size="sm" :disabled="!hasNext" @click="nextPage">{{ $t('common.next') }}</Button>
        </div>
      </div>
    </Card>
  </div>
</template>
