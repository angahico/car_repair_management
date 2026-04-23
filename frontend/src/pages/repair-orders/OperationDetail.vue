<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import {
  LucideArrowLeft,
  LucideWrench,
  LucideUser,
  LucideMessageSquare,
  LucideAlertTriangle,
  LucideMonitor,
  LucideListChecks,
  LucideClipboard,
  LucideSend,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, LinkField } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface Issue {
  name: string
  subject: string
  status: string
  priority: string
}

interface Comment {
  name: string
  content: string
  comment_by: string
  comment_email: string
  creation: string
}

interface TaskInfo {
  name: string
  subject: string
  status: string
  priority: string
  progress: number
  exp_start_date: string | null
  exp_end_date: string | null
  completed_on: string | null
  _assign: string | null
}

interface WorkstationInfo {
  name: string
  workstation_name: string
  description: string | null
  production_capacity: number | null
}

interface AssignedUserInfo {
  name: string
  full_name: string
  user_image: string | null
}

interface OperationInfo {
  name: string
  operation_name: string
  planned_minutes: number
  workstation: string | null
  is_qc: number
  assigned_to: string | null
  task: string | null
  status: string
}

interface RepairOrderInfo {
  name: string
  status: string
  vehicle: string | null
  customer: string | null
  company: string | null
}

interface OperationDetailData {
  operation: OperationInfo
  task: TaskInfo | null
  workstation: WorkstationInfo | null
  comments: Comment[]
  issues: Issue[]
  assigned_user: AssignedUserInfo | null
  repair_order: RepairOrderInfo
}

const props = defineProps<{ roId: string; opId: string }>()
const router = useRouter()

const isLoading = ref(true)
const detail = ref<OperationDetailData | null>(null)
const updatingStatus = ref(false)
const newComment = ref('')
const addingComment = ref(false)
const assignUser = ref('')
const assigning = ref(false)

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Open: 'default',
  Working: 'primary',
  'Pending Review': 'warning',
  Completed: 'success',
  Rejected: 'danger',
  Cancelled: 'danger',
}

const ISSUE_STATUS_VARIANTS: Record<string, StatusVariant> = {
  Open: 'danger',
  'In Progress': 'primary',
  Resolved: 'success',
  Closed: 'default',
}

const STATUSES = ['Open', 'Working', 'Pending Review', 'Completed', 'Rejected', 'Cancelled']

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

async function loadDetail() {
  isLoading.value = true
  try {
    detail.value = await apiCall<OperationDetailData>(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.get_operation_detail',
      { repair_order: props.roId, operation_idx: props.opId },
    )
    if (detail.value) {
      assignUser.value = detail.value.operation.assigned_to || ''
    }
  } catch (e) {
    console.warn('Failed to load operation detail', e)
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.push(`/repair-orders/${props.roId}`)
}

async function updateStatus(status: string) {
  if (!detail.value || detail.value.operation.status === status) return
  updatingStatus.value = true
  try {
    await apiCall(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_operation_status',
      { repair_order: props.roId, operation_idx: props.opId, status },
    )
    detail.value.operation.status = status
  } catch (e) {
    console.warn('Failed to update status', e)
  } finally {
    updatingStatus.value = false
  }
}

async function addComment() {
  if (!newComment.value.trim()) return
  addingComment.value = true
  try {
    await apiCall(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.add_operation_comment',
      { repair_order: props.roId, operation_idx: props.opId, content: newComment.value },
    )
    newComment.value = ''
    await loadDetail()
  } catch (e) {
    console.warn('Failed to add comment', e)
  } finally {
    addingComment.value = false
  }
}

async function assignOperation(user: string) {
  assigning.value = true
  try {
    await apiCall(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.assign_operation',
      { repair_order: props.roId, operation_idx: props.opId, user },
    )
    await loadDetail()
  } catch (e) {
    console.warn('Failed to assign operation', e)
  } finally {
    assigning.value = false
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
            <h1 class="text-page-title">{{ detail.operation.operation_name }}</h1>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ detail.operation.name }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Badge :variant="STATUS_VARIANTS[detail.operation.status] || 'default'" size="md">
            {{ detail.operation.status }}
          </Badge>
          <Badge v-if="detail.operation.is_qc" variant="info" size="md">QC</Badge>
        </div>
      </div>

      <!-- Main Layout: 2/3 + 1/3 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column (2/3) -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Operation Details Card -->
          <Card>
            <div class="flex items-center gap-2 mb-4">
              <LucideWrench class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Operation Details</h2>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Operation</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.operation.operation_name }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Planned Minutes</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.operation.planned_minutes ?? '—' }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">QC Operation</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">
                  <Badge v-if="detail.operation.is_qc" variant="info" size="sm">Yes</Badge>
                  <span v-else>No</span>
                </p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Status</p>
                <p class="text-sm mt-0.5">
                  <Badge :variant="STATUS_VARIANTS[detail.operation.status] || 'default'" size="sm">
                    {{ detail.operation.status }}
                  </Badge>
                </p>
              </div>
            </div>
          </Card>

          <!-- Status Update Section -->
          <Card>
            <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">Update Status</h2>
            <div class="flex flex-wrap gap-2">
              <Button
                v-for="s in STATUSES"
                :key="s"
                :variant="detail.operation.status === s ? 'primary' : 'outline'"
                size="sm"
                :disabled="updatingStatus || detail.operation.status === s"
                :loading="updatingStatus"
                @click="updateStatus(s)"
              >
                {{ s }}
              </Button>
            </div>
          </Card>

          <!-- Comments Section -->
          <Card>
            <div class="flex items-center gap-2 mb-4">
              <LucideMessageSquare class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
                Comments ({{ detail.comments?.length || 0 }})
              </h2>
            </div>

            <!-- Comments List -->
            <div v-if="detail.comments && detail.comments.length > 0" class="space-y-3 mb-4">
              <div
                v-for="c in detail.comments"
                :key="c.name"
                class="p-3 rounded-lg"
                style="background: var(--bg-tertiary)"
              >
                <p class="text-sm whitespace-pre-wrap" style="color: var(--text-primary)" v-html="c.content"></p>
                <p class="text-xs mt-2" style="color: var(--text-muted)">
                  {{ c.comment_by }} · {{ formatDateTime(c.creation) }}
                </p>
              </div>
            </div>
            <div v-else class="mb-4">
              <p class="text-sm" style="color: var(--text-muted)">No comments yet.</p>
            </div>

            <!-- Add Comment -->
            <div class="pt-4 border-t" style="border-color: var(--border-subtle)">
              <textarea
                v-model="newComment"
                rows="3"
                placeholder="Add a comment..."
                class="w-full rounded-lg border p-3 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none"
                style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary)"
              />
              <div class="flex justify-end mt-2">
                <Button
                  size="sm"
                  :disabled="!newComment.trim() || addingComment"
                  :loading="addingComment"
                  @click="addComment"
                >
                  <LucideSend class="size-4" />
                  Add Comment
                </Button>
              </div>
            </div>
          </Card>

          <!-- Issues Card -->
          <Card v-if="detail.issues && detail.issues.length > 0" padding="none">
            <div class="px-4 pt-4 pb-3 flex items-center gap-2">
              <LucideAlertTriangle class="size-4" style="color: #ef4444" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
                Issues ({{ detail.issues.length }})
              </h2>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-sm" style="color: var(--text-primary)">
                <thead>
                  <tr class="border-b" style="border-color: var(--border-subtle)">
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Issue</th>
                    <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="issue in detail.issues"
                    :key="issue.name"
                    class="border-b"
                    style="border-color: var(--border-subtle)"
                  >
                    <td class="px-4 py-3 font-medium">{{ issue.subject || issue.name }}</td>
                    <td class="px-4 py-3">
                      <Badge :variant="ISSUE_STATUS_VARIANTS[issue.status] || 'default'" size="sm">
                        {{ issue.status }}
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
          <!-- Assignment Card -->
          <Card>
            <div class="flex items-center gap-2 mb-4">
              <LucideUser class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Assignment</h2>
            </div>
            <div v-if="detail.assigned_user" class="flex items-center gap-3 mb-4">
              <div
                class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold"
                style="background: var(--bg-tertiary); color: var(--text-primary)"
              >
                {{ (detail.assigned_user.full_name || detail.assigned_user.name).charAt(0).toUpperCase() }}
              </div>
              <div>
                <p class="text-sm font-medium" style="color: var(--text-primary)">
                  {{ detail.assigned_user.full_name || detail.assigned_user.name }}
                </p>
                <p class="text-xs" style="color: var(--text-muted)">
                  {{ detail.assigned_user.name }}
                </p>
              </div>
            </div>
            <div v-else class="mb-4">
              <p class="text-sm" style="color: var(--text-muted)">Unassigned</p>
            </div>
            <div class="pt-3 border-t" style="border-color: var(--border-subtle)">
              <LinkField
                v-model="assignUser"
                doctype="User"
                label="Reassign"
                placeholder="Search user..."
                @update:model-value="assignOperation"
              />
              <div v-if="assigning" class="mt-2">
                <p class="text-xs" style="color: var(--text-muted)">Updating assignment...</p>
              </div>
            </div>
          </Card>

          <!-- Workstation Card -->
          <Card v-if="detail.workstation">
            <div class="flex items-center gap-2 mb-4">
              <LucideMonitor class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Workstation</h2>
            </div>
            <div>
              <p class="text-sm font-medium" style="color: var(--text-primary)">{{ detail.workstation.workstation_name || detail.workstation.name }}</p>
              <p
                v-if="detail.workstation.description"
                class="text-xs mt-1"
                style="color: var(--text-muted)"
              >
                {{ detail.workstation.description }}
              </p>
            </div>
          </Card>

          <!-- Task Card -->
          <Card v-if="detail.task">
            <div class="flex items-center gap-2 mb-4">
              <LucideListChecks class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Linked Task</h2>
            </div>
            <div class="space-y-3">
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Task</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.task.subject }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Status</p>
                <p class="text-sm mt-0.5">
                  <Badge :variant="STATUS_VARIANTS[detail.task.status] || 'default'" size="sm">
                    {{ detail.task.status }}
                  </Badge>
                </p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Progress</p>
                <div class="mt-1">
                  <div class="w-full h-2 rounded-full" style="background: var(--bg-tertiary)">
                    <div
                      class="h-2 rounded-full transition-all"
                      style="background: var(--accent)"
                      :style="{ width: `${detail.task.progress}%` }"
                    />
                  </div>
                  <p class="text-xs mt-1" style="color: var(--text-muted)">{{ detail.task.progress }}%</p>
                </div>
              </div>
              <a
                :href="`/app/task/${detail.task.name}`"
                target="_blank"
                class="inline-flex items-center gap-1.5 text-sm font-medium transition-colors hover:opacity-80"
                style="color: var(--accent)"
              >
                Open in Desk →
              </a>
            </div>
          </Card>

          <!-- Repair Order Card -->
          <Card>
            <div class="flex items-center gap-2 mb-4">
              <LucideClipboard class="size-4" style="color: var(--text-muted)" />
              <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Repair Order</h2>
            </div>
            <div class="space-y-3">
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">Repair Order</p>
                <RouterLink
                  :to="`/repair-orders/${props.roId}`"
                  class="text-sm mt-0.5 font-medium transition-colors hover:opacity-80"
                  style="color: var(--accent)"
                >
                  {{ detail.repair_order.name }}
                </RouterLink>
              </div>
              <div v-if="detail.repair_order.vehicle">
                <p class="text-xs font-medium" style="color: var(--text-muted)">Vehicle</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.repair_order.vehicle }}</p>
              </div>
              <div v-if="detail.repair_order.customer">
                <p class="text-xs font-medium" style="color: var(--text-muted)">Customer</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.repair_order.customer }}</p>
              </div>
              <div v-if="detail.repair_order.company">
                <p class="text-xs font-medium" style="color: var(--text-muted)">Company</p>
                <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.repair_order.company }}</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </template>

    <!-- Error / Not Found -->
    <Card v-else>
      <div class="flex flex-col items-center py-12 text-center">
        <p class="text-lg font-semibold" style="color: var(--text-primary)">Operation not found</p>
        <p class="text-sm mt-1 mb-4" style="color: var(--text-muted)">
          The operation "{{ opId }}" could not be loaded.
        </p>
        <Button variant="secondary" @click="goBack">
          <LucideArrowLeft class="size-4" />
          Back to Repair Order
        </Button>
      </div>
    </Card>
  </div>
</template>
