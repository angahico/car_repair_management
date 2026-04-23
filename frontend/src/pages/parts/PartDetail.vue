<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideArrowLeft,
  LucidePackage,
  LucideHistory,
  LucidePencil,
  LucideExternalLink,
  LucideWarehouse,
  LucideWrench,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface StockEntry {
  warehouse: string
  actual_qty: number
  reserved_qty: number
}

interface UsageEntry {
  repair_order: string
  qty: number
  rate: number
  amount: number
}

interface VersionChange {
  changed: string
  changed_by: string
  creation: string
}

interface PartDoc {
  name: string
  item_code: string
  item_name: string
  item_group: string | null
  stock_uom: string
  is_stock_item: number
  standard_rate: number
  description: string | null
  stock_status: string
  current_qty: number
  modified: string
}

interface PartDetailData {
  doc: PartDoc
  stock_by_warehouse: StockEntry[]
  usage_history: UsageEntry[]
  audit_trail: VersionChange[]
}

const props = defineProps<{ id: string }>()
const router = useRouter()

const isLoading = ref(true)
const detail = ref<PartDetailData | null>(null)

const STOCK_STATUS_VARIANTS: Record<string, StatusVariant> = {
  'In Stock': 'success',
  Low: 'warning',
  'Out of Stock': 'danger',
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

function formatCurrency(value: number): string {
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function goBack() {
  router.push('/parts')
}

function editItem() {
  router.push(`/parts/${props.id}/edit`)
}

function openRepairOrder(name: string) {
  router.push(`/repair-orders/${name}`)
}

async function loadDetail() {
  isLoading.value = true
  try {
    detail.value = await apiCall<PartDetailData>(
      'car_repair_management.api.parts.get_part_detail',
      { name: props.id },
    )
  } catch (e) {
    console.warn('Failed to load part detail', e)
  } finally {
    isLoading.value = false
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
            <h1 class="text-page-title">{{ detail.doc.item_name }}</h1>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ detail.doc.item_code }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Badge :variant="STOCK_STATUS_VARIANTS[detail.doc.stock_status] || 'default'" size="md">
            {{ detail.doc.stock_status }}
          </Badge>
          <Button variant="secondary" @click="editItem">
            <LucidePencil class="size-4" />
            Edit
          </Button>
          <a
            :href="`/app/item/${detail.doc.name}`"
            target="_blank"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
            style="background: var(--bg-tertiary); color: var(--text-secondary)"
          >
            <LucideExternalLink class="size-3.5" />
            Edit in Desk
          </a>
        </div>
      </div>

      <!-- Overview Card -->
      <Card>
        <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">Item Details</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Item Code</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.doc.item_code }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Item Name</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.doc.item_name }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Item Group</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.doc.item_group || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Stock UOM</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.doc.stock_uom }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Is Stock Item</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ detail.doc.is_stock_item ? 'Yes' : 'No' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium" style="color: var(--text-muted)">Standard Rate</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary)">{{ formatCurrency(detail.doc.standard_rate) }}</p>
          </div>
        </div>
        <div v-if="detail.doc.description" class="mt-4 pt-4 border-t" style="border-color: var(--border-subtle)">
          <p class="text-xs font-medium mb-1" style="color: var(--text-muted)">Description</p>
          <p class="text-sm whitespace-pre-wrap" style="color: var(--text-secondary)">{{ detail.doc.description }}</p>
        </div>
      </Card>

      <!-- Stock Levels Card -->
      <Card v-if="detail.doc.is_stock_item" padding="none">
        <div class="px-4 pt-4 pb-3 flex items-center gap-2">
          <LucideWarehouse class="size-4" style="color: var(--accent)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Stock Levels</h2>
        </div>
        <div v-if="detail.stock_by_warehouse.length === 0" class="px-4 pb-4">
          <p class="text-sm" style="color: var(--text-muted)">No stock data available</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Warehouse</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Actual Qty</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Reserved Qty</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="s in detail.stock_by_warehouse"
                :key="s.warehouse"
                class="border-b"
                style="border-color: var(--border-subtle)"
              >
                <td class="px-4 py-3 font-medium">{{ s.warehouse }}</td>
                <td class="px-4 py-3 text-right">{{ s.actual_qty }}</td>
                <td class="px-4 py-3 text-right">{{ s.reserved_qty }}</td>
              </tr>
              <!-- Total Row -->
              <tr
                class="border-t font-semibold"
                style="border-color: var(--border-color); background: var(--bg-tertiary)"
              >
                <td class="px-4 py-3">Total</td>
                <td class="px-4 py-3 text-right">
                  {{ detail.stock_by_warehouse.reduce((sum, s) => sum + s.actual_qty, 0) }}
                </td>
                <td class="px-4 py-3 text-right">
                  {{ detail.stock_by_warehouse.reduce((sum, s) => sum + s.reserved_qty, 0) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Work Order Usage Card -->
      <Card padding="none">
        <div class="px-4 pt-4 pb-3 flex items-center gap-2">
          <LucideWrench class="size-4" style="color: var(--text-muted)" />
          <h2 class="text-sm font-semibold" style="color: var(--text-primary)">
            Work Order Usage
          </h2>
        </div>
        <div v-if="detail.usage_history.length === 0" class="px-4 pb-4">
          <p class="text-sm" style="color: var(--text-muted)">No usage history</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm" style="color: var(--text-primary)">
            <thead>
              <tr class="border-b" style="border-color: var(--border-subtle)">
                <th class="text-left px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Repair Order</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Qty</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Rate</th>
                <th class="text-right px-4 py-2 text-xs font-medium" style="color: var(--text-muted)">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="u in detail.usage_history"
                :key="u.repair_order"
                class="border-b cursor-pointer transition-colors"
                style="border-color: var(--border-subtle)"
                @click="openRepairOrder(u.repair_order)"
                @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
                @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
              >
                <td class="px-4 py-3 font-medium whitespace-nowrap">{{ u.repair_order }}</td>
                <td class="px-4 py-3 text-right">{{ u.qty }}</td>
                <td class="px-4 py-3 text-right whitespace-nowrap">{{ formatCurrency(u.rate) }}</td>
                <td class="px-4 py-3 text-right whitespace-nowrap">{{ formatCurrency(u.amount) }}</td>
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
              <p class="text-sm" style="color: var(--text-primary)">{{ v.changed }}</p>
              <p class="text-xs mt-0.5" style="color: var(--text-muted)">
                {{ v.changed_by }} · {{ formatDateTime(v.creation) }}
              </p>
            </div>
          </div>
        </div>
      </Card>
    </template>

    <!-- Error / Not Found -->
    <Card v-else>
      <div class="flex flex-col items-center py-12 text-center">
        <LucidePackage class="size-12 mb-3" style="color: var(--text-muted)" />
        <p class="text-lg font-semibold" style="color: var(--text-primary)">Item not found</p>
        <p class="text-sm mt-1 mb-4" style="color: var(--text-muted)">
          The item "{{ id }}" could not be loaded.
        </p>
        <Button variant="secondary" @click="goBack">
          <LucideArrowLeft class="size-4" />
          Back to Parts
        </Button>
      </div>
    </Card>
  </div>
</template>
