<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideUsers,
  LucideRefreshCw,
  LucideDownload,
  LucidePlus,
  LucideUser,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, EmptyState, Skeleton, Badge } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface EmployeeRecord {
  name: string
  employee_name: string
  department: string | null
  designation: string | null
  status: string
  image: string | null
  cell_number: string | null
  company_email: string | null
  date_of_joining: string | null
  reports_to: string | null
  assigned_wo_count: number
  owner: string
  creation: string
  modified: string
}

interface EmployeeKPIs {
  total_employees: number
  active_employees: number
  assigned_work_orders: number
  avg_resolution_time: number
}

interface EmployeeListData {
  kpis: EmployeeKPIs
  records: EmployeeRecord[]
  total: number
}

const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const records = ref<EmployeeRecord[]>([])
const kpis = ref<EmployeeKPIs>({
  total_employees: 0,
  active_employees: 0,
  assigned_work_orders: 0,
  avg_resolution_time: 0,
})
const total = ref(0)
const page = ref(0)
const pageSize = 20

const searchQuery = ref('')
const departmentFilter = ref('')
const designationFilter = ref('')
const statusFilter = ref<string | null>(null)

const STATUS_OPTIONS = ['Active', 'Inactive', 'Suspended', 'Left']

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Active: 'success',
  Inactive: 'default',
  Suspended: 'warning',
  Left: 'danger',
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

function setStatusFilter(val: string | null) {
  statusFilter.value = val
  page.value = 0
  loadData()
}

function prevPage() { if (hasPrev.value) { page.value--; loadData() } }
function nextPage() { if (hasNext.value) { page.value++; loadData() } }

function openDetail(record: EmployeeRecord) {
  router.push(`/employees/${record.name}`)
}

async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: page.value * pageSize,
      limit_page_length: pageSize,
    }
    if (searchQuery.value) args.search = searchQuery.value
    if (departmentFilter.value) args.department = departmentFilter.value
    if (designationFilter.value) args.designation = designationFilter.value
    if (statusFilter.value) args.status = statusFilter.value

    const data = await apiCall<EmployeeListData>(
      'car_repair_management.api.employee.get_employees',
      args,
    )
    kpis.value = data.kpis
    records.value = data.records
    total.value = data.total
  } catch (e) {
    console.warn('Failed to load employees', e)
  } finally {
    isLoading.value = false
  }
}

function exportCSV() {
  const headers = [
    t('employees.employee_id'), t('common.name'), t('employees.department'), t('employees.designation'), t('common.status'),
    t('employees.assigned_wos'), t('customers.phone'), t('customers.email'), t('employees.joined'),
  ]
  const rows = records.value.map((r) => [
    r.name, r.employee_name, r.department || '', r.designation || '',
    r.status, r.assigned_wo_count, r.cell_number || '',
    r.company_email || '', r.date_of_joining || '',
  ])
  const csv = [headers, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `employees_${new Date().toISOString().slice(0, 10)}.csv`
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
        <h1 class="text-page-title" style="color: var(--text-primary)">{{ $t('employees.title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">{{ $t('employees.subtitle', { count: total }) }}</p>
      </div>
      <a href="/app/employee/new" target="_blank">
        <Button variant="primary">
          <LucidePlus class="size-4" />
          {{ $t('employees.add_employee') }}
        </Button>
      </a>
    </div>

    <!-- Control Bar -->
    <Card>
      <!-- Row 1: Search + Filters -->
      <div class="flex flex-wrap items-end gap-3 pb-4 border-b" style="border-color: var(--border-subtle)">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('common.search') }}</label>
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="$t('employees.search_placeholder')"
            class="w-full h-9 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @keyup.enter="() => { page = 0; loadData() }"
          />
        </div>
        <div class="min-w-[140px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('employees.department') }}</label>
          <input
            v-model="departmentFilter"
            type="text"
            :placeholder="$t('employees.department')"
            class="w-full h-9 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @keyup.enter="() => { page = 0; loadData() }"
          />
        </div>
        <div class="min-w-[140px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('employees.designation') }}</label>
          <input
            v-model="designationFilter"
            type="text"
            :placeholder="$t('employees.designation')"
            class="w-full h-9 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @keyup.enter="() => { page = 0; loadData() }"
          />
        </div>
      </div>

      <!-- Row 2: Status + Actions -->
      <div class="flex flex-wrap items-center gap-3 pt-4">
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
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('employees.total_employees') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">{{ kpis.total_employees }}</p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('employees.active_count') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: #22c55e">{{ kpis.active_employees }}</p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('employees.wo_in_progress') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">{{ kpis.assigned_work_orders }}</p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('employees.avg_resolution_time') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">{{ kpis.avg_resolution_time }} {{ $t('common.days') }}</p>
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
        :title="$t('employees.no_employees')"
        :description="$t('employees.no_employees_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm" style="color: var(--text-primary)">
          <thead>
            <tr class="border-b" style="border-color: var(--border-subtle)">
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('employees.employee_id') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.name') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('employees.department') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('employees.designation') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.status') }}</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('employees.assigned_wos') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.phone') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('customers.email') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('employees.joined') }}</th>
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
              <td class="px-4 py-3 whitespace-nowrap font-medium">{{ r.name }}</td>
              <td class="px-4 py-3 whitespace-nowrap">
                <div class="flex items-center gap-2">
                  <img v-if="r.image" :src="r.image" class="w-6 h-6 rounded-full object-cover" />
                  <div v-else class="w-6 h-6 rounded-full flex items-center justify-center" style="background: var(--bg-tertiary)">
                    <LucideUser class="size-3" style="color: var(--text-muted)" />
                  </div>
                  {{ r.employee_name }}
                </div>
              </td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ r.department || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ r.designation || '—' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="STATUS_VARIANTS[r.status] || 'default'" size="sm">{{ r.status }}</Badge>
              </td>
              <td class="px-4 py-3 text-right">{{ r.assigned_wo_count }}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ r.cell_number || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap truncate max-w-[180px]" style="color: var(--text-secondary)">{{ r.company_email || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ formatDate(r.date_of_joining) }}</td>
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
          <span class="text-xs" style="color: var(--text-muted)">{{ $t('common.page') }} {{ page + 1 }} {{ $t('common.of') }} {{ totalPages }}</span>
          <Button variant="outline" size="sm" :disabled="!hasNext" @click="nextPage">{{ $t('common.next') }}</Button>
        </div>
      </div>
    </Card>
  </div>
</template>
