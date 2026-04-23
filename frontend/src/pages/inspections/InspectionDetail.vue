<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import {
  LucideArrowLeft,
  LucideClipboardCheck,
  LucideAlertTriangle,
  LucideCalendarClock,
  LucideHistory,
  LucideEdit,
  LucideX,
  LucideSave,
  LucideLoader2,
  LucideWrench,
  LucideFileText,
  LucideUser,
  LucideCheckCircle,
  LucideBan,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, LinkField } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface Failure {
  name: string
  item_name: string
  severity: string
  failure_reason: string | null
  status: string
}

interface VersionEntry {
  name: string
  owner: string
  creation: string
  data: string
}

const props = defineProps<{ id: string }>()
const router = useRouter()

const isLoading = ref(true)
const doc = ref<any>(null)
const failures = ref<Failure[]>([])
const auditTrail = ref<VersionEntry[]>([])
const isEditing = ref(false)
const isSaving = ref(false)
const editForm = ref<any>({})
const saveError = ref('')

// Quick action refs
const quickScore = ref<number | null>(null)
const quickFindings = ref('')
const isSavingQuick = ref(false)
const quickInspector = ref('')

const RESULT_VARIANTS: Record<string, StatusVariant> = {
  Pass: 'success',
  Conditional: 'warning',
  Fail: 'danger',
}

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Draft: 'default',
  'In Progress': 'info',
  Completed: 'success',
  Cancelled: 'danger',
}

const SEVERITY_VARIANTS: Record<string, StatusVariant> = {
  Low: 'default',
  Medium: 'warning',
  High: 'danger',
  Critical: 'danger',
}

const STATUSES = ['Draft', 'In Progress', 'Completed', 'Cancelled']
const RESULTS = ['', 'Pass', 'Conditional', 'Fail']
const INSPECTION_TYPES = ['Pre-Trip', 'Post-Trip', 'Periodic', 'Ad-Hoc', 'Regulatory']

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

async function loadDetail() {
  isLoading.value = true
  try {
    const res = await apiCall<any>(
      'car_repair_management.api.inspection.get_inspection_detail',
      { name: props.id },
    )
    doc.value = res.doc
    failures.value = res.failures || []
    auditTrail.value = res.audit_trail || []
    quickScore.value = doc.value.score || null
    quickFindings.value = doc.value.findings || ''
    quickInspector.value = doc.value.inspector || ''
  } catch (e) {
    console.warn('Failed to load inspection detail', e)
  } finally {
    isLoading.value = false
  }
}

async function quickSave(updates: Record<string, any>) {
  isSavingQuick.value = true
  try {
    const res = await apiCall<any>(
      'car_repair_management.api.inspection.update_inspection',
      { name: props.id, updates: JSON.stringify(updates) },
    )
    doc.value = res.doc
    failures.value = res.failures || []
    auditTrail.value = res.audit_trail || []
    quickScore.value = doc.value.score || null
    quickFindings.value = doc.value.findings || ''
    quickInspector.value = doc.value.inspector || ''
  } catch (e: any) {
    console.error('Quick save failed', e)
  } finally {
    isSavingQuick.value = false
  }
}

async function setResult(result: string) {
  await quickSave({ result })
}

async function setScore() {
  if (quickScore.value !== null) {
    await quickSave({ score: quickScore.value })
  }
}

async function saveQuickFindings() {
  await quickSave({ findings: quickFindings.value })
}

async function changeInspector(val: string) {
  quickInspector.value = val
  await quickSave({ inspector: val })
}

async function setStatus(status: string) {
  await quickSave({ status })
}

function startEditing() {
  editForm.value = {
    status: doc.value.status || 'Draft',
    result: doc.value.result || '',
    score: doc.value.score || 0,
    inspection_date: doc.value.inspection_date || '',
    inspection_type: doc.value.inspection_type || '',
    form_template: doc.value.form_template || '',
    inspector: doc.value.inspector || '',
    findings: doc.value.findings || '',
    notes: doc.value.notes || '',
    follow_up_required: doc.value.follow_up_required || 0,
    follow_up_due_date: doc.value.follow_up_due_date || '',
    follow_up_assigned_to: doc.value.follow_up_assigned_to || '',
  }
  saveError.value = ''
  isEditing.value = true
}

function cancelEditing() {
  isEditing.value = false
  saveError.value = ''
}

async function saveInspection() {
  isSaving.value = true
  saveError.value = ''
  try {
    const res = await apiCall<any>(
      'car_repair_management.api.inspection.update_inspection',
      { name: props.id, updates: JSON.stringify(editForm.value) },
    )
    doc.value = res.doc
    failures.value = res.failures || []
    auditTrail.value = res.audit_trail || []
    quickScore.value = doc.value.score || null
    quickFindings.value = doc.value.findings || ''
    quickInspector.value = doc.value.inspector || ''
    isEditing.value = false
  } catch (e: any) {
    saveError.value = e.message || 'Failed to save inspection'
  } finally {
    isSaving.value = false
  }
}

function goBack() {
  router.back()
}

function openFailure(failure: Failure) {
  router.push(`/inspections/item-failures/${failure.name}`)
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
          <button
            class="w-9 h-9 flex items-center justify-center rounded-lg transition-colors"
            style="background: var(--bg-tertiary); color: var(--text-secondary)"
            @click="goBack"
          >
            <LucideArrowLeft class="size-5" />
          </button>
          <div>
            <h1 class="text-page-title">{{ doc.title || doc.name }}</h1>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ doc.name }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Badge :variant="STATUS_VARIANTS[doc.status] || 'default'" size="md">
            {{ doc.status }}
          </Badge>
          <Badge v-if="doc.result" :variant="RESULT_VARIANTS[doc.result] || 'default'" size="md">
            {{ doc.result }}
          </Badge>
          <div
            v-if="doc.score"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-semibold"
            style="background: var(--bg-tertiary); color: var(--text-primary)"
          >
            <LucideClipboardCheck class="size-4" />
            Score: {{ doc.score }}%
          </div>
          <Button v-if="!isEditing" variant="outline" size="sm" @click="startEditing">
            <LucideEdit class="size-4" />
            Edit
          </Button>
        </div>
      </div>

      <!-- Edit Form -->
      <Card v-if="isEditing">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Edit Inspection</h2>
          <div class="flex items-center gap-2">
            <Button variant="outline" size="sm" :disabled="isSaving" @click="cancelEditing">
              <LucideX class="size-4" />
              Cancel
            </Button>
            <Button size="sm" :disabled="isSaving" @click="saveInspection">
              <LucideLoader2 v-if="isSaving" class="size-4 animate-spin" />
              <LucideSave v-else class="size-4" />
              Save
            </Button>
          </div>
        </div>
        <div v-if="saveError" class="mb-4 p-3 rounded-lg text-sm" style="background: rgba(239,68,68,0.1); color: #ef4444;">
          {{ saveError }}
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Status</label>
            <select
              v-model="editForm.status"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
            >
              <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Result</label>
            <select
              v-model="editForm.result"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
            >
              <option value="">— Not Set —</option>
              <option v-for="r in RESULTS.filter(r => r)" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Score (%)</label>
            <input
              v-model.number="editForm.score"
              type="number"
              min="0"
              max="100"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Inspection Type</label>
            <select
              v-model="editForm.inspection_type"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
            >
              <option v-for="t in INSPECTION_TYPES" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div>
            <LinkField
              v-model="editForm.inspector"
              doctype="Employee"
              label="Inspector"
              placeholder="Search employee..."
              titleField="employee_name"
            />
          </div>
          <div>
            <LinkField
              v-model="editForm.form_template"
              doctype="Inspection Form Template"
              label="Form Template"
              placeholder="Search template..."
              titleField="title"
            />
          </div>
        </div>
        <div class="mt-4">
          <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Findings</label>
          <textarea
            v-model="editForm.findings"
            rows="4"
            class="w-full rounded-lg border p-3 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none"
            style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
            placeholder="Inspection findings..."
          />
        </div>
        <div class="mt-4">
          <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Notes</label>
          <textarea
            v-model="editForm.notes"
            rows="3"
            class="w-full rounded-lg border p-3 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none"
            style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
            placeholder="Additional notes..."
          />
        </div>
        <div class="mt-4 pt-4 border-t" style="border-color: var(--border-subtle)">
          <label class="flex items-center gap-2 text-sm font-medium cursor-pointer" style="color: var(--text-primary)">
            <input type="checkbox" v-model="editForm.follow_up_required" :true-value="1" :false-value="0" class="rounded" />
            Follow-up Required
          </label>
          <div v-if="editForm.follow_up_required" class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Follow-up Due Date</label>
              <input
                v-model="editForm.follow_up_due_date"
                type="date"
                class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
                style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
              />
            </div>
            <div>
              <LinkField
                v-model="editForm.follow_up_assigned_to"
                doctype="User"
                label="Follow-up Assigned To"
                placeholder="Search user..."
              />
            </div>
          </div>
        </div>
      </Card>

      <!-- Main Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column (2/3) -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Summary Card -->
          <Card>
            <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">Inspection Summary</h2>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Vehicle</p>
                <RouterLink v-if="doc.vehicle" :to="`/vehicles/${doc.vehicle}`" class="text-sm mt-0.5 font-medium" style="color: var(--accent)">
                  {{ doc.vehicle }}
                </RouterLink>
                <p v-else class="text-sm mt-0.5" style="color: var(--text-primary)">—</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Inspector</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.inspector || '—' }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Type</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.inspection_type }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Date</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDateTime(doc.inspection_date) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Form Template</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.form_template || '—' }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Score</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.score ? `${doc.score}%` : '—' }}</p>
              </div>
            </div>
          </Card>

          <!-- Findings Card -->
          <Card v-if="doc.findings">
            <h2 class="text-sm font-semibold mb-3" style="color: var(--text-primary)">Findings</h2>
            <div class="text-sm prose prose-sm max-w-none" style="color: var(--text-secondary)" v-html="doc.findings" />
          </Card>

          <!-- Notes Card -->
          <Card v-if="doc.notes">
            <h2 class="text-sm font-semibold mb-3" style="color: var(--text-primary)">Notes</h2>
            <p class="text-sm whitespace-pre-wrap" style="color: var(--text-secondary)">{{ doc.notes }}</p>
          </Card>

          <!-- Failures Card -->
          <Card v-if="failures.length > 0" padding="none">
            <div class="px-4 pt-4 pb-3 flex items-center gap-2">
              <LucideAlertTriangle class="size-4" style="color: #ef4444" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
                Failures ({{ failures.length }})
              </h2>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-sm" style="color: var(--text-primary)">
                <thead>
                  <tr class="border-b" style="border-color: var(--border-subtle)">
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Item</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Severity</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Reason</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="f in failures"
                    :key="f.name"
                    class="border-b cursor-pointer transition-colors"
                    style="border-color: var(--border-subtle)"
                    @click="openFailure(f)"
                    @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
                    @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
                  >
                    <td class="px-4 py-3 font-medium">{{ f.item_name }}</td>
                    <td class="px-4 py-3">
                      <Badge :variant="SEVERITY_VARIANTS[f.severity] || 'default'" size="sm">
                        {{ f.severity }}
                      </Badge>
                    </td>
                    <td class="px-4 py-3" style="color: var(--text-secondary)">
                      {{ f.failure_reason || '—' }}
                    </td>
                    <td class="px-4 py-3">
                      <Badge :variant="STATUS_VARIANTS[f.status] || 'default'" size="sm">
                        {{ f.status }}
                      </Badge>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <!-- Right Column / Sidebar (1/3) -->
        <div class="space-y-6">
          <!-- Quick Actions Card -->
          <Card>
            <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">Quick Actions</h2>

            <!-- Inspector Assignment -->
            <div class="mb-4 pb-4 border-b" style="border-color: var(--border-subtle)">
              <div class="flex items-center gap-2 mb-2">
                <LucideUser class="size-4" style="color: var(--text-muted)" />
                <p class="text-xs font-medium" style="color: var(--text-muted)">Inspector</p>
              </div>
              <LinkField
                :modelValue="quickInspector"
                @update:modelValue="changeInspector"
                doctype="Employee"
                placeholder="Assign inspector..."
                titleField="employee_name"
              />
            </div>

            <!-- Quick Result Buttons -->
            <div class="mb-4 pb-4 border-b" style="border-color: var(--border-subtle)">
              <p class="text-xs font-medium mb-2" style="color: var(--text-muted)">Result</p>
              <div class="flex gap-2">
                <button
                  v-for="r in ['Pass', 'Conditional', 'Fail']"
                  :key="r"
                  class="flex-1 px-3 py-2 rounded-lg text-xs font-semibold transition-all border"
                  :style="{
                    backgroundColor: doc.result === r
                      ? (r === 'Pass' ? 'rgba(34,197,94,0.15)' : r === 'Conditional' ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)')
                      : 'var(--bg-tertiary)',
                    borderColor: doc.result === r
                      ? (r === 'Pass' ? 'rgba(34,197,94,0.4)' : r === 'Conditional' ? 'rgba(245,158,11,0.4)' : 'rgba(239,68,68,0.4)')
                      : 'var(--border-color)',
                    color: doc.result === r
                      ? (r === 'Pass' ? '#16a34a' : r === 'Conditional' ? '#d97706' : '#dc2626')
                      : 'var(--text-secondary)',
                  }"
                  :disabled="isSavingQuick"
                  @click="setResult(r)"
                >
                  {{ r }}
                </button>
              </div>
            </div>

            <!-- Quick Score -->
            <div class="mb-4 pb-4 border-b" style="border-color: var(--border-subtle)">
              <p class="text-xs font-medium mb-2" style="color: var(--text-muted)">Score (%)</p>
              <div class="flex items-center gap-2">
                <input
                  v-model.number="quickScore"
                  type="number"
                  min="0"
                  max="100"
                  class="flex-1 h-9 px-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
                  style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
                  @keyup.enter="setScore"
                />
                <Button variant="outline" size="sm" :disabled="isSavingQuick" @click="setScore">
                  Set
                </Button>
              </div>
            </div>

            <!-- Quick Findings -->
            <div>
              <p class="text-xs font-medium mb-2" style="color: var(--text-muted)">Findings</p>
              <textarea
                v-model="quickFindings"
                rows="3"
                class="w-full rounded-lg border p-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none"
                style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
                placeholder="Add findings..."
              />
              <Button
                variant="outline"
                size="sm"
                class="mt-2"
                :disabled="isSavingQuick"
                @click="saveQuickFindings"
              >
                <LucideSave class="size-3.5" />
                Save Findings
              </Button>
            </div>
          </Card>

          <!-- Actions Card -->
          <Card>
            <h2 class="text-sm font-semibold mb-3" style="color: var(--text-primary)">Actions</h2>
            <div class="space-y-2">
              <Button
                v-if="doc.status !== 'Completed' && doc.status !== 'Cancelled'"
                variant="outline"
                size="sm"
                :disabled="isSavingQuick"
                @click="setStatus('Completed')"
                class="w-full justify-start"
              >
                <LucideCheckCircle class="size-4" />
                Complete Inspection
              </Button>
              <Button
                v-if="doc.status !== 'Cancelled'"
                variant="outline"
                size="sm"
                :disabled="isSavingQuick"
                @click="setStatus('Cancelled')"
                class="w-full justify-start"
              >
                <LucideBan class="size-4" />
                Cancel Inspection
              </Button>
              <Button
                v-if="!doc.follow_up_required"
                variant="outline"
                size="sm"
                :disabled="isSavingQuick"
                @click="quickSave({ follow_up_required: 1 })"
                class="w-full justify-start"
              >
                <LucideCalendarClock class="size-4" />
                Create Follow-up
              </Button>
              <a
                :href="`/app/vehicle-inspection/${doc.name}`"
                target="_blank"
                class="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors hover:opacity-80 border"
                style="color: var(--text-secondary); border-color: var(--border-color)"
              >
                <LucideFileText class="size-4" />
                Open in Desk
              </a>
            </div>
          </Card>

          <!-- Linked Repair Order -->
          <Card v-if="doc.linked_work_order">
            <div class="flex items-center gap-2 mb-3">
              <LucideWrench class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Linked Repair Order</h2>
            </div>
            <RouterLink
              :to="`/repair-orders/${doc.linked_work_order}`"
              class="text-sm font-medium transition-colors hover:opacity-80"
              style="color: var(--accent)"
            >
              {{ doc.linked_work_order }}
            </RouterLink>
          </Card>

          <!-- Handover Checklist Item -->
          <Card v-if="doc.handover_checklist_item">
            <div class="flex items-center gap-2 mb-3">
              <LucideClipboardCheck class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Checklist Item</h2>
            </div>
            <p class="text-sm" style="color: var(--text-primary)">{{ doc.handover_checklist_item }}</p>
          </Card>

          <!-- Follow-up Card -->
          <Card v-if="doc.follow_up_required">
            <div class="flex items-center gap-2 mb-3">
              <LucideCalendarClock class="size-4" style="color: var(--accent)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Follow-up Required</h2>
            </div>
            <div class="space-y-3">
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Due Date</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">
                  {{ formatDate(doc.follow_up_due_date) }}
                </p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Assigned To</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">
                  {{ doc.follow_up_assigned_to || '—' }}
                </p>
              </div>
            </div>
          </Card>

          <!-- Metadata -->
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
            </div>
          </Card>
        </div>
      </div>

      <!-- Audit Trail Card -->
      <Card v-if="auditTrail.length > 0">
        <div class="flex items-center gap-2 mb-4">
          <LucideHistory class="size-4" style="color: var(--text-muted)" />
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
    </template>

    <!-- Error / Not Found -->
    <Card v-else>
      <div class="flex flex-col items-center py-12 text-center">
        <p class="text-lg font-semibold" style="color: var(--text-primary)">Inspection not found</p>
        <p class="text-sm mt-1 mb-4" style="color: var(--text-muted)">
          The inspection "{{ id }}" could not be loaded.
        </p>
        <Button variant="secondary" @click="goBack">
          <LucideArrowLeft class="size-4" />
          Back
        </Button>
      </div>
    </Card>
  </div>
</template>
