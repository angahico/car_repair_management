<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideClipboardCheck,
  LucideRefreshCw,
  LucideDownload,
  LucideToggleLeft,
  LucideToggleRight,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, EmptyState, Skeleton, Badge } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface InspectionRecord {
  name: string
  inspection_date: string | null
  vehicle: string
  form_template: string | null
  inspection_type: string
  inspector: string | null
  result: string | null
  score: number
  failures_count: number
  follow_up_required: number
  linked_work_order: string | null
  status: string
  title: string
  owner: string
  creation: string
  modified: string
}

interface InspectionKPIs {
  total_inspections: number
  pass_rate: number
  fail_count: number
  average_score: number
  overdue_followups: number
}

interface InspectionHistoryData {
  kpis: InspectionKPIs
  records: InspectionRecord[]
  total: number
}

const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const records = ref<InspectionRecord[]>([])
const kpis = ref<InspectionKPIs>({
  total_inspections: 0,
  pass_rate: 0,
  fail_count: 0,
  average_score: 0,
  overdue_followups: 0,
})
const total = ref(0)
const page = ref(0)
const pageSize = 20

const searchQuery = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const resultFilter = ref<string | null>(null)
const typeFilter = ref<string | null>(null)
const hasFailures = ref(false)

const RESULT_OPTIONS = ['Pass', 'Conditional', 'Fail']
const TYPE_OPTIONS = ['Pre-Trip', 'Post-Trip', 'Periodic', 'Ad-Hoc', 'Regulatory']

const RESULT_VARIANTS: Record<string, StatusVariant> = {
  Pass: 'success',
  Conditional: 'warning',
  Fail: 'danger',
}

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Draft: 'default',
  'In Progress': 'info',
  Completed: 'success',
  Cancelled: 'danger',
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

function applyPreset(days: number) {
  const now = new Date()
  const from = new Date(now.getFullYear(), now.getMonth(), now.getDate() - days)
  dateTo.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  dateFrom.value = `${from.getFullYear()}-${String(from.getMonth() + 1).padStart(2, '0')}-${String(from.getDate()).padStart(2, '0')}`
  page.value = 0
  loadData()
}

function setResultFilter(val: string | null) {
  resultFilter.value = val
  page.value = 0
  loadData()
}

function setTypeFilter(val: string | null) {
  typeFilter.value = val
  page.value = 0
  loadData()
}

function toggleHasFailures() {
  hasFailures.value = !hasFailures.value
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

function openDetail(record: InspectionRecord) {
  router.push(`/inspections/${record.name}`)
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
    if (resultFilter.value) args.result = resultFilter.value
    if (typeFilter.value) args.inspection_type = typeFilter.value
    if (hasFailures.value) args.has_failures = 1
    if (searchQuery.value) args.search = searchQuery.value

    const data = await apiCall<InspectionHistoryData>(
      'car_repair_management.api.inspection.get_inspection_history',
      args,
    )
    kpis.value = data.kpis
    records.value = data.records
    total.value = data.total
  } catch (e) {
    console.warn('Failed to load inspection history', e)
  } finally {
    isLoading.value = false
  }
}

function exportCSV() {
  const headers = [
    'Inspection ID', 'Date/Time', 'Vehicle', 'Form Template', 'Type',
    'Inspector', 'Result', 'Score', 'Failures Count', 'Follow-up Required',
    'Linked Work Order', 'Status',
  ]
  const rows = records.value.map((r) => [
    r.name,
    r.inspection_date || '',
    r.vehicle,
    r.form_template || '',
    r.inspection_type,
    r.inspector || '',
    r.result || '',
    r.score,
    r.failures_count,
    r.follow_up_required ? 'Yes' : 'No',
    r.linked_work_order || '',
    r.status,
  ])
  const csv = [headers, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `inspection_history_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-page-title">{{ $t('inspections.title') }}</h1>
      <p class="text-sm mt-1" style="color: var(--text-muted)">
        {{ $t('inspections.subtitle', { count: total }) }}
      </p>
    </div>

    <!-- Control Bar -->
    <Card>
      <!-- Row 1: Search + Date Range + Presets -->
      <div class="flex flex-wrap items-end gap-3 pb-4 border-b" style="border-color: var(--border-subtle)">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('common.search') }}</label>
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="$t('inspections.search_placeholder')"
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

      <!-- Row 2: Filters + Actions -->
      <div class="flex flex-wrap items-center gap-3 pt-4">
        <!-- Result Filter -->
        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('inspections.result') }}:</span>
          <Button
            :variant="resultFilter === null ? 'secondary' : 'ghost'"
            size="sm"
            @click="setResultFilter(null)"
          >
            {{ $t('common.all') }}
          </Button>
          <Button
            v-for="opt in RESULT_OPTIONS"
            :key="opt"
            :variant="resultFilter === opt ? 'secondary' : 'ghost'"
            size="sm"
            @click="setResultFilter(opt)"
          >
            {{ opt }}
          </Button>
        </div>

        <div class="w-px h-6" style="background: var(--border-color)" />

        <!-- Type Filter -->
        <div class="flex items-center gap-1">
          <span class="text-xs font-medium mr-1" style="color: var(--text-muted)">{{ $t('common.type') }}:</span>
          <Button
            :variant="typeFilter === null ? 'secondary' : 'ghost'"
            size="sm"
            @click="setTypeFilter(null)"
          >
            {{ $t('common.all') }}
          </Button>
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

        <!-- Has Failures Toggle -->
        <button
          class="flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded"
          :style="{
            color: hasFailures ? 'var(--accent)' : 'var(--text-muted)',
            background: hasFailures ? 'var(--bg-tertiary)' : 'transparent',
          }"
          @click="toggleHasFailures"
        >
          <component :is="hasFailures ? LucideToggleRight : LucideToggleLeft" class="size-4" />
          {{ $t('inspections.has_failures') }}
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
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.total_inspections') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ kpis.total_inspections }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.pass_rate') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p
          v-else
          class="text-2xl font-bold mt-1"
          :style="{ color: kpis.pass_rate >= 80 ? '#22c55e' : '#ef4444' }"
        >
          {{ kpis.pass_rate.toFixed(1) }}%
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.fail_count') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ kpis.fail_count }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.average_score') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p v-else class="text-2xl font-bold mt-1" style="color: var(--text-primary)">
          {{ kpis.average_score.toFixed(1) }}
        </p>
      </Card>
      <Card>
        <p class="text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.overdue_followups') }}</p>
        <p v-if="isLoading" class="mt-1"><Skeleton width="60px" height="28px" /></p>
        <p
          v-else
          class="text-2xl font-bold mt-1"
          :style="{ color: kpis.overdue_followups > 0 ? '#ef4444' : 'var(--text-primary)' }"
        >
          {{ kpis.overdue_followups }}
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
        :icon="LucideClipboardCheck"
        :title="$t('inspections.no_inspections')"
        :description="$t('inspections.no_inspections_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm" style="color: var(--text-primary)">
          <thead>
            <tr class="border-b" style="border-color: var(--border-subtle)">
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.inspection_id') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.date_time') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.vehicle') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.form_template') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.type') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.inspector') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.result') }}</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.score') }}</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.failures') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('inspections.follow_up') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('expenses.work_order') }}</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.status') }}</th>
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
              <td class="px-4 py-3 whitespace-nowrap">{{ formatDateTime(r.inspection_date) }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.vehicle }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.form_template || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.inspection_type }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.inspector || '—' }}</td>
              <td class="px-4 py-3">
                <Badge v-if="r.result" :variant="RESULT_VARIANTS[r.result] || 'default'">
                  {{ r.result }}
                </Badge>
                <span v-else style="color: var(--text-muted)">—</span>
              </td>
              <td class="px-4 py-3 text-right">{{ r.score }}</td>
              <td class="px-4 py-3 text-right">{{ r.failures_count }}</td>
              <td class="px-4 py-3">{{ r.follow_up_required ? $t('common.yes') : $t('common.no') }}</td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.linked_work_order || '—' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="STATUS_VARIANTS[r.status] || 'default'">
                  {{ r.status }}
                </Badge>
              </td>
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
