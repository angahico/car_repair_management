<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideReceipt,
  LucideRefreshCw,
  LucideDownload,
  LucideToggleLeft,
  LucideToggleRight,
  LucidePlus,
  LucidePaperclip,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, EmptyState, Skeleton, Badge } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface ExpenseRecord {
  name: string
  expense_date: string | null
  vehicle: string | null
  category: string
  amount: number
  vendor: string | null
  work_order: string | null
  payment_status: string
  has_receipt: number
  entered_by: string | null
  modified: string | null
}

interface ExpenseKPIs {
  total_expenses: number
  fuel_spend: number
  maintenance_spend: number
  avg_per_vehicle: number
  unlinked_expenses: number
  missing_receipts: number
}

interface ExpenseListData {
  kpis: ExpenseKPIs
  records: ExpenseRecord[]
  total: number
}

const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const records = ref<ExpenseRecord[]>([])
const kpis = ref<ExpenseKPIs>({
  total_expenses: 0,
  fuel_spend: 0,
  maintenance_spend: 0,
  avg_per_vehicle: 0,
  unlinked_expenses: 0,
  missing_receipts: 0,
})
const total = ref(0)
const page = ref(0)
const pageSize = 20

const searchQuery = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const categoryFilter = ref<string | null>(null)
const paymentFilter = ref<string | null>(null)
const hasReceipt = ref(false)

const CATEGORY_OPTIONS = ['Fuel', 'Parts', 'Labor', 'External Service', 'Insurance', 'Taxes', 'Other']
const PAYMENT_OPTIONS = ['Unpaid', 'Paid', 'Partially Paid']

const CATEGORY_VARIANTS: Record<string, StatusVariant> = {
  Fuel: 'info',
  Parts: 'primary',
  Labor: 'warning',
  'External Service': 'default',
  Insurance: 'success',
  Taxes: 'danger',
  Other: 'default',
}

const PAYMENT_VARIANTS: Record<string, StatusVariant> = {
  Paid: 'success',
  Unpaid: 'danger',
  'Partially Paid': 'warning',
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

function setCategoryFilter(val: string | null) {
  categoryFilter.value = val
  page.value = 0
  loadData()
}

function setPaymentFilter(val: string | null) {
  paymentFilter.value = val
  page.value = 0
  loadData()
}

function toggleHasReceipt() {
  hasReceipt.value = !hasReceipt.value
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

function openDetail(record: ExpenseRecord) {
  router.push(`/expenses/${record.name}`)
}

function addExpense() {
  router.push('/expenses/new')
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
    if (categoryFilter.value) args.category = categoryFilter.value
    if (paymentFilter.value) args.payment_status = paymentFilter.value
    if (hasReceipt.value) args.has_receipt = 1
    if (searchQuery.value) args.search = searchQuery.value

    const data = await apiCall<ExpenseListData>(
      'car_repair_management.api.expense.get_expenses',
      args,
    )
    kpis.value = data.kpis
    records.value = data.records
    total.value = data.total
  } catch (e) {
    console.warn('Failed to load expenses', e)
  } finally {
    isLoading.value = false
  }
}

function exportCSV() {
  const headers = [
    t('expenses.expense_id'), t('common.date'), t('common.vehicle'), t('issues.category'), t('common.amount'), t('expenses.vendor'),
    t('expenses.work_order'), t('expenses.payment_status'), t('expenses.has_receipt'), t('expenses.entered_by'), t('expenses.last_updated'),
  ]
  const rows = records.value.map((r) => [
    r.name,
    r.expense_date || '',
    r.vehicle || '',
    r.category,
    r.amount,
    r.vendor || '',
    r.work_order || '',
    r.payment_status,
    r.has_receipt ? 'Yes' : 'No',
    r.entered_by || '',
    r.modified || '',
  ])
  const csv = [headers, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `expenses_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-page-title">{{ $t('expenses.title') }}</h1>
      <p class="text-sm mt-1" style="color: var(--text-muted)">
        {{ $t('expenses.subtitle', { count: total }) }}
      </p>
    </div>

    <!-- Control Bar -->
    <Card>
      <!-- Row 1: Search + Date Range + Presets + Add Button -->
      <div class="flex flex-wrap items-end gap-3 pb-4 border-b" style="border-color: var(--border-subtle)">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('common.search') }}</label>
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="$t('expenses.search_placeholder')"
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
        <Button variant="primary" size="sm" @click="addExpense">
          <LucidePlus class="size-3.5" />
          {{ $t('expenses.add_expense') }}
        </Button>
      </div>

      <!-- Row 2: Filters + Actions -->
      <div class="flex flex-wrap items-center gap-3 pt-4">
        <!-- Category Filter -->
        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('issues.category') }}:</span>
          <Button
            :variant="categoryFilter === null ? 'secondary' : 'ghost'"
            size="sm"
            @click="setCategoryFilter(null)"
          >
            {{ $t('common.all') }}
          </Button>
          <Button
            v-for="opt in CATEGORY_OPTIONS"
            :key="opt"
            :variant="categoryFilter === opt ? 'secondary' : 'ghost'"
            size="sm"
            @click="setCategoryFilter(opt)"
          >
            {{ opt }}
          </Button>
        </div>

        <div class="w-px h-6" style="background: var(--border-color)" />

        <!-- Payment Status Filter -->
        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('expenses.payment') }}:</span>
          <Button
            :variant="paymentFilter === null ? 'secondary' : 'ghost'"
            size="sm"
            @click="setPaymentFilter(null)"
          >
            {{ $t('common.all') }}
          </Button>
          <Button
            v-for="opt in PAYMENT_OPTIONS"
            :key="opt"
            :variant="paymentFilter === opt ? 'secondary' : 'ghost'"
            size="sm"
            @click="setPaymentFilter(opt)"
          >
            {{ opt }}
          </Button>
        </div>

        <div class="w-px h-6" style="background: var(--border-color)" />

        <!-- Has Receipt Toggle -->
        <button
          class="flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded"
          :style="{
            color: hasReceipt ? 'var(--accent)' : 'var(--text-muted)',
            background: hasReceipt ? 'var(--bg-tertiary)' : 'transparent',
          }"
          @click="toggleHasReceipt"
        >
          <component :is="hasReceipt ? LucideToggleRight : LucideToggleLeft" class="size-4" />
          {{ $t('expenses.has_receipt') }}
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
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.total_expenses') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ formatCurrency(kpis.total_expenses) }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.fuel_spend') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ formatCurrency(kpis.fuel_spend) }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.maintenance_spend') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ formatCurrency(kpis.maintenance_spend) }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.avg_per_vehicle') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ formatCurrency(kpis.avg_per_vehicle) }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.unlinked_expenses') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p
          v-else
          class="text-2xl font-bold mt-1"
          :style="{ color: kpis.unlinked_expenses > 0 ? '#ef4444' : 'var(--text-primary)' }"
        >
          {{ kpis.unlinked_expenses }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.missing_receipts') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p
          v-else
          class="text-2xl font-bold mt-1"
          :style="{ color: kpis.missing_receipts > 0 ? '#ef4444' : 'var(--text-primary)' }"
        >
          {{ kpis.missing_receipts }}
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
        :icon="LucideReceipt"
        :title="$t('expenses.no_expenses')"
        :description="$t('expenses.no_expenses_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm" style="color: var(--text-primary)">
          <thead>
            <tr class="border-b" style="border-color: var(--border-subtle)">
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.expense_id') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.date') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.vehicle') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('issues.category') }}</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.amount') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.vendor') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.work_order') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.payment_status') }}</th>
              <th class="text-center px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.receipt') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.entered_by') }}</th>
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
              <td class="px-4 py-3 font-medium whitespace-nowrap">{{ r.name }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ formatDate(r.expense_date) }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.vehicle || '—' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="CATEGORY_VARIANTS[r.category] || 'default'">
                  {{ r.category }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right whitespace-nowrap">{{ formatCurrency(r.amount) }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.vendor || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.work_order || '—' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="PAYMENT_VARIANTS[r.payment_status] || 'default'">
                  {{ r.payment_status }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-center">
                <LucidePaperclip
                  v-if="r.has_receipt"
                  class="size-4 inline-block"
                  style="color: var(--accent)"
                />
                <span v-else style="color: var(--text-muted)">—</span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.entered_by || '—' }}</td>
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
