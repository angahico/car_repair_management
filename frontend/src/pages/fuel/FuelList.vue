<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideFuel,
  LucidePlus,
  LucideRefreshCw,
  LucideSearch,
  LucideAlertTriangle,
  LucideCheckCircle,
  LucideClock,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Input } from '@/components/ui'

const router = useRouter()
const { t } = useI18n()

interface RefuelRecord {
  name: string
  vehicle: string
  refuel_date: string
  liters: number
  total_cost: number
  fuel_station: string | null
  approval_status: string
  is_over_quota: number
  driver: string | null
  creation: string
  modified: string
}

const isLoading = ref(true)
const records = ref<RefuelRecord[]>([])
const total = ref(0)
const searchQuery = ref('')
const selectedStatus = ref('')
const selectedVehicle = ref('')
const page = ref(0)
const PAGE_SIZE = 20

const APPROVAL_VARIANTS: Record<string, string> = {
  Approved: 'success',
  'Pending Dept Head Approval': 'warning',
  'Pending Depot Manager Approval': 'warning',
  'Dept Head Approved': 'info',
  Rejected: 'danger',
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

async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: page.value * PAGE_SIZE,
      limit_page_length: PAGE_SIZE,
    }
    if (searchQuery.value) args.search = searchQuery.value
    if (selectedStatus.value) args.status = selectedStatus.value
    if (selectedVehicle.value) args.vehicle = selectedVehicle.value

    const result = await apiCall<{ records: RefuelRecord[]; total: number }>(
      'car_repair_management.api.fuel.get_refueling_records',
      args,
    )
    records.value = result.records || []
    total.value = result.total || 0
  } catch (e) {
    console.warn('Failed to load refueling records', e)
  } finally {
    isLoading.value = false
  }
}

function applyFilters() {
  page.value = 0
  loadData()
}

function nextPage() {
  if ((page.value + 1) * PAGE_SIZE < total.value) {
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

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div>
        <h1 class="text-page-title">{{ $t('fuel.title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">{{ $t('fuel.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="loadData">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
        <Button variant="primary" @click="router.push('/fuel/new')">
          <LucidePlus class="size-4" /> {{ $t('fuel.new_record') }}
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <Card>
      <div class="flex flex-wrap items-end gap-3">
        <div class="flex-1 min-w-[200px]">
          <Input v-model="searchQuery" :placeholder="$t('fuel.search_placeholder')" @keyup.enter="applyFilters">
            <template #prefix><LucideSearch class="size-4" style="color: var(--text-muted)" /></template>
          </Input>
        </div>
        <select v-model="selectedStatus" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" @change="applyFilters">
          <option value="">{{ $t('fuel.all_statuses') }}</option>
          <option v-for="s in ['Approved', 'Pending Dept Head Approval', 'Pending Depot Manager Approval', 'Dept Head Approved', 'Rejected']" :key="s" :value="s">{{ s }}</option>
        </select>
        <Button variant="primary" size="sm" @click="applyFilters">{{ $t('common.apply') }}</Button>
      </div>
    </Card>

    <!-- Loading -->
    <div v-if="isLoading" class="space-y-4">
      <Card><Skeleton height="200px" /></Card>
    </div>

    <!-- Table -->
    <Card v-if="!isLoading" padding="none">
      <div class="p-4 border-b" style="border-color: var(--border-color);">
        <h2 class="text-section-title">{{ $t('fuel.refueling_records') }}</h2>
        <p class="text-xs mt-1" style="color: var(--text-muted)">{{ total }} {{ $t('common.total') }}</p>
      </div>

      <EmptyState
        v-if="records.length === 0"
        :icon="LucideFuel"
        :title="$t('fuel.no_records')"
        :description="$t('fuel.no_records_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b" style="border-color: var(--border-color);">
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('fuel.record_id') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('common.vehicle') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('common.date') }}</th>
              <th class="text-right px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('fuel.liters') }}</th>
              <th class="text-right px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('fuel.total_cost') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('fuel.station') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('common.status') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('fuel.over_quota') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in records"
              :key="r.name"
              class="border-b cursor-pointer transition-colors"
              :style="{ borderColor: 'var(--border-color)' }"
              @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = 'transparent'"
              @click="router.push(`/fuel/${r.name}`)"
            >
              <td class="px-4 py-3 font-medium" style="color: var(--accent)">{{ r.name }}</td>
              <td class="px-4 py-3" style="color: var(--text-primary)">{{ r.vehicle }}</td>
              <td class="px-4 py-3" style="color: var(--text-muted)">{{ formatDate(r.refuel_date) }}</td>
              <td class="px-4 py-3 text-right" style="color: var(--text-primary)">{{ r.liters?.toFixed(1) }} L</td>
              <td class="px-4 py-3 text-right" style="color: var(--text-primary)">{{ r.total_cost?.toLocaleString() }} ETB</td>
              <td class="px-4 py-3" style="color: var(--text-muted)">{{ r.fuel_station || '—' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="APPROVAL_VARIANTS[r.approval_status] || 'default'" size="sm">{{ r.approval_status }}</Badge>
              </td>
              <td class="px-4 py-3">
                <Badge v-if="r.is_over_quota" variant="danger" size="sm">{{ $t('fuel.over_quota') }}</Badge>
                <span v-else style="color: var(--text-muted)">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="flex items-center justify-between p-4 border-t" style="border-color: var(--border-color);">
        <Button variant="outline" size="sm" :disabled="page === 0" @click="prevPage">{{ $t('common.previous') }}</Button>
        <span class="text-sm" style="color: var(--text-muted)">{{ $t('common.page') }} {{ page + 1 }} {{ $t('common.of') }} {{ Math.ceil((total || 1) / PAGE_SIZE) }}</span>
        <Button variant="outline" size="sm" :disabled="(page + 1) * PAGE_SIZE >= total" @click="nextPage">{{ $t('common.next') }}</Button>
      </div>
    </Card>
  </div>
</template>
