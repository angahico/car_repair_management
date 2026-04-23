<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideArrowLeft,
  LucideEdit,
  LucidePrinter,
  LucideUser,
  LucideCar,
  LucideClipboardList,
  LucideWrench,
  LucidePackage,
  LucideFileText,
  LucideAlertCircle,
  LucidePlay,
  LucideCheck,
  LucideLoader2,
  LucideSend,
  LucideShieldCheck,
  LucidePlus,
  LucideChevronRight,
  LucideMessageSquare,
  LucideHistory,
  LucideUpload,
  LucideDownload,
  LucideEye,
  LucideFolder,
  LucideFolderOpen,
  LucideImage,
  LucidePaperclip,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, Tabs } from '@/components/ui'
import { REPAIR_ORDER_STATUSES, PRIORITY_VARIANTS } from '@/types'

interface Props {
  id: string
}

const props = defineProps<Props>()
const { t } = useI18n()
const router = useRouter()

const order = ref<any>(null)
const orderData = ref<any>(null)
const isLoading = ref(true)
const isStartingWork = ref(false)
const isSubmitting = ref(false)
const isSettingReady = ref(false)
const error = ref('')
const activeTab = ref('overview')
const checklistData = ref<any>(null)
const isLoadingChecklist = ref(false)
const isCreatingInspection = ref('')

// Timeline
const timelineData = ref<any[]>([])
const isLoadingTimeline = ref(false)
const newComment = ref('')
const isAddingComment = ref(false)

// Documents/Attachments
const attachmentsData = ref<any>(null)
const isLoadingAttachments = ref(false)
const isUploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const activeFolder = ref<string | null>(null)
const targetFolder = ref<string | null>(null)

const tabs = computed(() => [
  { id: 'overview', label: t('repair_orders.overview') },
  { id: 'operations', label: t('repair_orders.operations') },
  { id: 'parts', label: t('repair_orders.parts_plan') },
  { id: 'checklist', label: 'Handover Checklist' },
  { id: 'timeline', label: t('repair_orders.timeline') },
  { id: 'documents', label: t('repair_orders.documents') },
])

async function loadOrder() {
  isLoading.value = true
  error.value = ''
  try {
    const result = await apiCall<any>(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.get_repair_order_detail',
      { name: props.id }
    )
    orderData.value = result
    order.value = result.doc
  } catch (e: any) {
    error.value = e.message || t('repair_orders.failed_to_load_order')
  } finally {
    isLoading.value = false
  }
}

async function startWork() {
  isStartingWork.value = true
  try {
    await apiCall(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.start_work',
      { name: props.id }
    )
    await loadOrder()
  } catch (e: any) {
    error.value = e.message || 'Failed to start work'
  } finally {
    isStartingWork.value = false
  }
}

async function submitOrder() {
  isSubmitting.value = true
  try {
    await apiCall('frappe.client.submit', {
      doc: JSON.stringify({
        ...order.value,
        doctype: 'Repair Order',
      })
    })
    await loadOrder()
  } catch (e: any) {
    if (e.message?.includes('modified after you have opened')) {
      await loadOrder()
      error.value = 'Document was modified. Please try submitting again.'
    } else {
      error.value = e.message || 'Failed to submit order'
    }
  } finally {
    isSubmitting.value = false
  }
}

async function loadChecklist() {
  if (!order.value) return
  isLoadingChecklist.value = true
  try {
    checklistData.value = await apiCall<any>(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.get_handover_checklist_status',
      { repair_order: props.id }
    )
  } catch (e: any) {
    console.warn('Failed to load checklist', e)
  } finally {
    isLoadingChecklist.value = false
  }
}

async function createInspection(checkItem: string) {
  isCreatingInspection.value = checkItem
  try {
    const inspection = await apiCall<any>(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.create_handover_inspection',
      { repair_order: props.id, checklist_item_name: checkItem }
    )
    if (inspection?.name) {
      router.push(`/inspections/${inspection.name}`)
    } else {
      await loadChecklist()
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to create inspection'
  } finally {
    isCreatingInspection.value = ''
  }
}

async function setReadyForHandover() {
  isSettingReady.value = true
  try {
    await apiCall(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.set_status',
      { name: props.id, status: 'Ready for Handover' }
    )
    await loadOrder()
  } catch (e: any) {
    error.value = e.message || 'Failed to set Ready for Handover'
  } finally {
    isSettingReady.value = false
  }
}

// Timeline
async function loadTimeline() {
  isLoadingTimeline.value = true
  try {
    timelineData.value = await apiCall<any[]>(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.get_repair_order_timeline',
      { name: props.id }
    ) || []
  } catch (e) {
    console.warn('Failed to load timeline', e)
  } finally {
    isLoadingTimeline.value = false
  }
}

async function addTimelineComment() {
  if (!newComment.value.trim()) return
  isAddingComment.value = true
  try {
    await apiCall(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.add_repair_order_comment',
      { name: props.id, content: newComment.value }
    )
    newComment.value = ''
    await loadTimeline()
  } catch (e: any) {
    error.value = e.message || 'Failed to add comment'
  } finally {
    isAddingComment.value = false
  }
}

function stripHtml(html: string): string {
  return html?.replace(/<[^>]*>/g, '').trim() || ''
}

function formatTimelineDate(dateStr: string): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleString()
}

// Documents/Attachments
const docFolderConfig = [
  { id: 'photos', label: 'Photos & Images', icon: LucideImage },
  { id: 'estimates', label: 'Estimates & Quotes', icon: LucideFileText },
  { id: 'invoices', label: 'Invoices & Receipts', icon: LucideFileText },
  { id: 'reports', label: 'Reports', icon: LucideFileText },
  { id: 'other', label: 'Other', icon: LucideFolder },
]

async function loadAttachments() {
  isLoadingAttachments.value = true
  try {
    attachmentsData.value = await apiCall<any>(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.get_repair_order_attachments',
      { name: props.id }
    )
  } catch (e) {
    console.warn('Failed to load attachments', e)
  } finally {
    isLoadingAttachments.value = false
  }
}

function triggerUpload(folderId?: string) {
  targetFolder.value = folderId || null
  fileInput.value?.click()
}

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  isUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('doctype', 'Repair Order')
    formData.append('docname', props.id)
    formData.append('is_private', '0')
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'X-Frappe-Site-Name': window.location.hostname,
    }
    const csrfToken = (window as any).csrf_token
    if (csrfToken && csrfToken !== '{{ csrf_token }}') {
      headers['X-Frappe-CSRF-Token'] = csrfToken
    }
    const response = await fetch('/api/method/upload_file', {
      method: 'POST', headers, credentials: 'include', body: formData,
    })
    const responseData = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(responseData.message || response.statusText)
    if (targetFolder.value) {
      const fileUrl = responseData?.message?.file_url
      if (fileUrl) {
        await apiCall('car_repair_management.car_repair_management.doctype.repair_order.repair_order.upload_repair_order_attachment', {
          name: props.id, file_url: fileUrl, category: targetFolder.value,
        })
      }
    }
    await loadAttachments()
  } catch (e) {
    console.error('Failed to upload file', e)
  } finally {
    isUploading.value = false
    input.value = ''
  }
}

function previewFile(file: any) {
  if (file.file_url) window.open(file.file_url, '_blank')
}

function downloadFile(file: any) {
  if (file.file_url) {
    const link = document.createElement('a')
    link.href = file.file_url
    link.download = file.file_name
    link.click()
  }
}

function formatFileSize(bytes: number | null): string {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getFileIcon(type: string) {
  const imageTypes = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg']
  if (imageTypes.includes(type.toLowerCase())) return LucideImage
  return LucideFileText
}

const folderFiles = computed(() => {
  if (!activeFolder.value || !attachmentsData.value?.folders) return []
  return attachmentsData.value.folders[activeFolder.value] || []
})

const OP_STATUS_VARIANTS: Record<string, string> = {
  Open: 'default',
  Working: 'primary',
  'Pending Review': 'warning',
  Completed: 'success',
  Rejected: 'danger',
  Cancelled: 'danger',
}

const statusConfig = computed(() => REPAIR_ORDER_STATUSES[order.value?.status] || { variant: 'default' })

watch(activeTab, (tab) => {
  if (tab === 'checklist' && !checklistData.value) {
    loadChecklist()
  }
  if (tab === 'timeline' && timelineData.value.length === 0) {
    loadTimeline()
  }
  if (tab === 'documents' && !attachmentsData.value) {
    loadAttachments()
  }
})

onMounted(loadOrder)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
      <div class="flex items-start gap-4">
        <Button variant="ghost" size="sm" @click="router.back()">
          <LucideArrowLeft class="size-4" />
        </Button>
        
        <div v-if="isLoading" class="space-y-2">
          <Skeleton width="200px" height="28px" />
          <Skeleton width="300px" height="16px" />
        </div>
        
        <div v-else-if="order">
          <div class="flex items-center gap-3">
            <h1 class="text-page-title text-ink">
              {{ order.name }}
            </h1>
            <Badge :variant="statusConfig.variant" size="md">
              {{ order.status }}
            </Badge>
            <Badge :variant="PRIORITY_VARIANTS[order.priority] || 'default'" size="sm">
              {{ order.priority }}
            </Badge>
          </div>
          <p class="text-sm text-ink-muted mt-1">
            {{ order.problem_summary || $t('repair_orders.no_summary') }}
          </p>
        </div>
      </div>

      <div v-if="order" class="flex items-center gap-2 ml-auto lg:ml-0">
        <Button variant="outline">
          <LucidePrinter class="size-4" />
          {{ $t('common.print') }}
        </Button>
        <RouterLink :to="`/repair-orders/${order.name}/edit`">
          <Button variant="outline">
            <LucideEdit class="size-4" />
            {{ $t('common.edit') }}
          </Button>
        </RouterLink>
        <Button
          v-if="order.docstatus === 0"
          variant="primary"
          :disabled="isSubmitting"
          @click="submitOrder"
        >
          <LucideLoader2 v-if="isSubmitting" class="size-4 animate-spin" />
          <LucideSend v-else class="size-4" />
          Submit
        </Button>
        <Button
          v-if="order.status === 'Scheduled' && order.docstatus === 1"
          variant="primary"
          :disabled="isStartingWork"
          @click="startWork"
        >
          <LucideLoader2 v-if="isStartingWork" class="size-4 animate-spin" />
          <LucidePlay v-else class="size-4" />
          Start Work
        </Button>
      </div>
    </div>

    <!-- Error state -->
    <Card v-if="error" class="border-danger-DEFAULT/50 bg-danger-DEFAULT/5">
      <div class="flex items-center gap-3 text-danger-DEFAULT">
        <LucideAlertCircle class="size-5" />
        <p>{{ error }}</p>
      </div>
    </Card>

    <!-- Content -->
    <template v-else-if="order">
      <!-- Tabs -->
      <Tabs :tabs="tabs" v-model="activeTab" />

      <!-- Tab content -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main content -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Overview tab -->
          <template v-if="activeTab === 'overview'">
            <Card>
              <h3 class="text-section-title text-ink mb-4">
                {{ $t('repair_orders.problem_details') }}
              </h3>
              <p class="text-sm text-ink whitespace-pre-wrap">
                {{ order.problem_details || $t('repair_orders.no_details_provided') }}
              </p>
            </Card>

            <!-- Costs summary -->
            <Card>
              <h3 class="text-section-title text-ink mb-4">
                {{ $t('repair_orders.cost_summary') }}
              </h3>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <p class="text-xs text-ink-muted">{{ $t('repair_orders.parts_cost') }}</p>
                  <p class="text-lg font-semibold text-ink">
                    ETB {{ order.parts_cost?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00' }}
                  </p>
                </div>
                <div>
                  <p class="text-xs text-ink-muted">{{ $t('repair_orders.labor_cost') }}</p>
                  <p class="text-lg font-semibold text-ink">
                    ETB {{ order.labor_cost?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00' }}
                  </p>
                </div>
                <div>
                  <p class="text-xs text-ink-muted">{{ $t('repair_orders.other_charges') }}</p>
                  <p class="text-lg font-semibold text-ink">
                    ETB {{ order.other_charges?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00' }}
                  </p>
                </div>
                <div>
                  <p class="text-xs text-ink-muted">{{ $t('common.total') }}</p>
                  <p class="text-lg font-semibold text-primary-600 dark:text-primary-400">
                    ETB {{ order.total_job_cost?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00' }}
                  </p>
                </div>
              </div>
            </Card>
          </template>

          <!-- Operations tab -->
          <template v-else-if="activeTab === 'operations'">
            <Card>
              <h3 class="text-section-title text-ink mb-4">
                {{ $t('repair_orders.operations') }}
              </h3>
              <div v-if="!order.operations?.length" class="py-8 text-center text-ink-muted">
                {{ $t('repair_orders.no_operations') }}
              </div>
              <div v-else class="divide-y divide-border-light dark:divide-border-dark">
                <RouterLink
                  v-for="op in order.operations"
                  :key="op.name"
                  :to="`/repair-orders/${order.name}/operations/${op.name}`"
                  class="py-3 flex items-center justify-between hover:bg-surface-gray-1 px-3 -mx-3 rounded-lg transition-colors cursor-pointer block"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center">
                      <LucideWrench class="size-4 text-primary-600 dark:text-primary-400" />
                    </div>
                    <div>
                      <p class="text-sm font-medium text-ink">
                        {{ op.operation_name }}
                      </p>
                      <p class="text-xs text-ink-muted">
                        {{ op.planned_minutes }} min • {{ op.workstation || $t('repair_orders.no_workstation') }}
                        <span v-if="op.assigned_to"> • {{ op.assigned_to }}</span>
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <Badge v-if="op.status" :variant="OP_STATUS_VARIANTS[op.status] || 'default'" size="sm">
                      {{ op.status }}
                    </Badge>
                    <Badge v-if="op.is_qc" variant="info" size="sm">QC</Badge>
                    <LucideChevronRight class="size-4 text-ink-muted" />
                  </div>
                </RouterLink>
              </div>
            </Card>
          </template>

          <!-- Parts tab -->
          <template v-else-if="activeTab === 'parts'">
            <Card>
              <h3 class="text-section-title text-ink mb-4">
                {{ $t('repair_orders.parts_plan') }}
              </h3>
              <div v-if="!order.parts_plan?.length" class="py-8 text-center text-ink-muted">
                {{ $t('repair_orders.no_parts') }}
              </div>
              <div v-else class="divide-y divide-border-light dark:divide-border-dark">
                <div
                  v-for="(part, idx) in order.parts_plan"
                  :key="idx"
                  class="py-3 flex items-center justify-between"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center">
                      <LucidePackage class="size-4 text-amber-600 dark:text-amber-400" />
                    </div>
                    <div>
                      <p class="text-sm font-medium text-ink">
                        {{ part.item_name || part.item_code }}
                      </p>
                      <p class="text-xs text-ink-muted">
                        Qty: {{ part.qty_planned }} {{ part.uom }}
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <Badge v-if="part.is_billable" variant="success" size="sm">{{ $t('repair_orders.billable') }}</Badge>
                    <Badge v-if="part.is_foc" variant="warning" size="sm">{{ $t('repair_orders.foc') }}</Badge>
                  </div>
                </div>
              </div>
            </Card>
          </template>

          <!-- Checklist tab -->
          <template v-else-if="activeTab === 'checklist'">
            <Card>
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-section-title text-ink">Handover Checklist</h3>
                <Button
                  v-if="checklistData?.all_passed && order.docstatus === 1 && order.status === 'In Progress'"
                  variant="primary"
                  size="sm"
                  :disabled="isSettingReady"
                  @click="setReadyForHandover"
                >
                  <LucideLoader2 v-if="isSettingReady" class="size-4 animate-spin" />
                  <LucideShieldCheck v-else class="size-4" />
                  Mark Ready for Handover
                </Button>
              </div>

              <div v-if="isLoadingChecklist" class="py-8 text-center">
                <Skeleton height="120px" />
              </div>
              <div v-else-if="!checklistData?.items?.length" class="py-8 text-center text-ink-muted">
                No handover checklist items
              </div>
              <div v-else>
                <div class="mb-4 flex items-center gap-3">
                  <div class="flex-1 bg-surface-gray-2 rounded-full h-2">
                    <div
                      class="bg-green-500 h-2 rounded-full transition-all"
                      :style="{ width: (checklistData.total ? (checklistData.passed_count / checklistData.total * 100) : 0) + '%' }"
                    ></div>
                  </div>
                  <span class="text-sm text-ink-muted whitespace-nowrap">
                    {{ checklistData.passed_count }} / {{ checklistData.total }} passed
                  </span>
                </div>

                <div class="divide-y divide-border-light dark:divide-border-dark">
                  <div
                    v-for="item in checklistData.items"
                    :key="item.name"
                    class="py-3 flex items-center justify-between"
                  >
                    <div class="flex items-center gap-3">
                      <div
                        class="w-8 h-8 rounded-lg flex items-center justify-center"
                        :class="item.inspection?.result === 'Pass' ? 'bg-green-100 dark:bg-green-500/20' : 'bg-gray-100 dark:bg-gray-500/20'"
                      >
                        <LucideCheck v-if="item.inspection?.result === 'Pass'" class="size-4 text-green-600 dark:text-green-400" />
                        <LucideClipboardList v-else class="size-4 text-gray-500" />
                      </div>
                      <div>
                        <p class="text-sm font-medium text-ink">{{ item.check_item }}</p>
                        <p class="text-xs text-ink-muted">{{ item.type }}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      <template v-if="item.inspection">
                        <Badge
                          :variant="item.inspection.result === 'Pass' ? 'success' : item.inspection.result === 'Fail' ? 'danger' : 'warning'"
                          size="sm"
                        >
                          {{ item.inspection.result || item.inspection.status }}
                        </Badge>
                        <RouterLink
                          :to="`/inspections/${item.inspection.name}`"
                          class="text-xs text-primary-500 hover:text-primary-600"
                        >
                          View
                        </RouterLink>
                      </template>
                      <Button
                        v-else
                        variant="outline"
                        size="sm"
                        :disabled="isCreatingInspection === item.check_item"
                        @click="createInspection(item.check_item)"
                      >
                        <LucideLoader2 v-if="isCreatingInspection === item.check_item" class="size-3 animate-spin" />
                        <LucidePlus v-else class="size-3" />
                        Create Inspection
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </template>

          <!-- Timeline tab -->
          <template v-else-if="activeTab === 'timeline'">
            <!-- Add Comment -->
            <Card>
              <h3 class="text-section-title text-ink mb-4">
                <LucideMessageSquare class="inline size-4 mr-1" />
                {{ $t('repair_orders.add_comment') || 'Add Comment' }}
              </h3>
              <div class="flex gap-3">
                <textarea
                  v-model="newComment"
                  class="flex-1 rounded-lg border p-3 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
                  style="background: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary); min-height: 80px; resize: vertical;"
                  :placeholder="$t('repair_orders.write_comment') || 'Write a comment...'"
                ></textarea>
                <Button
                  variant="primary"
                  :disabled="!newComment.trim() || isAddingComment"
                  @click="addTimelineComment"
                  class="self-end"
                >
                  <LucideLoader2 v-if="isAddingComment" class="size-4 animate-spin" />
                  <LucideSend v-else class="size-4" />
                </Button>
              </div>
            </Card>

            <!-- Activity Timeline -->
            <Card>
              <h3 class="text-section-title text-ink mb-4">
                <LucideHistory class="inline size-4 mr-1" />
                {{ $t('repair_orders.activity_timeline') }}
              </h3>

              <div v-if="isLoadingTimeline" class="space-y-3">
                <Skeleton height="60px" v-for="i in 5" :key="i" />
              </div>

              <div v-else-if="timelineData.length === 0" class="py-8 text-center">
                <LucideHistory class="size-12 mx-auto mb-3 text-ink-muted" />
                <p class="text-sm text-ink-muted">{{ $t('repair_orders.no_activity') || 'No activity recorded yet' }}</p>
              </div>

              <div v-else class="space-y-3">
                <div
                  v-for="(entry, idx) in timelineData"
                  :key="idx"
                  class="flex items-start gap-3 p-3 rounded-lg"
                  style="background: var(--bg-tertiary);"
                >
                  <!-- Icon -->
                  <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                    :class="entry.type === 'comment' ? 'bg-blue-100 dark:bg-blue-500/20' : entry.type === 'task_comment' ? 'bg-green-100 dark:bg-green-500/20' : 'bg-gray-100 dark:bg-gray-500/20'"
                  >
                    <LucideMessageSquare v-if="entry.type === 'comment' || entry.type === 'task_comment'" class="size-4" :class="entry.type === 'task_comment' ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'" />
                    <LucideHistory v-else class="size-4 text-gray-500" />
                  </div>

                  <!-- Content -->
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span class="text-sm font-medium text-ink">{{ entry.user }}</span>
                      <span class="text-xs text-ink-muted">{{ formatTimelineDate(entry.timestamp) }}</span>
                      <Badge v-if="entry.type === 'task_comment'" variant="default" size="sm">Task: {{ entry.task_subject }}</Badge>
                    </div>
                    <!-- Comment content -->
                    <p v-if="entry.type === 'comment' || entry.type === 'task_comment'" class="text-sm text-ink mt-1">
                      {{ stripHtml(entry.content || '') }}
                    </p>
                    <!-- Field changes -->
                    <div v-if="entry.type === 'change' && entry.changes" class="mt-1 space-y-1">
                      <div v-for="(change, ci) in entry.changes" :key="ci" class="text-xs">
                        <span class="text-ink-muted">{{ change.field }}:</span>
                        <span v-if="change.old" class="text-red-500 line-through ml-1">{{ change.old }}</span>
                        <span class="text-green-600 ml-1">{{ change.new }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </template>

          <!-- Documents tab -->
          <template v-else-if="activeTab === 'documents'">
            <input ref="fileInput" type="file" class="hidden" @change="uploadFile" />

            <!-- Linked Documents -->
            <Card v-if="order.quotation || order.sales_order || order.sales_invoice">
              <h3 class="text-section-title text-ink mb-4">{{ $t('repair_orders.linked_documents') || 'Linked Documents' }}</h3>
              <div class="space-y-3">
                <div v-if="order.quotation" class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary);">
                  <LucideFileText class="size-5 text-primary-500" />
                  <div class="flex-1">
                    <p class="text-sm font-medium text-ink">{{ $t('repair_orders.quotation') }}</p>
                    <p class="text-xs text-ink-muted">{{ order.quotation }}</p>
                  </div>
                  <a :href="`/app/quotation/${order.quotation}`" target="_blank">
                    <Button variant="ghost" size="sm"><LucideEye class="size-4" /></Button>
                  </a>
                </div>
                <div v-if="order.sales_order" class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary);">
                  <LucideFileText class="size-5 text-blue-500" />
                  <div class="flex-1">
                    <p class="text-sm font-medium text-ink">{{ $t('repair_orders.sales_order') }}</p>
                    <p class="text-xs text-ink-muted">{{ order.sales_order }}</p>
                  </div>
                  <a :href="`/app/sales-order/${order.sales_order}`" target="_blank">
                    <Button variant="ghost" size="sm"><LucideEye class="size-4" /></Button>
                  </a>
                </div>
                <div v-if="order.sales_invoice" class="flex items-center gap-3 p-3 rounded-lg" style="background: var(--bg-tertiary);">
                  <LucideFileText class="size-5 text-green-500" />
                  <div class="flex-1">
                    <p class="text-sm font-medium text-ink">{{ $t('repair_orders.sales_invoice') }}</p>
                    <p class="text-xs text-ink-muted">{{ order.sales_invoice }}</p>
                  </div>
                  <RouterLink :to="`/invoices/${order.sales_invoice}`">
                    <Button variant="ghost" size="sm"><LucideEye class="size-4" /></Button>
                  </RouterLink>
                </div>
              </div>
            </Card>

            <!-- File Attachments -->
            <Card>
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-section-title text-ink">
                  <LucidePaperclip class="inline size-4 mr-1" />
                  {{ $t('repair_orders.file_attachments') || 'File Attachments' }}
                  <span v-if="attachmentsData" class="text-ink-muted font-normal text-sm ml-1">({{ attachmentsData.total }})</span>
                </h3>
                <Button @click="triggerUpload()" :disabled="isUploading">
                  <LucideUpload class="size-4" />
                  {{ isUploading ? $t('common.loading') : ($t('common.upload') || 'Upload') }}
                </Button>
              </div>

              <div v-if="isLoadingAttachments" class="space-y-3">
                <Skeleton height="80px" v-for="i in 3" :key="i" />
              </div>

              <template v-else-if="attachmentsData">
                <!-- Folders -->
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                  <button
                    v-for="folder in docFolderConfig"
                    :key="folder.id"
                    @click="activeFolder = activeFolder === folder.id ? null : folder.id"
                    class="p-3 rounded-lg border text-left transition-colors hover:opacity-80"
                    :class="activeFolder === folder.id ? 'ring-2 ring-blue-500' : ''"
                    :style="{ backgroundColor: 'var(--bg-tertiary)', borderColor: activeFolder === folder.id ? 'var(--accent)' : 'var(--border-color)' }"
                  >
                    <div class="flex items-center gap-2">
                      <component :is="activeFolder === folder.id ? LucideFolderOpen : LucideFolder" class="size-5 text-ink-muted" />
                      <div>
                        <p class="text-sm font-medium text-ink">{{ folder.label }}</p>
                        <p class="text-xs text-ink-muted">{{ attachmentsData.counts?.[folder.id] || 0 }} files</p>
                      </div>
                    </div>
                  </button>
                </div>

                <!-- Folder Contents -->
                <div v-if="activeFolder && folderFiles.length" class="space-y-2">
                  <div class="flex items-center justify-between mb-2">
                    <h4 class="text-sm font-medium text-ink">{{ docFolderConfig.find(f => f.id === activeFolder)?.label }}</h4>
                    <Button size="sm" @click="triggerUpload(activeFolder)" :disabled="isUploading">
                      <LucideUpload class="size-3.5" />
                      Upload Here
                    </Button>
                  </div>
                  <div
                    v-for="file in folderFiles"
                    :key="file.name"
                    class="flex items-center justify-between p-3 rounded-lg"
                    style="background: var(--bg-tertiary);"
                  >
                    <div class="flex items-center gap-3">
                      <component :is="getFileIcon(file.type)" class="size-6 text-ink-muted" />
                      <div>
                        <p class="text-sm font-medium text-ink">{{ file.file_name }}</p>
                        <p class="text-xs text-ink-muted">{{ file.type }} · {{ formatFileSize(file.size) }} · {{ file.uploaded_by }} · {{ file.upload_date }}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-1">
                      <Button variant="ghost" size="sm" @click="previewFile(file)"><LucideEye class="size-4" /></Button>
                      <Button variant="ghost" size="sm" @click="downloadFile(file)"><LucideDownload class="size-4" /></Button>
                    </div>
                  </div>
                </div>
                <div v-else-if="activeFolder" class="py-6 text-center text-ink-muted text-sm">
                  No files in this folder
                </div>

                <!-- Empty state -->
                <div v-if="!attachmentsData.total && !activeFolder" class="py-8 text-center">
                  <LucidePaperclip class="size-12 mx-auto mb-3 text-ink-muted" />
                  <p class="text-sm text-ink-muted">{{ $t('repair_orders.no_documents') }}</p>
                </div>
              </template>
            </Card>
          </template>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
          <!-- Customer / Company info -->
          <Card v-if="order.customer">
            <h3 class="text-section-title text-ink mb-4">
              {{ $t('common.customer') }}
            </h3>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center">
                <LucideUser class="size-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <p class="text-sm font-medium text-ink">
                  {{ order.customer }}
                </p>
                <RouterLink :to="`/customers/${order.customer}`" class="text-xs text-primary-500 hover:text-primary-600">
                  {{ $t('common.view_customer') }}
                </RouterLink>
              </div>
            </div>
          </Card>
          <Card v-else-if="order.company">
            <h3 class="text-section-title text-ink mb-4">
              Company (Internal)
            </h3>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center">
                <LucideUser class="size-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <p class="text-sm font-medium text-ink">
                  {{ order.company }}
                </p>
              </div>
            </div>
          </Card>

          <!-- Vehicle info -->
          <Card>
            <h3 class="text-section-title text-ink mb-4">
              {{ $t('common.vehicle') }}
            </h3>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center">
                <LucideCar class="size-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p class="text-sm font-medium text-ink">
                  {{ order.vehicle }}
                </p>
                <RouterLink :to="`/vehicles/${order.vehicle}`" class="text-xs text-primary-500 hover:text-primary-600">
                  {{ $t('common.view_vehicle') }}
                </RouterLink>
              </div>
            </div>
          </Card>

          <!-- Dates -->
          <Card>
            <h3 class="text-section-title text-ink mb-4">
              {{ $t('repair_orders.dates') }}
            </h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-sm text-ink-muted">{{ $t('common.created') }}</span>
                <span class="text-sm text-ink">
                  {{ new Date(order.creation).toLocaleDateString() }}
                </span>
              </div>
              <div v-if="order.sla_delivery_by" class="flex items-center justify-between">
                <span class="text-sm text-ink-muted">{{ $t('common.due') }}</span>
                <span class="text-sm text-ink">
                  {{ new Date(order.sla_delivery_by).toLocaleDateString() }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-ink-muted">{{ $t('common.modified') }}</span>
                <span class="text-sm text-ink">
                  {{ new Date(order.modified).toLocaleDateString() }}
                </span>
              </div>
            </div>
          </Card>

          <!-- Linked Project -->
          <Card v-if="order.project">
            <h3 class="text-section-title text-ink mb-4">
              {{ $t('common.project') }}
            </h3>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-green-100 dark:bg-green-500/20 flex items-center justify-center">
                <LucideClipboardList class="size-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p class="text-sm font-medium text-ink">
                  {{ order.project }}
                </p>
                <a :href="`/app/project/${order.project}`" target="_blank" class="text-xs text-primary-500 hover:text-primary-600">
                  {{ $t('common.open_in_desk') }}
                </a>
              </div>
            </div>
          </Card>

          <!-- Progress -->
          <Card v-if="orderData?.progress !== undefined && order?.status === 'In Progress'">
            <h3 class="text-section-title text-ink mb-4">Progress</h3>
            <div class="mb-2 flex justify-between text-sm">
              <span class="text-ink-muted">Completion</span>
              <span class="text-ink font-medium">{{ orderData.progress }}%</span>
            </div>
            <div class="w-full bg-surface-tertiary rounded-full h-2">
              <div class="bg-primary-500 h-2 rounded-full transition-all" :style="{ width: orderData.progress + '%' }"></div>
            </div>
          </Card>

          <!-- Tasks -->
          <Card v-if="orderData?.tasks?.length">
            <h3 class="text-section-title text-ink mb-4">Tasks</h3>
            <div class="divide-y divide-border-light dark:divide-border-dark">
              <div
                v-for="task in orderData.tasks"
                :key="task.name"
                class="flex items-center justify-between py-3"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="w-8 h-8 rounded-lg flex items-center justify-center"
                    :class="task.status === 'Completed' ? 'bg-green-100 dark:bg-green-500/20' : 'bg-gray-100 dark:bg-gray-500/20'"
                  >
                    <LucideCheck v-if="task.status === 'Completed'" class="size-4 text-green-600 dark:text-green-400" />
                    <LucideWrench v-else class="size-4 text-gray-500" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-ink">{{ task.subject }}</p>
                    <p class="text-xs text-ink-muted">{{ task.status }}</p>
                  </div>
                </div>
                <Badge :variant="task.status === 'Completed' ? 'success' : 'default'" size="sm">
                  {{ task.status }}
                </Badge>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </template>

    <!-- Loading state -->
    <template v-else-if="isLoading">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 space-y-6">
          <Card><Skeleton height="200px" /></Card>
          <Card><Skeleton height="150px" /></Card>
        </div>
        <div class="space-y-6">
          <Card><Skeleton height="100px" /></Card>
          <Card><Skeleton height="100px" /></Card>
        </div>
      </div>
    </template>
  </div>
</template>
