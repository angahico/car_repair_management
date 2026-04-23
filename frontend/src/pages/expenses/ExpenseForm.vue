<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LucideArrowLeft, LucideSave, LucideUpload, LucideLoader2 } from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button } from '@/components/ui'
import LinkField from '@/components/ui/LinkField.vue'

const props = withDefaults(defineProps<{ id?: string; isNew?: boolean }>(), { isNew: false })
const router = useRouter()
const { t } = useI18n()

const isLoading = ref(false)
const isSaving = ref(false)
const error = ref('')

const form = ref({
  title: '',
  expense_date: new Date().toISOString().slice(0, 10),
  category: '',
  amount: 0,
  vehicle: '',
  vendor: '',
  payment_method: '',
  work_order: '',
  quantity: 0,
  unit_cost: 0,
  odometer_reading: 0,
  notes: '',
  payment_status: 'Unpaid',
  receipt_required: 0,
})

const receiptFilename = ref('')

const CATEGORIES = ['Fuel', 'Parts', 'Labor', 'External Service', 'Insurance', 'Taxes', 'Other']
const PAYMENT_METHODS = ['Cash', 'Bank Transfer', 'Credit Card', 'Check', 'Other']
const PAYMENT_STATUSES = ['Unpaid', 'Paid', 'Partially Paid']

const pageTitle = computed(() => props.isNew ? 'New Expense' : 'Edit Expense')
const isEditing = computed(() => !!props.id && !props.isNew)
const showQuantityFields = computed(() => form.value.category === 'Fuel' || form.value.category === 'Parts')
const showOdometerField = computed(() => form.value.category === 'Fuel')

watch(
  () => [form.value.quantity, form.value.unit_cost],
  ([qty, cost]) => {
    if (showQuantityFields.value && qty && cost) {
      form.value.amount = parseFloat((Number(qty) * Number(cost)).toFixed(2))
    }
  },
)

function validate(): boolean {
  if (!form.value.title.trim()) {
    error.value = 'Title is required'
    return false
  }
  if (!form.value.expense_date) {
    error.value = 'Expense Date is required'
    return false
  }
  if (!form.value.category) {
    error.value = 'Category is required'
    return false
  }
  if (!form.value.amount || form.value.amount <= 0) {
    error.value = 'Amount is required and must be greater than 0'
    return false
  }
  if (!form.value.vehicle) {
    error.value = 'Vehicle is required'
    return false
  }
  return true
}

async function loadData() {
  if (!isEditing.value) return

  isLoading.value = true
  error.value = ''

  try {
    const data = await apiCall<any>(
      'car_repair_management.api.expense.get_expense_detail',
      { name: props.id },
    )
    if (data) {
      form.value = {
        title: data.title || '',
        expense_date: data.expense_date || new Date().toISOString().slice(0, 10),
        category: data.category || '',
        amount: data.amount || 0,
        vehicle: data.vehicle || '',
        vendor: data.vendor || '',
        payment_method: data.payment_method || '',
        work_order: data.work_order || '',
        quantity: data.quantity || 0,
        unit_cost: data.unit_cost || 0,
        odometer_reading: data.odometer_reading || 0,
        notes: data.notes || '',
        payment_status: data.payment_status || 'Unpaid',
        receipt_required: data.receipt_required || 0,
      }
      if (data.receipt_attachment) {
        receiptFilename.value = data.receipt_attachment.split('/').pop() || data.receipt_attachment
      }
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to load expense'
  } finally {
    isLoading.value = false
  }
}

async function handleSubmit() {
  if (!validate()) return

  isSaving.value = true
  error.value = ''

  try {
    if (isEditing.value) {
      await apiCall('car_repair_management.api.expense.update_expense', {
        name: props.id,
        ...form.value,
      })
      router.push(`/expenses/${props.id}`)
    } else {
      const result = await apiCall<{ name: string }>(
        'car_repair_management.api.expense.create_expense',
        form.value,
      )
      router.push(`/expenses/${result.name}`)
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to save expense'
  } finally {
    isSaving.value = false
  }
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

      <div class="flex items-center gap-2">
        <Button variant="primary" :disabled="isSaving" @click="handleSubmit">
          <LucideLoader2 v-if="isSaving" class="size-4 animate-spin" />
          <LucideSave v-else class="size-4" />
          {{ isSaving ? 'Saving...' : 'Save' }}
        </Button>
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

    <!-- Form -->
    <template v-else>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Core Details -->
          <Card>
            <h2 class="text-section-title mb-4" style="color: var(--text-primary);">Core Details</h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Title -->
              <div class="md:col-span-2">
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Title <span class="text-red-500">*</span>
                </label>
                <input
                  v-model="form.title"
                  type="text"
                  placeholder="e.g., Fuel refill, Oil change parts"
                  class="w-full h-9 px-3 text-sm rounded border"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                />
              </div>

              <!-- Expense Date -->
              <div>
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Expense Date <span class="text-red-500">*</span>
                </label>
                <input
                  v-model="form.expense_date"
                  type="date"
                  class="w-full h-9 px-3 text-sm rounded border"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                />
              </div>

              <!-- Category -->
              <div>
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Category <span class="text-red-500">*</span>
                </label>
                <select
                  v-model="form.category"
                  class="w-full h-9 px-3 text-sm rounded border appearance-none"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                >
                  <option value="">Select category...</option>
                  <option v-for="cat in CATEGORIES" :key="cat" :value="cat">{{ cat }}</option>
                </select>
              </div>

              <!-- Amount -->
              <div>
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Amount <span class="text-red-500">*</span>
                </label>
                <input
                  v-model.number="form.amount"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  class="w-full h-9 px-3 text-sm rounded border"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                />
              </div>

              <!-- Vehicle -->
              <div>
                <LinkField
                  v-model="form.vehicle"
                  doctype="Vehicle"
                  label="Vehicle"
                  placeholder="Search vehicle..."
                  :required="true"
                />
              </div>

              <!-- Vendor -->
              <div>
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Vendor
                </label>
                <input
                  v-model="form.vendor"
                  type="text"
                  placeholder="e.g., Shell, AutoZone"
                  class="w-full h-9 px-3 text-sm rounded border"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                />
              </div>

              <!-- Payment Method -->
              <div>
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Payment Method
                </label>
                <select
                  v-model="form.payment_method"
                  class="w-full h-9 px-3 text-sm rounded border appearance-none"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                >
                  <option value="">Select method...</option>
                  <option v-for="m in PAYMENT_METHODS" :key="m" :value="m">{{ m }}</option>
                </select>
              </div>
            </div>
          </Card>

          <!-- Additional Details -->
          <Card>
            <h2 class="text-section-title mb-4" style="color: var(--text-primary);">Additional Details</h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Work Order -->
              <div>
                <LinkField
                  v-model="form.work_order"
                  doctype="Repair Order"
                  label="Work Order"
                  placeholder="Search work order..."
                />
              </div>

              <!-- Quantity (Fuel / Parts) -->
              <div v-if="showQuantityFields">
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Quantity
                </label>
                <input
                  v-model.number="form.quantity"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0"
                  class="w-full h-9 px-3 text-sm rounded border"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                />
              </div>

              <!-- Unit Cost (Fuel / Parts) -->
              <div v-if="showQuantityFields">
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Unit Cost
                </label>
                <input
                  v-model.number="form.unit_cost"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  class="w-full h-9 px-3 text-sm rounded border"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                />
              </div>

              <!-- Odometer Reading (Fuel only) -->
              <div v-if="showOdometerField">
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Odometer Reading
                </label>
                <input
                  v-model.number="form.odometer_reading"
                  type="number"
                  min="0"
                  placeholder="e.g., 45000"
                  class="w-full h-9 px-3 text-sm rounded border"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                />
              </div>

              <!-- Notes -->
              <div class="md:col-span-2">
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Notes
                </label>
                <textarea
                  v-model="form.notes"
                  rows="3"
                  placeholder="Additional notes..."
                  class="w-full px-3 py-2 text-sm rounded border resize-none"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                />
              </div>
            </div>
          </Card>
        </div>

        <!-- Right Column -->
        <div class="space-y-6">
          <!-- Payment & Status -->
          <Card>
            <h2 class="text-section-title mb-4" style="color: var(--text-primary);">Payment &amp; Status</h2>

            <div class="space-y-4">
              <!-- Payment Status -->
              <div>
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
                  Payment Status
                </label>
                <select
                  v-model="form.payment_status"
                  class="w-full h-9 px-3 text-sm rounded border appearance-none"
                  style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
                >
                  <option v-for="s in PAYMENT_STATUSES" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>

              <!-- Receipt Required -->
              <div class="flex items-center gap-3">
                <input
                  :checked="!!form.receipt_required"
                  type="checkbox"
                  class="size-4 rounded border"
                  style="border-color: var(--border-color); accent-color: var(--accent)"
                  @change="form.receipt_required = ($event.target as HTMLInputElement).checked ? 1 : 0"
                />
                <label class="text-sm" style="color: var(--text-primary);">Receipt Required</label>
              </div>
            </div>
          </Card>

          <!-- Receipt / Attachment -->
          <Card>
            <h2 class="text-section-title mb-4" style="color: var(--text-primary);">Receipt / Attachment</h2>

            <div
              class="flex flex-col items-center justify-center gap-3 p-6 rounded-lg border-2 border-dashed"
              style="border-color: var(--border-color); background: var(--bg-tertiary)"
            >
              <LucideUpload class="size-8" style="color: var(--text-muted);" />
              <p class="text-sm text-center" style="color: var(--text-muted);">
                Upload receipt (photo/PDF)
              </p>
              <p v-if="receiptFilename" class="text-xs font-medium text-center" style="color: var(--text-secondary);">
                Current: {{ receiptFilename }}
              </p>
            </div>
          </Card>
        </div>
      </div>
    </template>
  </div>
</template>
