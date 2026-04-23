<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideClipboardCheck,
  LucideAlertCircle,
  LucideCheckCircle,
  LucideChevronDown,
  LucideChevronUp,
  LucideCalendar,
  LucideExternalLink,
  LucideEdit,
  LucideSave,
  LucideX,
  LucideLoader2,
  LucideUser,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Badge, Skeleton, Button, LinkField } from '@/components/ui'

const props = defineProps<{ vehicleId: string }>()
const router = useRouter()

const isLoading = ref(true)
const inspectionData = ref<any>(null)
const expandedRows = ref<Set<number>>(new Set())
const editingIdx = ref<number | null>(null)
const editForm = ref<any>({})
const isSaving = ref(false)
const saveError = ref('')

const STATUSES = ['Draft', 'In Progress', 'Completed', 'Cancelled']
const RESULTS = ['', 'Pass', 'Conditional', 'Fail']

async function loadInspections() {
  isLoading.value = true
  try {
    inspectionData.value = await apiCall('car_repair_management.api.vehicle.get_vehicle_inspection_history', {
      vehicle_name: props.vehicleId,
    })
  } catch (e) {
    console.error('Failed to load inspections', e)
  } finally {
    isLoading.value = false
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString()
}

function toggleRow(idx: number) {
  if (expandedRows.value.has(idx)) {
    expandedRows.value.delete(idx)
  } else {
    expandedRows.value.add(idx)
  }
}

function openInspection(name: string) {
  router.push(`/inspections/${name}`)
}

function startEditing(idx: number, inspection: any) {
  editingIdx.value = idx
  editForm.value = {
    status: inspection.status || 'Draft',
    result: inspection.result || '',
    score: inspection.score || 0,
    inspector: inspection.inspector || '',
    findings: inspection.findings || '',
    notes: inspection.notes || '',
  }
  saveError.value = ''
  if (!expandedRows.value.has(idx)) {
    expandedRows.value.add(idx)
  }
}

function cancelEditing() {
  editingIdx.value = null
  saveError.value = ''
}

async function saveEdit(inspectionName: string) {
  isSaving.value = true
  saveError.value = ''
  try {
    await apiCall(
      'car_repair_management.api.inspection.update_inspection',
      { name: inspectionName, updates: JSON.stringify(editForm.value) },
    )
    editingIdx.value = null
    await loadInspections()
  } catch (e: any) {
    saveError.value = e.message || 'Failed to save'
  } finally {
    isSaving.value = false
  }
}

const resultColors: Record<string, string> = {
  'Pass': 'success',
  'Passed': 'success',
  'Conditional': 'warning',
  'Fail': 'danger',
  'Failed': 'danger',
}

const statusColors: Record<string, string> = {
  'Draft': 'default',
  'In Progress': 'info',
  'Completed': 'success',
  'Cancelled': 'danger',
}

onMounted(loadInspections)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <template v-if="isLoading">
      <Card><Skeleton height="100px" /></Card>
      <Card><Skeleton height="300px" /></Card>
    </template>

    <template v-else-if="inspectionData">
      <!-- Compliance Summary -->
      <Card>
        <h3 class="text-lg font-semibold mb-4" style="color: var(--text-primary);">Compliance Status</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="flex items-center gap-3 p-4 rounded-lg" style="background-color: var(--bg-tertiary);">
            <component 
              :is="inspectionData.compliance_summary?.status === 'Compliant' ? LucideCheckCircle : LucideAlertCircle"
              :class="inspectionData.compliance_summary?.status === 'Compliant' ? 'text-green-500' : 'text-red-500'"
              class="size-10"
            />
            <div>
              <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">Overall Status</p>
              <p class="text-xl font-bold" :class="inspectionData.compliance_summary?.status === 'Compliant' ? 'text-green-600' : 'text-red-600'">
                {{ inspectionData.compliance_summary?.status || 'Unknown' }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3 p-4 rounded-lg" style="background-color: var(--bg-tertiary);">
            <LucideCalendar class="size-10" style="color: var(--text-muted);" />
            <div>
              <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">Next Required</p>
              <p class="text-xl font-bold" style="color: var(--text-primary);">
                {{ formatDate(inspectionData.compliance_summary?.next_required) }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3 p-4 rounded-lg" :class="inspectionData.compliance_summary?.is_overdue ? 'border-l-4 border-red-500' : ''" style="background-color: var(--bg-tertiary);">
            <LucideAlertCircle :class="inspectionData.compliance_summary?.is_overdue ? 'text-red-500' : 'text-gray-400'" class="size-10" />
            <div>
              <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">Overdue</p>
              <p class="text-xl font-bold" :class="inspectionData.compliance_summary?.is_overdue ? 'text-red-600' : ''">
                {{ inspectionData.compliance_summary?.is_overdue ? 'Yes' : 'No' }}
              </p>
            </div>
          </div>
        </div>
      </Card>

      <!-- Inspection Log Table -->
      <Card padding="none">
        <div class="p-4 border-b" style="border-color: var(--border-color);">
          <h3 class="text-lg font-semibold" style="color: var(--text-primary);">
            <LucideClipboardCheck class="inline size-5 mr-2" />
            Inspection History
          </h3>
        </div>

        <div v-if="inspectionData.inspections?.length" class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b" style="background-color: var(--bg-tertiary); border-color: var(--border-color);">
                <th class="w-8 px-4 py-3"></th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Date</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Type</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Inspector</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Status</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Result</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Score</th>
                <th class="text-right px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Actions</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(inspection, idx) in inspectionData.inspections" :key="inspection.name">
                <!-- Main Row -->
                <tr 
                  class="border-b transition-colors"
                  style="border-color: var(--border-subtle);"
                >
                  <td class="px-4 py-3">
                    <button @click="toggleRow(idx)" class="p-0.5 rounded hover:opacity-70">
                      <component 
                        :is="expandedRows.has(idx) ? LucideChevronUp : LucideChevronDown" 
                        class="size-4" 
                        style="color: var(--text-muted);"
                      />
                    </button>
                  </td>
                  <td class="px-4 py-3 text-sm" style="color: var(--text-primary);">{{ formatDate(inspection.date) }}</td>
                  <td class="px-4 py-3 text-sm" style="color: var(--text-primary);">{{ inspection.type || '—' }}</td>
                  <td class="px-4 py-3 text-sm" style="color: var(--text-muted);">{{ inspection.inspector || '—' }}</td>
                  <td class="px-4 py-3">
                    <Badge :variant="statusColors[inspection.status] || 'default'">
                      {{ inspection.status || '—' }}
                    </Badge>
                  </td>
                  <td class="px-4 py-3">
                    <Badge v-if="inspection.result" :variant="resultColors[inspection.result] || 'default'">
                      {{ inspection.result }}
                    </Badge>
                    <span v-else class="text-sm" style="color: var(--text-muted);">—</span>
                  </td>
                  <td class="px-4 py-3 text-sm" style="color: var(--text-primary);">{{ inspection.score || '—' }}</td>
                  <td class="px-4 py-3 text-right">
                    <div class="flex items-center justify-end gap-1">
                      <Button variant="outline" size="sm" @click="openInspection(inspection.name)">
                        <LucideExternalLink class="size-3.5" />
                        Open
                      </Button>
                      <Button variant="outline" size="sm" @click.stop="startEditing(idx, inspection)">
                        <LucideEdit class="size-3.5" />
                        Edit
                      </Button>
                    </div>
                  </td>
                </tr>

                <!-- Expanded: Findings or Edit Form -->
                <tr v-if="expandedRows.has(idx)" style="background-color: var(--bg-tertiary);">
                  <td colspan="8" class="px-4 py-4">
                    <!-- Edit Mode -->
                    <div v-if="editingIdx === idx" class="pl-8 space-y-4">
                      <div class="flex items-center justify-between">
                        <h4 class="text-sm font-semibold" style="color: var(--text-primary);">Edit Inspection</h4>
                        <div class="flex items-center gap-2">
                          <Button variant="outline" size="sm" :disabled="isSaving" @click="cancelEditing">
                            <LucideX class="size-3.5" />
                            Cancel
                          </Button>
                          <Button size="sm" :disabled="isSaving" @click="saveEdit(inspection.name)">
                            <LucideLoader2 v-if="isSaving" class="size-3.5 animate-spin" />
                            <LucideSave v-else class="size-3.5" />
                            Save
                          </Button>
                        </div>
                      </div>
                      <div v-if="saveError" class="p-2 rounded text-sm" style="background: rgba(239,68,68,0.1); color: #ef4444;">
                        {{ saveError }}
                      </div>
                      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div>
                          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Status</label>
                          <select
                            v-model="editForm.status"
                            class="w-full h-9 px-2 text-sm rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
                            style="background-color: var(--bg-elevated); border-color: var(--border-color); color: var(--text-primary)"
                          >
                            <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
                          </select>
                        </div>
                        <div>
                          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Result</label>
                          <select
                            v-model="editForm.result"
                            class="w-full h-9 px-2 text-sm rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
                            style="background-color: var(--bg-elevated); border-color: var(--border-color); color: var(--text-primary)"
                          >
                            <option value="">— Not Set —</option>
                            <option v-for="r in RESULTS.filter(r => r)" :key="r" :value="r">{{ r }}</option>
                          </select>
                        </div>
                        <div>
                          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Score (%)</label>
                          <input
                            v-model.number="editForm.score"
                            type="number"
                            min="0"
                            max="100"
                            class="w-full h-9 px-2 text-sm rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
                            style="background-color: var(--bg-elevated); border-color: var(--border-color); color: var(--text-primary)"
                          />
                        </div>
                        <div>
                          <LinkField
                            v-model="editForm.inspector"
                            doctype="Employee"
                            label="Inspector"
                            placeholder="Search..."
                            titleField="employee_name"
                          />
                        </div>
                      </div>
                      <div>
                        <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Findings</label>
                        <textarea
                          v-model="editForm.findings"
                          rows="3"
                          class="w-full rounded-lg border p-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none"
                          style="background-color: var(--bg-elevated); border-color: var(--border-color); color: var(--text-primary)"
                          placeholder="Inspection findings..."
                        />
                      </div>
                      <div>
                        <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Notes</label>
                        <textarea
                          v-model="editForm.notes"
                          rows="2"
                          class="w-full rounded-lg border p-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none"
                          style="background-color: var(--bg-elevated); border-color: var(--border-color); color: var(--text-primary)"
                          placeholder="Additional notes..."
                        />
                      </div>
                    </div>

                    <!-- Read-only Findings -->
                    <div v-else class="pl-8">
                      <h4 class="text-sm font-semibold mb-2" style="color: var(--text-primary);">Findings</h4>
                      <p v-if="inspection.findings" class="text-sm whitespace-pre-wrap" style="color: var(--text-secondary);">
                        {{ inspection.findings }}
                      </p>
                      <p v-else class="text-sm italic" style="color: var(--text-muted);">No findings recorded</p>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-12">
          <LucideClipboardCheck class="size-12 mx-auto mb-4" style="color: var(--text-muted);" />
          <h3 class="text-lg font-semibold mb-2" style="color: var(--text-primary);">No Inspections</h3>
          <p class="text-sm" style="color: var(--text-muted);">This vehicle has no inspection records.</p>
        </div>
      </Card>
    </template>
  </div>
</template>
