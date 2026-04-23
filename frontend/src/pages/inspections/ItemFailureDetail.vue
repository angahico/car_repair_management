<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import {
  LucideArrowLeft,
  LucideAlertTriangle,
  LucideImage,
  LucideWrench,
  LucideClock,
  LucideHistory,
  LucideCheckCircle,
  LucideExternalLink,
  LucideLoader2,
  LucideX,
  LucideFileText,
  LucideRepeat,
  LucideClipboardCheck,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'
import type { StatusVariant } from '@/types'

const props = defineProps<{ id: string }>()
const router = useRouter()

// --- Types ---
interface FailureDoc {
  name: string
  item_name: string
  vehicle: string
  inspection: string | null
  severity: string
  status: string
  failure_reason: string | null
  resolution_type: string | null
  linked_work_order: string | null
  assigned_to: string | null
  evidence: string | null
  is_recurring: number
  reported_date: string | null
  resolved_date: string | null
  notes: string | null
  owner: string
  creation: string
  modified: string
}

interface OccurrenceRecord {
  name: string
  reported_date: string | null
  severity: string
  status: string
  inspection: string | null
  resolved_date: string | null
}

interface VersionEntry {
  name: string
  owner: string
  creation: string
  data: string
}

const SEVERITY_VARIANTS: Record<string, StatusVariant> = {
  Low: 'default',
  Medium: 'warning',
  High: 'danger',
  Critical: 'danger',
}

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Open: 'warning',
  Converted: 'info',
  Resolved: 'success',
  Ignored: 'default',
}

// --- State ---
const isLoading = ref(true)
const doc = ref<FailureDoc | null>(null)
const occurrenceHistory = ref<OccurrenceRecord[]>([])
const auditTrail = ref<VersionEntry[]>([])
const actionLoading = ref<string | null>(null)

// --- Helpers ---
function formatDisplayDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const parts = dateStr.split('-')
  if (parts.length !== 3) return dateStr
  const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
  return d.toLocaleDateString()
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—'
  const [datePart, timePart] = dateStr.split(' ')
  const parts = datePart.split('-')
  if (parts.length !== 3) return dateStr
  const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
  const formatted = d.toLocaleDateString()
  return timePart ? `${formatted} ${timePart.substring(0, 5)}` : formatted
}

function parseVersionChanges(data: string): string[] {
  try {
    const parsed = JSON.parse(data)
    const changes: string[] = []
    if (parsed.changed) {
      for (const [field, oldVal, newVal] of parsed.changed) {
        changes.push(`${field}: ${oldVal || '(empty)'} → ${newVal || '(empty)'}`)
      }
    }
    return changes
  } catch {
    return []
  }
}

// --- Load ---
async function loadDetail() {
  isLoading.value = true
  try {
    const res = await apiCall<any>(
      'car_repair_management.api.inspection.get_failure_detail',
      { name: props.id },
    )
    doc.value = res.doc
    occurrenceHistory.value = res.occurrence_history || []
    auditTrail.value = res.audit_trail || []
  } catch (e) {
    console.warn('Failed to load failure detail', e)
  } finally {
    isLoading.value = false
  }
}

// --- Actions ---
async function createWorkOrder() {
  if (!doc.value) return
  actionLoading.value = 'create_wo'
  try {
    const result = await apiCall<any>(
      'car_repair_management.api.inspection.create_work_order_from_failure',
      { name: doc.value.name },
    )
    if (result.repair_order) {
      router.push(`/repair-orders/${result.repair_order}`)
    }
  } catch (e) {
    console.warn('Failed to create work order', e)
  } finally {
    actionLoading.value = null
  }
}

async function resolveFailure() {
  if (!doc.value) return
  actionLoading.value = 'resolve'
  try {
    await apiCall(
      'car_repair_management.api.inspection.update_failure',
      { name: doc.value.name, updates: JSON.stringify({ status: 'Resolved' }) },
    )
    await loadDetail()
  } catch (e) {
    console.warn('Failed to resolve failure', e)
  } finally {
    actionLoading.value = null
  }
}

async function ignoreFailure() {
  if (!doc.value) return
  actionLoading.value = 'ignore'
  try {
    await apiCall(
      'car_repair_management.api.inspection.update_failure',
      { name: doc.value.name, updates: JSON.stringify({ status: 'Ignored' }) },
    )
    await loadDetail()
  } catch (e) {
    console.warn('Failed to ignore failure', e)
  } finally {
    actionLoading.value = null
  }
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
    </div>

    <template v-else-if="doc">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <RouterLink to="/inspections/item-failures">
            <button
              class="w-9 h-9 flex items-center justify-center rounded-lg transition-colors"
              style="background: var(--bg-tertiary); color: var(--text-secondary)"
            >
              <LucideArrowLeft class="size-5" />
            </button>
          </RouterLink>
          <div>
            <h1 class="text-page-title">{{ doc.name }}</h1>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">
              {{ doc.item_name }} •
              <RouterLink :to="`/vehicles/${doc.vehicle}`" style="color: var(--accent)">{{ doc.vehicle }}</RouterLink>
              • {{ formatDisplayDate(doc.reported_date) }}
            </p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Badge :variant="SEVERITY_VARIANTS[doc.severity] || 'default'" size="md">
            {{ doc.severity }}
          </Badge>
          <Badge :variant="STATUS_VARIANTS[doc.status] || 'default'" size="md">
            {{ doc.status }}
          </Badge>
          <Badge v-if="doc.is_recurring" variant="warning" size="md">
            <LucideRepeat class="size-3" />
            Recurring
          </Badge>
        </div>
      </div>

      <!-- Main Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column (2/3) -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Failure Evidence Card -->
          <Card>
            <div class="flex items-center gap-2 mb-4">
              <LucideAlertTriangle class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Failure Evidence</h2>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-4">
                <div>
                  <p class="text-xs font-medium" style="color: var(--text-muted)">Item / Component</p>
                  <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.item_name }}</p>
                </div>
                <div>
                  <p class="text-xs font-medium" style="color: var(--text-muted)">Vehicle</p>
                  <RouterLink :to="`/vehicles/${doc.vehicle}`" class="text-sm mt-0.5 font-medium" style="color: var(--accent)">
                    {{ doc.vehicle }}
                  </RouterLink>
                </div>
                <div>
                  <p class="text-xs font-medium" style="color: var(--text-muted)">Failure Reason</p>
                  <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.failure_reason || '—' }}</p>
                </div>
                <div v-if="doc.inspection">
                  <p class="text-xs font-medium" style="color: var(--text-muted)">Inspection</p>
                  <RouterLink :to="`/inspections/${doc.inspection}`" class="text-sm mt-0.5 font-medium" style="color: var(--accent)">
                    {{ doc.inspection }}
                  </RouterLink>
                </div>
              </div>

              <div v-if="doc.evidence">
                <p class="text-xs font-medium mb-2" style="color: var(--text-muted)">Evidence</p>
                <img
                  :src="doc.evidence"
                  :alt="`Evidence for ${doc.name}`"
                  class="rounded-lg border max-h-64 object-contain"
                  style="border-color: var(--border-color)"
                />
              </div>
              <div v-else class="flex items-center justify-center rounded-lg p-8" style="background-color: var(--bg-tertiary)">
                <div class="text-center">
                  <LucideImage class="size-8 mx-auto mb-2" style="color: var(--text-muted)" />
                  <p class="text-sm" style="color: var(--text-muted)">No evidence attached</p>
                </div>
              </div>
            </div>
          </Card>

          <!-- Notes Card -->
          <Card v-if="doc.notes">
            <div class="flex items-center gap-2 mb-3">
              <LucideFileText class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Notes</h2>
            </div>
            <div class="text-sm prose prose-sm max-w-none" style="color: var(--text-secondary)" v-html="doc.notes" />
          </Card>

          <!-- Resolution Card -->
          <Card>
            <div class="flex items-center gap-2 mb-4">
              <LucideCheckCircle class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Resolution</h2>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div class="space-y-4">
                <div>
                  <p class="text-xs font-medium" style="color: var(--text-muted)">Resolution Type</p>
                  <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.resolution_type || '—' }}</p>
                </div>
                <div>
                  <p class="text-xs font-medium" style="color: var(--text-muted)">Assigned To</p>
                  <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.assigned_to || '—' }}</p>
                </div>
              </div>
              <div class="space-y-4">
                <div>
                  <p class="text-xs font-medium" style="color: var(--text-muted)">Linked Work Order</p>
                  <p v-if="doc.linked_work_order" class="text-sm mt-0.5 font-medium">
                    <RouterLink
                      :to="`/repair-orders/${doc.linked_work_order}`"
                      class="flex items-center gap-1"
                      style="color: var(--accent)"
                    >
                      {{ doc.linked_work_order }}
                      <LucideExternalLink class="size-3" />
                    </RouterLink>
                  </p>
                  <p v-else class="text-sm mt-0.5" style="color: var(--text-primary)">—</p>
                </div>
                <div>
                  <p class="text-xs font-medium" style="color: var(--text-muted)">Resolved Date</p>
                  <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDisplayDate(doc.resolved_date) }}</p>
                </div>
              </div>
            </div>

            <div v-if="doc.status === 'Open'" class="flex items-center gap-2 pt-4 border-t" style="border-color: var(--border-color)">
              <Button variant="primary" size="sm" :disabled="!!actionLoading" @click="createWorkOrder">
                <LucideLoader2 v-if="actionLoading === 'create_wo'" class="size-4 animate-spin" />
                <LucideWrench v-else class="size-4" />
                Create Work Order
              </Button>
              <Button variant="outline" size="sm" :disabled="!!actionLoading" @click="resolveFailure">
                <LucideLoader2 v-if="actionLoading === 'resolve'" class="size-4 animate-spin" />
                <LucideCheckCircle v-else class="size-4" />
                Resolve
              </Button>
              <Button variant="outline" size="sm" :disabled="!!actionLoading" @click="ignoreFailure">
                <LucideLoader2 v-if="actionLoading === 'ignore'" class="size-4 animate-spin" />
                <LucideX v-else class="size-4" />
                Ignore
              </Button>
            </div>
          </Card>

          <!-- Occurrence History Card -->
          <Card>
            <div class="flex items-center gap-2 mb-4">
              <LucideHistory class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Occurrence History</h2>
              <span class="text-xs px-2 py-0.5 rounded-full" style="background-color: var(--bg-tertiary); color: var(--text-muted)">
                {{ occurrenceHistory.length }}
              </span>
            </div>

            <div v-if="occurrenceHistory.length === 0" class="py-6 text-center text-sm" style="color: var(--text-muted)">
              No previous occurrences on this component/vehicle
            </div>

            <div v-else class="overflow-x-auto">
              <table class="w-full text-sm" style="color: var(--text-primary)">
                <thead>
                  <tr class="border-b" style="border-color: var(--border-subtle)">
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Failure ID</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Date</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Severity</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Status</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Inspection</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="occ in occurrenceHistory"
                    :key="occ.name"
                    class="border-b cursor-pointer transition-colors"
                    style="border-color: var(--border-subtle)"
                    @click="$router.push(`/inspections/item-failures/${occ.name}`)"
                    @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
                    @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
                  >
                    <td class="px-4 py-3 font-medium" style="color: var(--accent)">{{ occ.name }}</td>
                    <td class="px-4 py-3">{{ formatDisplayDate(occ.reported_date) }}</td>
                    <td class="px-4 py-3">
                      <Badge :variant="SEVERITY_VARIANTS[occ.severity] || 'default'" size="sm">{{ occ.severity }}</Badge>
                    </td>
                    <td class="px-4 py-3">
                      <Badge :variant="STATUS_VARIANTS[occ.status] || 'default'" size="sm">{{ occ.status }}</Badge>
                    </td>
                    <td class="px-4 py-3" style="color: var(--text-muted)">{{ occ.inspection || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>

          <!-- Audit Trail Card -->
          <Card v-if="auditTrail.length > 0">
            <div class="flex items-center gap-2 mb-4">
              <LucideClock class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Audit Trail</h2>
            </div>
            <div class="space-y-3">
              <div
                v-for="v in auditTrail"
                :key="v.name"
                class="pl-3 border-l-2 py-1"
                style="border-color: var(--border-color)"
              >
                <template v-for="(change, idx) in parseVersionChanges(v.data)" :key="idx">
                  <p class="text-sm" style="color: var(--text-primary)">{{ change }}</p>
                </template>
                <p v-if="parseVersionChanges(v.data).length === 0" class="text-sm" style="color: var(--text-muted)">Document updated</p>
                <p class="text-xs mt-0.5" style="color: var(--text-muted)">
                  {{ v.owner }} · {{ formatDateTime(v.creation) }}
                </p>
              </div>
            </div>
          </Card>
        </div>

        <!-- Right Column / Sidebar (1/3) -->
        <div class="space-y-6">
          <!-- Metadata Card -->
          <Card>
            <div class="flex items-center gap-2 mb-3">
              <LucideFileText class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Details</h2>
            </div>
            <div class="space-y-3">
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Created</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDateTime(doc.creation) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Modified</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDateTime(doc.modified) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Owner</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.owner }}</p>
              </div>
              <a
                :href="`/app/inspection-item-failure/${doc.name}`"
                target="_blank"
                class="inline-flex items-center gap-1.5 text-sm font-medium transition-colors hover:opacity-80"
                style="color: var(--accent)"
              >
                Open in Desk →
              </a>
            </div>
          </Card>

          <!-- Inspection Link Card -->
          <Card v-if="doc.inspection">
            <div class="flex items-center gap-2 mb-3">
              <LucideClipboardCheck class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Inspection</h2>
            </div>
            <RouterLink
              :to="`/inspections/${doc.inspection}`"
              class="text-sm font-medium transition-colors hover:opacity-80"
              style="color: var(--accent)"
            >
              {{ doc.inspection }}
            </RouterLink>
          </Card>

          <!-- Linked Work Order Card -->
          <Card v-if="doc.linked_work_order">
            <div class="flex items-center gap-2 mb-3">
              <LucideWrench class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Linked Work Order</h2>
            </div>
            <RouterLink
              :to="`/repair-orders/${doc.linked_work_order}`"
              class="text-sm font-medium transition-colors hover:opacity-80"
              style="color: var(--accent)"
            >
              {{ doc.linked_work_order }}
            </RouterLink>
          </Card>
        </div>
      </div>
    </template>

    <!-- Error / Not Found -->
    <Card v-else>
      <div class="flex flex-col items-center py-12 text-center">
        <p class="text-lg font-semibold" style="color: var(--text-primary)">Failure not found</p>
        <p class="text-sm mt-1 mb-4" style="color: var(--text-muted)">
          The failure record "{{ id }}" could not be loaded.
        </p>
        <RouterLink to="/inspections/item-failures">
          <Button variant="secondary">
            <LucideArrowLeft class="size-4" />
            Back
          </Button>
        </RouterLink>
      </div>
    </Card>
  </div>
</template>
