<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideArrowLeft,
  LucideBell,
  LucideHistory,
  LucideShield,
  LucideCar,
  LucideBarChart3,
  LucideSettings,
  LucideExternalLink,
  LucideCalendarClock,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface AffectedVehicle {
  name: string
  license_plate: string | null
  make: string | null
  model: string | null
  year: number | null
}

interface VersionChange {
  changed: string
  changed_by: string
  creation: string
}

interface RecallDetailData {
  name: string
  title: string
  description: string | null
  manufacturer: string
  affected_models: string | null
  affected_years: string | null
  issue_type: string | null
  external_reference: string | null
  recall_start_date: string | null
  deadline: string | null
  status: string
  priority: string
  vehicles_affected: number
  vehicles_completed: number
  compliance_pct: number
  owner: string
  creation: string
  modified: string
  affected_vehicles: AffectedVehicle[]
  versions: VersionChange[]
}

const props = defineProps<{ id: string }>()
const router = useRouter()

const isLoading = ref(true)
const detail = ref<RecallDetailData | null>(null)

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Active: 'danger',
  'In Progress': 'warning',
  Completed: 'success',
  Cancelled: 'default',
}

const PRIORITY_VARIANTS: Record<string, StatusVariant> = {
  Low: 'default',
  Medium: 'warning',
  High: 'danger',
  Critical: 'danger',
}

const remaining = computed(() => {
  if (!detail.value) return 0
  return Math.max(0, detail.value.vehicles_affected - detail.value.vehicles_completed)
})

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

function complianceColor(pct: number): string {
  if (pct >= 80) return '#22c55e'
  if (pct >= 50) return '#f59e0b'
  return '#ef4444'
}

async function loadDetail() {
  isLoading.value = true
  try {
    detail.value = await apiCall<RecallDetailData>(
      'car_repair_management.api.issue.get_recall_detail',
      { name: props.id },
    )
  } catch (e) {
    console.warn('Failed to load recall detail', e)
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.push('/issues/recalls')
}

onMounted(loadDetail)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <div v-if="isLoading" class="space-y-6">
      <Skeleton height="48px" />
      <Skeleton height="200px" />
      <Skeleton height="160px" />
      <Skeleton height="120px" />
    </div>

    <template v-else-if="detail">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <button
            class="w-9 h-9 flex items-center justify-center rounded-lg transition-colors"
            style="background: var(--bg-tertiary); color: var(--text-secondary)"
            @click="goBack"
          >
            <LucideArrowLeft class="size-5" />
          </button>
          <div>
            <h1 class="text-page-title" style="color: var(--text-primary)">{{ detail.title || detail.name }}</h1>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ detail.name }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Badge :variant="STATUS_VARIANTS[detail.status] || 'default'" size="md">
            {{ detail.status }}
          </Badge>
          <Badge :variant="PRIORITY_VARIANTS[detail.priority] || 'default'" size="md">
            {{ detail.priority }}
          </Badge>
        </div>
      </div>

      <!-- Recall Overview Card -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideBell class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Recall Overview</h2>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Title</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.title }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Manufacturer</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.manufacturer }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Issue Type</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.issue_type || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Affected Models</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.affected_models || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Affected Years</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.affected_years || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">External Reference</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.external_reference || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Start Date</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDate(detail.recall_start_date) }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Deadline</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDate(detail.deadline) }}</p>
          </div>
        </div>
        <div v-if="detail.description" class="mt-4 pt-4 border-t" style="border-color: var(--border-subtle)">
          <p class="text-xs font-medium mb-1" style="color: var(--text-muted)">Description</p>
          <p class="text-sm whitespace-pre-wrap" style="color: var(--text-secondary)">{{ detail.description }}</p>
        </div>
        <!-- Compliance Progress -->
        <div class="mt-4 pt-4 border-t" style="border-color: var(--border-subtle)">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs font-medium" style="color: var(--text-muted)">Compliance</p>
            <span class="text-sm font-semibold" :style="{ color: complianceColor(detail.compliance_pct) }">
              {{ detail.compliance_pct }}%
            </span>
          </div>
          <div class="h-2.5 rounded-full" style="background: var(--bg-tertiary)">
            <div
              class="h-2.5 rounded-full transition-all"
              :style="{ width: `${Math.min(detail.compliance_pct, 100)}%`, backgroundColor: complianceColor(detail.compliance_pct) }"
            />
          </div>
        </div>
      </Card>

      <!-- Eligibility Rules Card -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideShield class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Eligibility Rules</h2>
        </div>
        <div class="space-y-3">
          <div class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary)">
            <span class="text-xs font-medium w-32 shrink-0" style="color: var(--text-muted)">Manufacturer</span>
            <span class="text-sm" style="color: var(--text-primary)">{{ detail.manufacturer }}</span>
          </div>
          <div class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary)">
            <span class="text-xs font-medium w-32 shrink-0" style="color: var(--text-muted)">Affected Models</span>
            <span class="text-sm" style="color: var(--text-primary)">{{ detail.affected_models || 'All models' }}</span>
          </div>
          <div class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary)">
            <span class="text-xs font-medium w-32 shrink-0" style="color: var(--text-muted)">Affected Years</span>
            <span class="text-sm" style="color: var(--text-primary)">{{ detail.affected_years || 'All years' }}</span>
          </div>
        </div>
      </Card>

      <!-- Affected Vehicles Card -->
      <Card padding="none">
        <div class="px-4 pt-4 pb-3 flex items-center gap-2">
          <LucideCar class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Affected Vehicles ({{ detail.affected_vehicles?.length || 0 }})
          </h2>
        </div>

        <div v-if="!detail.affected_vehicles || detail.affected_vehicles.length === 0" class="px-4 pb-4">
          <div class="flex flex-col items-center py-8 text-center">
            <LucideCar class="size-8 mb-2" style="color: var(--text-muted)" />
            <p class="text-sm" style="color: var(--text-muted)">No matching vehicles found in the fleet</p>
          </div>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Vehicle ID</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">License Plate</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Make</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Model</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Year</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="v in detail.affected_vehicles"
                :key="v.name"
                class="border-b"
                style="border-color: var(--border-subtle)"
              >
                <td class="px-4 py-3 font-medium">{{ v.name }}</td>
                <td class="px-4 py-3" style="color: var(--text-secondary)">{{ v.license_plate || '—' }}</td>
                <td class="px-4 py-3">{{ v.make || '—' }}</td>
                <td class="px-4 py-3">{{ v.model || '—' }}</td>
                <td class="px-4 py-3">{{ v.year || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Progress Tracking Card -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideBarChart3 class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Progress Tracking</h2>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div class="p-3 rounded-lg text-center" style="background: var(--bg-tertiary)">
            <p class="text-2xl font-bold" style="color: var(--text-primary)">{{ detail.vehicles_affected }}</p>
            <p class="text-xs mt-1" style="color: var(--text-muted)">Vehicles Affected</p>
          </div>
          <div class="p-3 rounded-lg text-center" style="background: var(--bg-tertiary)">
            <p class="text-2xl font-bold" style="color: #22c55e">{{ detail.vehicles_completed }}</p>
            <p class="text-xs mt-1" style="color: var(--text-muted)">Vehicles Completed</p>
          </div>
          <div class="p-3 rounded-lg text-center" style="background: var(--bg-tertiary)">
            <p class="text-2xl font-bold" :style="{ color: complianceColor(detail.compliance_pct) }">{{ detail.compliance_pct }}%</p>
            <p class="text-xs mt-1" style="color: var(--text-muted)">Compliance</p>
          </div>
          <div class="p-3 rounded-lg text-center" style="background: var(--bg-tertiary)">
            <p class="text-2xl font-bold" :style="{ color: remaining > 0 ? '#f59e0b' : '#22c55e' }">{{ remaining }}</p>
            <p class="text-xs mt-1" style="color: var(--text-muted)">Remaining</p>
          </div>
        </div>
        <div>
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs font-medium" style="color: var(--text-muted)">Overall Progress</p>
            <span class="text-xs font-semibold" :style="{ color: complianceColor(detail.compliance_pct) }">
              {{ detail.vehicles_completed }} / {{ detail.vehicles_affected }}
            </span>
          </div>
          <div class="h-3 rounded-full" style="background: var(--bg-tertiary)">
            <div
              class="h-3 rounded-full transition-all"
              :style="{ width: `${Math.min(detail.compliance_pct, 100)}%`, backgroundColor: complianceColor(detail.compliance_pct) }"
            />
          </div>
        </div>
      </Card>

      <!-- Actions Card -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideSettings class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Actions</h2>
        </div>
        <div class="flex flex-wrap gap-3">
          <Button variant="outline" disabled>
            <LucideCalendarClock class="size-4" />
            Bulk Schedule Inspections
            <span class="text-xs opacity-60 ml-1">(Coming soon)</span>
          </Button>
          <Button variant="outline" disabled>
            Bulk Create Work Orders
            <span class="text-xs opacity-60 ml-1">(Coming soon)</span>
          </Button>
          <Button variant="outline" disabled>
            Mark All Addressed
            <span class="text-xs opacity-60 ml-1">(Coming soon)</span>
          </Button>
          <a :href="`/app/vehicle-recall/${id}`" target="_blank">
            <Button variant="secondary">
              <LucideExternalLink class="size-4" />
              Edit in Desk
            </Button>
          </a>
        </div>
      </Card>

      <!-- Audit Trail Card -->
      <Card v-if="detail.versions && detail.versions.length > 0">
        <div class="flex items-center gap-2 mb-4">
          <LucideHistory class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Audit Trail</h2>
        </div>
        <div class="space-y-3">
          <div
            v-for="(v, idx) in detail.versions"
            :key="idx"
            class="flex items-start gap-3 pl-2 border-l-2"
            style="border-color: var(--border-color)"
          >
            <div class="flex-1 py-1">
              <p class="text-sm" style="color: var(--text-primary)">{{ v.changed }}</p>
              <p class="text-xs mt-0.5" style="color: var(--text-muted)">
                {{ v.changed_by }} · {{ formatDateTime(v.creation) }}
              </p>
            </div>
          </div>
        </div>
      </Card>
    </template>

    <!-- Error / Not Found -->
    <Card v-else>
      <div class="flex flex-col items-center py-12 text-center">
        <p class="text-lg font-semibold" style="color: var(--text-primary)">Recall not found</p>
        <p class="text-sm mt-1 mb-4" style="color: var(--text-muted)">
          The recall "{{ id }}" could not be loaded.
        </p>
        <Button variant="secondary" @click="goBack">
          <LucideArrowLeft class="size-4" />
          Back to Recalls
        </Button>
      </div>
    </Card>
  </div>
</template>
