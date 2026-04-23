<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideArrowLeft,
  LucideReceipt,
  LucideHistory,
  LucideLink,
  LucideAlertTriangle,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface AuditEntry {
  name: string
  owner: string
  creation: string
  data: string
}

interface ParsedAuditEntry {
  description: string
  changed_by: string
  timestamp: string
}

interface ExpenseDoc {
  name: string
  title: string | null
  vehicle: string
  category: string
  amount: number
  expense_date: string | null
  vendor: string | null
  payment_method: string | null
  payment_status: string
  notes: string | null
  work_order: string | null
  quantity: number | null
  unit_cost: number | null
  odometer_reading: number | null
  receipt_attachment: string | null
  receipt_required: number
}

interface ExpenseDetailData {
  doc: ExpenseDoc
  audit_trail: AuditEntry[]
}

const props = defineProps<{ id: string }>()
const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const detail = ref<ExpenseDoc | null>(null)
const auditTrail = ref<ParsedAuditEntry[]>([])

const PAYMENT_VARIANTS: Record<string, StatusVariant> = {
  Paid: 'success',
  Unpaid: 'danger',
  'Partially Paid': 'warning',
}

const CATEGORY_VARIANTS: Record<string, StatusVariant> = {
  Fuel: 'info',
  Parts: 'primary',
  Labor: 'warning',
  'External Service': 'default',
  Insurance: 'success',
  Taxes: 'danger',
  Other: 'default',
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const parts = dateStr.split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    return d.toLocaleDateString()
  }
  return dateStr
}

function formatCurrency(val: number): string {
  return 'ETB ' + (val?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00')
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

function parseAuditTrail(entries: AuditEntry[]): ParsedAuditEntry[] {
  const parsed: ParsedAuditEntry[] = []
  for (const entry of entries) {
    try {
      const data = JSON.parse(entry.data)
      if (data.changed && Array.isArray(data.changed)) {
        const changes = data.changed
          .map((c: [string, unknown, unknown]) => `${c[0]}: ${c[1]} → ${c[2]}`)
          .join(', ')
        parsed.push({
          description: changes || 'Document updated',
          changed_by: entry.owner,
          timestamp: entry.creation,
        })
      } else {
        parsed.push({
          description: 'Document updated',
          changed_by: entry.owner,
          timestamp: entry.creation,
        })
      }
    } catch {
      parsed.push({
        description: 'Document updated',
        changed_by: entry.owner,
        timestamp: entry.creation,
      })
    }
  }
  return parsed
}

async function loadDetail() {
  isLoading.value = true
  try {
    const data = await apiCall<ExpenseDetailData>(
      'car_repair_management.api.expense.get_expense_detail',
      { name: props.id },
    )
    if (data) {
      detail.value = data.doc
      auditTrail.value = parseAuditTrail(data.audit_trail || [])
    }
  } catch (e) {
    console.warn('Failed to load expense detail', e)
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.push('/expenses')
}

function goEdit() {
  router.push(`/expenses/${props.id}/edit`)
}

const hasAdditionalDetails = () => {
  if (!detail.value) return false
  return detail.value.quantity || detail.value.unit_cost || detail.value.odometer_reading
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
            <h1 class="text-page-title">{{ detail.title || detail.name }}</h1>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ detail.name }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Badge :variant="PAYMENT_VARIANTS[detail.payment_status] || 'default'" size="md">
            {{ detail.payment_status }}
          </Badge>
          <Badge :variant="CATEGORY_VARIANTS[detail.category] || 'default'" size="md">
            {{ detail.category }}
          </Badge>
          <div
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-semibold"
            style="background: var(--bg-tertiary); color: var(--text-primary)"
          >
            <LucideReceipt class="size-4" />
            {{ formatCurrency(detail.amount) }}
          </div>
          <Button variant="secondary" @click="goEdit">Edit</Button>
        </div>
      </div>

      <!-- Summary Card -->
      <Card>
        <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">Expense Summary</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Vehicle</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.vehicle }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Category</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.category }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Amount</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatCurrency(detail.amount) }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Date</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDate(detail.expense_date) }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Vendor</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.vendor || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Payment Method</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.payment_method || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Payment Status</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">
              <Badge :variant="PAYMENT_VARIANTS[detail.payment_status] || 'default'" size="sm">
                {{ detail.payment_status }}
              </Badge>
            </p>
          </div>
        </div>
        <div v-if="detail.notes" class="mt-4 pt-4 border-t" style="border-color: var(--border-subtle)">
          <p class="text-xs font-medium mb-1" style="color: var(--text-muted)">Notes</p>
          <p class="text-sm whitespace-pre-wrap" style="color: var(--text-secondary)">{{ detail.notes }}</p>
        </div>
      </Card>

      <!-- Links Card -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideLink class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Links &amp; References</h2>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Work Order</p>
            <p class="text-sm mt-0.5">
              <router-link
                v-if="detail.work_order"
                :to="`/repair-orders/${detail.work_order}`"
                style="color: var(--accent)"
                class="hover:underline"
              >
                {{ detail.work_order }}
              </router-link>
              <span v-else style="color: var(--text-primary)">—</span>
            </p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Vehicle</p>
            <p class="text-sm mt-0.5">
              <router-link
                :to="`/vehicles/${detail.vehicle}`"
                style="color: var(--accent)"
                class="hover:underline"
              >
                {{ detail.vehicle }}
              </router-link>
            </p>
          </div>
        </div>
      </Card>

      <!-- Additional Details Card -->
      <Card v-if="hasAdditionalDetails()">
        <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">Additional Details</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
          <div v-if="detail.quantity">
            <p class="text-xs font-medium" style="color: var(--text-muted)">Quantity</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.quantity }}</p>
          </div>
          <div v-if="detail.unit_cost">
            <p class="text-xs font-medium" style="color: var(--text-muted)">Unit Cost</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatCurrency(detail.unit_cost) }}</p>
          </div>
          <div v-if="detail.odometer_reading">
            <p class="text-xs font-medium" style="color: var(--text-muted)">Odometer Reading</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.odometer_reading.toLocaleString() }}</p>
          </div>
        </div>
      </Card>

      <!-- Receipt / Attachments Card -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideReceipt class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Receipt / Attachments</h2>
        </div>
        <div v-if="detail.receipt_attachment">
          <a
            :href="detail.receipt_attachment"
            target="_blank"
            rel="noopener noreferrer"
            style="color: var(--accent)"
            class="text-sm hover:underline"
          >
            {{ detail.receipt_attachment.split('/').pop() }}
          </a>
        </div>
        <div v-else-if="detail.receipt_required" class="flex items-center gap-2">
          <LucideAlertTriangle class="size-4" style="color: #f59e0b" />
          <p class="text-sm" style="color: var(--text-secondary)">
            Receipt is required but has not been uploaded yet.
          </p>
        </div>
        <div v-else>
          <p class="text-sm" style="color: var(--text-muted)">No attachments</p>
        </div>
      </Card>

      <!-- Audit Trail Card -->
      <Card v-if="auditTrail.length > 0">
        <div class="flex items-center gap-2 mb-4">
          <LucideHistory class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Audit Trail</h2>
        </div>
        <div class="space-y-3">
          <div
            v-for="(v, idx) in auditTrail"
            :key="idx"
            class="flex items-start gap-3 pl-2 border-l-2"
            style="border-color: var(--border-color)"
          >
            <div class="flex-1 py-1">
              <p class="text-sm" style="color: var(--text-primary)">{{ v.description }}</p>
              <p class="text-xs mt-0.5" style="color: var(--text-muted)">
                {{ v.changed_by }} · {{ formatDateTime(v.timestamp) }}
              </p>
            </div>
          </div>
        </div>
      </Card>
    </template>

    <!-- Error / Not Found -->
    <Card v-else>
      <div class="flex flex-col items-center py-12 text-center">
        <p class="text-lg font-semibold" style="color: var(--text-primary)">Expense not found</p>
        <p class="text-sm mt-1 mb-4" style="color: var(--text-muted)">
          The expense "{{ id }}" could not be loaded.
        </p>
        <Button variant="secondary" @click="goBack">
          <LucideArrowLeft class="size-4" />
          Back to Expenses
        </Button>
      </div>
    </Card>
  </div>
</template>
