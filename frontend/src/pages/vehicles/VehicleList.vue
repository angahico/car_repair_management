<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucidePlus,
  LucideSearch,
  LucideCar,
  LucideRefreshCw,
  LucideEye,
} from 'lucide-vue-next'
import { apiList, apiGetCount } from '@/api'
import { Card, Button, Skeleton, EmptyState, ViewToggle } from '@/components/ui'

type ViewMode = 'table' | 'card'

const { t } = useI18n()
const router = useRouter()

const vehicles = ref<any[]>([])
const isLoading = ref(true)
const searchQuery = ref('')
const viewMode = ref<ViewMode>('card')
const pagination = ref({ page: 1, pageSize: 20, total: 0 })

async function loadVehicles() {
  isLoading.value = true
  try {
    const [data, count] = await Promise.all([
      apiList({
        doctype: 'Vehicle',
        fields: ['name', 'license_plate', 'make', 'model', 'year', 'variant', 'transmission', 'fuel_type', 'modified'],
        orderBy: 'modified desc',
        limitStart: (pagination.value.page - 1) * pagination.value.pageSize,
        limitPageLength: pagination.value.pageSize,
      }),
      apiGetCount('Vehicle'),
    ])
    vehicles.value = data
    pagination.value.total = count
  } catch (e) {
    console.error('Failed to load vehicles', e)
  } finally {
    isLoading.value = false
  }
}

function handlePageChange(newPage: number) {
  pagination.value.page = newPage
  loadVehicles()
}

const totalPages = computed(() => Math.ceil(pagination.value.total / pagination.value.pageSize))

onMounted(loadVehicles)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-page-title" style="color: var(--text-primary);">{{ $t('vehicles.title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted);">{{ $t('vehicles.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <Button variant="outline" @click="loadVehicles">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
        <RouterLink to="/vehicles/new">
          <Button variant="primary">
            <LucidePlus class="size-4" />
            {{ $t('vehicles.add_vehicle') }}
          </Button>
        </RouterLink>
      </div>
    </div>

    <!-- Search & View Toggle -->
    <div class="flex flex-col sm:flex-row gap-4">
      <div class="relative flex-1 max-w-md">
        <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4" style="color: var(--text-muted);" />
        <input
          v-model="searchQuery"
          type="search"
          :placeholder="$t('vehicles.search_placeholder')"
          class="w-full h-10 pl-10 pr-4 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
          style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
        />
      </div>
      <ViewToggle v-model="viewMode" />
    </div>

    <!-- Table View -->
    <Card v-if="viewMode === 'table'" padding="none">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b" style="background-color: var(--bg-tertiary); border-color: var(--border-color);">
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicles.vehicle') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicles.license_plate') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicles.make_model') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicles.year') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicles.transmission') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicles.modified') }}</th>
              <th class="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y" style="border-color: var(--border-color);">
            <template v-if="isLoading">
              <tr v-for="i in 5" :key="i">
                <td class="px-4 py-4" colspan="7"><Skeleton height="20px" /></td>
              </tr>
            </template>

            <tr v-else-if="vehicles.length === 0">
              <td colspan="7" class="px-4 py-8">
                <EmptyState :title="$t('vehicles.no_vehicles')" :description="$t('vehicles.no_vehicles_desc')" :action-label="$t('vehicles.add_vehicle')" action-route="/vehicles/new" />
              </td>
            </tr>

            <tr
              v-else
              v-for="vehicle in vehicles"
              :key="vehicle.name"
              class="transition-colors cursor-pointer hover:opacity-80"
              @click="router.push(`/vehicles/${vehicle.name}`)"
            >
              <td class="px-4 py-4">
                <span class="text-sm font-medium" style="color: var(--text-primary);">{{ vehicle.name }}</span>
              </td>
              <td class="px-4 py-4 text-sm font-medium" style="color: var(--accent);">
                {{ vehicle.license_plate || '-' }}
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-primary);">
                {{ [vehicle.make, vehicle.model].filter(Boolean).join(' ') || '-' }}
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-primary);">
                {{ vehicle.year || '-' }}
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-muted);">
                {{ vehicle.transmission || '-' }}
              </td>
              <td class="px-4 py-4 text-sm" style="color: var(--text-muted);">
                {{ new Date(vehicle.modified).toLocaleDateString() }}
              </td>
              <td class="px-4 py-4 text-right" @click.stop>
                <RouterLink :to="`/vehicles/${vehicle.name}`">
                  <Button variant="ghost" size="sm"><LucideEye class="size-4" /></Button>
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!isLoading && vehicles.length > 0" class="flex items-center justify-between px-4 py-3 border-t" style="border-color: var(--border-color);">
        <p class="text-sm" style="color: var(--text-muted);">
          {{ $t('common.showing') }} {{ (pagination.page - 1) * pagination.pageSize + 1 }} to {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} {{ $t('common.of') }} {{ pagination.total }}
        </p>
        <div class="flex gap-2">
          <Button variant="outline" size="sm" :disabled="pagination.page === 1" @click="handlePageChange(pagination.page - 1)">{{ $t('common.previous') }}</Button>
          <Button variant="outline" size="sm" :disabled="pagination.page >= totalPages" @click="handlePageChange(pagination.page + 1)">{{ $t('common.next') }}</Button>
        </div>
      </div>
    </Card>

    <!-- Card View -->
    <template v-else-if="viewMode === 'card'">
      <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <Card v-for="i in 8" :key="i"><Skeleton height="120px" /></Card>
      </div>

      <Card v-else-if="vehicles.length === 0">
        <EmptyState :title="$t('vehicles.no_vehicles')" :description="$t('vehicles.no_vehicles_desc')" :action-label="$t('vehicles.add_vehicle')" action-route="/vehicles/new" />
      </Card>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <RouterLink v-for="vehicle in vehicles" :key="vehicle.name" :to="`/vehicles/${vehicle.name}`">
          <Card hoverable>
            <div class="flex items-start gap-3">
              <div class="w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0" style="background-color: var(--bg-tertiary);">
                <LucideCar class="size-6" style="color: var(--text-secondary);" />
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium truncate" style="color: var(--text-primary);">
                  {{ vehicle.name }}
                </p>
                <p class="text-xs" style="color: var(--text-muted);">
                  {{ [vehicle.year, vehicle.make, vehicle.model].filter(Boolean).join(' ') || 'No details' }}
                </p>
                <p v-if="vehicle.license_plate" class="text-xs font-medium mt-1" style="color: var(--accent);">
                  {{ vehicle.license_plate }}
                </p>
              </div>
            </div>
          </Card>
        </RouterLink>
      </div>

      <div v-if="!isLoading && vehicles.length > 0" class="flex items-center justify-between">
        <p class="text-sm" style="color: var(--text-muted);">
          {{ $t('common.showing') }} {{ (pagination.page - 1) * pagination.pageSize + 1 }} to {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} {{ $t('common.of') }} {{ pagination.total }}
        </p>
        <div class="flex gap-2">
          <Button variant="outline" size="sm" :disabled="pagination.page === 1" @click="handlePageChange(pagination.page - 1)">{{ $t('common.previous') }}</Button>
          <Button variant="outline" size="sm" :disabled="pagination.page >= totalPages" @click="handlePageChange(pagination.page + 1)">{{ $t('common.next') }}</Button>
        </div>
      </div>
    </template>
  </div>
</template>
