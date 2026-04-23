<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideArrowLeft,
  LucideUser,
  LucideEdit,
  LucideCar,
  LucideHistory,
  LucideClipboardList,
  LucideBarChart3,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState } from '@/components/ui'
import type { StatusVariant } from '@/types'

const props = defineProps<{ id: string }>()
const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const doc = ref<any>(null)
const vehicleAssignments = ref<any[]>([])
const repairOrders = ref<any[]>([])
const performance = ref<any>({
  completed_wo_count: 0,
  active_wo_count: 0,
  avg_completion_days: 0,
})
const auditTrail = ref<any[]>([])

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Active: 'success',
  Inactive: 'default',
  Suspended: 'warning',
  Left: 'danger',
}

const RO_STATUS_VARIANTS: Record<string, StatusVariant> = {
  Draft: 'default',
  Scheduled: 'info',
  'In Progress': 'primary',
  'Awaiting Parts': 'warning',
  'Ready for Handover': 'success',
  Delivered: 'success',
  Closed: 'default',
  Cancelled: 'danger',
}

const VEHICLE_STATUS_VARIANTS: Record<string, StatusVariant> = {
  Active: 'success',
  'In Maintenance': 'warning',
  'Undergoing Tests': 'info',
  'Delivered to Customer': 'default',
  Scrapped: 'danger',
}

const ASSIGNMENT_STATUS_VARIANTS: Record<string, StatusVariant> = {
  Active: 'success',
  Removed: 'danger',
  'Removal Requested': 'warning',
}

const ACTIVE_RO_STATUSES = ['Draft', 'Scheduled', 'In Progress', 'Awaiting Parts', 'Ready for Handover']

const currentVehicleAssignments = computed(() =>
  vehicleAssignments.value.filter(a => a.assignment_status === 'Active')
)
const pastVehicleAssignments = computed(() =>
  vehicleAssignments.value.filter(a => a.assignment_status !== 'Active')
)
const currentRepairOrders = computed(() =>
  repairOrders.value.filter(o => ACTIVE_RO_STATUSES.includes(o.status))
)
const pastRepairOrders = computed(() =>
  repairOrders.value.filter(o => !ACTIVE_RO_STATUSES.includes(o.status))
)

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const parts = String(dateStr).split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    return d.toLocaleDateString()
  }
  return String(dateStr)
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—'
  const [datePart, timePart] = String(dateStr).split(' ')
  const parts = datePart.split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    const formatted = d.toLocaleDateString()
    return timePart ? `${formatted} ${timePart.substring(0, 5)}` : formatted
  }
  return String(dateStr)
}

function formatCurrency(val: number): string {
  return 'ETB ' + (val?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00')
}

async function loadData() {
  isLoading.value = true
  try {
    const data = await apiCall<any>(
      'car_repair_management.api.employee.get_employee_detail',
      { name: props.id },
    )
    doc.value = data.doc
    vehicleAssignments.value = data.vehicle_assignments || []
    repairOrders.value = data.repair_orders || []
    performance.value = data.performance || {}
    auditTrail.value = data.audit_trail || []
  } catch (e) {
    console.warn('Failed to load employee', e)
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.push('/employees')
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading -->
    <div v-if="isLoading" class="space-y-6">
      <Skeleton height="48px" />
      <Skeleton height="200px" />
      <Skeleton height="160px" />
    </div>

    <template v-else-if="doc">
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
          <img v-if="doc.image" :src="doc.image" class="w-12 h-12 rounded-full object-cover" />
          <div v-else class="w-12 h-12 rounded-full flex items-center justify-center" style="background: var(--bg-tertiary)">
            <LucideUser class="size-6" style="color: var(--text-secondary)" />
          </div>
          <div>
            <h1 class="text-page-title" style="color: var(--text-primary)">{{ doc.employee_name || doc.name }}</h1>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ doc.name }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Badge :variant="STATUS_VARIANTS[doc.status] || 'default'" size="md">{{ doc.status }}</Badge>
          <a :href="`/app/employee/${doc.name}`" target="_blank">
            <Button variant="outline">
              <LucideEdit class="size-4" />
              Edit
            </Button>
          </a>
        </div>
      </div>

      <!-- Profile Card -->
      <Card>
        <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">Profile</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Full Name</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">
              {{ [doc.first_name, doc.last_name].filter(Boolean).join(' ') || doc.employee_name || '—' }}
            </p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Department</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.department || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Designation</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.designation || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Company</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.company || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Employment Type</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.employment_type || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Date of Joining</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDate(doc.date_of_joining) }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Phone</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.cell_number || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Email</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.company_email || doc.personal_email || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Reports To</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.reports_to || '—' }}</p>
          </div>
        </div>
      </Card>

      <!-- Performance Card -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideBarChart3 class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Performance</h2>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div class="text-center p-4 rounded-lg" style="background: var(--bg-tertiary)">
            <p class="text-2xl font-bold" style="color: var(--text-primary)">{{ performance.completed_wo_count }}</p>
            <p class="text-xs mt-1" style="color: var(--text-muted)">Completed WOs</p>
          </div>
          <div class="text-center p-4 rounded-lg" style="background: var(--bg-tertiary)">
            <p class="text-2xl font-bold" style="color: var(--text-primary)">{{ performance.active_wo_count }}</p>
            <p class="text-xs mt-1" style="color: var(--text-muted)">Active WOs</p>
          </div>
          <div class="text-center p-4 rounded-lg" style="background: var(--bg-tertiary)">
            <p class="text-2xl font-bold" style="color: var(--text-primary)">{{ performance.avg_completion_days }}</p>
            <p class="text-xs mt-1" style="color: var(--text-muted)">Avg Days to Complete</p>
          </div>
        </div>
      </Card>

      <!-- Current Vehicle Assignments -->
      <Card padding="none">
        <div class="px-4 pt-4 pb-3 flex items-center gap-2">
          <LucideCar class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Current Vehicle Assignments ({{ currentVehicleAssignments.length }})
          </h2>
        </div>

        <div v-if="currentVehicleAssignments.length === 0" class="px-4 pb-4">
          <EmptyState title="No current assignments" description="This employee has no active vehicle assignments" />
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Vehicle</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Make / Model</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Role</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Vehicle Status</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Assigned</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="a in currentVehicleAssignments"
                :key="`${a.vehicle}-${a.role}`"
                class="border-b cursor-pointer transition-colors"
                style="border-color: var(--border-subtle)"
                @click="router.push(`/vehicles/${a.vehicle}`)"
                @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
                @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
              >
                <td class="px-4 py-3 font-medium whitespace-nowrap">{{ a.license_plate }}</td>
                <td class="px-4 py-3 whitespace-nowrap">{{ [a.make, a.model].filter(Boolean).join(' ') || '—' }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="a.role === 'Driver' ? 'primary' : 'info'" size="sm">{{ a.role }}</Badge>
                </td>
                <td class="px-4 py-3">
                  <Badge :variant="VEHICLE_STATUS_VARIANTS[a.vehicle_status] || 'default'" size="sm">{{ a.vehicle_status || '—' }}</Badge>
                </td>
                <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ formatDate(a.assigned_date) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Past Vehicle Assignments -->
      <Card v-if="pastVehicleAssignments.length > 0" padding="none">
        <div class="px-4 pt-4 pb-3 flex items-center gap-2">
          <LucideHistory class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Past Vehicle Assignments ({{ pastVehicleAssignments.length }})
          </h2>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Vehicle</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Make / Model</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Role</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Status</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Assigned</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Ended</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="a in pastVehicleAssignments"
                :key="`${a.vehicle}-${a.role}-${a.ended_date}`"
                class="border-b cursor-pointer transition-colors"
                style="border-color: var(--border-subtle)"
                @click="router.push(`/vehicles/${a.vehicle}`)"
                @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
                @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
              >
                <td class="px-4 py-3 font-medium whitespace-nowrap">{{ a.license_plate }}</td>
                <td class="px-4 py-3 whitespace-nowrap">{{ [a.make, a.model].filter(Boolean).join(' ') || '—' }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="a.role === 'Driver' ? 'primary' : 'info'" size="sm">{{ a.role }}</Badge>
                </td>
                <td class="px-4 py-3">
                  <Badge :variant="ASSIGNMENT_STATUS_VARIANTS[a.assignment_status] || 'default'" size="sm">{{ a.assignment_status }}</Badge>
                </td>
                <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ formatDate(a.assigned_date) }}</td>
                <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ formatDate(a.ended_date) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Current Repair Order Assignments -->
      <Card padding="none">
        <div class="px-4 pt-4 pb-3 flex items-center gap-2">
          <LucideClipboardList class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Current Repair Orders ({{ currentRepairOrders.length }})
          </h2>
        </div>

        <div v-if="currentRepairOrders.length === 0" class="px-4 pb-4">
          <EmptyState title="No active repair orders" description="No in-progress repair orders assigned to this employee" />
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Order</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Vehicle</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Status</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Cost</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Created</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="ro in currentRepairOrders"
                :key="ro.name"
                class="border-b cursor-pointer transition-colors"
                style="border-color: var(--border-subtle)"
                @click="router.push(`/repair-orders/${ro.name}`)"
                @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
                @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
              >
                <td class="px-4 py-3 font-medium whitespace-nowrap">{{ ro.name }}</td>
                <td class="px-4 py-3 whitespace-nowrap">{{ ro.vehicle || '—' }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="RO_STATUS_VARIANTS[ro.status] || 'default'" size="sm">{{ ro.status }}</Badge>
                </td>
                <td class="px-4 py-3 text-right">{{ formatCurrency(ro.total_job_cost || 0) }}</td>
                <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ formatDate(ro.creation) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Past Repair Orders -->
      <Card v-if="pastRepairOrders.length > 0" padding="none">
        <div class="px-4 pt-4 pb-3 flex items-center gap-2">
          <LucideHistory class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Past Repair Orders ({{ pastRepairOrders.length }})
          </h2>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Order</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Vehicle</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Status</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Cost</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Created</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="ro in pastRepairOrders"
                :key="ro.name"
                class="border-b cursor-pointer transition-colors"
                style="border-color: var(--border-subtle)"
                @click="router.push(`/repair-orders/${ro.name}`)"
                @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
                @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
              >
                <td class="px-4 py-3 font-medium whitespace-nowrap">{{ ro.name }}</td>
                <td class="px-4 py-3 whitespace-nowrap">{{ ro.vehicle || '—' }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="RO_STATUS_VARIANTS[ro.status] || 'default'" size="sm">{{ ro.status }}</Badge>
                </td>
                <td class="px-4 py-3 text-right">{{ formatCurrency(ro.total_job_cost || 0) }}</td>
                <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ formatDate(ro.creation) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Audit Trail -->
      <Card v-if="auditTrail.length > 0">
        <div class="flex items-center gap-2 mb-4">
          <LucideHistory class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Audit Trail</h2>
        </div>
        <div class="space-y-3">
          <div
            v-for="(v, idx) in auditTrail"
            :key="idx"
            class="flex items-start gap-3 pl-2 border-l-2"
            style="border-color: var(--border-color)"
          >
            <div class="flex-1 py-1">
              <p class="text-sm" style="color: var(--text-primary)">Record updated</p>
              <p class="text-xs mt-0.5" style="color: var(--text-muted)">
                {{ v.owner }} · {{ formatDateTime(v.creation) }}
              </p>
            </div>
          </div>
        </div>
      </Card>
    </template>

    <!-- Not Found -->
    <Card v-else>
      <div class="flex flex-col items-center py-12 text-center">
        <p class="text-lg font-semibold" style="color: var(--text-primary)">Employee not found</p>
        <p class="text-sm mt-1 mb-4" style="color: var(--text-muted)">
          The employee "{{ id }}" could not be loaded.
        </p>
        <Button variant="secondary" @click="goBack">
          <LucideArrowLeft class="size-4" />
          Back to Employees
        </Button>
      </div>
    </Card>
  </div>
</template>
