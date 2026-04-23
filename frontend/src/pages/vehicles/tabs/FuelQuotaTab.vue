<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideFuel,
  LucideLoader2,
  LucideRefreshCw,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'

const props = defineProps<{ vehicleId: string }>()
const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const quota = ref<any>(null)
const records = ref<any[]>([])

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
    const [quotaResult, recordsResult] = await Promise.all([
      apiCall<any>('car_repair_management.api.fuel.get_vehicle_quota_status', {
        vehicle: props.vehicleId,
      }),
      apiCall<any>('car_repair_management.api.fuel.get_refueling_records', {
        vehicle: props.vehicleId,
        limit_page_length: 20,
      }),
    ])
    quota.value = quotaResult
    records.value = recordsResult?.records || []
  } catch (e) {
    console.warn('Failed to load fuel data', e)
  } finally {
    isLoading.value = false
  }
}

const usagePercent = () => {
  if (!quota.value || !quota.value.quota_liters) return 0
  return Math.min(100, Math.round((quota.value.consumed_liters / quota.value.quota_liters) * 100))
}

const usageColor = () => {
  const pct = usagePercent()
  if (pct >= 100) return '#ef4444'
  if (pct >= 80) return '#f59e0b'
  return '#22c55e'
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading -->
    <div v-if="isLoading" class="space-y-4">
      <Card><Skeleton height="120px" /></Card>
      <Card><Skeleton height="200px" /></Card>
    </div>

    <template v-else>
      <!-- Quota Overview -->
      <Card>
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <LucideFuel class="size-5" style="color: var(--text-muted)" />
            <h2 class="text-section-title">{{ $t('fuel.quota_status') }}</h2>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs px-2 py-1 rounded" style="background: var(--bg-tertiary); color: var(--text-muted);">
              {{ quota?.quota_month || '—' }}
            </span>
            <Button variant="outline" size="sm" @click="loadData">
              <LucideRefreshCw class="size-3.5" />
            </Button>
          </div>
        </div>

        <div v-if="quota && quota.quota_liters > 0">
          <!-- Usage Bar -->
          <div class="mb-4">
            <div class="flex justify-between text-sm mb-1">
              <span style="color: var(--text-primary)">
                {{ quota.consumed_liters?.toFixed(1) }} / {{ quota.quota_liters?.toFixed(1) }} L
              </span>
              <span :style="{ color: usageColor() }" class="font-medium">
                {{ usagePercent() }}%
              </span>
            </div>
            <div class="h-3 rounded-full overflow-hidden" style="background: var(--bg-tertiary)">
              <div
                class="h-full rounded-full transition-all"
                :style="{ width: `${usagePercent()}%`, backgroundColor: usageColor() }"
              />
            </div>
          </div>

          <!-- Stats -->
          <div class="grid grid-cols-3 gap-3">
            <div class="p-3 rounded-lg text-center" style="background: var(--bg-tertiary)">
              <p class="text-lg font-bold" style="color: var(--text-primary)">{{ quota.quota_liters?.toFixed(0) }}</p>
              <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.monthly_quota') }}</p>
            </div>
            <div class="p-3 rounded-lg text-center" style="background: var(--bg-tertiary)">
              <p class="text-lg font-bold" style="color: var(--text-primary)">{{ quota.consumed_liters?.toFixed(1) }}</p>
              <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.consumed') }}</p>
            </div>
            <div class="p-3 rounded-lg text-center" style="background: var(--bg-tertiary)">
              <p class="text-lg font-bold" :style="{ color: (quota.remaining_liters || 0) <= 0 ? '#ef4444' : 'var(--text-primary)' }">
                {{ quota.remaining_liters?.toFixed(1) }}
              </p>
              <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.remaining') }}</p>
            </div>
          </div>

          <div v-if="quota.fuel_capacity_liters" class="mt-3 text-xs" style="color: var(--text-muted)">
            {{ $t('fuel.tank_capacity_info') }}: {{ quota.fuel_capacity_liters }} L
            <span v-if="quota.km_per_liter"> · {{ quota.km_per_liter }} km/L</span>
          </div>
        </div>

        <div v-else class="text-center py-6">
          <LucideFuel class="size-10 mx-auto mb-2" style="color: var(--text-muted)" />
          <p class="text-sm" style="color: var(--text-muted)">{{ $t('fuel.no_quota_configured') }}</p>
          <p class="text-xs mt-1" style="color: var(--text-muted)">{{ $t('fuel.configure_quota_hint') }}</p>
        </div>
      </Card>

      <!-- Recent Refueling Records -->
      <Card>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-section-title">{{ $t('fuel.recent_refueling') }}</h2>
          <Button variant="outline" size="sm" @click="router.push(`/fuel?vehicle=${props.vehicleId}`)">
            {{ $t('common.view_all') }}
          </Button>
        </div>

        <div v-if="records.length === 0" class="text-center py-4">
          <p class="text-sm" style="color: var(--text-muted)">{{ $t('fuel.no_records') }}</p>
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="r in records"
            :key="r.name"
            class="flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors"
            style="background: var(--bg-tertiary)"
            @click="router.push(`/fuel/${r.name}`)"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium" style="color: var(--text-primary)">{{ r.liters?.toFixed(1) }} L</span>
                <span class="text-xs" style="color: var(--text-muted)">{{ formatDate(r.refuel_date) }}</span>
              </div>
              <p v-if="r.fuel_station" class="text-xs mt-0.5" style="color: var(--text-muted)">{{ r.fuel_station }}</p>
            </div>
            <div class="flex items-center gap-2">
              <span v-if="r.total_cost" class="text-sm" style="color: var(--text-primary)">{{ r.total_cost?.toLocaleString() }} ETB</span>
              <Badge :variant="APPROVAL_VARIANTS[r.approval_status] || 'default'" size="sm">{{ r.approval_status }}</Badge>
            </div>
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>
