<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideArrowLeft,
  LucideSave,
  LucideLoader2,
  LucideChevronRight,
  LucideChevronLeft,
  LucideUser,
  LucideClipboardList,
  LucideWrench,
  LucideCheckCircle,
  LucidePlus,
  LucideTrash2,
} from 'lucide-vue-next'
import { apiGet, apiCreate, apiUpdate, apiCall } from '@/api'
import { Card, Button, LinkField } from '@/components/ui'

interface Props {
  id?: string
  isNew?: boolean
}

const props = defineProps<Props>()
const router = useRouter()
const { t } = useI18n()

const isLoading = ref(false)
const isSaving = ref(false)
const isLoadingTemplate = ref(false)
const error = ref('')
const currentStep = ref(1)

interface OperationRow {
  operation_name: string
  planned_minutes: number
  workstation: string
  is_qc: boolean
}

interface PartRow {
  item_code: string
  item_name: string
  qty_planned: number
  uom: string
  is_billable: boolean
  is_foc: boolean
}

interface ChecklistRow {
  item_name: string
  type: string
}

const form = ref({
  order_for: 'Customer' as 'Customer' | 'Company',
  company: '',
  customer: '',
  vehicle: '',
  priority: 'Normal',
  status: 'Draft',
  problem_summary: '',
  problem_details: '',
  intake_channel: '',
  entry_datetime: new Date().toISOString().slice(0, 16),
  entry_datetime_editable: false,
  service_template: '',
  sla_template: '',
  expected_delivery_datetime: '',
  sla_delivery_by: '',
})

const operations = ref<OperationRow[]>([])
const partsPlan = ref<PartRow[]>([])
const handoverChecklist = ref<ChecklistRow[]>([])

const pageTitle = computed(() => props.isNew ? t('repair_orders.new_work_order') : t('repair_orders.edit_work_order'))

const steps = [
  { id: 1, label: 'Customer & Vehicle', icon: LucideUser },
  { id: 2, label: 'Problem Details', icon: LucideClipboardList },
  { id: 3, label: 'Service Planning', icon: LucideWrench },
  { id: 4, label: 'Review & Save', icon: LucideCheckCircle },
]

const totalPlannedMinutes = computed(() =>
  operations.value.reduce((sum, op) => sum + (op.planned_minutes || 0), 0)
)

// Vehicle filtering by customer/company via Asset link
const filteredVehicles = ref<{ value: string; label: string }[]>([])

async function fetchFilteredVehicles() {
  const orderFor = form.value.order_for
  const customer = form.value.customer
  const company = form.value.company

  if (orderFor === 'Customer' && customer) {
    try {
      const vehicles = await apiCall<any[]>(
        'car_repair_management.car_repair_management.doctype.repair_order.repair_order.get_vehicles_for_customer',
        { customer }
      )
      filteredVehicles.value = (vehicles || []).map((v: any) => ({
        value: v.name,
        label: `${v.license_plate} - ${v.make} ${v.model}`,
      }))
    } catch (e) {
      filteredVehicles.value = []
    }
  } else if (orderFor === 'Company' && company) {
    try {
      const vehicles = await apiCall<any[]>(
        'car_repair_management.car_repair_management.doctype.repair_order.repair_order.get_vehicles_for_company',
        { company }
      )
      filteredVehicles.value = (vehicles || []).map((v: any) => ({
        value: v.name,
        label: `${v.license_plate} - ${v.make} ${v.model}`,
      }))
    } catch (e) {
      filteredVehicles.value = []
    }
  } else {
    filteredVehicles.value = []
  }
}

watch(() => form.value.customer, () => fetchFilteredVehicles())
watch(() => form.value.company, () => fetchFilteredVehicles())

// Clear dependent fields when order_for changes
watch(() => form.value.order_for, () => {
  form.value.customer = ''
  form.value.company = ''
  form.value.vehicle = ''
  filteredVehicles.value = []
})

// Auto-calculate expected delivery when operations change
watch(totalPlannedMinutes, (minutes) => {
  if (minutes > 0) {
    const now = new Date()
    now.setMinutes(now.getMinutes() + minutes)
    form.value.expected_delivery_datetime = now.toISOString().slice(0, 16)
  }
})

async function loadData() {
  isLoading.value = true
  error.value = ''
  try {
    if (props.id && !props.isNew) {
      const data = await apiGet<any>('Repair Order', props.id)
      if (data) {
        form.value = {
          order_for: data.order_for || 'Customer',
          company: data.company || '',
          customer: data.customer || '',
          vehicle: data.vehicle || '',
          priority: data.priority || 'Normal',
          status: data.status || 'Draft',
          problem_summary: data.problem_summary || '',
          problem_details: data.problem_details || '',
          intake_channel: data.intake_channel || '',
          entry_datetime: data.entry_datetime ? data.entry_datetime.slice(0, 16) : new Date().toISOString().slice(0, 16),
          entry_datetime_editable: !!data.entry_datetime_editable,
          service_template: data.service_template || '',
          sla_template: data.sla_template || '',
          expected_delivery_datetime: data.expected_delivery_datetime ? data.expected_delivery_datetime.slice(0, 16) : '',
          sla_delivery_by: data.sla_delivery_by || '',
        }
        operations.value = (data.operations || []).map((op: any) => ({
          operation_name: op.operation_name || '',
          planned_minutes: op.planned_minutes || 0,
          workstation: op.workstation || '',
          is_qc: !!op.is_qc,
        }))
        partsPlan.value = (data.parts_plan || []).map((p: any) => ({
          item_code: p.item_code || '',
          item_name: p.item_name || '',
          qty_planned: p.qty_planned || 0,
          uom: p.uom || '',
          is_billable: !!p.is_billable,
          is_foc: !!p.is_foc,
        }))
        handoverChecklist.value = (data.handover_checklist || []).map((c: any) => ({
          item_name: c.check_item || c.item_name || '',
          type: c.type || '',
        }))
      }
    }
  } catch (e: any) {
    error.value = e.message || t('common.failed_to_load')
  } finally {
    isLoading.value = false
  }
}

async function loadServiceTemplate(templateName: string) {
  if (!templateName) return
  isLoadingTemplate.value = true
  try {
    const data = await apiCall<any>(
      'car_repair_management.car_repair_management.doctype.repair_order.repair_order.get_service_template_data',
      { template_name: templateName }
    )
    if (data) {
      operations.value = (data.operations || []).map((op: any) => ({
        operation_name: op.operation_name || '',
        planned_minutes: op.planned_minutes || 0,
        workstation: op.workstation || '',
        is_qc: !!op.is_qc,
      }))
      partsPlan.value = (data.parts || []).map((p: any) => ({
        item_code: p.item_code || '',
        item_name: p.item_name || '',
        qty_planned: p.qty_planned || 0,
        uom: p.uom || '',
        is_billable: !!p.is_billable,
        is_foc: !!p.is_foc,
      }))
      handoverChecklist.value = (data.checklist || []).map((c: any) => ({
        item_name: c.check_item || '',
        type: c.type || '',
      }))
    }
  } catch (e) {
    console.error('Failed to load template', e)
  } finally {
    isLoadingTemplate.value = false
  }
}

watch(() => form.value.service_template, (val) => {
  if (val) loadServiceTemplate(val)
})

function addOperation() {
  operations.value.push({ operation_name: '', planned_minutes: 30, workstation: '', is_qc: false })
}

function removeOperation(idx: number) {
  operations.value.splice(idx, 1)
}

function addPart() {
  partsPlan.value.push({ item_code: '', item_name: '', qty_planned: 1, uom: 'Nos', is_billable: true, is_foc: false })
}

function removePart(idx: number) {
  partsPlan.value.splice(idx, 1)
}

function addChecklistItem() {
  handoverChecklist.value.push({ item_name: '', type: 'Inspection' })
}

function removeChecklistItem(idx: number) {
  handoverChecklist.value.splice(idx, 1)
}

async function onChecklistItemSelected(idx: number, itemName: string) {
  if (!itemName) {
    handoverChecklist.value[idx].type = ''
    return
  }
  try {
    const data = await apiGet<any>('Handover Checklist Item', itemName)
    if (data?.type) {
      handoverChecklist.value[idx].type = data.type
    }
  } catch (e) {
    // Type will be populated server-side on save as fallback
  }
}

function nextStep() {
  if (currentStep.value === 1) {
    if (form.value.order_for === 'Customer' && !form.value.customer) {
      error.value = 'Customer is required when order is for a Customer'
      return
    }
    if (form.value.order_for === 'Company' && !form.value.company) {
      error.value = 'Company is required when order is for the Company'
      return
    }
    if (!form.value.vehicle) {
      error.value = t('repair_orders.customer_vehicle_required')
      return
    }
  }
  error.value = ''
  if (currentStep.value < 4) currentStep.value++
}

function prevStep() {
  error.value = ''
  if (currentStep.value > 1) currentStep.value--
}

async function handleSubmit() {
  if (form.value.order_for === 'Customer' && !form.value.customer) {
    error.value = 'Customer is required when order is for a Customer'
    currentStep.value = 1
    return
  }
  if (form.value.order_for === 'Company' && !form.value.company) {
    error.value = 'Company is required when order is for the Company'
    currentStep.value = 1
    return
  }
  if (!form.value.vehicle) {
    error.value = t('repair_orders.customer_vehicle_required')
    currentStep.value = 1
    return
  }

  isSaving.value = true
  error.value = ''

  try {
    const payload: Record<string, unknown> = {
      ...form.value,
      naming_series: 'RO-.YYYY.-.#####',
      operations: operations.value.filter(op => op.operation_name),
      parts_plan: partsPlan.value.filter(p => p.item_code),
      handover_checklist: handoverChecklist.value
        .filter(c => c.item_name)
        .map(c => ({ check_item: c.item_name, type: c.type })),
    }

    // Remove empty customer/company to avoid mandatory validation errors
    if (form.value.order_for === 'Company') {
      delete payload.customer
    } else {
      delete payload.company
    }

    if (form.value.expected_delivery_datetime) {
      payload.sla_delivery_by = form.value.expected_delivery_datetime
    }

    if (props.isNew) {
      const result = await apiCreate<{ name: string }>('Repair Order', payload)
      router.push(`/repair-orders/${result.name}`)
    } else if (props.id) {
      await apiUpdate('Repair Order', props.id, payload)
      router.push(`/repair-orders/${props.id}`)
    }
  } catch (e: any) {
    error.value = e.message || t('common.failed_to_save')
  } finally {
    isSaving.value = false
  }
}

function formatMinutes(mins: number): string {
  if (mins < 60) return `${mins} min`
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <Button variant="ghost" size="sm" @click="router.back()">
          <LucideArrowLeft class="size-4" />
        </Button>
        <h1 class="text-page-title">{{ pageTitle }}</h1>
      </div>
      <div v-if="currentStep === 4" class="flex items-center gap-2">
        <Button variant="primary" :disabled="isSaving" @click="handleSubmit">
          <LucideLoader2 v-if="isSaving" class="size-4 animate-spin" />
          <LucideSave v-else class="size-4" />
          {{ isSaving ? $t('common.saving') : 'Save as Draft' }}
        </Button>
      </div>
    </div>

    <!-- Step Progress -->
    <div class="flex items-center justify-between px-4 py-2 bg-surface-bg border border-default rounded-xl">
      <div v-for="step in steps" :key="step.id" class="flex items-center gap-2">
        <div
          :class="[
            'size-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors',
            currentStep === step.id ? 'bg-accent text-accent-text' :
            currentStep > step.id ? 'bg-green-500 text-white' : 'bg-surface-tertiary text-ink-muted'
          ]"
        >
          <component :is="step.icon" class="size-4" />
        </div>
        <span class="text-xs font-medium hidden sm:block"
              :class="currentStep === step.id ? 'text-ink' : 'text-ink-muted'">
          {{ step.label }}
        </span>
        <LucideChevronRight v-if="step.id < 4" class="size-4 text-ink-muted mx-2" />
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400">
      {{ error }}
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <LucideLoader2 class="size-8 animate-spin" style="color: var(--text-muted);" />
    </div>

    <!-- Multi-Step Form -->
    <template v-else>
      <Card class="min-h-[400px]">
        <!-- Step 1: Customer & Vehicle -->
        <div v-if="currentStep === 1" class="space-y-6">
          <h2 class="text-xl font-semibold" style="color: var(--text-primary);">Customer & Vehicle</h2>

          <!-- Order For toggle -->
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary);">
              Order For <span class="text-red-500">*</span>
            </label>
            <select v-model="form.order_for" class="form-select">
              <option value="Customer">Customer</option>
              <option value="Company">Company (Internal)</option>
            </select>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Customer field (shown when order_for is Customer) -->
            <LinkField
              v-if="form.order_for === 'Customer'"
              v-model="form.customer"
              doctype="Customer"
              :label="$t('common.customer')"
              :placeholder="$t('repair_orders.search_customers')"
              title-field="customer_name"
              :required="true"
            />

            <!-- Company field (shown when order_for is Company) -->
            <LinkField
              v-if="form.order_for === 'Company'"
              v-model="form.company"
              doctype="Company"
              label="Company"
              placeholder="Select company..."
              title-field="company_name"
              :required="true"
            />

            <!-- Vehicle field -->
            <div>
              <template v-if="filteredVehicles.length">
                <label class="block text-sm font-medium mb-1" style="color: var(--text-primary);">
                  {{ $t('common.vehicle') }} <span class="text-red-500">*</span>
                </label>
                <select v-model="form.vehicle" class="form-select">
                  <option value="">Select vehicle...</option>
                  <option v-for="v in filteredVehicles" :key="v.value" :value="v.value">
                    {{ v.label }}
                  </option>
                </select>
                <p class="text-xs mt-1" style="color: var(--text-muted);">
                  Showing vehicles linked to this {{ form.order_for === 'Company' ? 'company' : 'customer' }}
                </p>
              </template>
              <LinkField
                v-else
                v-model="form.vehicle"
                doctype="Vehicle"
                :label="$t('common.vehicle')"
                :placeholder="$t('repair_orders.search_vehicles')"
                title-field="license_plate"
                :required="true"
              />
            </div>
          </div>
        </div>

        <!-- Step 2: Problem Details & Intake -->
        <div v-if="currentStep === 2" class="space-y-6">
          <h2 class="text-xl font-semibold" style="color: var(--text-primary);">Problem & Intake Details</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="md:col-span-2">
              <label class="block text-sm font-medium mb-1">Problem Summary *</label>
              <input v-model="form.problem_summary" type="text" class="form-input" placeholder="Brief description of the issue" />
            </div>
            <div class="md:col-span-2">
              <label class="block text-sm font-medium mb-1">Problem Details</label>
              <textarea v-model="form.problem_details" rows="4" class="form-input !h-auto" placeholder="Detailed description..." />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Intake Channel</label>
              <select v-model="form.intake_channel" class="form-select">
                <option value="">Select...</option>
                <option value="Walk-in">Walk-in</option>
                <option value="Web Intake">Web Intake</option>
                <option value="Phone">Phone</option>
                <option value="Partner">Partner</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Priority</label>
              <select v-model="form.priority" class="form-select">
                <option value="Low">Low</option>
                <option value="Normal">Normal</option>
                <option value="High">High</option>
                <option value="Urgent">Urgent</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Entry Date/Time</label>
              <input
                v-model="form.entry_datetime"
                type="datetime-local"
                class="form-input"
                :disabled="!form.entry_datetime_editable"
              />
            </div>
            <div class="flex items-center gap-2 pt-6">
              <input
                v-model="form.entry_datetime_editable"
                type="checkbox"
                id="entry_dt_edit"
                class="rounded"
              />
              <label for="entry_dt_edit" class="text-sm" style="color: var(--text-secondary);">
                Allow editing entry date/time
              </label>
            </div>
          </div>
        </div>

        <!-- Step 3: Service Planning -->
        <div v-if="currentStep === 3" class="space-y-6">
          <h2 class="text-xl font-semibold" style="color: var(--text-primary);">Service Planning</h2>

          <!-- Service Template -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <LinkField
              v-model="form.service_template"
              doctype="Service Template"
              label="Service Template (auto-populates below)"
              placeholder="Select a template..."
              title-field="template_name"
            />
            <div v-if="isLoadingTemplate" class="flex items-center gap-2 pt-6">
              <LucideLoader2 class="size-4 animate-spin" style="color: var(--text-muted);" />
              <span class="text-sm" style="color: var(--text-muted);">Loading template...</span>
            </div>
          </div>

          <!-- Operations -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Operations</h3>
              <Button variant="outline" size="sm" @click="addOperation">
                <LucidePlus class="size-3" /> Add
              </Button>
            </div>
            <div v-if="operations.length" class="space-y-2">
              <div
                v-for="(op, idx) in operations"
                :key="idx"
                class="grid grid-cols-12 gap-2 items-center p-3 rounded-lg"
                style="background-color: var(--bg-tertiary);"
              >
                <div class="col-span-4">
                  <LinkField
                    v-model="op.operation_name"
                    doctype="Operation"
                    placeholder="Select operation..."
                    title-field="name"
                  />
                </div>
                <input v-model.number="op.planned_minutes" type="number" class="form-input col-span-2" placeholder="Min" />
                <div class="col-span-3">
                  <LinkField
                    v-model="op.workstation"
                    doctype="Workstation"
                    placeholder="Select workstation..."
                    title-field="name"
                  />
                </div>
                <div class="col-span-2 flex items-center gap-1">
                  <input v-model="op.is_qc" type="checkbox" class="rounded" />
                  <span class="text-xs" style="color: var(--text-muted);">QC</span>
                </div>
                <button @click="removeOperation(idx)" class="col-span-1 p-1 text-red-500 hover:text-red-700">
                  <LucideTrash2 class="size-4" />
                </button>
              </div>
            </div>
            <p v-else class="text-sm py-4 text-center" style="color: var(--text-muted);">
              No operations added. Select a template or add manually.
            </p>
            <p v-if="totalPlannedMinutes > 0" class="text-xs mt-2" style="color: var(--text-muted);">
              Total estimated time: {{ formatMinutes(totalPlannedMinutes) }}
            </p>
          </div>

          <!-- Parts Plan -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Parts / Consumables</h3>
              <Button variant="outline" size="sm" @click="addPart">
                <LucidePlus class="size-3" /> Add
              </Button>
            </div>
            <div v-if="partsPlan.length" class="space-y-2">
              <div
                v-for="(part, idx) in partsPlan"
                :key="idx"
                class="grid grid-cols-12 gap-2 items-center p-3 rounded-lg"
                style="background-color: var(--bg-tertiary);"
              >
                <div class="col-span-4">
                  <LinkField
                    v-model="part.item_code"
                    doctype="Item"
                    placeholder="Search item..."
                    title-field="item_name"
                  />
                </div>
                <input v-model="part.item_name" type="text" class="form-input col-span-2" placeholder="Name" />
                <input v-model.number="part.qty_planned" type="number" class="form-input col-span-1" placeholder="Qty" />
                <input v-model="part.uom" type="text" class="form-input col-span-1" placeholder="UOM" />
                <div class="col-span-2 flex items-center gap-2">
                  <label class="flex items-center gap-1 text-xs">
                    <input v-model="part.is_billable" type="checkbox" class="rounded" /> Bill
                  </label>
                  <label class="flex items-center gap-1 text-xs">
                    <input v-model="part.is_foc" type="checkbox" class="rounded" /> FoC
                  </label>
                </div>
                <button @click="removePart(idx)" class="col-span-1 p-1 text-red-500 hover:text-red-700">
                  <LucideTrash2 class="size-4" />
                </button>
              </div>
            </div>
            <p v-else class="text-sm py-4 text-center" style="color: var(--text-muted);">
              No parts added.
            </p>
          </div>

          <!-- Handover Checklist -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Handover Checklist</h3>
              <Button variant="outline" size="sm" @click="addChecklistItem">
                <LucidePlus class="size-3" /> Add
              </Button>
            </div>
            <div v-if="handoverChecklist.length" class="space-y-2">
              <div
                v-for="(item, idx) in handoverChecklist"
                :key="idx"
                class="grid grid-cols-12 gap-2 items-center p-3 rounded-lg"
                style="background-color: var(--bg-tertiary);"
              >
                <div class="col-span-7">
                  <LinkField
                    v-model="item.item_name"
                    doctype="Handover Checklist Item"
                    placeholder="Select checklist item..."
                    title-field="item_name"
                    @update:model-value="onChecklistItemSelected(idx, $event)"
                  />
                </div>
                <input v-model="item.type" type="text" class="form-input col-span-4" readonly disabled />
                <button @click="removeChecklistItem(idx)" class="col-span-1 p-1 text-red-500 hover:text-red-700">
                  <LucideTrash2 class="size-4" />
                </button>
              </div>
            </div>
            <p v-else class="text-sm py-4 text-center" style="color: var(--text-muted);">
              No checklist items.
            </p>
          </div>

          <!-- Expected Delivery & SLA -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t" style="border-color: var(--border-color);">
            <div>
              <label class="block text-sm font-medium mb-1">Expected Delivery</label>
              <input v-model="form.expected_delivery_datetime" type="datetime-local" class="form-input" />
              <p class="text-xs mt-1" style="color: var(--text-muted);">
                Auto-calculated from operations duration. You can edit this.
              </p>
            </div>
            <LinkField
              v-model="form.sla_template"
              doctype="SLA Template"
              label="SLA Template"
              placeholder="Select SLA template..."
              title-field="template_name"
            />
          </div>
        </div>

        <!-- Step 4: Review & Confirm -->
        <div v-if="currentStep === 4" class="space-y-6">
          <h2 class="text-xl font-semibold" style="color: var(--text-primary);">Review & Confirm</h2>

          <!-- Basic Info Summary -->
          <div class="rounded-lg p-4" style="background-color: var(--bg-tertiary);">
            <h3 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">Basic Information</h3>
            <div class="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span style="color: var(--text-muted);">Order For:</span>
                <span class="ml-2 font-medium" style="color: var(--text-primary);">{{ form.order_for }}</span>
              </div>
              <div v-if="form.order_for === 'Customer'">
                <span style="color: var(--text-muted);">Customer:</span>
                <span class="ml-2 font-medium" style="color: var(--text-primary);">{{ form.customer }}</span>
              </div>
              <div v-if="form.order_for === 'Company'">
                <span style="color: var(--text-muted);">Company:</span>
                <span class="ml-2 font-medium" style="color: var(--text-primary);">{{ form.company }}</span>
              </div>
              <div>
                <span style="color: var(--text-muted);">Vehicle:</span>
                <span class="ml-2 font-medium" style="color: var(--text-primary);">{{ form.vehicle }}</span>
              </div>
              <div>
                <span style="color: var(--text-muted);">Priority:</span>
                <span class="ml-2 font-medium" style="color: var(--text-primary);">{{ form.priority }}</span>
              </div>
              <div>
                <span style="color: var(--text-muted);">Intake Channel:</span>
                <span class="ml-2 font-medium" style="color: var(--text-primary);">{{ form.intake_channel || '—' }}</span>
              </div>
              <div class="col-span-2">
                <span style="color: var(--text-muted);">Problem:</span>
                <span class="ml-2" style="color: var(--text-primary);">{{ form.problem_summary || '—' }}</span>
              </div>
            </div>
          </div>

          <!-- Operations Summary -->
          <div v-if="operations.length" class="rounded-lg p-4" style="background-color: var(--bg-tertiary);">
            <h3 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">
              Operations ({{ operations.length }}) — {{ formatMinutes(totalPlannedMinutes) }}
            </h3>
            <ul class="space-y-1 text-sm">
              <li v-for="op in operations" :key="op.operation_name" class="flex justify-between" style="color: var(--text-secondary);">
                <span>{{ op.operation_name }}</span>
                <span>{{ op.planned_minutes }} min{{ op.is_qc ? ' (QC)' : '' }}</span>
              </li>
            </ul>
          </div>

          <!-- Parts Summary -->
          <div v-if="partsPlan.length" class="rounded-lg p-4" style="background-color: var(--bg-tertiary);">
            <h3 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">
              Parts ({{ partsPlan.length }})
            </h3>
            <ul class="space-y-1 text-sm">
              <li v-for="part in partsPlan" :key="part.item_code" class="flex justify-between" style="color: var(--text-secondary);">
                <span>{{ part.item_name || part.item_code }}</span>
                <span>{{ part.qty_planned }} {{ part.uom }}{{ part.is_billable ? ' (Billable)' : '' }}{{ part.is_foc ? ' (FoC)' : '' }}</span>
              </li>
            </ul>
          </div>

          <!-- Checklist Summary -->
          <div v-if="handoverChecklist.length" class="rounded-lg p-4" style="background-color: var(--bg-tertiary);">
            <h3 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">
              Handover Checklist ({{ handoverChecklist.length }})
            </h3>
            <ul class="space-y-1 text-sm">
              <li v-for="item in handoverChecklist" :key="item.item_name" style="color: var(--text-secondary);">
                {{ item.item_name }} <span class="text-xs" style="color: var(--text-muted);">({{ item.type }})</span>
              </li>
            </ul>
          </div>

          <!-- Delivery -->
          <div v-if="form.expected_delivery_datetime" class="rounded-lg p-4" style="background-color: var(--bg-tertiary);">
            <h3 class="text-sm font-semibold mb-2" style="color: var(--text-primary);">Expected Delivery</h3>
            <p class="text-sm" style="color: var(--text-secondary);">
              {{ new Date(form.expected_delivery_datetime).toLocaleString() }}
            </p>
          </div>

          <div class="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg text-xs leading-relaxed" style="color: var(--text-secondary);">
            <LucideCheckCircle class="size-4 inline mr-1 text-blue-500" />
            This work order will be saved as <strong>Draft</strong>. An authorized user can then review and submit it to change the status to <strong>Scheduled</strong>.
          </div>
        </div>

        <!-- Navigation Buttons -->
        <div class="flex items-center justify-between mt-12 pt-6 border-t border-default">
          <Button variant="outline" :disabled="currentStep === 1" @click="prevStep">
            <LucideChevronLeft class="size-4" />
            {{ $t('common.previous') }}
          </Button>

          <Button v-if="currentStep < 4" variant="primary" @click="nextStep">
            {{ $t('common.next') }}
            <LucideChevronRight class="size-4" />
          </Button>

          <Button v-else variant="primary" :disabled="isSaving" @click="handleSubmit">
            <LucideLoader2 v-if="isSaving" class="size-4 animate-spin" />
            <LucideSave v-else class="size-4" />
            {{ isSaving ? $t('common.saving') : 'Save as Draft' }}
          </Button>
        </div>
      </Card>
    </template>
  </div>
</template>

<style scoped>
.form-input {
  @apply w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400 transition-all;
  background-color: var(--bg-tertiary);
  border-color: var(--border-color);
  color: var(--text-primary);
}

.form-select {
  @apply w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400 transition-all appearance-none cursor-pointer;
  background-color: var(--bg-tertiary);
  border-color: var(--border-color);
  color: var(--text-primary);
}
</style>
