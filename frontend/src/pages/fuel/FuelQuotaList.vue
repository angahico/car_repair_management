<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideFuel,
  LucideRefreshCw,
  LucideSearch,
  LucideEdit,
  LucideCheck,
  LucideX,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Input } from '@/components/ui'

const router = useRouter()
const { t } = useI18n()

interface QuotaRecord {
  name: string
  vehicle: string
  quota_month: string
  fuel_capacity_liters: number
  km_per_liter: number
  quota_liters: number
  consumed_liters: number
  remaining_liters: number
  status: string
}

const isLoading = ref(true)
const records = ref<QuotaRecord[]>([])
const total = ref(0)
const searchQuery = ref('')
const selectedStatus = ref('')
const page = ref(0)
const PAGE_SIZE = 20
const editingRow = ref<string | null>(null)
const editQuotaValue = ref(0)
const isSaving = ref(false)

const STATUS_VARIANTS: Record<string, string> = {
  Active: 'success',
  Exhausted: 'danger',
  Closed: 'default',
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

    const result = await apiCall<{ records: QuotaRecord[]; total: number }>(
      'car_repair_management.api.fuel.get_fuel_quotas',
      args,
    )
    records.value = result.records || []
    total.value = result.total || 0
  } catch (e) {
    console.warn('Failed to load quotas', e)
  } finally {
    isLoading.value = false
  }
}

function startEdit(r: QuotaRecord) {
  editingRow.value = r.name
  editQuotaValue.value = r.quota_liters
}

function cancelEdit() {
  editingRow.value = null
}

async function saveEdit(name: string) {
  isSaving.value = true
  try {
    await apiCall('car_repair_management.api.fuel.update_fuel_quota', {
      name,
      quota_liters: editQuotaValue.value,
    })
    editingRow.value = null
    await loadData()
  } catch (e: any) {
    alert(e.message || 'Failed to update quota')
  } finally {
    isSaving.value = false
  }
}

function usagePercent(r: QuotaRecord): number {
  if (!r.quota_liters) return 0
  return Math.min(100, Math.round((r.consumed_liters / r.quota_liters) * 100))
}

function applyFilters() {
  page.value = 0
  loadData()
}

function nextPage() {
  if ((page.value + 1) * PAGE_SIZE < total.value) { page.value++; loadData() }
}
function prevPage() {
  if (page.value > 0) { page.value--; loadData() }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div>
        <h1 class="text-page-title">{{ $t('fuel.quotas_title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">{{ $t('fuel.quotas_subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="loadData">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
        <Button variant="outline" @click="router.push('/fuel')">{{ $t('fuel.refueling_records') }}</Button>
      </div>
    </div>

    <!-- Filters -->
    <Card>
      <div class="flex flex-wrap items-end gap-3">
        <div class="flex-1 min-w-[200px]">
          <Input v-model="searchQuery" :placeholder="$t('fuel.search_quota_placeholder')" @keyup.enter="applyFilters">
            <template #prefix><LucideSearch class="size-4" style="color: var(--text-muted)" /></template>
          </Input>
        </div>
        <select v-model="selectedStatus" class="rounded-lg border px-3 py-2 text-sm" style="background: var(--bg-primary); color: var(--text-primary); border-color: var(--border-color);" @change="applyFilters">
          <option value="">{{ $t('fuel.all_statuses') }}</option>
          <option value="Active">Active</option>
          <option value="Exhausted">Exhausted</option>
          <option value="Closed">Closed</option>
        </select>
        <Button variant="primary" size="sm" @click="applyFilters">{{ $t('common.apply') }}</Button>
      </div>
    </Card>

    <!-- Loading -->
    <Card v-if="isLoading"><Skeleton height="300px" /></Card>

    <!-- Table -->
    <Card v-if="!isLoading" padding="none">
      <div class="p-4 border-b" style="border-color: var(--border-color);">
        <h2 class="text-section-title">{{ $t('fuel.quotas_title') }}</h2>
        <p class="text-xs mt-1" style="color: var(--text-muted)">{{ total }} {{ $t('common.total') }}</p>
      </div>

      <EmptyState
        v-if="records.length === 0"
        :icon="LucideFuel"
        :title="$t('fuel.no_quotas')"
        :description="$t('fuel.no_quotas_desc')"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b" style="border-color: var(--border-color)">
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('common.vehicle') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('fuel.quota_month') }}</th>
              <th class="text-right px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('fuel.monthly_quota') }}</th>
              <th class="text-right px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('fuel.consumed') }}</th>
              <th class="text-right px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('fuel.remaining') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('fuel.usage') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('common.status') }}</th>
              <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">{{ $t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in records"
              :key="r.name"
              class="border-b"
              :style="{ borderColor: 'var(--border-color)' }"
            >
              <td class="px-4 py-3 font-medium cursor-pointer" style="color: var(--accent)" @click="router.push(`/vehicles/${r.vehicle}`)">{{ r.vehicle }}</td>
              <td class="px-4 py-3" style="color: var(--text-primary)">{{ r.quota_month }}</td>
              <td class="px-4 py-3 text-right">
                <template v-if="editingRow === r.name">
                  <input v-model.number="editQuotaValue" type="number" step="1" min="0" class="w-20 h-8 px-2 text-right rounded border text-sm" style="background: var(--bg-tertiary); color: var(--text-primary); border-color: var(--border-color)" />
                </template>
                <template v-else>
                  <span style="color: var(--text-primary)">{{ r.quota_liters?.toFixed(0) }} L</span>
                </template>
              </td>
              <td class="px-4 py-3 text-right" style="color: var(--text-primary)">{{ r.consumed_liters?.toFixed(1) }} L</td>
              <td class="px-4 py-3 text-right" :style="{ color: (r.remaining_liters || 0) <= 0 ? '#ef4444' : 'var(--text-primary)' }">{{ r.remaining_liters?.toFixed(1) }} L</td>
              <td class="px-4 py-3">
                <div class="w-20 h-2 rounded-full overflow-hidden" style="background: var(--bg-tertiary)">
                  <div class="h-full rounded-full" :style="{ width: `${usagePercent(r)}%`, backgroundColor: usagePercent(r) >= 100 ? '#ef4444' : usagePercent(r) >= 80 ? '#f59e0b' : '#22c55e' }" />
                </div>
                <span class="text-xs" style="color: var(--text-muted)">{{ usagePercent(r) }}%</span>
              </td>
              <td class="px-4 py-3">
                <Badge :variant="STATUS_VARIANTS[r.status] || 'default'" size="sm">{{ r.status }}</Badge>
              </td>
              <td class="px-4 py-3">
                <template v-if="editingRow === r.name">
                  <div class="flex items-center gap-1">
                    <button class="p-1 rounded hover:opacity-70" style="color: #22c55e" :disabled="isSaving" @click="saveEdit(r.name)"><LucideCheck class="size-4" /></button>
                    <button class="p-1 rounded hover:opacity-70" style="color: var(--text-muted)" @click="cancelEdit"><LucideX class="size-4" /></button>
                  </div>
                </template>
                <template v-else>
                  <button class="p-1 rounded hover:opacity-70" style="color: var(--text-muted)" @click="startEdit(r)"><LucideEdit class="size-4" /></button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="flex items-center justify-between p-4 border-t" style="border-color: var(--border-color)">
        <Button variant="outline" size="sm" :disabled="page === 0" @click="prevPage">{{ $t('common.previous') }}</Button>
        <span class="text-sm" style="color: var(--text-muted)">{{ $t('common.page') }} {{ page + 1 }} {{ $t('common.of') }} {{ Math.ceil((total || 1) / PAGE_SIZE) }}</span>
        <Button variant="outline" size="sm" :disabled="(page + 1) * PAGE_SIZE >= total" @click="nextPage">{{ $t('common.next') }}</Button>
      </div>
    </Card>
  </div>
</template>
