<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import {
  LucideArrowLeft,
  LucideEdit,
  LucideCalendarClock,
  LucideRepeat,
  LucideClipboardCheck,
  LucideHistory,
  LucideZap,
  LucideBan,
  LucideAlertCircle,
  LucideCheck,
  LucideBell,
  LucideX,
  LucideSave,
  LucideLoader2,
  LucideFileText,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, LinkField } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface CompletionRecord {
  name: string
  inspection_date: string | null
  result: string | null
  score: number | null
  inspector: string | null
  status: string | null
}

interface VersionEntry {
  name: string
  owner: string
  creation: string
  data: string
}

interface Props {
  id: string
}

const props = defineProps<Props>()
const router = useRouter()

const doc = ref<any>(null)
const completionHistory = ref<CompletionRecord[]>([])
const auditTrail = ref<VersionEntry[]>([])
const isLoading = ref(true)
const error = ref('')
const isEditing = ref(false)
const isSaving = ref(false)
const editForm = ref<any>({})
const saveError = ref('')

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Active: 'success',
  Paused: 'warning',
  Completed: 'default',
  Cancelled: 'danger',
}

const STATUSES = ['Active', 'Paused', 'Completed', 'Cancelled']
const FREQUENCIES = ['Daily', 'Weekly', 'Bi-Weekly', 'Monthly', 'Quarterly', 'Semi-Annually', 'Annually', 'One-Time']

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  const parts = dateStr.split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    return d.toLocaleDateString()
  }
  return dateStr
}

function formatDateTime(dateStr: string | null | undefined): string {
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

function applyResponse(res: any) {
  doc.value = res.doc
  completionHistory.value = res.completion_history || []
  auditTrail.value = res.audit_trail || []
}

async function loadSchedule() {
  isLoading.value = true
  error.value = ''
  try {
    const result = await apiCall<any>(
      'car_repair_management.api.inspection.get_schedule_detail',
      { name: props.id },
    )
    applyResponse(result)
  } catch (e: any) {
    error.value = e.message || 'Failed to load schedule'
  } finally {
    isLoading.value = false
  }
}

function startEditing() {
  editForm.value = {
    title: doc.value.title || '',
    vehicle: doc.value.vehicle || '',
    form_template: doc.value.form_template || '',
    assigned_to: doc.value.assigned_to || '',
    status: doc.value.status || 'Active',
    frequency: doc.value.frequency || 'Monthly',
    scheduled_date: doc.value.scheduled_date || '',
    next_due: doc.value.next_due || '',
    auto_create_inspection: doc.value.auto_create_inspection || 0,
    notify_before_days: doc.value.notify_before_days ?? '',
    notes: doc.value.notes || '',
  }
  saveError.value = ''
  isEditing.value = true
}

function cancelEditing() {
  isEditing.value = false
  saveError.value = ''
}

async function saveSchedule() {
  isSaving.value = true
  saveError.value = ''
  try {
    const res = await apiCall<any>(
      'car_repair_management.api.inspection.update_schedule',
      { name: doc.value.name, updates: JSON.stringify(editForm.value) },
    )
    applyResponse(res)
    isEditing.value = false
  } catch (e: any) {
    saveError.value = e.message || 'Failed to save schedule'
  } finally {
    isSaving.value = false
  }
}

async function generateInspectionNow() {
  try {
    const result = await apiCall<any>(
      'car_repair_management.api.inspection.generate_inspection_now',
      { schedule_name: doc.value.name },
    )
    router.push(`/inspections/${result.name}`)
  } catch (e: any) {
    error.value = e.message || 'Failed to generate inspection'
  }
}

async function cancelSchedule() {
  try {
    await apiCall<any>(
      'car_repair_management.api.inspection.cancel_schedule',
      { name: doc.value.name },
    )
    await loadSchedule()
  } catch (e: any) {
    error.value = e.message || 'Failed to cancel schedule'
  }
}

function goBack() {
  router.push('/inspections/schedules')
}

onMounted(loadSchedule)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <div v-if="isLoading" class="space-y-6">
      <Skeleton height="48px" />
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 space-y-6">
          <Card><Skeleton height="200px" /></Card>
          <Card><Skeleton height="150px" /></Card>
        </div>
        <div class="space-y-6">
          <Card><Skeleton height="120px" /></Card>
          <Card><Skeleton height="120px" /></Card>
        </div>
      </div>
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
          <Button v-if="!isEditing" variant="outline" size="sm" @click="startEditing">
            <LucideEdit class="size-4" />
            Edit
          </Button>
        </div>
      </div>

      <!-- Error -->
      <Card v-if="error">
        <div class="flex items-center gap-3" style="color: #ef4444;">
          <LucideAlertCircle class="size-5" />
          <p>{{ error }}</p>
        </div>
      </Card>

      <!-- Edit Form -->
      <Card v-if="isEditing">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Edit Schedule</h2>
          <div class="flex items-center gap-2">
            <Button variant="outline" size="sm" :disabled="isSaving" @click="cancelEditing">
              <LucideX class="size-4" />
              Cancel
            </Button>
            <Button size="sm" :disabled="isSaving" @click="saveSchedule">
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
          <!-- Title -->
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Title</label>
            <input
              v-model="editForm.title"
              type="text"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
              placeholder="Schedule title..."
            />
          </div>
          <!-- Vehicle -->
          <div>
            <LinkField
              v-model="editForm.vehicle"
              doctype="Vehicle"
              label="Vehicle"
              placeholder="Search vehicle..."
              titleField="license_plate"
            />
          </div>
          <!-- Form Template -->
          <div>
            <LinkField
              v-model="editForm.form_template"
              doctype="Inspection Form Template"
              label="Form Template"
              placeholder="Search template..."
              titleField="title"
            />
          </div>
          <!-- Assigned To -->
          <div>
            <LinkField
              v-model="editForm.assigned_to"
              doctype="Employee"
              label="Assigned To"
              placeholder="Search employee..."
              titleField="employee_name"
            />
          </div>
          <!-- Status -->
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
          <!-- Frequency -->
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Frequency</label>
            <select
              v-model="editForm.frequency"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
            >
              <option v-for="f in FREQUENCIES" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <!-- Scheduled Date -->
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Scheduled Date</label>
            <input
              v-model="editForm.scheduled_date"
              type="date"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
            />
          </div>
          <!-- Next Due -->
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Next Due</label>
            <input
              v-model="editForm.next_due"
              type="date"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
            />
          </div>
          <!-- Notify Before Days -->
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">Notify Before (days)</label>
            <input
              v-model.number="editForm.notify_before_days"
              type="number"
              min="0"
              class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
            />
          </div>
        </div>
        <!-- Auto Create Inspection -->
        <div class="mt-4">
          <label class="flex items-center gap-2 text-sm font-medium cursor-pointer" style="color: var(--text-primary)">
            <input type="checkbox" v-model="editForm.auto_create_inspection" :true-value="1" :false-value="0" class="rounded" />
            Auto-create Inspection
          </label>
        </div>
        <!-- Notes -->
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
      </Card>

      <!-- Main Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column (2/3) -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Schedule Details Card -->
          <Card>
            <div class="flex items-center gap-2 mb-4">
              <LucideCalendarClock class="size-4" style="color: var(--text-muted);" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary);">Schedule Details</h2>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Vehicle</p>
                <RouterLink v-if="doc.vehicle" :to="`/vehicles/${doc.vehicle}`" class="text-sm mt-0.5 font-medium" style="color: var(--accent);">
                  {{ doc.vehicle }}
                </RouterLink>
                <p v-else class="text-sm mt-0.5" style="color: var(--text-primary);">—</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Form Template</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary);">{{ doc.form_template || '—' }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Assigned To</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary);">{{ doc.assigned_to || '—' }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Frequency</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary);">{{ doc.frequency }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Scheduled Date</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary);">{{ formatDate(doc.scheduled_date) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Next Due</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary);">{{ formatDate(doc.next_due) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Last Completed</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary);">{{ formatDate(doc.last_completed) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Auto-create Inspection</p>
                <div class="flex items-center gap-1 mt-0.5">
                  <LucideCheck v-if="doc.auto_create_inspection" class="size-4 text-green-500" />
                  <LucideBan v-else class="size-4" style="color: var(--text-muted);" />
                  <span class="text-sm" style="color: var(--text-primary);">
                    {{ doc.auto_create_inspection ? 'Yes' : 'No' }}
                  </span>
                </div>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Notify Before</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary);">
                  {{ doc.notify_before_days != null ? `${doc.notify_before_days} days` : '—' }}
                </p>
              </div>
            </div>
          </Card>

          <!-- Notes Card -->
          <Card v-if="doc.notes">
            <h2 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">Notes</h2>
            <p class="text-sm whitespace-pre-wrap" style="color: var(--text-secondary);">{{ doc.notes }}</p>
          </Card>

          <!-- Completion History Card -->
          <Card padding="none">
            <div class="flex items-center gap-2 px-4 pt-4 pb-3">
              <LucideClipboardCheck class="size-4" style="color: var(--text-muted);" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary);">Completion History</h2>
            </div>
            <div v-if="!completionHistory.length" class="px-4 pb-4">
              <p class="text-sm py-8 text-center" style="color: var(--text-muted);">
                No completed inspections yet
              </p>
            </div>
            <div v-else class="overflow-x-auto">
              <table class="w-full text-sm" style="color: var(--text-primary);">
                <thead>
                  <tr class="border-b" style="border-color: var(--border-subtle);">
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted);">Inspection</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted);">Date</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted);">Result</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted);">Score</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted);">Inspector</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted);">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="record in completionHistory"
                    :key="record.name"
                    class="border-b cursor-pointer transition-colors"
                    style="border-color: var(--border-subtle);"
                    @click="router.push(`/inspections/${record.name}`)"
                    @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
                    @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
                  >
                    <td class="px-4 py-3 font-medium" style="color: var(--accent);">
                      {{ record.name }}
                    </td>
                    <td class="px-4 py-3" style="color: var(--text-muted);">
                      {{ formatDate(record.inspection_date) }}
                    </td>
                    <td class="px-4 py-3">
                      <Badge
                        v-if="record.result"
                        :variant="record.result === 'Pass' ? 'success' : record.result === 'Fail' ? 'danger' : 'default'"
                        size="sm"
                      >
                        {{ record.result }}
                      </Badge>
                      <span v-else class="text-sm" style="color: var(--text-muted);">—</span>
                    </td>
                    <td class="px-4 py-3">
                      {{ record.score != null ? record.score : '—' }}
                    </td>
                    <td class="px-4 py-3">
                      {{ record.inspector || '—' }}
                    </td>
                    <td class="px-4 py-3">
                      <Badge v-if="record.status" :variant="STATUS_VARIANTS[record.status] || 'default'" size="sm">
                        {{ record.status }}
                      </Badge>
                      <span v-else style="color: var(--text-muted);">—</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <!-- Right Column / Sidebar (1/3) -->
        <div class="space-y-6">
          <!-- Actions Card -->
          <Card>
            <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary);">Actions</h2>
            <div class="space-y-2">
              <Button variant="outline" fullWidth @click="startEditing">
                <LucideEdit class="size-4" />
                Edit Schedule
              </Button>
              <Button
                v-if="doc.status === 'Active'"
                variant="outline"
                fullWidth
                @click="generateInspectionNow"
              >
                <LucideZap class="size-4" />
                Generate Inspection Now
              </Button>
              <Button
                v-if="doc.status === 'Active' || doc.status === 'Paused'"
                variant="outline"
                fullWidth
                @click="cancelSchedule"
              >
                <LucideBan class="size-4" />
                Cancel Schedule
              </Button>
            </div>
          </Card>

          <!-- Details Card -->
          <Card>
            <div class="flex items-center gap-2 mb-3">
              <LucideFileText class="size-4" style="color: var(--text-muted);" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary);">Details</h2>
            </div>
            <div class="space-y-3">
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Created</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary);">{{ formatDateTime(doc.creation) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Modified</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary);">{{ formatDateTime(doc.modified) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted);">Owner</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary);">{{ doc.owner }}</p>
              </div>
              <a
                :href="`/app/inspection-schedule/${doc.name}`"
                target="_blank"
                class="inline-flex items-center gap-1.5 text-sm font-medium transition-colors hover:opacity-80"
                style="color: var(--accent)"
              >
                Open in Desk →
              </a>
            </div>
          </Card>
        </div>
      </div>

      <!-- Audit Trail Card -->
      <Card v-if="auditTrail.length > 0">
        <div class="flex items-center gap-2 mb-4">
          <LucideHistory class="size-4" style="color: var(--text-muted);" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary);">Audit Trail</h2>
        </div>
        <div class="space-y-3">
          <div
            v-for="v in auditTrail"
            :key="v.name"
            class="pl-3 border-l-2 py-1"
            style="border-color: var(--border-color)"
          >
            <template v-for="(change, idx) in parseVersionChanges(v.data)" :key="idx">
              <p class="text-sm" style="color: var(--text-primary);">{{ change }}</p>
            </template>
            <p v-if="parseVersionChanges(v.data).length === 0" class="text-sm" style="color: var(--text-muted);">Document updated</p>
            <p class="text-xs mt-0.5" style="color: var(--text-muted);">
              {{ v.owner }} · {{ formatDateTime(v.creation) }}
            </p>
          </div>
        </div>
      </Card>
    </template>

    <!-- Error / Not Found -->
    <Card v-else-if="!isLoading">
      <div class="flex flex-col items-center py-12 text-center">
        <LucideAlertCircle class="size-8 mb-3" style="color: var(--text-muted);" />
        <p class="text-lg font-semibold" style="color: var(--text-primary);">Schedule not found</p>
        <p class="text-sm mt-1 mb-4" style="color: var(--text-muted);">
          {{ error || `The schedule "${id}" could not be loaded.` }}
        </p>
        <Button variant="secondary" @click="goBack">
          <LucideArrowLeft class="size-4" />
          Back
        </Button>
      </div>
    </Card>
  </div>
</template>
