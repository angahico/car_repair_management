<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import {
  LucideArrowLeft,
  LucideEdit,
  LucideCar,
  LucideMapPin,
  LucideHistory,
  LucideReceipt,
  LucideWrench,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface CustomerDetailData {
  doc: Record<string, unknown>
  vehicles: Array<Record<string, unknown>>
  repair_orders: Array<Record<string, unknown>>
  invoices: Array<Record<string, unknown>>
  addresses: Array<Record<string, unknown>>
  audit_trail: Array<Record<string, unknown>>
}

const props = defineProps<{ id: string }>()
const router = useRouter()

const isLoading = ref(true)
const detail = ref<CustomerDetailData | null>(null)

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Draft: 'default',
  Open: 'info',
  'In Progress': 'info',
  Completed: 'success',
  Cancelled: 'danger',
  Closed: 'default',
  Paid: 'success',
  Unpaid: 'danger',
  'Partly Paid': 'warning',
  Overdue: 'danger',
  'Return': 'warning',
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  const str = String(dateStr)
  const [datePart] = str.split(' ')
  const parts = datePart.split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    return d.toLocaleDateString()
  }
  return str
}

function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  const str = String(dateStr)
  const [datePart, timePart] = str.split(' ')
  const parts = datePart.split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    const formatted = d.toLocaleDateString()
    return timePart ? `${formatted} ${timePart.substring(0, 5)}` : formatted
  }
  return str
}

function formatCurrency(amount: unknown): string {
  const num = Number(amount) || 0
  return 'ETB ' + num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadDetail() {
  isLoading.value = true
  try {
    detail.value = await apiCall<CustomerDetailData>(
      'car_repair_management.api.customer.get_customer_detail',
      { name: props.id },
    )
  } catch (e) {
    console.warn('Failed to load customer detail', e)
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.push('/customers')
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
            <h1 class="text-page-title">{{ detail.doc.customer_name || detail.doc.name }}</h1>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ detail.doc.name }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Badge :variant="detail.doc.customer_type === 'Company' ? 'info' : 'default'" size="md">
            {{ detail.doc.customer_type || 'Individual' }}
          </Badge>
          <Badge :variant="detail.doc.disabled ? 'danger' : 'success'" size="md">
            {{ detail.doc.disabled ? 'Inactive' : 'Active' }}
          </Badge>
          <a :href="`/app/customer/${detail.doc.name}`" target="_blank">
            <Button variant="outline" size="sm">
              <LucideEdit class="size-3.5" />
              Edit
            </Button>
          </a>
        </div>
      </div>

      <!-- Profile Card -->
      <Card>
        <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">Customer Profile</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Type</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.doc.customer_type || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Group</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.doc.customer_group || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Territory</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.doc.territory || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Phone</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.doc.mobile_no || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Email</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.doc.email_id || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Created</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatDate(detail.doc.creation as string) }}</p>
          </div>
        </div>
      </Card>

      <!-- Addresses Card -->
      <Card v-if="detail.addresses && detail.addresses.length > 0">
        <div class="flex items-center gap-2 mb-4">
          <LucideMapPin class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Addresses ({{ detail.addresses.length }})
          </h2>
        </div>
        <div class="space-y-3">
          <div
            v-for="addr in detail.addresses"
            :key="String(addr.name)"
            class="p-3 rounded-lg"
            style="background: var(--bg-tertiary)"
          >
            <p class="text-sm" style="color: var(--text-primary)">{{ addr.address_line1 }}</p>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">
              {{ [addr.city, addr.state, addr.country].filter(Boolean).join(', ') }}
              <template v-if="addr.pincode"> — {{ addr.pincode }}</template>
            </p>
            <p v-if="addr.phone" class="text-xs mt-0.5" style="color: var(--text-muted)">{{ addr.phone }}</p>
          </div>
        </div>
      </Card>

      <!-- Vehicles Card -->
      <Card v-if="detail.vehicles && detail.vehicles.length > 0">
        <div class="flex items-center gap-2 mb-4">
          <LucideCar class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Vehicles ({{ detail.vehicles.length }})
          </h2>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <RouterLink
            v-for="v in detail.vehicles"
            :key="String(v.name)"
            :to="`/vehicles/${v.name}`"
            class="block p-3 rounded-lg transition-colors"
            style="background: var(--bg-tertiary)"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                style="background: var(--bg-secondary)"
              >
                <LucideCar class="size-5" style="color: var(--text-secondary)" />
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium truncate" style="color: var(--text-primary)">{{ v.name }}</p>
                <p class="text-xs" style="color: var(--text-muted)">
                  {{ [v.make, v.model, v.year].filter(Boolean).join(' ') || v.license_plate || '—' }}
                </p>
              </div>
            </div>
          </RouterLink>
        </div>
      </Card>

      <!-- Orders Card -->
      <Card v-if="detail.repair_orders && detail.repair_orders.length > 0" padding="none">
        <div class="px-4 pt-4 pb-3 flex items-center gap-2">
          <LucideWrench class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Repair Orders ({{ detail.repair_orders.length }})
          </h2>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Order ID</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Vehicle</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Status</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Total</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Date</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="o in detail.repair_orders"
                :key="String(o.name)"
                class="border-b cursor-pointer transition-colors"
                style="border-color: var(--border-subtle)"
                @click="router.push(`/repair-orders/${o.name}`)"
                @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
                @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
              >
                <td class="px-4 py-3 font-medium whitespace-nowrap">{{ o.name }}</td>
                <td class="px-4 py-3 whitespace-nowrap">{{ o.vehicle || '—' }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="STATUS_VARIANTS[String(o.status)] || 'default'" size="sm">
                    {{ o.status }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-right whitespace-nowrap">{{ o.grand_total ? formatCurrency(o.grand_total) : '—' }}</td>
                <td class="px-4 py-3 whitespace-nowrap">{{ formatDate(o.creation as string) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Financials Card -->
      <Card v-if="detail.invoices && detail.invoices.length > 0" padding="none">
        <div class="px-4 pt-4 pb-3 flex items-center gap-2">
          <LucideReceipt class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Invoices ({{ detail.invoices.length }})
          </h2>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Invoice ID</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Date</th>
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Status</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Amount</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Outstanding</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="inv in detail.invoices"
                :key="String(inv.name)"
                class="border-b"
                style="border-color: var(--border-subtle)"
              >
                <td class="px-4 py-3 font-medium whitespace-nowrap">{{ inv.name }}</td>
                <td class="px-4 py-3 whitespace-nowrap">{{ formatDate(inv.posting_date as string) }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="STATUS_VARIANTS[String(inv.status)] || 'default'" size="sm">
                    {{ inv.status }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-right whitespace-nowrap">{{ formatCurrency(inv.grand_total) }}</td>
                <td
                  class="px-4 py-3 text-right whitespace-nowrap"
                  :style="{ color: Number(inv.outstanding_amount) > 0 ? '#ef4444' : 'var(--text-primary)' }"
                >
                  {{ formatCurrency(inv.outstanding_amount) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Audit Trail Card -->
      <Card v-if="detail.audit_trail && detail.audit_trail.length > 0">
        <div class="flex items-center gap-2 mb-4">
          <LucideHistory class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Audit Trail</h2>
        </div>
        <div class="space-y-3">
          <div
            v-for="(v, idx) in detail.audit_trail"
            :key="idx"
            class="flex items-start gap-3 pl-2 border-l-2"
            style="border-color: var(--border-color)"
          >
            <div class="flex-1 py-1">
              <p class="text-sm" style="color: var(--text-primary)">Changed by {{ v.owner }}</p>
              <p class="text-xs mt-0.5" style="color: var(--text-muted)">
                {{ formatDateTime(v.creation as string) }}
              </p>
            </div>
          </div>
        </div>
      </Card>
    </template>

    <!-- Error / Not Found -->
    <Card v-else>
      <div class="flex flex-col items-center py-12 text-center">
        <p class="text-lg font-semibold" style="color: var(--text-primary)">Customer not found</p>
        <p class="text-sm mt-1 mb-4" style="color: var(--text-muted)">
          The customer "{{ id }}" could not be loaded.
        </p>
        <Button variant="secondary" @click="goBack">
          <LucideArrowLeft class="size-4" />
          Back to Customers
        </Button>
      </div>
    </Card>
  </div>
</template>
