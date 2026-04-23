<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { LucideCalendar, LucideWrench, LucideUser, LucideDollarSign, LucideGauge, LucideExternalLink, LucideHistory } from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Badge, Skeleton } from '@/components/ui'

const props = defineProps<{ vehicleId: string }>()

const isLoading = ref(true)
const serviceHistory = ref<any>(null)

async function loadServiceHistory() {
  isLoading.value = true
  try {
    serviceHistory.value = await apiCall('car_repair_management.api.vehicle.get_vehicle_service_history', {
      vehicle_name: props.vehicleId,
    })
  } catch (e) {
    console.error('Failed to load service history', e)
  } finally {
    isLoading.value = false
  }
}

function formatCurrency(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'ETB', maximumFractionDigits: 0 }).format(value)
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString()
}

const serviceTypeColors: Record<string, string> = {
  'Scheduled': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  'Corrective': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  'Emergency': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

onMounted(loadServiceHistory)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <template v-if="isLoading">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card v-for="i in 4" :key="i"><Skeleton height="80px" /></Card>
      </div>
      <Card><Skeleton height="300px" /></Card>
    </template>

    <template v-else-if="serviceHistory">
      <!-- B. Service Summary Panel -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Total Services</p>
          <p class="text-3xl font-bold" style="color: var(--text-primary);">
            {{ serviceHistory.summary?.total_services || 0 }}
          </p>
        </Card>
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Avg Interval</p>
          <p class="text-3xl font-bold" style="color: var(--text-primary);">
            {{ serviceHistory.summary?.avg_interval_days || 0 }}
            <span class="text-sm font-normal" style="color: var(--text-muted);">days</span>
          </p>
        </Card>
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Last Service</p>
          <p class="text-lg font-bold" style="color: var(--text-primary);">
            {{ formatDate(serviceHistory.summary?.last_service_date) }}
          </p>
        </Card>
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Next Expected</p>
          <p class="text-lg font-bold" style="color: var(--text-primary);">
            {{ formatDate(serviceHistory.summary?.next_expected) }}
          </p>
        </Card>
      </div>

      <!-- A. Service Timeline -->
      <Card>
        <h3 class="text-lg font-semibold mb-6" style="color: var(--text-primary);">
          <LucideHistory class="inline size-5 mr-2" />
          Service Timeline
        </h3>

        <div v-if="serviceHistory.timeline?.length" class="relative">
          <!-- Timeline line -->
          <div class="absolute left-6 top-0 bottom-0 w-0.5" style="background-color: var(--border-color);"></div>

          <!-- Timeline entries -->
          <div v-for="(entry, idx) in serviceHistory.timeline" :key="idx" class="relative pl-16 pb-8 last:pb-0">
            <!-- Timeline dot -->
            <div 
              class="absolute left-4 w-5 h-5 rounded-full border-2 flex items-center justify-center"
              style="background-color: var(--bg-secondary); border-color: var(--border-color);"
            >
              <LucideWrench class="size-3" style="color: var(--text-muted);" />
            </div>

            <!-- Entry card -->
            <div class="p-4 rounded-lg" style="background-color: var(--bg-tertiary);">
              <div class="flex items-start justify-between mb-2">
                <div>
                  <div class="flex items-center gap-2 mb-1">
                    <span 
                      :class="['px-2 py-0.5 rounded text-xs font-medium', serviceTypeColors[entry.service_type] || serviceTypeColors['Corrective']]"
                    >
                      {{ entry.service_type }}
                    </span>
                    <span class="text-xs" style="color: var(--text-muted);">{{ entry.date }}</span>
                  </div>
                  <p class="text-sm font-medium" style="color: var(--text-primary);">{{ entry.summary }}</p>
                </div>
                <RouterLink 
                  v-if="entry.linked_work_order"
                  :to="`/repair-orders/${entry.linked_work_order}`"
                  class="flex items-center gap-1 text-xs hover:underline"
                  style="color: var(--text-muted);"
                >
                  {{ entry.linked_work_order }}
                  <LucideExternalLink class="size-3" />
                </RouterLink>
              </div>

              <div class="flex flex-wrap items-center gap-4 text-xs" style="color: var(--text-muted);">
                <span v-if="entry.performed_by" class="flex items-center gap-1">
                  <LucideUser class="size-3" />
                  {{ entry.performed_by }}
                </span>
                <span v-if="entry.cost" class="flex items-center gap-1">
                  <LucideDollarSign class="size-3" />
                  {{ formatCurrency(entry.cost) }}
                </span>
                <span v-if="entry.odometer" class="flex items-center gap-1">
                  <LucideGauge class="size-3" />
                  {{ entry.odometer?.toLocaleString() }} km
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-12">
          <LucideHistory class="size-12 mx-auto mb-4" style="color: var(--text-muted);" />
          <h3 class="text-lg font-semibold mb-2" style="color: var(--text-primary);">No Service History</h3>
          <p class="text-sm" style="color: var(--text-muted);">This vehicle has no completed services recorded.</p>
        </div>
      </Card>
    </template>
  </div>
</template>
