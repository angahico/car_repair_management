<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideUsers,
  LucideRefreshCw,
  LucideDownload,
  LucidePlus,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, EmptyState, Skeleton, Badge } from '@/components/ui'

interface CustomerRecord {
  name: string
  customer_name: string
  customer_type: string
  customer_group: string
  territory: string | null
  mobile_no: string | null
  email_id: string | null
  disabled: number
  creation: string
  modified: string
  owner: string
  outstanding_amount: number
}

interface CustomerKPIs {
  total_customers: number
  active_customers: number
  new_customers_30d: number
  customers_with_outstanding: number
}

interface CustomerListData {
  kpis: CustomerKPIs
  records: CustomerRecord[]
  total: number
}

const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const records = ref<CustomerRecord[]>([])
const kpis = ref<CustomerKPIs>({
  total_customers: 0,
  active_customers: 0,
  new_customers_30d: 0,
  customers_with_outstanding: 0,
})
const total = ref(0)
const page = ref(0)
const pageSize = 20

const searchQuery = ref('')
const customerGroupFilter = ref('')
const customerTypeFilter = ref<string | null>(null)
const statusFilter = ref<string | null>(null)

const TYPE_OPTIONS = ['Individual', 'Company']
const STATUS_OPTIONS = ['Active', 'Inactive']

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const hasPrev = computed(() => page.value > 0)
const hasNext = computed(() => (page.value + 1) * pageSize < total.value)

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const [datePart] = dateStr.split(' ')
  const parts = datePart.split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    return d.toLocaleDateString()
  }
  return dateStr
}

function formatCurrency(amount: number): string {
  return amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function setTypeFilter(val: string | null) {
  customerTypeFilter.value = val
  page.value = 0
  loadData()
}

function setStatusFilter(val: string | null) {
  statusFilter.value = val
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

async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: page.value * pageSize,
      limit_page_length: pageSize,
    }
    if (searchQuery.value) args.search = searchQuery.value
    if (customerGroupFilter.value) args.customer_group = customerGroupFilter.value
    if (customerTypeFilter.value) args.customer_type = customerTypeFilter.value
    if (statusFilter.value) args.status = statusFilter.value

    const data = await apiCall<CustomerListData>(
      'car_repair_management.api.customer.get_customers',
      args,
    )
    kpis.value = data.kpis
    records.value = data.records
    total.value = data.total
  } catch (e) {
    console.warn('Failed to load customers', e)
  } finally {
    isLoading.value = false
  }
}

function exportCSV() {
  const headers = [
    t('customers.customer_id'), t('customers.customer_name'), t('common.type'), t('customers.customer_group'), t('customers.phone'),
    t('customers.email'), t('customers.outstanding'), t('customers.created_on'),
  ]
  const rows = records.value.map((r) => [
    r.name,
    r.customer_name || '',
    r.customer_type || '',
    r.customer_group || '',
    r.mobile_no || '',
    r.email_id || '',
    r.outstanding_amount,
    r.creation || '',
  ])
  const csv = [headers, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `customers_${new Date().toISOString().slice(0, 10)}.csv`
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
        <h1 class="text-page-title">{{ $t('customers.title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">
          {{ $t('customers.subtitle', { count: total }) }}
        </p>
      </div>
      <a href="/app/customer/new" target="_blank">
        <Button variant="primary">
          <LucidePlus class="size-4" />
          {{ $t('customers.add_customer') }}
        </Button>
      </a>
    </div>

    <!-- Control Bar -->
    <Card>
      <!-- Row 1: Search + Customer Group + Type + Status -->
      <div class="flex flex-wrap items-end gap-3 pb-4 border-b" style="border-color: var(--border-subtle)">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('common.search') }}</label>
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="$t('customers.search_placeholder')"
            class="w-full h-9 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @keyup.enter="() => { page = 0; loadData() }"
          />
        </div>
        <div class="min-w-[160px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('customers.customer_group') }}</label>
          <input
            v-model="customerGroupFilter"
            type="text"
            placeholder="e.g. Commercial"
            class="w-full h-9 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @keyup.enter="() => { page = 0; loadData() }"
          />
        </div>

        <!-- Customer Type -->
        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('common.type') }}:</span>
          <Button
            :variant="customerTypeFilter === null ? 'secondary' : 'ghost'"
            size="sm"
            @click="setTypeFilter(null)"
          >
            {{ $t('common.all') }}
          </Button>
          <Button
            v-for="opt in TYPE_OPTIONS"
            :key="opt"
            :variant="customerTypeFilter === opt ? 'secondary' : 'ghost'"
            size="sm"
            @click="setTypeFilter(opt)"
          >
            {{ opt }}
          </Button>
        </div>

        <div class="w-px h-6" style="background: var(--border-color)" />

        <!-- Status -->
        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('common.status') }}:</span>
          <Button
            :variant="statusFilter === null ? 'secondary' : 'ghost'"
            size="sm"
            @click="setStatusFilter(null)"
          >
            {{ $t('common.all') }}
          </Button>
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
      </div>

      <!-- Row 2: Export + Refresh -->
      <div class="flex flex-wrap items-center gap-3 pt-4">
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
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.total_customers') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ kpis.total_customers }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.active_customers') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: #22c55e">
          {{ kpis.active_customers }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.new_30d') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ kpis.new_customers_30d }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.with_outstanding') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p
          v-else
          class="text-2xl font-bold mt-1"
          :style="{ color: kpis.customers_with_outstanding > 0 ? '#ef4444' : 'var(--text-primary)' }"
        >
          {{ kpis.customers_with_outstanding }}
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
        :icon="LucideUsers"
        :title="$t('customers.no_customers')"
        :description="$t('customers.no_customers_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm" style="color: var(--text-primary)">
          <thead>
            <tr class="border-b" style="border-color: var(--border-subtle)">
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.customer_id') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.customer_name') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.type') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.customer_group') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.phone') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.email') }}</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.outstanding') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.created_on') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in records"
              :key="c.name"
              class="border-b cursor-pointer transition-colors"
              style="border-color: var(--border-subtle)"
              @click="router.push(`/customers/${c.name}`)"
              @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
            >
              <td class="px-4 py-3 font-medium whitespace-nowrap">{{ c.name }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ c.customer_name || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ c.customer_type || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ c.customer_group || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ c.mobile_no || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap truncate max-w-[200px]">{{ c.email_id || '—' }}</td>
              <td
                class="px-4 py-3 text-right whitespace-nowrap"
                :style="{ color: c.outstanding_amount > 0 ? '#ef4444' : 'var(--text-primary)' }"
              >
                {{ c.outstanding_amount > 0 ? formatCurrency(c.outstanding_amount) : '—' }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap">{{ formatDate(c.creation) }}</td>
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
