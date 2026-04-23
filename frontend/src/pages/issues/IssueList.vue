<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideAlertTriangle,
  LucideAlertCircle,
  LucideClock,
  LucideTimer,
  LucideShieldAlert,
  LucideRefreshCw,
  LucideDownload,
  LucidePlus,
  LucideSearch,
  LucideClipboardList,
  LucideClipboardCheck,
  LucideBug,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Input } from '@/components/ui'

const router = useRouter()
const { t } = useI18n()

// --- Types ---
interface KPIs {
  new_issues: number
  open_issues: number
  avg_time_to_triage: number
  avg_time_to_resolve: number
  critical_open: number
}

interface IssueRecord {
  name: string
  subject: string
  custom_vehicle: string | null
  custom_severity: string | null
  status: string
  custom_category: string | null
  raised_by: string | null
  creation: string
  custom_assigned_to: string | null
  custom_linked_work_order: string | null
  custom_linked_inspection: string | null
  custom_linked_fault: string | null
  custom_source: string | null
  custom_workflow_state: string | null
  modified: string
  owner: string
}

interface IssueData {
  kpis: KPIs
  records: IssueRecord[]
  total: number
}

// --- State ---
const isLoading = ref(true)
const data = ref<IssueData | null>(null)
const searchQuery = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const selectedStatus = ref('')
const selectedSeverity = ref('')
const selectedCategory = ref('')
const selectedSource = ref('')
const page = ref(0)
const PAGE_SIZE = 20

// --- Helpers ---
function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const parts = dateStr.substring(0, 10).split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    return d.toLocaleDateString()
  }
  return dateStr
}

function fmtDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function setPreset(days: number) {
  const now = new Date()
  const from = new Date(now.getFullYear(), now.getMonth(), now.getDate() - days)
  dateTo.value = fmtDate(now)
  dateFrom.value = fmtDate(from)
  page.value = 0
  loadData()
}

const SEVERITY_VARIANTS: Record<string, string> = {
  Low: 'default',
  Medium: 'warning',
  High: 'danger',
  Critical: 'danger',
}

const STATUS_VARIANTS: Record<string, string> = {
  Open: 'warning',
  Replied: 'info',
  Resolved: 'success',
  Closed: 'default',
}

const WORKFLOW_VARIANTS: Record<string, string> = {
  Draft: 'default',
  'Pending Custodian Approval': 'warning',
  Rejected: 'danger',
  Submitted: 'success',
  'Work Order Created': 'info',
}

// --- Load ---
async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: page.value * PAGE_SIZE,
      limit_page_length: PAGE_SIZE,
    }
    if (dateFrom.value) args.date_from = dateFrom.value
    if (dateTo.value) args.date_to = dateTo.value
    if (searchQuery.value) args.search = searchQuery.value
    if (selectedStatus.value) args.status = selectedStatus.value
    if (selectedSeverity.value) args.severity = selectedSeverity.value
    if (selectedCategory.value) args.category = selectedCategory.value
    if (selectedSource.value) args.source = selectedSource.value

    const result = await apiCall<IssueData>(
      'car_repair_management.api.issue.get_issues',
      args,
    )
    data.value = result
  } catch (e) {
    console.warn('Failed to load issues', e)
  } finally {
    isLoading.value = false
  }
}

function applyFilters() {
  page.value = 0
  loadData()
}

function nextPage() {
  if (data.value && (page.value + 1) * PAGE_SIZE < data.value.total) {
    page.value++
    loadData()
  }
}

function prevPage() {
  if (page.value > 0) {
    page.value--
    loadData()
  }
}

function goToDetail(name: string) {
  router.push(`/issues/${name}`)
}

// --- Export ---
function exportCSV() {
  if (!data.value?.records.length) return
  const headers = ['Issue ID', 'Title', 'Vehicle', 'Severity', 'Status', 'Category', 'Reported By', 'Reported On', 'Assigned To', 'Modified']
  const rows = data.value.records.map((r) => [
    r.name, r.subject, r.custom_vehicle || '', r.custom_severity || '', r.status,
    r.custom_category || '', r.raised_by || '', formatDate(r.creation),
    r.custom_assigned_to || '', formatDate(r.modified),
  ])
  const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `issues_${fmtDate(new Date())}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div>
        <h1 class="text-page-title">{{ $t('issues.title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">{{ $t('issues.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="exportCSV"><LucideDownload class="size-4" /></Button>
        <Button variant="outline" @click="loadData">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
        <Button variant="primary" @click="router.push('/issues/new')">
          <LucidePlus class="size-4" /> {{ $t('issues.new_issue') }}
        </Button>
      </div>
    </div>

    <!-- Control Bar -->
    <Card>
      <div class="flex flex-wrap items-end gap-3">
        <div class="flex-1 min-w-[200px]">
          <Input v-model="searchQuery" :placeholder="$t('issues.search_placeholder')" @keyup.enter="applyFilters">
            <template #prefix><LucideSearch class="size-4" style="color: var(--text-muted)" /></template>
          </Input>
        </div>
        <div>
          <label class="text-xs block mb-1" style="color: var(--text-muted)">{{ $t('common.from') }}</label>
          <input v-model="dateFrom" type="date" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" />
        </div>
        <div>
          <label class="text-xs block mb-1" style="color: var(--text-muted)">{{ $t('common.to') }}</label>
          <input v-model="dateTo" type="date" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" />
        </div>
        <div class="flex items-center gap-1">
          <button
            v-for="preset in [{ label: '7D', days: 7 }, { label: '30D', days: 30 }, { label: '90D', days: 90 }, { label: '1Y', days: 365 }]"
            :key="preset.days"
            class="px-3 py-2 text-xs font-medium rounded-lg border transition-colors"
            :style="{ borderColor: 'var(--border-color)', color: 'var(--text-secondary)', backgroundColor: 'var(--bg-tertiary)' }"
            @click="setPreset(preset.days)"
          >{{ preset.label }}</button>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-3 mt-3">
        <select v-model="selectedStatus" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" @change="applyFilters">
          <option value="">{{ $t('issues.all_statuses') }}</option>
          <option v-for="s in ['Open', 'Replied', 'Resolved', 'Closed']" :key="s" :value="s">{{ s }}</option>
        </select>
        <select v-model="selectedSeverity" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" @change="applyFilters">
          <option value="">{{ $t('issues.all_severities') }}</option>
          <option v-for="s in ['Low', 'Medium', 'High', 'Critical']" :key="s" :value="s">{{ s }}</option>
        </select>
        <select v-model="selectedCategory" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" @change="applyFilters">
          <option value="">{{ $t('issues.all_categories') }}</option>
          <option v-for="c in ['Mechanical', 'Electrical', 'Body/Paint', 'Interior', 'Safety', 'Compliance', 'Other']" :key="c" :value="c">{{ c }}</option>
        </select>
        <select v-model="selectedSource" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" @change="applyFilters">
          <option value="">{{ $t('issues.all_sources') }}</option>
          <option v-for="s in ['Inspection', 'Driver Report', 'Mechanic', 'Customer', 'Sensor', 'Other']" :key="s" :value="s">{{ s }}</option>
        </select>
        <Button variant="primary" size="sm" @click="applyFilters">{{ $t('common.apply') }}</Button>
      </div>
    </Card>

    <!-- KPI Cards -->
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <Card v-for="i in 5" :key="i"><Skeleton height="80px" /></Card>
    </div>
    <div v-else-if="data" class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style="background: var(--bg-tertiary);">
            <LucideAlertTriangle class="size-5" style="color: var(--accent);" />
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.new_issues') }}</p>
            <p class="text-2xl font-semibold" style="color: var(--text-primary)">{{ data.kpis.new_issues }}</p>
          </div>
        </div>
      </Card>
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style="background: var(--bg-tertiary);">
            <LucideAlertCircle class="size-5" style="color: var(--text-muted);" />
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.open_issues') }}</p>
            <p class="text-2xl font-semibold" style="color: var(--text-primary)">{{ data.kpis.open_issues }}</p>
          </div>
        </div>
      </Card>
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style="background: var(--bg-tertiary);">
            <LucideClock class="size-5" style="color: var(--text-muted);" />
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.avg_time_to_triage') }}</p>
            <p class="text-2xl font-semibold" style="color: var(--text-primary)">{{ data.kpis.avg_time_to_triage }} <span class="text-sm font-normal" style="color: var(--text-muted)">{{ $t('common.days') }}</span></p>
          </div>
        </div>
      </Card>
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style="background: var(--bg-tertiary);">
            <LucideTimer class="size-5" style="color: var(--text-muted);" />
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.avg_time_to_resolve') }}</p>
            <p class="text-2xl font-semibold" style="color: var(--text-primary)">{{ data.kpis.avg_time_to_resolve }} <span class="text-sm font-normal" style="color: var(--text-muted)">{{ $t('common.days') }}</span></p>
          </div>
        </div>
      </Card>
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" :style="{ background: data.kpis.critical_open > 0 ? 'rgba(239, 68, 68, 0.1)' : 'var(--bg-tertiary)' }">
            <LucideShieldAlert class="size-5" :style="{ color: data.kpis.critical_open > 0 ? '#ef4444' : 'var(--text-muted)' }" />
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.critical_open') }}</p>
            <p class="text-2xl font-semibold" :style="{ color: data.kpis.critical_open > 0 ? '#ef4444' : 'var(--text-primary)' }">{{ data.kpis.critical_open }}</p>
          </div>
        </div>
      </Card>
    </div>

    <!-- Data Table -->
    <Card v-if="!isLoading && data" padding="none">
      <div class="p-4 border-b" style="border-color: var(--border-color);">
        <h2 class="text-section-title">{{ $t('issues.issue_records') }}</h2>
        <p class="text-xs mt-1" style="color: var(--text-muted)">{{ data.total }} total · Showing {{ page * PAGE_SIZE + 1 }}–{{ Math.min((page + 1) * PAGE_SIZE, data.total) }}</p>
      </div>

      <EmptyState
        v-if="data.records.length === 0"
        :icon="LucideAlertTriangle"
        :title="$t('issues.no_issues')"
        :description="$t('issues.no_issues_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b" style="border-color: var(--border-color);">
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.issue_id') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.subject') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('common.vehicle') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('inspections.severity') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('common.status') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.workflow') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.category') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.reported_by') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.reported_on') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.assigned_to') }}</th>
              <th class="text-center px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.links') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.updated') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in data.records"
              :key="r.name"
              class="border-b cursor-pointer transition-colors"
              :style="{ borderColor: 'var(--border-color)' }"
              style="--hover-bg: var(--bg-tertiary);"
              @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = 'transparent'"
              @click="goToDetail(r.name)"
            >
              <td class="px-4 py-3 font-medium" style="color: var(--accent)">{{ r.name }}</td>
              <td class="px-4 py-3" style="color: var(--text-primary)">{{ r.subject }}</td>
              <td class="px-4 py-3" style="color: var(--text-secondary)">{{ r.custom_vehicle || '—' }}</td>
              <td class="px-4 py-3">
                <Badge v-if="r.custom_severity" :variant="SEVERITY_VARIANTS[r.custom_severity] || 'default'" size="sm">{{ r.custom_severity }}</Badge>
                <span v-else style="color: var(--text-muted)">—</span>
              </td>
              <td class="px-4 py-3">
                <Badge :variant="STATUS_VARIANTS[r.status] || 'default'" size="sm">{{ r.status }}</Badge>
              </td>
              <td class="px-4 py-3">
                <Badge v-if="r.custom_workflow_state" :variant="WORKFLOW_VARIANTS[r.custom_workflow_state] || 'default'" size="sm">{{ r.custom_workflow_state }}</Badge>
                <span v-else style="color: var(--text-muted)">—</span>
              </td>
              <td class="px-4 py-3" style="color: var(--text-secondary)">{{ r.custom_category || '—' }}</td>
              <td class="px-4 py-3" style="color: var(--text-muted)">{{ r.raised_by || r.owner }}</td>
              <td class="px-4 py-3" style="color: var(--text-muted)">{{ formatDate(r.creation) }}</td>
              <td class="px-4 py-3" style="color: var(--text-muted)">{{ r.custom_assigned_to || '—' }}</td>
              <td class="px-4 py-3 text-center">
                <div class="flex items-center justify-center gap-1">
                  <LucideClipboardList v-if="r.custom_linked_work_order" class="size-3.5" style="color: var(--accent)" title="Linked Work Order" />
                  <LucideClipboardCheck v-if="r.custom_linked_inspection" class="size-3.5" style="color: var(--text-muted)" title="Linked Inspection" />
                  <LucideBug v-if="r.custom_linked_fault" class="size-3.5" style="color: var(--text-muted)" title="Linked Fault" />
                  <span v-if="!r.custom_linked_work_order && !r.custom_linked_inspection && !r.custom_linked_fault" style="color: var(--text-muted)">—</span>
                </div>
              </td>
              <td class="px-4 py-3" style="color: var(--text-muted)">{{ formatDate(r.modified) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="flex items-center justify-between p-4 border-t" style="border-color: var(--border-color);">
        <Button variant="outline" size="sm" :disabled="page === 0" @click="prevPage">{{ $t('common.previous') }}</Button>
        <span class="text-sm" style="color: var(--text-muted)">{{ $t('common.page') }} {{ page + 1 }} {{ $t('common.of') }} {{ Math.ceil((data?.total || 1) / PAGE_SIZE) }}</span>
        <Button variant="outline" size="sm" :disabled="!data || (page + 1) * PAGE_SIZE >= data.total" @click="nextPage">{{ $t('common.next') }}</Button>
      </div>
    </Card>
  </div>
</template>
