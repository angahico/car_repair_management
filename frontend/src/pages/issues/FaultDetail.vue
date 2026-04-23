<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideArrowLeft,
  LucideBug,
  LucideClock,
  LucideShield,
  LucideClipboardList,
  LucideClipboardCheck,
  LucideImage,
  LucideWrench,
  LucidePlus,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState } from '@/components/ui'

const props = defineProps<{ id: string }>()
const router = useRouter()

interface FaultDetailData {
  doc: Record<string, any>
  occurrence_history: { name: string; title: string; fault_code: string | null; reported_date: string | null; severity: string; status: string; resolved_date: string | null }[]
  audit_trail: { name: string; owner: string; creation: string; data: string }[]
}

const isLoading = ref(true)
const data = ref<FaultDetailData | null>(null)

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

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—'
  const parts = dateStr.substring(0, 10).split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    const time = dateStr.substring(11, 16)
    return `${d.toLocaleDateString()} ${time || ''}`
  }
  return dateStr
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '').trim()
}

async function loadData() {
  isLoading.value = true
  try {
    const result = await apiCall<FaultDetailData>(
      'car_repair_management.api.issue.get_fault_detail',
      { name: props.id },
    )
    data.value = result
  } catch (e) {
    console.warn('Failed to load fault detail', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div class="flex items-center gap-4">
        <Button variant="outline" @click="router.push('/issues/faults')">
          <LucideArrowLeft class="size-4" />
        </Button>
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <h1 class="text-page-title">{{ data?.doc?.name || id }}</h1>
            <Badge v-if="data?.doc?.severity" :variant="SEVERITY_VARIANTS[data.doc.severity] || 'default'">{{ data.doc.severity }}</Badge>
            <Badge v-if="data?.doc?.confirmed" :variant="CONFIRMED_VARIANTS[data.doc.confirmed] || 'default'">{{ data.doc.confirmed }}</Badge>
            <Badge v-if="data?.doc?.status" :variant="STATUS_VARIANTS[data.doc.status] || 'default'">{{ data.doc.status }}</Badge>
          </div>
          <p v-if="data?.doc?.title" class="text-sm mt-1" style="color: var(--text-muted)">{{ data.doc.title }}</p>
        </div>
      </div>
      <a :href="`/app/vehicle-fault/${id}`" target="_blank">
        <Button variant="outline">Edit in Desk</Button>
      </a>
    </div>

    <!-- Loading -->
    <template v-if="isLoading">
      <Card><Skeleton height="200px" /></Card>
      <Card><Skeleton height="150px" /></Card>
    </template>

    <template v-else-if="data">
      <!-- Fault Summary -->
      <Card>
        <h2 class="text-section-title mb-4">Fault Summary</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Vehicle</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.vehicle || '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Fault Code</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.fault_code || '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Detection Type</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.detection_type || '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Component System</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.component_system || '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Reported By</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.reported_by || data.doc.owner || '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Reported Date</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ formatDate(data.doc.reported_date) }}</p>
          </div>
        </div>
        <div v-if="data.doc.description" class="mt-4 pt-4 border-t" :style="{ borderColor: 'var(--border-color)' }">
          <p class="text-xs mb-1" style="color: var(--text-muted)">Description</p>
          <p class="text-sm" style="color: var(--text-primary); white-space: pre-wrap;">{{ stripHtml(data.doc.description || '') }}</p>
        </div>
      </Card>

      <!-- Detection Evidence -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideImage class="size-5" style="color: var(--text-muted)" />
          <h2 class="text-section-title">Detection Evidence</h2>
        </div>
        <div v-if="data.doc.evidence">
          <img :src="data.doc.evidence" alt="Fault evidence" class="max-w-full max-h-96 rounded-lg border" :style="{ borderColor: 'var(--border-color)' }" />
        </div>
        <p v-else class="text-sm" style="color: var(--text-muted)">No evidence attached</p>
      </Card>

      <!-- Occurrence History -->
      <Card padding="none">
        <div class="p-4 border-b" style="border-color: var(--border-color);">
          <h2 class="text-section-title">Occurrence History</h2>
          <p class="text-xs mt-1" style="color: var(--text-muted)">Similar faults on this vehicle</p>
        </div>
        <EmptyState
          v-if="data.occurrence_history.length === 0"
          :icon="LucideBug"
          title="No previous occurrences"
          description="No similar faults found for this vehicle"
        />
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">Fault ID</th>
                <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">Date</th>
                <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">Severity</th>
                <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">Status</th>
                <th class="text-left px-4 py-3 font-medium" style="color: var(--text-muted)">Resolved</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="occ in data.occurrence_history"
                :key="occ.name"
                class="border-b cursor-pointer transition-colors"
                :style="{ borderColor: 'var(--border-color)' }"
                @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
                @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = 'transparent'"
                @click="router.push(`/issues/faults/${occ.name}`)"
              >
                <td class="px-4 py-3 font-medium" style="color: var(--accent)">{{ occ.name }}</td>
                <td class="px-4 py-3" style="color: var(--text-secondary)">{{ formatDate(occ.reported_date) }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="SEVERITY_VARIANTS[occ.severity] || 'default'" size="sm">{{ occ.severity }}</Badge>
                </td>
                <td class="px-4 py-3">
                  <Badge :variant="STATUS_VARIANTS[occ.status] || 'default'" size="sm">{{ occ.status }}</Badge>
                </td>
                <td class="px-4 py-3" style="color: var(--text-muted)">{{ formatDate(occ.resolved_date) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Actions -->
      <Card>
        <h2 class="text-section-title mb-4">Actions</h2>
        <div class="space-y-3">
          <div v-if="data.doc.linked_work_order" class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary);">
            <LucideClipboardList class="size-5" style="color: var(--accent)" />
            <div>
              <p class="text-xs" style="color: var(--text-muted)">Linked Work Order</p>
              <p class="text-sm font-medium cursor-pointer" style="color: var(--accent)" @click="router.push(`/repair-orders/${data.doc.linked_work_order}`)">{{ data.doc.linked_work_order }}</p>
            </div>
          </div>
          <div v-if="data.doc.linked_inspection" class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary);">
            <LucideClipboardCheck class="size-5" style="color: var(--text-muted)" />
            <div>
              <p class="text-xs" style="color: var(--text-muted)">Linked Inspection</p>
              <p class="text-sm font-medium cursor-pointer" style="color: var(--accent)" @click="router.push(`/inspections/${data.doc.linked_inspection}`)">{{ data.doc.linked_inspection }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2 pt-2">
            <a href="/app/repair-order/new" target="_blank">
              <Button variant="primary" size="sm"><LucidePlus class="size-4" /> Create Work Order</Button>
            </a>
            <Button variant="outline" size="sm" disabled>Mark Resolved</Button>
          </div>
        </div>
      </Card>

      <!-- Audit Trail -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideClock class="size-5" style="color: var(--text-muted)" />
          <h2 class="text-section-title">Audit Trail</h2>
        </div>
        <div v-if="data.audit_trail.length === 0" class="text-sm" style="color: var(--text-muted)">No change history available</div>
        <div v-else class="space-y-2">
          <div
            v-for="entry in data.audit_trail"
            :key="entry.name"
            class="flex items-center gap-3 p-2 rounded-lg text-sm"
            style="background: var(--bg-tertiary);"
          >
            <LucideClock class="size-3.5 shrink-0" style="color: var(--text-muted)" />
            <span style="color: var(--text-primary)">{{ entry.owner }}</span>
            <span style="color: var(--text-muted)">{{ formatDateTime(entry.creation) }}</span>
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>
