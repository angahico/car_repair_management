<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  LucideArrowLeft,
  LucideFileText,
  LucideHistory,
  LucideCreditCard,
  LucideEdit,
  LucideExternalLink,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'
import type { StatusVariant } from '@/types'

const props = defineProps<{ id: string }>()
const router = useRouter()
const route = useRoute()

const isLoading = ref(true)
const doc = ref<any>(null)
const payments = ref<any[]>([])
const auditTrail = ref<any[]>([])
const invoiceType = ref('Sales')

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Draft: 'default',
  Unpaid: 'danger',
  Paid: 'success',
  Overdue: 'danger',
  Cancelled: 'default',
  'Partly Paid': 'warning',
  'Return': 'info',
  Submitted: 'info',
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const parts = String(dateStr).split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    return d.toLocaleDateString()
  }
  return String(dateStr)
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—'
  const [datePart, timePart] = String(dateStr).split(' ')
  const parts = datePart.split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    const formatted = d.toLocaleDateString()
    return timePart ? `${formatted} ${timePart.substring(0, 5)}` : formatted
  }
  return String(dateStr)
}

function formatCurrency(val: number): string {
  return 'ETB ' + (val?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00')
}

async function loadData() {
  isLoading.value = true
  const type = (route.query.type as string) || 'Sales'
  invoiceType.value = type
  try {
    const data = await apiCall<any>(
      'car_repair_management.api.invoice.get_invoice_detail',
      { name: props.id, invoice_type: type },
    )
    doc.value = data.doc
    payments.value = data.payments || []
    auditTrail.value = data.audit_trail || []
  } catch (e) {
    console.warn('Failed to load invoice detail', e)
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.push('/invoices')
}

function getDeskUrl(): string {
  const dt = invoiceType.value === 'Sales' ? 'sales-invoice' : 'purchase-invoice'
  return `/app/${dt}/${props.id}`
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading -->
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
            <h1 class="text-page-title" style="color: var(--text-primary)">{{ doc.name }}</h1>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ invoiceType }} Invoice</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Badge :variant="STATUS_VARIANTS[doc.status] || 'default'" size="md">{{ doc.status }}</Badge>
          <div
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-semibold"
            style="background: var(--bg-tertiary); color: var(--text-primary)"
          >
            {{ formatCurrency(doc.grand_total || 0) }}
          </div>
          <a :href="getDeskUrl()" target="_blank">
            <Button variant="outline">
              <LucideExternalLink class="size-4" />
              Open in Desk
            </Button>
          </a>
        </div>
      </div>

      <!-- Summary Card -->
      <Card>
        <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">Invoice Summary</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">{{ invoiceType === 'Sales' ? 'Customer' : 'Supplier' }}</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.customer || doc.supplier || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Posting Date</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDate(doc.posting_date) }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Due Date</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDate(doc.due_date) }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Grand Total</p>
            <p class="text-sm mt-0.5 font-semibold" style="color: var(--text-primary)">{{ formatCurrency(doc.grand_total || 0) }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Outstanding</p>
            <p class="text-sm mt-0.5 font-semibold" :style="{ color: (doc.outstanding_amount || 0) > 0 ? '#ef4444' : 'var(--text-primary)' }">
              {{ formatCurrency(doc.outstanding_amount || 0) }}
            </p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Company</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ doc.company || '—' }}</p>
          </div>
        </div>
        <div v-if="doc.terms" class="mt-4 pt-4 border-t" style="border-color: var(--border-subtle)">
          <p class="text-xs font-medium mb-1" style="color: var(--text-muted)">Terms</p>
          <p class="text-sm whitespace-pre-wrap" style="color: var(--text-secondary)">{{ doc.terms }}</p>
        </div>
      </Card>

      <!-- Line Items -->
      <Card padding="none">
        <div class="px-4 pt-4 pb-3 flex items-center gap-2">
          <LucideFileText class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Line Items ({{ (doc.items || []).length }})
          </h2>
        </div>
        <div v-if="(doc.items || []).length === 0" class="px-4 pb-4 text-sm" style="color: var(--text-muted)">
          No line items
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Item</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Description</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Qty</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Rate</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in (doc.items || [])"
                :key="item.name"
                class="border-b"
                style="border-color: var(--border-subtle)"
              >
                <td class="px-4 py-3 font-medium whitespace-nowrap">{{ item.item_code || item.item_name }}</td>
                <td class="px-4 py-3 truncate max-w-[200px]" style="color: var(--text-secondary)">{{ item.description || '—' }}</td>
                <td class="px-4 py-3 text-right">{{ item.qty }}</td>
                <td class="px-4 py-3 text-right">{{ formatCurrency(item.rate || 0) }}</td>
                <td class="px-4 py-3 text-right font-medium">{{ formatCurrency(item.amount || 0) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="border-t" style="border-color: var(--border-subtle)">
                <td colspan="4" class="px-4 py-3 text-right font-semibold" style="color: var(--text-muted)">Total</td>
                <td class="px-4 py-3 text-right font-bold">{{ formatCurrency(doc.grand_total || 0) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </Card>

      <!-- Payments -->
      <Card>
        <div class="flex items-center gap-2 mb-4">
          <LucideCreditCard class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Payments & Allocations</h2>
        </div>
        <div v-if="payments.length === 0" class="text-sm" style="color: var(--text-muted)">
          No payments recorded
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="p in payments"
            :key="p.name"
            class="flex items-center justify-between p-3 rounded-lg"
            style="background: var(--bg-tertiary)"
          >
            <div>
              <p class="text-sm font-medium" style="color: var(--text-primary)">{{ p.name }}</p>
              <p class="text-xs" style="color: var(--text-muted)">
                {{ formatDate(p.posting_date) }} · {{ p.mode_of_payment || 'N/A' }}
              </p>
            </div>
            <p class="text-sm font-semibold" style="color: #22c55e">{{ formatCurrency(p.allocated_amount) }}</p>
          </div>
        </div>
      </Card>

      <!-- Audit Trail -->
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
              <p class="text-sm" style="color: var(--text-primary)">Record updated</p>
              <p class="text-xs mt-0.5" style="color: var(--text-muted)">
                {{ v.owner }} · {{ formatDateTime(v.creation) }}
              </p>
            </div>
          </div>
        </div>
      </Card>
    </template>

    <!-- Not Found -->
    <Card v-else>
      <div class="flex flex-col items-center py-12 text-center">
        <p class="text-lg font-semibold" style="color: var(--text-primary)">Invoice not found</p>
        <p class="text-sm mt-1 mb-4" style="color: var(--text-muted)">
          The invoice "{{ id }}" could not be loaded.
        </p>
        <Button variant="secondary" @click="goBack">
          <LucideArrowLeft class="size-4" />
          Back to Invoices
        </Button>
      </div>
    </Card>
  </div>
</template>
