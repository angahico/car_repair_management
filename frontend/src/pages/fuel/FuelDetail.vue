<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideArrowLeft,
  LucideFuel,
  LucideCheck,
  LucideX,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'
import ActivityTimeline from '@/components/common/ActivityTimeline.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const data = ref<any>(null)
const isActioning = ref(false)
const activityKey = ref(0)

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
    const result = await apiCall<any>(
      'car_repair_management.api.fuel.get_refueling_detail',
      { name: props.id },
    )
    data.value = result
  } catch (e) {
    console.warn('Failed to load refueling detail', e)
  } finally {
    isLoading.value = false
  }
}

async function handleApprove(role: string) {
  isActioning.value = true
  try {
    await apiCall('car_repair_management.api.fuel.approve_refueling', {
      name: props.id,
      role,
    })
    await loadData()
    activityKey.value++
  } catch (e: any) {
    alert(e.message || 'Failed to approve')
  } finally {
    isActioning.value = false
  }
}

async function handleReject() {
  const reason = prompt(t('fuel.reject_reason_prompt'))
  if (reason === null) return
  isActioning.value = true
  try {
    await apiCall('car_repair_management.api.fuel.reject_refueling', {
      name: props.id,
      reason: reason || '',
    })
    await loadData()
    activityKey.value++
  } catch (e: any) {
    alert(e.message || 'Failed to reject')
  } finally {
    isActioning.value = false
  }
}

const needsDeptHeadApproval = computed(() =>
  data.value?.doc?.approval_status === 'Pending Dept Head Approval'
)
const needsDepotManagerApproval = computed(() =>
  ['Pending Depot Manager Approval', 'Dept Head Approved'].includes(data.value?.doc?.approval_status)
)

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div class="flex items-center gap-4">
        <Button variant="outline" @click="router.push('/fuel')">
          <LucideArrowLeft class="size-4" />
        </Button>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-page-title">{{ data?.doc?.name || id }}</h1>
            <Badge v-if="data?.doc?.approval_status" :variant="APPROVAL_VARIANTS[data.doc.approval_status] || 'default'">{{ data.doc.approval_status }}</Badge>
            <Badge v-if="data?.doc?.is_over_quota" variant="danger">{{ $t('fuel.over_quota') }}</Badge>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button v-if="needsDeptHeadApproval" variant="primary" :loading="isActioning" @click="handleApprove('dept_head')">
          <LucideCheck class="size-4" /> {{ $t('fuel.approve_dept_head') }}
        </Button>
        <Button v-if="needsDepotManagerApproval" variant="primary" :loading="isActioning" @click="handleApprove('depot_manager')">
          <LucideCheck class="size-4" /> {{ $t('fuel.approve_depot_manager') }}
        </Button>
        <Button v-if="needsDeptHeadApproval || needsDepotManagerApproval" variant="danger" :loading="isActioning" @click="handleReject">
          <LucideX class="size-4" /> {{ $t('issues.reject') }}
        </Button>
      </div>
    </div>

    <template v-if="isLoading">
      <Card><Skeleton height="200px" /></Card>
    </template>

    <template v-if="!isLoading && data">
      <Card>
        <h2 class="text-section-title mb-4">{{ $t('fuel.refueling_details') }}</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('common.vehicle') }}</p>
            <p class="text-sm font-medium cursor-pointer" style="color: var(--accent)" @click="router.push(`/vehicles/${data.doc.vehicle}`)">{{ data.doc.vehicle }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('common.date') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ formatDate(data.doc.refuel_date) }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.liters') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.liters?.toFixed(1) }} L</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.cost_per_liter') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.cost_per_liter?.toFixed(2) }} ETB</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.total_cost') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.total_cost?.toLocaleString() }} ETB</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.station') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.fuel_station || '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.odometer') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.odometer_reading ? `${data.doc.odometer_reading.toLocaleString()} km` : '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.driver') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.driver || '—' }}</p>
          </div>
        </div>
        <div v-if="data.doc.notes" class="mt-4 pt-4 border-t" :style="{ borderColor: 'var(--border-color)' }">
          <p class="text-xs mb-1" style="color: var(--text-muted)">{{ $t('common.notes') }}</p>
          <p class="text-sm" style="color: var(--text-primary)">{{ data.doc.notes }}</p>
        </div>
      </Card>

      <!-- Quota Info -->
      <Card v-if="data.quota">
        <h2 class="text-section-title mb-4">{{ $t('fuel.quota_status') }}</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.monthly_quota') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.quota.quota_liters?.toFixed(1) }} L</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.consumed') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.quota.consumed_liters?.toFixed(1) }} L</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.remaining') }}</p>
            <p class="text-sm font-medium" :style="{ color: (data.quota.remaining_liters || 0) <= 0 ? '#ef4444' : 'var(--text-primary)' }">{{ data.quota.remaining_liters?.toFixed(1) }} L</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('fuel.quota_month') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.quota.quota_month }}</p>
          </div>
        </div>
      </Card>

      <!-- Activity -->
      <ActivityTimeline :key="activityKey" doctype="Vehicle Refueling Record" :name="id" />
    </template>
  </div>
</template>
