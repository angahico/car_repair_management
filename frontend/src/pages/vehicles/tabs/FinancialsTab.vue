<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  LucideDollarSign, 
  LucideTrendingUp, 
  LucideTrendingDown, 
  LucideFileText, 
  LucideExternalLink,
  LucideInfo,
  LucideShieldCheck
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Skeleton, Badge, Button } from '@/components/ui'

const props = defineProps<{ vehicleId: string }>()

const isLoading = ref(true)
const financials = ref<any>(null)

async function loadFinancials() {
  isLoading.value = true
  try {
    financials.value = await apiCall('car_repair_management.api.vehicle.get_vehicle_financials_full', {
      vehicle_name: props.vehicleId,
    })
  } catch (e) {
    console.error('Failed to load financials', e)
  } finally {
    isLoading.value = false
  }
}

const currency = computed(() => financials.value?.currency || 'ETB')

function formatCurrency(value: number | null): string {
  if (value === null || value === undefined) return '—'
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency.value, maximumFractionDigits: 0 }).format(value)
  } catch {
    return `${currency.value} ${value.toLocaleString()}`
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
}

function openAsset() {
  if (financials.value?.linked_records?.asset_link) {
    const url = `/app/asset/${financials.value.linked_records.asset_link}`
    window.open(url, '_blank')
  }
}

onMounted(loadFinancials)
</script>

<template>
  <div class="space-y-6 pb-12">
    <!-- Loading State -->
    <template v-if="isLoading">
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card v-for="i in 5" :key="i"><Skeleton height="100px" /></Card>
      </div>
      <Card><Skeleton height="300px" /></Card>
    </template>

    <template v-else-if="financials">
      <!-- Overview Section -->
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-bold" style="color: var(--text-primary);">Financial Overview</h2>
        <div v-if="financials.linked_records?.asset_link" class="flex items-center gap-2">
          <Badge variant="success" class="px-3 py-1 font-bold">
            <LucideShieldCheck class="size-3 mr-1" />
            Asset Synced
          </Badge>
          <Button variant="outline" size="sm" @click="openAsset">
            <LucideExternalLink class="size-3 mr-2" />
            View in ERPNext
          </Button>
        </div>
      </div>

      <!-- Financial Snapshot KPI Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
        <Card class="relative overflow-hidden group">
          <div class="p-2">
            <p class="text-xs font-semibold mb-1" style="color: var(--text-muted);">Acquisition Cost</p>
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ formatCurrency(financials.kpi_cards?.acquisition_cost) }}</p>
          </div>
          <div class="absolute -right-2 -bottom-2 opacity-10 group-hover:opacity-20 transition-opacity">
            <LucideDollarSign class="size-16 text-blue-500" />
          </div>
        </Card>

        <Card class="relative overflow-hidden group">
          <div class="p-2">
            <p class="text-xs font-semibold mb-1" style="color: var(--text-muted);">Lifetime Spend</p>
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ formatCurrency(financials.kpi_cards?.total_lifetime_spend) }}</p>
          </div>
          <div class="absolute -right-2 -bottom-2 opacity-10 group-hover:opacity-20 transition-opacity">
            <LucideTrendingUp class="size-16 text-indigo-500" />
          </div>
        </Card>

        <Card class="relative overflow-hidden group">
          <div class="p-2">
            <p class="text-xs font-semibold mb-1" style="color: var(--text-muted);">Total Depreciation</p>
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ formatCurrency(financials.kpi_cards?.total_depreciation) }}</p>
          </div>
          <div class="absolute -right-2 -bottom-2 opacity-10 group-hover:opacity-20 transition-opacity">
            <LucideTrendingDown class="size-16 text-rose-500" />
          </div>
        </Card>

        <Card class="relative overflow-hidden group">
          <div class="p-2">
            <p class="text-xs font-semibold mb-1" style="color: var(--text-muted);">Current Value</p>
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ formatCurrency(financials.kpi_cards?.current_book_value) }}</p>
          </div>
          <div class="absolute -right-2 -bottom-2 opacity-10 group-hover:opacity-20 transition-opacity">
            <LucideFileText class="size-16 text-emerald-500" />
          </div>
        </Card>

        <Card class="relative overflow-hidden group">
          <div class="p-2">
            <p class="text-xs font-semibold mb-1" style="color: var(--text-muted);">Cost / KM</p>
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ 
              financials.kpi_cards?.total_lifetime_spend && financials.overview?.current_odometer 
                ? formatCurrency(financials.kpi_cards.total_lifetime_spend / financials.overview.current_odometer)
                : '—' 
            }}</p>
          </div>
          <div class="absolute -right-2 -bottom-2 opacity-10 group-hover:opacity-20 transition-opacity">
            <LucideDollarSign class="size-16 text-amber-500" />
          </div>
        </Card>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Cost Breakdown -->
        <Card class="p-0 overflow-hidden">
          <div class="p-6 border-b" style="border-color: var(--border-color);">
            <h3 class="text-lg font-bold" style="color: var(--text-primary);">Maintenance Spend Profile</h3>
            <p class="text-sm mt-1" style="color: var(--text-muted);">Distribution of external repair costs</p>
          </div>
          
          <div v-if="financials.cost_breakdown?.length" class="p-6 space-y-6">
            <div v-for="item in financials.cost_breakdown" :key="item.category" class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-sm font-bold">{{ item.category }}</span>
                <span class="text-sm font-black">{{ formatCurrency(item.amount) }}</span>
              </div>
              <div class="flex items-center gap-4">
                <div class="flex-1 h-3 rounded-full bg-surface-tertiary overflow-hidden">
                  <div 
                    class="h-full rounded-full transition-all duration-700"
                    :class="{
                      'bg-blue-500': item.category === 'Parts',
                      'bg-amber-500': item.category === 'Labor',
                      'bg-purple-500': item.category === 'Other',
                    }"
                    :style="{ width: `${item.percentage}%` }"
                  />
                </div>
                <span class="text-[10px] font-black w-8">{{ item.percentage }}%</span>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-20 opacity-30">
            <LucideInfo class="size-12 mx-auto mb-4" />
            <p class="font-bold">No maintenance data recorded yet</p>
          </div>
        </Card>

        <!-- Depreciation & Valuation -->
        <Card class="p-0 overflow-hidden">
          <div class="p-6 border-b" style="border-color: var(--border-color);">
            <h3 class="text-lg font-bold" style="color: var(--text-primary);">Total Value Calculation</h3>
            <p class="text-sm mt-1" style="color: var(--text-muted);">Asset valuation based on depreciation</p>
          </div>
          <div class="p-8 space-y-8">
            <div class="grid grid-cols-2 gap-8">
              <div>
                <p class="text-[10px] font-black uppercase tracking-widest opacity-50 mb-1">Methodology</p>
                <p class="text-lg font-bold">{{ financials.depreciation?.method || 'Straight Line' }}</p>
              </div>
              <div>
                <p class="text-[10px] font-black uppercase tracking-widest opacity-50 mb-1">Activation Date</p>
                <p class="text-lg font-bold">{{ formatDate(financials.depreciation?.start_date) }}</p>
              </div>
              <div>
                <p class="text-[10px] font-black uppercase tracking-widest opacity-50 mb-1">Total Depreciated</p>
                <p class="text-lg font-bold text-red-500">{{ formatCurrency(financials.depreciation?.total_depreciated) }}</p>
              </div>
              <div>
                <p class="text-[10px] font-black uppercase tracking-widest opacity-50 mb-1">Residual Salvage Value</p>
                <p class="text-lg font-bold">{{ formatCurrency(financials.depreciation?.residual_value) }}</p>
              </div>
            </div>

            <!-- Visualization of Value -->
            <div class="pt-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-[10px] font-black uppercase opacity-50">Remaining Value Potential</span>
                <span class="text-sm font-black">{{ financials.kpi_cards?.acquisition_cost ? Math.round((financials.depreciation?.current_value / financials.kpi_cards.acquisition_cost) * 100) : 0 }}%</span>
              </div>
              <div class="h-4 rounded-full bg-surface-tertiary overflow-hidden flex">
                <div 
                  class="h-full bg-emerald-500" 
                  :style="{ width: `${financials.kpi_cards?.acquisition_cost ? (financials.depreciation?.current_value / financials.kpi_cards.acquisition_cost) * 100 : 0}%` }"
                ></div>
                <div 
                  class="h-full bg-red-500/20" 
                  :style="{ width: `${financials.kpi_cards?.acquisition_cost ? (financials.depreciation?.total_depreciated / financials.kpi_cards.acquisition_cost) * 100 : 0}%` }"
                ></div>
              </div>
              <div class="flex justify-between mt-2">
                <span class="text-[10px] font-bold text-emerald-600">Active Value</span>
                <span class="text-[10px] font-bold text-red-400">Depreciated</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <!-- Linked Financial Records -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card class="p-6">
          <h3 class="text-lg font-black uppercase tracking-tighter mb-6 flex items-center gap-2">
            <LucideFileText class="size-5" />
            Governance & Documentation
          </h3>
          <div class="space-y-4">
            <div class="flex items-center justify-between p-4 rounded-xl bg-surface-tertiary border border-dashed border-default">
              <div>
                <p class="text-sm font-black">Maintenance Work Orders</p>
                <p class="text-xs opacity-50">{{ financials.linked_records?.work_orders_count }} records found</p>
              </div>
              <p class="text-lg font-black">{{ formatCurrency(financials.linked_records?.work_orders_total) }}</p>
            </div>
            <div class="flex items-center justify-between p-4 rounded-xl bg-surface-tertiary border border-dashed border-default">
              <div>
                <p class="text-sm font-black">Success Rate</p>
                <p class="text-xs opacity-50">Completed vs Pending orders</p>
              </div>
              <p class="text-lg font-black">{{ financials.linked_records?.completed_orders }} / {{ financials.linked_records?.work_orders_count }}</p>
            </div>
          </div>
        </Card>

        <!-- Insurance Info -->
        <Card v-if="financials.insurance?.company || financials.insurance?.policy_no" class="p-6 bg-blue-500/[0.01]">
          <h3 class="text-lg font-black uppercase tracking-tighter mb-6 flex items-center gap-2">
            <LucideShieldCheck class="size-5 text-blue-500" />
            Insurance Risk Coverage
          </h3>
          <div class="grid grid-cols-2 gap-y-6 gap-x-12">
            <div>
              <p class="text-[10px] font-black uppercase tracking-widest opacity-50">Provider</p>
              <p class="font-black text-blue-600">{{ financials.insurance?.company || '—' }}</p>
            </div>
            <div>
              <p class="text-[10px] font-black uppercase tracking-widest opacity-50">Policy Identification</p>
              <p class="font-bold">{{ financials.insurance?.policy_no || '—' }}</p>
            </div>
            <div>
              <p class="text-[10px] font-black uppercase tracking-widest opacity-50">Valid From</p>
              <p class="text-sm font-bold">{{ formatDate(financials.insurance?.start_date) }}</p>
            </div>
            <div>
              <p class="text-[10px] font-black uppercase tracking-widest opacity-50">Expiry Date</p>
              <p class="text-sm font-black" :class="new Date(financials.insurance?.end_date) < new Date() ? 'text-red-500' : ''">
                {{ formatDate(financials.insurance?.end_date) }}
              </p>
            </div>
          </div>
        </Card>
      </div>
    </template>
  </div>
</template>
