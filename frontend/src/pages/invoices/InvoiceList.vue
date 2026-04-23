<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideFileText,
  LucideRefreshCw,
  LucideDownload,
  LucidePlus,
  LucideChevronDown,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, EmptyState, Skeleton, Badge } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface InvoiceRecord {
  name: string
  invoice_type: string
  posting_date: string | null
  party: string
  grand_total: number
  outstanding_amount: number
  status: string
  due_date: string | null
  owner: string
  creation: string | null
  modified: string | null
}

interface InvoiceKPIs {
  total_invoiced: number
  total_paid: number
  outstanding: number
  overdue_count: number
}

interface InvoiceListData {
  kpis: InvoiceKPIs
  records: InvoiceRecord[]
  total: number
}

const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const records = ref<InvoiceRecord[]>([])
const kpis = ref<InvoiceKPIs>({
  total_invoiced: 0,
  total_paid: 0,
  outstanding: 0,
  overdue_count: 0,
})
const total = ref(0)
const page = ref(0)
const pageSize = 20

const showCreateDropdown = ref(false)

function onClickOutsideCreate(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.create-dropdown-wrapper')) {
    showCreateDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutsideCreate)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutsideCreate)
})

const searchQuery = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const typeFilter = ref<string | null>(null)
const statusFilter = ref<string | null>(null)

const TYPE_OPTIONS = ['Sales', 'Purchase']
const STATUS_OPTIONS = ['Draft', 'Unpaid', 'Paid', 'Overdue', 'Cancelled']

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Draft: 'default',
  Unpaid: 'danger',
  Paid: 'success',
  Overdue: 'danger',
  Cancelled: 'default',
  'Partly Paid': 'warning',
  'Return': 'info',
  Submitted: 'info',
}

const TYPE_VARIANTS: Record<string, StatusVariant> = {
  Sales: 'primary',
  Purchase: 'warning',
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const hasPrev = computed(() => page.value > 0)
const hasNext = computed(() => (page.value + 1) * pageSize < total.value)

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const parts = dateStr.split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    return d.toLocaleDateString()
  }
  return dateStr
}

function formatCurrency(val: number): string {
  return 'ETB ' + (val?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00')
}

function applyPreset(days: number) {
  const now = new Date()
  const from = new Date(now.getFullYear(), now.getMonth(), now.getDate() - days)
  dateTo.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  dateFrom.value = `${from.getFullYear()}-${String(from.getMonth() + 1).padStart(2, '0')}-${String(from.getDate()).padStart(2, '0')}`
  page.value = 0
  loadData()
}

function setTypeFilter(val: string | null) {
  typeFilter.value = val
  page.value = 0
  loadData()
}

function setStatusFilter(val: string | null) {
  statusFilter.value = val
  page.value = 0
  loadData()
}

function prevPage() { if (hasPrev.value) { page.value--; loadData() } }
function nextPage() { if (hasNext.value) { page.value++; loadData() } }

function openDetail(record: InvoiceRecord) {
  router.push(`/invoices/${record.name}?type=${record.invoice_type}`)
}

async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: page.value * pageSize,
      limit_page_length: pageSize,
    }
    if (dateFrom.value) args.date_from = dateFrom.value
    if (dateTo.value) args.date_to = dateTo.value
    if (typeFilter.value) args.invoice_type = typeFilter.value
    if (statusFilter.value) args.status = statusFilter.value
    if (searchQuery.value) args.search = searchQuery.value

    const data = await apiCall<InvoiceListData>(
      'car_repair_management.api.invoice.get_invoices',
      args,
    )
    kpis.value = data.kpis
    records.value = data.records
    total.value = data.total
  } catch (e) {
    console.warn('Failed to load invoices', e)
  } finally {
    isLoading.value = false
  }
}

function exportCSV() {
  const headers = [
    'Invoice ID', 'Type', 'Date', 'Customer/Supplier', 'Amount',
    'Outstanding', 'Status', 'Due Date', 'Last Updated',
  ]
  const rows = records.value.map((r) => [
    r.name, r.invoice_type, r.posting_date || '', r.party,
    r.grand_total, r.outstanding_amount, r.status,
    r.due_date || '', r.modified || '',
  ])
  const csv = [headers, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `invoices_${new Date().toISOString().slice(0, 10)}.csv`
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
        <h1 class="text-page-title" style="color: var(--text-primary)">{{ $t('invoices.title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">{{ $t('invoices.subtitle', { count: total }) }}</p>
      </div>
      <div class="flex items-center gap-2">
        <div class="relative create-dropdown-wrapper">
          <Button variant="primary" @click="showCreateDropdown = !showCreateDropdown">
            <LucidePlus class="size-4" />
            {{ $t('invoices.create_invoice') }}
            <LucideChevronDown class="size-4" />
          </Button>
          <div
            v-if="showCreateDropdown"
            class="absolute right-0 top-full mt-1 w-48 rounded-lg border shadow-lg py-1 z-50"
            style="background-color: var(--bg-elevated); border-color: var(--border-color);"
          >
            <a
              href="/app/sales-invoice/new"
              target="_blank"
              class="flex items-center gap-2 px-4 py-2 text-sm transition-colors hover:opacity-80"
              style="color: var(--text-primary);"
              @click="showCreateDropdown = false"
            >
              {{ $t('invoices.sales_invoice') }}
            </a>
            <a
              href="/app/purchase-invoice/new"
              target="_blank"
              class="flex items-center gap-2 px-4 py-2 text-sm transition-colors hover:opacity-80"
              style="color: var(--text-primary);"
              @click="showCreateDropdown = false"
            >
              {{ $t('invoices.purchase_invoice') }}
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Control Bar -->
    <Card>
      <div class="flex flex-wrap items-end gap-3 pb-4 border-b" style="border-color: var(--border-subtle)">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('common.search') }}</label>
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="$t('invoices.search_placeholder')"
            class="w-full h-9 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @keyup.enter="() => { page = 0; loadData() }"
          />
        </div>
        <div>
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('common.from') }}</label>
          <input
            v-model="dateFrom"
            type="date"
            class="h-9 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @change="() => { page = 0; loadData() }"
          />
        </div>
        <div>
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('common.to') }}</label>
          <input
            v-model="dateTo"
            type="date"
            class="h-9 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @change="() => { page = 0; loadData() }"
          />
        </div>
        <div class="flex items-center gap-1">
          <Button variant="ghost" size="sm" @click="applyPreset(7)">7D</Button>
          <Button variant="ghost" size="sm" @click="applyPreset(30)">30D</Button>
          <Button variant="ghost" size="sm" @click="applyPreset(90)">90D</Button>
          <Button variant="ghost" size="sm" @click="applyPreset(365)">1Y</Button>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-3 pt-4">
        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('common.type') }}:</span>
          <Button :variant="typeFilter === null ? 'secondary' : 'ghost'" size="sm" @click="setTypeFilter(null)">{{ $t('common.all') }}</Button>
          <Button
            v-for="opt in TYPE_OPTIONS"
            :key="opt"
            :variant="typeFilter === opt ? 'secondary' : 'ghost'"
            size="sm"
            @click="setTypeFilter(opt)"
          >
            {{ opt }}
          </Button>
        </div>

        <div class="w-px h-6" style="background: var(--border-color)" />

        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('common.status') }}:</span>
          <Button :variant="statusFilter === null ? 'secondary' : 'ghost'" size="sm" @click="setStatusFilter(null)">{{ $t('common.all') }}</Button>
          <Button
            v-for="opt in STATUS_OPTIONS"
            :key="opt"
            :variant="statusFilter === opt ? 'secondary' : 'ghost'"
            size="sm"
            @click="setStatusFilter(opt)"
          >
            {{ opt }}
          </Button>
        </div>

        <div class="flex-1" />

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
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('invoices.total_invoiced') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="80px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">{{ formatCurrency(kpis.total_invoiced) }}</p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('invoices.total_paid') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="80px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: #22c55e">{{ formatCurrency(kpis.total_paid) }}</p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.outstanding') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="80px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" :style="{ color: kpis.outstanding > 0 ? '#ef4444' : 'var(--text-primary)' }">
          {{ formatCurrency(kpis.outstanding) }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('invoices.overdue') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" :style="{ color: kpis.overdue_count > 0 ? '#ef4444' : 'var(--text-primary)' }">
          {{ kpis.overdue_count }}
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
        :icon="LucideFileText"
        :title="$t('invoices.no_invoices')"
        :description="$t('invoices.no_invoices_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm" style="color: var(--text-primary)">
          <thead>
            <tr class="border-b" style="border-color: var(--border-subtle)">
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('invoices.invoice_id') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.type') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.date') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('invoices.customer_supplier') }}</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.amount') }}</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.outstanding') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.status') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('invoices.due_date') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.last_updated') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in records"
              :key="r.name + r.invoice_type"
              class="border-b cursor-pointer transition-colors"
              style="border-color: var(--border-subtle)"
              @click="openDetail(r)"
              @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
            >
              <td class="px-4 py-3 font-medium whitespace-nowrap">{{ r.name }}</td>
              <td class="px-4 py-3">
                <Badge :variant="TYPE_VARIANTS[r.invoice_type] || 'default'" size="sm">{{ r.invoice_type }}</Badge>
              </td>
              <td class="px-4 py-3 whitespace-nowrap">{{ formatDate(r.posting_date) }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.party }}</td>
              <td class="px-4 py-3 text-right whitespace-nowrap">{{ formatCurrency(r.grand_total) }}</td>
              <td class="px-4 py-3 text-right whitespace-nowrap" :style="{ color: r.outstanding_amount > 0 ? '#ef4444' : 'inherit' }">
                {{ formatCurrency(r.outstanding_amount) }}
              </td>
              <td class="px-4 py-3">
                <Badge :variant="STATUS_VARIANTS[r.status] || 'default'" size="sm">{{ r.status }}</Badge>
              </td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ formatDate(r.due_date) }}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ formatDate(r.modified) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

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
          <span class="text-xs" style="color: var(--text-muted)">{{ $t('common.page') }} {{ page + 1 }} {{ $t('common.of') }} {{ totalPages }}</span>
          <Button variant="outline" size="sm" :disabled="!hasNext" @click="nextPage">{{ $t('common.next') }}</Button>
        </div>
      </div>
    </Card>
  </div>
</template>
