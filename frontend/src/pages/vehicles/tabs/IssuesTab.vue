<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import {
  LucideAlertTriangle,
  LucidePlus,
  LucideUser,
  LucideCalendar,
  LucideExternalLink,
  LucideWrench,
  LucideX,
  LucideCopy,
  LucideChevronDown,
  LucideChevronUp,
  LucideImage,
  LucideFileText,
  LucideLoader2,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'

const props = defineProps<{ vehicleId: string }>()
const router = useRouter()

const isLoading = ref(true)
const issuesData = ref<any>(null)
const expandedIssue = ref<string | null>(null)

// Action state
const isConverting = ref<string | null>(null)
const showDuplicateModal = ref<string | null>(null)
const duplicateOfValue = ref('')
const showCloseModal = ref<string | null>(null)
const closeReasonValue = ref('')
const isDuplicateSubmitting = ref(false)
const isCloseSubmitting = ref(false)

async function convertToWorkOrder(issueName: string) {
  if (!confirm('Convert this issue to a new Work Order?')) return
  isConverting.value = issueName
  try {
    const roName = await apiCall<string>('car_repair_management.api.issue.convert_issue_to_work_order', {
      issue_name: issueName,
    })
    router.push(`/repair-orders/${roName}`)
  } catch (e) {
    console.error('Failed to convert issue to work order', e)
    alert('Failed to convert issue. Please try again.')
  } finally {
    isConverting.value = null
  }
}

function openDuplicateModal(issueName: string) {
  duplicateOfValue.value = ''
  showDuplicateModal.value = issueName
}

async function markAsDuplicate() {
  if (!showDuplicateModal.value || !duplicateOfValue.value.trim()) return
  isDuplicateSubmitting.value = true
  try {
    await apiCall('car_repair_management.api.issue.mark_issue_duplicate', {
      issue_name: showDuplicateModal.value,
      duplicate_of: duplicateOfValue.value.trim(),
    })
    showDuplicateModal.value = null
    duplicateOfValue.value = ''
    await loadIssues()
  } catch (e) {
    console.error('Failed to mark issue as duplicate', e)
    alert('Failed to mark as duplicate. Please try again.')
  } finally {
    isDuplicateSubmitting.value = false
  }
}

function openCloseModal(issueName: string) {
  closeReasonValue.value = ''
  showCloseModal.value = issueName
}

async function closeWithReason() {
  if (!showCloseModal.value || !closeReasonValue.value.trim()) return
  isCloseSubmitting.value = true
  try {
    await apiCall('car_repair_management.api.issue.close_issue_with_reason', {
      issue_name: showCloseModal.value,
      reason: closeReasonValue.value.trim(),
    })
    showCloseModal.value = null
    closeReasonValue.value = ''
    await loadIssues()
  } catch (e) {
    console.error('Failed to close issue', e)
    alert('Failed to close issue. Please try again.')
  } finally {
    isCloseSubmitting.value = false
  }
}

const severityColors: Record<string, string> = {
  'Critical': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  'High': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  'Medium': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  'Low': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
}

const statusColors: Record<string, string> = {
  'Open': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  'In Progress': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  'Resolved': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  'Closed': 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
}

async function loadIssues() {
  isLoading.value = true
  try {
    issuesData.value = await apiCall('car_repair_management.api.vehicle.get_vehicle_issues_full', {
      vehicle_name: props.vehicleId,
    })
  } catch (e) {
    console.error('Failed to load issues', e)
  } finally {
    isLoading.value = false
  }
}

function toggleIssue(issueId: string) {
  expandedIssue.value = expandedIssue.value === issueId ? null : issueId
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString()
}

onMounted(loadIssues)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <template v-if="isLoading">
      <div class="grid grid-cols-3 gap-4">
        <Card v-for="i in 3" :key="i"><Skeleton height="80px" /></Card>
      </div>
      <Card><Skeleton height="300px" /></Card>
    </template>

    <template v-else-if="issuesData">
      <!-- Issue Counts -->
      <div class="grid grid-cols-3 gap-4">
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Open Issues</p>
          <p class="text-3xl font-bold" style="color: var(--text-primary);">{{ issuesData.counts?.open || 0 }}</p>
        </Card>
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Overdue</p>
          <p class="text-3xl font-bold text-red-500">{{ issuesData.counts?.overdue || 0 }}</p>
        </Card>
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Resolved</p>
          <p class="text-3xl font-bold text-green-600">{{ issuesData.counts?.closed || 0 }}</p>
        </Card>
      </div>

      <!-- Open Issues List -->
      <Card>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold" style="color: var(--text-primary);">
            <LucideAlertTriangle class="inline size-5 mr-2" />
            Open Issues
          </h3>
          <a :href="`/app/issue/new?custom_vehicle=${props.vehicleId}`" target="_blank">
            <Button>
              <LucidePlus class="size-4" />
              Report Issue
            </Button>
          </a>
        </div>

        <div v-if="issuesData.open_issues?.length" class="space-y-3">
          <div
            v-for="issue in issuesData.open_issues"
            :key="issue.name"
            class="rounded-lg border overflow-hidden"
            style="border-color: var(--border-color);"
          >
            <!-- Issue Header -->
            <button
              @click="toggleIssue(issue.name)"
              class="w-full flex items-center justify-between p-4 text-left transition-colors hover:opacity-90"
              style="background-color: var(--bg-tertiary);"
            >
              <div class="flex items-center gap-3">
                <LucideAlertTriangle
                  class="size-5"
                  :class="issue.severity === 'Critical' || issue.severity === 'High' ? 'text-red-500' : ''"
                  :style="issue.severity !== 'Critical' && issue.severity !== 'High' ? { color: 'var(--text-muted)' } : {}"
                />
                <div>
                  <div class="flex items-center gap-2">
                    <p class="text-sm font-medium" style="color: var(--text-primary);">{{ issue.title }}</p>
                    <span v-if="issue.is_overdue" class="px-1.5 py-0.5 rounded text-xs bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                      Overdue
                    </span>
                  </div>
                  <div class="flex items-center gap-3 text-xs mt-1" style="color: var(--text-muted);">
                    <span class="flex items-center gap-1">
                      <LucideUser class="size-3" />
                      {{ issue.reported_by }}
                    </span>
                    <span class="flex items-center gap-1">
                      <LucideCalendar class="size-3" />
                      {{ issue.date }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <span :class="['px-2 py-1 rounded-full text-xs font-medium', severityColors[issue.severity] || severityColors['Medium']]">
                  {{ issue.severity }}
                </span>
                <span :class="['px-2 py-1 rounded-full text-xs font-medium', statusColors[issue.status] || statusColors['Open']]">
                  {{ issue.status }}
                </span>
                <component
                  :is="expandedIssue === issue.name ? LucideChevronUp : LucideChevronDown"
                  class="size-4"
                  style="color: var(--text-muted);"
                />
              </div>
            </button>

            <!-- Issue Detail (Expandable) -->
            <div
              v-if="expandedIssue === issue.name"
              class="p-4 border-t"
              style="border-color: var(--border-color);"
            >
              <!-- Description -->
              <div class="mb-4">
                <h4 class="text-xs uppercase tracking-wide mb-2" style="color: var(--text-muted);">Description</h4>
                <p class="text-sm" style="color: var(--text-secondary);">
                  {{ issue.description || 'No description provided.' }}
                </p>
              </div>

              <!-- Linked Work Order -->
              <div v-if="issue.linked_work_order" class="mb-4">
                <h4 class="text-xs uppercase tracking-wide mb-2" style="color: var(--text-muted);">Linked Work Order</h4>
                <RouterLink
                  :to="`/repair-orders/${issue.linked_work_order}`"
                  class="inline-flex items-center gap-1 text-sm hover:underline"
                  style="color: var(--text-primary);"
                >
                  {{ issue.linked_work_order }}
                  <LucideExternalLink class="size-3" />
                </RouterLink>
              </div>

              <!-- Resolution Actions -->
              <div class="flex flex-wrap gap-2 pt-4 border-t" style="border-color: var(--border-subtle);">
                <Button size="sm" :disabled="isConverting === issue.name" @click.stop="convertToWorkOrder(issue.name)">
                  <LucideLoader2 v-if="isConverting === issue.name" class="size-4 animate-spin" />
                  <LucideWrench v-else class="size-4" />
                  Convert to Work Order
                </Button>
                <Button variant="outline" size="sm" @click.stop="openDuplicateModal(issue.name)">
                  <LucideCopy class="size-4" />
                  Mark as Duplicate
                </Button>
                <Button variant="outline" size="sm" @click.stop="openCloseModal(issue.name)">
                  <LucideX class="size-4" />
                  Close with Reason
                </Button>
              </div>

              <!-- Duplicate Modal -->
              <div
                v-if="showDuplicateModal === issue.name"
                class="mt-4 p-4 rounded-lg border"
                style="background-color: var(--bg-tertiary); border-color: var(--border-color);"
                @click.stop
              >
                <h4 class="text-sm font-medium mb-2" style="color: var(--text-primary);">Mark as Duplicate</h4>
                <label class="block text-xs mb-1" style="color: var(--text-muted);">Duplicate of (Issue ID)</label>
                <input
                  v-model="duplicateOfValue"
                  type="text"
                  placeholder="e.g. ISS-00042"
                  class="w-full px-3 py-2 rounded border text-sm mb-3"
                  style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
                />
                <div class="flex gap-2 justify-end">
                  <Button variant="outline" size="sm" @click="showDuplicateModal = null">Cancel</Button>
                  <Button size="sm" :disabled="!duplicateOfValue.trim() || isDuplicateSubmitting" @click="markAsDuplicate()">
                    <LucideLoader2 v-if="isDuplicateSubmitting" class="size-4 animate-spin" />
                    Confirm
                  </Button>
                </div>
              </div>

              <!-- Close with Reason Modal -->
              <div
                v-if="showCloseModal === issue.name"
                class="mt-4 p-4 rounded-lg border"
                style="background-color: var(--bg-tertiary); border-color: var(--border-color);"
                @click.stop
              >
                <h4 class="text-sm font-medium mb-2" style="color: var(--text-primary);">Close with Reason</h4>
                <label class="block text-xs mb-1" style="color: var(--text-muted);">Resolution Reason</label>
                <textarea
                  v-model="closeReasonValue"
                  rows="3"
                  placeholder="Enter the reason for closing this issue..."
                  class="w-full px-3 py-2 rounded border text-sm mb-3"
                  style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary); resize: vertical;"
                ></textarea>
                <div class="flex gap-2 justify-end">
                  <Button variant="outline" size="sm" @click="showCloseModal = null">Cancel</Button>
                  <Button size="sm" :disabled="!closeReasonValue.trim() || isCloseSubmitting" @click="closeWithReason()">
                    <LucideLoader2 v-if="isCloseSubmitting" class="size-4 animate-spin" />
                    Close Issue
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-8">
          <LucideAlertTriangle class="size-12 mx-auto mb-4" style="color: var(--text-muted);" />
          <h3 class="text-lg font-semibold mb-2" style="color: var(--text-primary);">No Open Issues</h3>
          <p class="text-sm" style="color: var(--text-muted);">This vehicle has no open issues.</p>
        </div>
      </Card>

      <!-- Recently Resolved -->
      <Card v-if="issuesData.closed_issues?.length">
        <h3 class="text-lg font-semibold mb-4" style="color: var(--text-primary);">Recently Resolved</h3>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Issue</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Severity</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Reported</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Linked WO</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="issue in issuesData.closed_issues"
                :key="issue.name"
                class="border-b"
                style="border-color: var(--border-subtle);"
              >
                <td class="px-4 py-3">
                  <p class="text-sm font-medium" style="color: var(--text-primary);">{{ issue.title }}</p>
                  <p class="text-xs truncate max-w-xs" style="color: var(--text-muted);">{{ issue.resolution_notes }}</p>
                </td>
                <td class="px-4 py-3">
                  <span :class="['px-2 py-1 rounded-full text-xs font-medium', severityColors[issue.severity] || severityColors['Medium']]">
                    {{ issue.severity }}
                  </span>
                </td>
                <td class="px-4 py-3 text-sm" style="color: var(--text-secondary);">{{ issue.date }}</td>
                <td class="px-4 py-3">
                  <RouterLink
                    v-if="issue.linked_work_order"
                    :to="`/repair-orders/${issue.linked_work_order}`"
                    class="flex items-center gap-1 text-sm hover:underline"
                    style="color: var(--text-primary);"
                  >
                    {{ issue.linked_work_order }}
                    <LucideExternalLink class="size-3" />
                  </RouterLink>
                  <span v-else class="text-sm" style="color: var(--text-muted);">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </template>
  </div>
</template>
