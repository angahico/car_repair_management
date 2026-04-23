<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideArrowLeft,
  LucideAlertTriangle,
  LucideUser,
  LucideClipboardList,
  LucideClipboardCheck,
  LucideBug,
  LucideShield,
  LucideCheck,
  LucideX,
  LucideWrench,
  LucideExternalLink,
  LucideLoader2,
  LucideSend,
  LucideSearch,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, ConfirmModal } from '@/components/ui'
import ActivityTimeline from '@/components/common/ActivityTimeline.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()
const { t } = useI18n()

interface IssueDetailData {
  doc: Record<string, any>
  comments: any[]
  audit_trail: any[]
  available_actions: string[]
}

const isLoading = ref(true)
const data = ref<IssueDetailData | null>(null)
const isActioning = ref(false)
const showRejectModal = ref(false)
const showCloseModal = ref(false)
const showDuplicateModal = ref(false)
const duplicateOf = ref('')
const newComment = ref('')
const isPostingComment = ref(false)
const activityKey = ref(0)

// Work Order creation modal state
const showWOModal = ref(false)
const woOrderFor = ref<'Company' | 'Customer'>('Company')
const woCustomer = ref('')
const woCompany = ref('')
const woCustomerDisplay = ref('')
const woCompanyDisplay = ref('')
const woSearchOpen = ref<'customer' | 'company' | null>(null)
const woSearchQuery = ref('')
const woSearchResults = ref<{ name: string; label: string }[]>([])
const woSearchLoading = ref(false)

const SEVERITY_VARIANTS: Record<string, string> = {
  Low: 'default', Medium: 'warning', High: 'danger', Critical: 'danger',
}
const STATUS_VARIANTS: Record<string, string> = {
  Open: 'warning', Replied: 'info', Resolved: 'success', Closed: 'default',
}
const WORKFLOW_VARIANTS: Record<string, string> = {
  Draft: 'default',
  'Pending Custodian Approval': 'warning',
  Rejected: 'danger',
  Submitted: 'success',
  'Work Order Created': 'info',
}

const actions = computed(() => data.value?.available_actions || [])

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
    const result = await apiCall<IssueDetailData>(
      'car_repair_management.api.issue.get_issue_detail',
      { name: props.id },
    )
    data.value = result
  } catch (e) {
    console.warn('Failed to load issue detail', e)
  } finally {
    isLoading.value = false
  }
}

async function handleApprove() {
  isActioning.value = true
  try {
    await apiCall('car_repair_management.api.issue.approve_issue', { issue_name: props.id })
    await loadData()
    activityKey.value++
  } catch (e: any) {
    alert(e.message || 'Failed to approve')
  } finally {
    isActioning.value = false
  }
}

async function handleReject(reason: string) {
  isActioning.value = true
  try {
    await apiCall('car_repair_management.api.issue.reject_issue', {
      issue_name: props.id,
      reason: reason || undefined,
    })
    showRejectModal.value = false
    await loadData()
    activityKey.value++
  } catch (e: any) {
    alert(e.message || 'Failed to reject')
  } finally {
    isActioning.value = false
  }
}

function openWOModal() {
  woOrderFor.value = 'Company'
  woCustomer.value = ''
  woCompany.value = ''
  woCustomerDisplay.value = ''
  woCompanyDisplay.value = ''
  woSearchOpen.value = null
  woSearchQuery.value = ''
  woSearchResults.value = []
  showWOModal.value = true
}

async function woSearch(doctype: string, txt: string) {
  woSearchLoading.value = true
  try {
    const results = await apiCall<any[]>(
      'car_repair_management.api.issue.search_link_options',
      { doctype, txt, limit_page_length: 20 },
    )
    woSearchResults.value = (results || []).map((r: any) => ({ name: r.name, label: r.name }))
  } catch {
    woSearchResults.value = []
  } finally {
    woSearchLoading.value = false
  }
}

function handleWOSearchFocus(type: 'customer' | 'company') {
  woSearchOpen.value = type
  woSearchQuery.value = ''
  woSearch(type === 'customer' ? 'Customer' : 'Company', '')
}

function handleWOSearchInput(type: 'customer' | 'company', e: Event) {
  const val = (e.target as HTMLInputElement).value
  woSearchQuery.value = val
  if (type === 'customer') woCustomerDisplay.value = val
  else woCompanyDisplay.value = val
  woSearch(type === 'customer' ? 'Customer' : 'Company', val)
}

function selectWOOption(type: 'customer' | 'company', option: { name: string; label: string }) {
  if (type === 'customer') {
    woCustomer.value = option.name
    woCustomerDisplay.value = option.label
  } else {
    woCompany.value = option.name
    woCompanyDisplay.value = option.label
  }
  woSearchOpen.value = null
  woSearchQuery.value = ''
}

async function handleCreateWorkOrder() {
  isActioning.value = true
  try {
    const params: Record<string, string> = {
      issue_name: props.id,
      order_for: woOrderFor.value,
    }
    if (woOrderFor.value === 'Customer') params.customer = woCustomer.value
    else params.company = woCompany.value

    const roName = await apiCall<string>(
      'car_repair_management.api.issue.convert_issue_to_work_order',
      params,
    )
    showWOModal.value = false
    router.push(`/repair-orders/${roName}`)
  } catch (e: any) {
    alert(e.message || 'Failed to create work order')
  } finally {
    isActioning.value = false
  }
}

async function handleClose(reason: string) {
  isActioning.value = true
  try {
    await apiCall('car_repair_management.api.issue.close_issue_with_reason', {
      issue_name: props.id,
      reason,
    })
    showCloseModal.value = false
    await loadData()
    activityKey.value++
  } catch (e: any) {
    alert(e.message || 'Failed to close')
  } finally {
    isActioning.value = false
  }
}

async function handleMarkDuplicate() {
  if (!duplicateOf.value.trim()) return
  isActioning.value = true
  try {
    await apiCall('car_repair_management.api.issue.mark_issue_duplicate', {
      issue_name: props.id,
      duplicate_of: duplicateOf.value,
    })
    showDuplicateModal.value = false
    await loadData()
    activityKey.value++
  } catch (e: any) {
    alert(e.message || 'Failed to mark duplicate')
  } finally {
    isActioning.value = false
  }
}

async function postComment() {
  if (!newComment.value.trim()) return
  isPostingComment.value = true
  try {
    await apiCall('frappe.client.add_comment', {
      reference_doctype: 'Issue',
      reference_name: props.id,
      content: newComment.value,
      comment_email: '',
    })
    newComment.value = ''
    activityKey.value++
  } catch (e: any) {
    alert(e.message || 'Failed to post comment')
  } finally {
    isPostingComment.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div class="flex items-center gap-4">
        <Button variant="outline" @click="router.push('/issues')">
          <LucideArrowLeft class="size-4" />
        </Button>
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <h1 class="text-page-title">{{ data?.doc?.name || id }}</h1>
            <Badge v-if="data?.doc?.custom_severity" :variant="SEVERITY_VARIANTS[data.doc.custom_severity] || 'default'">{{ data.doc.custom_severity }}</Badge>
            <Badge v-if="data?.doc?.status" :variant="STATUS_VARIANTS[data.doc.status] || 'default'">{{ data.doc.status }}</Badge>
            <Badge v-if="data?.doc?.custom_workflow_state" :variant="WORKFLOW_VARIANTS[data.doc.custom_workflow_state] || 'default'">{{ data.doc.custom_workflow_state }}</Badge>
          </div>
          <p v-if="data?.doc?.subject" class="text-sm mt-1" style="color: var(--text-muted)">{{ data.doc.subject }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <!-- Workflow Actions -->
        <Button v-if="actions.includes('approve')" variant="primary" :loading="isActioning" @click="handleApprove">
          <LucideCheck class="size-4" /> {{ $t('issues.approve') }}
        </Button>
        <Button v-if="actions.includes('reject')" variant="danger" :loading="isActioning" @click="showRejectModal = true">
          <LucideX class="size-4" /> {{ $t('issues.reject') }}
        </Button>
        <Button v-if="actions.includes('create_work_order')" variant="primary" :loading="isActioning" @click="openWOModal">
          <LucideWrench class="size-4" /> {{ $t('issues.create_work_order') }}
        </Button>
        <Button v-if="actions.includes('open_draft_ro')" variant="outline" @click="router.push(`/repair-orders/${data?.doc?.custom_linked_work_order}`)">
          <LucideExternalLink class="size-4" /> {{ $t('issues.open_work_order') }}
        </Button>
        <Button v-if="actions.includes('close')" variant="outline" @click="showCloseModal = true">{{ $t('issues.close_issue') }}</Button>
        <Button v-if="actions.includes('mark_duplicate')" variant="outline" @click="showDuplicateModal = true">{{ $t('issues.mark_duplicate') }}</Button>
        <a :href="`/app/issue/${id}`" target="_blank">
          <Button variant="outline">{{ $t('common.open_in_desk') }}</Button>
        </a>
      </div>
    </div>

    <!-- Loading -->
    <template v-if="isLoading">
      <Card><Skeleton height="200px" /></Card>
    </template>

    <template v-if="!isLoading && data">
      <!-- Summary -->
      <Card>
        <h2 class="text-section-title mb-4">{{ $t('common.summary') }}</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('common.vehicle') }}</p>
            <p v-if="data.doc.custom_vehicle" class="text-sm font-medium cursor-pointer" style="color: var(--accent)" @click="router.push(`/vehicles/${data.doc.custom_vehicle}`)">{{ data.doc.custom_vehicle }}</p>
            <p v-else class="text-sm font-medium" style="color: var(--text-primary)">—</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.category') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.custom_category || '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.source') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.custom_source || '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.reported_by') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.raised_by || data.doc.owner || '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('common.created') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ formatDateTime(data.doc.creation) }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.assigned_to') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.custom_assigned_to || '—' }}</p>
          </div>
        </div>
        <div v-if="data.doc.description" class="mt-4 pt-4 border-t" :style="{ borderColor: 'var(--border-color)' }">
          <p class="text-xs mb-1" style="color: var(--text-muted)">{{ $t('common.description') }}</p>
          <p class="text-sm" style="color: var(--text-primary); white-space: pre-wrap;">{{ stripHtml(data.doc.description || '') }}</p>
        </div>
      </Card>

      <!-- Rejection Info -->
      <Card v-if="data.doc.custom_workflow_state === 'Rejected'">
        <div class="flex items-center gap-2 mb-3">
          <LucideX class="size-5" style="color: #ef4444" />
          <h2 class="text-section-title" style="color: #ef4444">{{ $t('issues.rejection_info') }}</h2>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.rejected_by') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ data.doc.custom_rejected_by || '—' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.rejected_on') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ formatDateTime(data.doc.custom_rejected_on) }}</p>
          </div>
        </div>
        <div v-if="data.doc.custom_rejection_reason" class="mt-3">
          <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.rejection_reason') }}</p>
          <p class="text-sm" style="color: var(--text-primary)">{{ data.doc.custom_rejection_reason }}</p>
        </div>
      </Card>

      <!-- Relationships -->
      <Card>
        <h2 class="text-section-title mb-4">{{ $t('issues.relationships') }}</h2>
        <div class="space-y-3">
          <div v-if="data.doc.custom_linked_work_order" class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary);">
            <LucideClipboardList class="size-5" style="color: var(--accent)" />
            <div>
              <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.linked_work_order') }}</p>
              <p class="text-sm font-medium cursor-pointer" style="color: var(--accent)" @click="router.push(`/repair-orders/${data.doc.custom_linked_work_order}`)">{{ data.doc.custom_linked_work_order }}</p>
            </div>
          </div>
          <div v-if="data.doc.custom_linked_inspection" class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary);">
            <LucideClipboardCheck class="size-5" style="color: var(--text-muted)" />
            <div>
              <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.linked_inspection') }}</p>
              <p class="text-sm font-medium cursor-pointer" style="color: var(--accent)" @click="router.push(`/inspections/${data.doc.custom_linked_inspection}`)">{{ data.doc.custom_linked_inspection }}</p>
            </div>
          </div>
          <div v-if="data.doc.custom_linked_fault" class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary);">
            <LucideBug class="size-5" style="color: var(--text-muted)" />
            <div>
              <p class="text-xs" style="color: var(--text-muted)">{{ $t('issues.linked_fault') }}</p>
              <p class="text-sm font-medium cursor-pointer" style="color: var(--accent)" @click="router.push(`/issues/faults/${data.doc.custom_linked_fault}`)">{{ data.doc.custom_linked_fault }}</p>
            </div>
          </div>
          <p v-if="!data.doc.custom_linked_work_order && !data.doc.custom_linked_inspection && !data.doc.custom_linked_fault" class="text-sm" style="color: var(--text-muted)">{{ $t('issues.no_linked_entities') }}</p>
        </div>
      </Card>

      <!-- Resolution -->
      <Card v-if="data.doc.resolution_details || data.doc.custom_resolution_notes">
        <div class="flex items-center gap-2 mb-4">
          <LucideShield class="size-5" style="color: var(--text-muted)" />
          <h2 class="text-section-title">{{ $t('issues.resolution') }}</h2>
        </div>
        <div v-if="data.doc.resolution_details" class="mb-3">
          <p class="text-xs mb-1" style="color: var(--text-muted)">{{ $t('issues.resolution_details') }}</p>
          <p class="text-sm" style="color: var(--text-primary); white-space: pre-wrap;">{{ stripHtml(data.doc.resolution_details) }}</p>
        </div>
        <div v-if="data.doc.custom_resolution_notes">
          <p class="text-xs mb-1" style="color: var(--text-muted)">{{ $t('issues.resolution_notes') }}</p>
          <p class="text-sm" style="color: var(--text-primary); white-space: pre-wrap;">{{ stripHtml(data.doc.custom_resolution_notes) }}</p>
        </div>
      </Card>

      <!-- Post Comment -->
      <Card>
        <h2 class="text-section-title mb-3">{{ $t('issues.add_comment') }}</h2>
        <div class="flex gap-3">
          <textarea
            v-model="newComment"
            rows="2"
            class="flex-1 px-3 py-2 text-sm rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-gray-400"
            style="background: var(--bg-tertiary); color: var(--text-primary); border-color: var(--border-color);"
            :placeholder="$t('issues.comment_placeholder')"
          />
          <Button variant="primary" :loading="isPostingComment" @click="postComment" class="self-end">
            <LucideSend class="size-4" />
          </Button>
        </div>
      </Card>

      <!-- Activity Timeline -->
      <ActivityTimeline :key="activityKey" doctype="Issue" :name="id" />
    </template>

    <!-- Reject Modal -->
    <ConfirmModal
      v-if="showRejectModal"
      :title="$t('issues.reject_issue')"
      :message="$t('issues.reject_confirm')"
      :confirm-label="$t('issues.reject')"
      variant="danger"
      :show-reason="true"
      :reason-label="$t('issues.rejection_reason')"
      :loading="isActioning"
      @confirm="handleReject"
      @cancel="showRejectModal = false"
    />

    <!-- Close Modal -->
    <ConfirmModal
      v-if="showCloseModal"
      :title="$t('issues.close_issue')"
      :message="$t('issues.close_confirm')"
      :confirm-label="$t('common.close')"
      variant="warning"
      :show-reason="true"
      :reason-label="$t('issues.close_reason')"
      :loading="isActioning"
      @confirm="handleClose"
      @cancel="showCloseModal = false"
    />

    <!-- Duplicate Modal -->
    <Teleport to="body">
      <div
        v-if="showDuplicateModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        style="background: rgba(0, 0, 0, 0.4);"
        @click.self="showDuplicateModal = false"
      >
        <Card class="w-full max-w-md">
          <h3 class="text-base font-semibold mb-3" style="color: var(--text-primary)">{{ $t('issues.mark_duplicate') }}</h3>
          <p class="text-sm mb-3" style="color: var(--text-muted)">{{ $t('issues.duplicate_confirm') }}</p>
          <input
            v-model="duplicateOf"
            type="text"
            class="w-full h-10 px-3 rounded-lg border mb-4"
            style="background: var(--bg-tertiary); color: var(--text-primary); border-color: var(--border-color);"
            :placeholder="$t('issues.duplicate_of_placeholder')"
          />
          <div class="flex justify-end gap-2">
            <Button variant="ghost" size="sm" @click="showDuplicateModal = false">{{ $t('common.cancel') }}</Button>
            <Button variant="primary" size="sm" :loading="isActioning" @click="handleMarkDuplicate">{{ $t('common.confirm') }}</Button>
          </div>
        </Card>
      </div>
    </Teleport>

    <!-- Work Order Creation Modal -->
    <Teleport to="body">
      <div
        v-if="showWOModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        style="background: rgba(0, 0, 0, 0.4);"
        @click.self="showWOModal = false"
      >
        <Card class="w-full max-w-md">
          <div class="flex items-center gap-3 mb-4">
            <div class="p-2 rounded-lg shrink-0" style="background: var(--bg-tertiary);">
              <LucideWrench class="size-5" style="color: var(--accent);" />
            </div>
            <div>
              <h3 class="text-base font-semibold" style="color: var(--text-primary);">Create Work Order</h3>
              <p class="text-sm" style="color: var(--text-muted);">Select who this work order is for</p>
            </div>
          </div>

          <!-- Order For -->
          <div class="mb-4">
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary);">Order For <span class="text-red-500">*</span></label>
            <div class="flex gap-3">
              <label
                class="flex-1 flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors"
                :style="{
                  borderColor: woOrderFor === 'Company' ? 'var(--accent)' : 'var(--border-color)',
                  background: woOrderFor === 'Company' ? 'var(--bg-tertiary)' : 'transparent',
                }"
              >
                <input type="radio" v-model="woOrderFor" value="Company" class="accent-current" />
                <span class="text-sm font-medium" style="color: var(--text-primary);">Company</span>
              </label>
              <label
                class="flex-1 flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors"
                :style="{
                  borderColor: woOrderFor === 'Customer' ? 'var(--accent)' : 'var(--border-color)',
                  background: woOrderFor === 'Customer' ? 'var(--bg-tertiary)' : 'transparent',
                }"
              >
                <input type="radio" v-model="woOrderFor" value="Customer" class="accent-current" />
                <span class="text-sm font-medium" style="color: var(--text-primary);">Customer</span>
              </label>
            </div>
          </div>

          <!-- Company Search (when order_for == Company) -->
          <div v-if="woOrderFor === 'Company'" class="mb-4 relative">
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary);">Company <span class="text-red-500">*</span></label>
            <div class="relative">
              <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4" style="color: var(--text-muted);" />
              <input
                type="text"
                :value="woCompanyDisplay"
                placeholder="Search company..."
                class="w-full h-10 pl-10 pr-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
                style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
                @focus="handleWOSearchFocus('company')"
                @input="handleWOSearchInput('company', $event)"
              />
            </div>
            <div
              v-if="woSearchOpen === 'company'"
              class="absolute z-50 w-full mt-1 rounded-lg border shadow-lg overflow-hidden"
              style="background-color: var(--bg-elevated); border-color: var(--border-color);"
            >
              <div v-if="woSearchLoading" class="flex items-center justify-center py-4">
                <LucideLoader2 class="size-5 animate-spin" style="color: var(--text-muted);" />
              </div>
              <div v-else-if="woSearchResults.length === 0" class="py-4 text-center text-sm" style="color: var(--text-muted);">No companies found</div>
              <ul v-else class="max-h-48 overflow-y-auto">
                <li
                  v-for="opt in woSearchResults"
                  :key="opt.name"
                  class="px-4 py-2.5 cursor-pointer transition-colors hover:opacity-80"
                  :style="{ backgroundColor: opt.name === woCompany ? 'var(--bg-tertiary)' : 'transparent' }"
                  @click="selectWOOption('company', opt)"
                >
                  <p class="text-sm" style="color: var(--text-primary);">{{ opt.label }}</p>
                </li>
              </ul>
            </div>
          </div>

          <!-- Customer Search (when order_for == Customer) -->
          <div v-if="woOrderFor === 'Customer'" class="mb-4 relative">
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary);">Customer <span class="text-red-500">*</span></label>
            <div class="relative">
              <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4" style="color: var(--text-muted);" />
              <input
                type="text"
                :value="woCustomerDisplay"
                placeholder="Search customer..."
                class="w-full h-10 pl-10 pr-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
                style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
                @focus="handleWOSearchFocus('customer')"
                @input="handleWOSearchInput('customer', $event)"
              />
            </div>
            <div
              v-if="woSearchOpen === 'customer'"
              class="absolute z-50 w-full mt-1 rounded-lg border shadow-lg overflow-hidden"
              style="background-color: var(--bg-elevated); border-color: var(--border-color);"
            >
              <div v-if="woSearchLoading" class="flex items-center justify-center py-4">
                <LucideLoader2 class="size-5 animate-spin" style="color: var(--text-muted);" />
              </div>
              <div v-else-if="woSearchResults.length === 0" class="py-4 text-center text-sm" style="color: var(--text-muted);">No customers found</div>
              <ul v-else class="max-h-48 overflow-y-auto">
                <li
                  v-for="opt in woSearchResults"
                  :key="opt.name"
                  class="px-4 py-2.5 cursor-pointer transition-colors hover:opacity-80"
                  :style="{ backgroundColor: opt.name === woCustomer ? 'var(--bg-tertiary)' : 'transparent' }"
                  @click="selectWOOption('customer', opt)"
                >
                  <p class="text-sm" style="color: var(--text-primary);">{{ opt.label }}</p>
                </li>
              </ul>
            </div>
          </div>

          <div class="flex justify-end gap-2">
            <Button variant="ghost" size="sm" @click="showWOModal = false">Cancel</Button>
            <Button
              variant="primary"
              size="sm"
              :loading="isActioning"
              :disabled="(woOrderFor === 'Customer' && !woCustomer) || (woOrderFor === 'Company' && !woCompany)"
              @click="handleCreateWorkOrder"
            >
              <LucideWrench class="size-4" />
              Create
            </Button>
          </div>
        </Card>
      </div>
    </Teleport>
  </div>
</template>
