<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideBug,
  LucideRefreshCw,
  LucideDownload,
  LucidePlus,
  LucideSearch,
  LucideImage,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Input } from '@/components/ui'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { t } = useI18n()

interface FaultRecord {
  name: string
  title: string
  vehicle: string
  fault_code: string | null
  detection_type: string | null
  severity: string
  confirmed: string
  status: string
  linked_work_order: string | null
  linked_inspection: string | null
  reported_by: string | null
  reported_date: string | null
  resolved_date: string | null
  component_system: string | null
  evidence: string | null
  owner: string
  creation: string
  modified: string
}

interface FaultsData {
  records: FaultRecord[]
  total: number
}

const isLoading = ref(true)
const data = ref<FaultsData | null>(null)
const searchQuery = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const selectedDetection = ref('')
const selectedSeverity = ref('')
const selectedConfirmed = ref('')
const selectedStatus = ref('')
const componentFilter = ref('')
const page = ref(0)
const PAGE_SIZE = 20

const SEVERITY_VARIANTS: Record<string, string> = {
  Low: 'default', Medium: 'warning', High: 'danger', Critical: 'danger',
}
const STATUS_VARIANTS: Record<string, string> = {
  Open: 'warning', 'In Progress': 'info', Resolved: 'success', Closed: 'default',
}
const CONFIRMED_VARIANTS: Record<string, string> = {
  Unconfirmed: 'warning', Confirmed: 'danger', 'False Positive': 'default',
}

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
    if (selectedDetection.value) args.detection_type = selectedDetection.value
    if (selectedSeverity.value) args.severity = selectedSeverity.value
    if (selectedConfirmed.value) args.confirmed = selectedConfirmed.value
    if (selectedStatus.value) args.status = selectedStatus.value
    if (componentFilter.value) args.component_system = componentFilter.value

    const result = await apiCall<FaultsData>(
      'car_repair_management.api.issue.get_faults',
      args,
    )
    data.value = result
  } catch (e) {
    console.warn('Failed to load faults', e)
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
  router.push(`/issues/faults/${name}`)
}

function exportCSV() {
  if (!data.value?.records.length) return
  const headers = ['Fault ID', 'Vehicle', 'Title', 'Fault Code', 'Detection Type', 'Severity', 'Confirmed', 'Status', 'Component', 'Reported Date', 'Modified']
  const rows = data.value.records.map((r) => [
    r.name, r.vehicle, r.title, r.fault_code || '', r.detection_type || '',
    r.severity, r.confirmed, r.status, r.component_system || '',
    formatDate(r.reported_date), formatDate(r.modified),
  ])
  const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `faults_${fmtDate(new Date())}.csv`
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
        <h1 class="text-page-title">{{ $t('issues.faults_title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">{{ $t('issues.faults_subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="exportCSV"><LucideDownload class="size-4" /></Button>
        <Button variant="outline" @click="loadData">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
        <a href="/app/vehicle-fault/new" target="_blank">
          <Button variant="primary"><LucidePlus class="size-4" /> Report Fault</Button>
        </a>
      </div>
    </div>

    <!-- Control Bar -->
    <Card>
      <div class="flex flex-wrap items-end gap-3">
        <div class="flex-1 min-w-[200px]">
          <Input v-model="searchQuery" placeholder="Search faults..." @keyup.enter="applyFilters">
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
        <select v-model="selectedDetection" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" @change="applyFilters">
          <option value="">All Detection Types</option>
          <option v-for="d in ['OBD Scan', 'Manual Inspection', 'Driver Report', 'Sensor Alert', 'Other']" :key="d" :value="d">{{ d }}</option>
        </select>
        <select v-model="selectedSeverity" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" @change="applyFilters">
          <option value="">{{ $t('issues.all_severities') }}</option>
          <option v-for="s in ['Low', 'Medium', 'High', 'Critical']" :key="s" :value="s">{{ s }}</option>
        </select>
        <select v-model="selectedConfirmed" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" @change="applyFilters">
          <option value="">All Confirmed</option>
          <option v-for="c in ['Unconfirmed', 'Confirmed', 'False Positive']" :key="c" :value="c">{{ c }}</option>
        </select>
        <select v-model="selectedStatus" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" @change="applyFilters">
          <option value="">{{ $t('issues.all_statuses') }}</option>
          <option v-for="s in ['Open', 'In Progress', 'Resolved', 'Closed']" :key="s" :value="s">{{ s }}</option>
        </select>
        <Input v-model="componentFilter" placeholder="Component..." class="w-36" @keyup.enter="applyFilters" />
        <Button variant="primary" size="sm" @click="applyFilters">{{ $t('common.apply') }}</Button>
      </div>
    </Card>

    <!-- Data Table -->
    <Card v-if="!isLoading && data" padding="none">
      <div class="p-4 border-b" style="border-color: var(--border-color);">
        <h2 class="text-section-title">{{ $t('issues.faults_title') }}</h2>
        <p class="text-xs mt-1" style="color: var(--text-muted)">{{ data.total }} total</p>
      </div>

      <EmptyState
        v-if="data.records.length === 0"
        :icon="LucideBug"
        :title="$t('issues.no_faults')"
        :description="$t('issues.no_faults_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b" style="border-color: var(--border-color);">
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">Fault ID</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('common.vehicle') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.fault_code') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.detection_type') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('inspections.severity') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.confirmed') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('expenses.work_order') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('common.status') }}</th>
              <th class="text-center px-4 py-3 font-medium" style="color: var(--text-muted)">Evidence</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('issues.updated') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in data.records"
              :key="r.name"
              class="border-b cursor-pointer transition-colors"
              :style="{ borderColor: 'var(--border-color)' }"
              @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = 'transparent'"
              @click="goToDetail(r.name)"
            >
              <td class="px-4 py-3 font-medium" style="color: var(--accent)">{{ r.name }}</td>
              <td class="px-4 py-3" style="color: var(--text-primary)">{{ r.vehicle }}</td>
              <td class="px-4 py-3" style="color: var(--text-secondary)">{{ r.fault_code || '—' }}</td>
              <td class="px-4 py-3" style="color: var(--text-secondary)">{{ r.detection_type || '—' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="SEVERITY_VARIANTS[r.severity] || 'default'" size="sm">{{ r.severity }}</Badge>
              </td>
              <td class="px-4 py-3">
                <Badge :variant="CONFIRMED_VARIANTS[r.confirmed] || 'default'" size="sm">{{ r.confirmed }}</Badge>
              </td>
              <td class="px-4 py-3" style="color: var(--accent)">{{ r.linked_work_order || '—' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="STATUS_VARIANTS[r.status] || 'default'" size="sm">{{ r.status }}</Badge>
              </td>
              <td class="px-4 py-3 text-center">
                <LucideImage v-if="r.evidence" class="size-4 inline" style="color: var(--accent)" />
                <span v-else style="color: var(--text-muted)">—</span>
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

    <!-- Loading -->
    <Card v-if="isLoading" padding="none">
      <div class="p-4 space-y-3">
        <Skeleton v-for="i in 8" :key="i" height="48px" />
      </div>
    </Card>
  </div>
</template>
