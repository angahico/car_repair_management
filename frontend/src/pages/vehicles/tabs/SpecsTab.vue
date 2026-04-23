<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { 
  LucideChevronDown, 
  LucideChevronUp, 
  LucideEdit, 
  LucideClock, 
  LucideUser,
  LucideSave,
  LucideX,
  LucideLoader2
} from 'lucide-vue-next'
import { apiCall, apiUpdate } from '@/api'
import { Card, Button, Skeleton } from '@/components/ui'

const props = defineProps<{ vehicleId: string }>()
const { t } = useI18n()

const isLoading = ref(true)
const isSaving = ref(false)
const isEditing = ref(false)
const specs = ref<any>(null)
const editForm = ref<any>({})
const expandedSections = ref<Set<string>>(new Set(['vehicle_identity', 'technical_specs', 'capacity_limits', 'ownership_registration']))

const sections = computed(() => [
  { 
    id: 'vehicle_identity', 
    title: t('vehicles.specs_vehicle_identity'),
    fields: [
      { key: 'vin_chassis', label: t('vehicles.specs_vin_chassis'), fieldname: 'chassis_no' },
      { key: 'plate_number', label: t('vehicles.specs_plate_number'), fieldname: 'license_plate' },
      { key: 'engine_number', label: t('vehicles.specs_engine_number'), fieldname: 'engine_number' },
      { key: 'make', label: t('vehicles.make'), fieldname: 'make' },
      { key: 'model', label: t('vehicles.model'), fieldname: 'model' },
      { key: 'variant', label: t('vehicles.specs_trim_variant'), fieldname: 'variant' },
      { key: 'vehicle_type', label: t('vehicles.specs_vehicle_type'), fieldname: 'vehicle_type' },
      { key: 'manufacture_year', label: t('vehicles.specs_manufacture_year'), fieldname: 'year' },
      { key: 'country_of_origin', label: t('vehicles.specs_country_of_origin'), fieldname: 'country_of_origin' },
    ]
  },
  { 
    id: 'technical_specs', 
    title: t('vehicles.specs_technical'),
    fields: [
      { key: 'engine_type', label: t('vehicles.specs_engine_type'), fieldname: 'engine_type' },
      { key: 'engine_capacity', label: t('vehicles.specs_engine_capacity'), fieldname: 'engine_capacity' },
      { key: 'cylinders', label: t('vehicles.specs_cylinders'), fieldname: 'cylinders' },
      { key: 'transmission', label: t('vehicles.transmission'), fieldname: 'transmission' },
      { key: 'drivetrain', label: t('vehicles.specs_drivetrain'), fieldname: 'drivetrain' },
      { key: 'fuel_type', label: t('vehicles.fuel_type'), fieldname: 'fuel_type' },
      { key: 'fuel_tank_capacity', label: t('vehicles.specs_fuel_tank_capacity'), fieldname: 'fuel_tank_capacity' },
      { key: 'battery_capacity', label: t('vehicles.specs_battery_capacity'), fieldname: 'battery_capacity' },
    ]
  },
  { 
    id: 'capacity_limits', 
    title: t('vehicles.specs_capacity_limits'),
    fields: [
      { key: 'seating_capacity', label: t('vehicles.specs_seating_capacity'), fieldname: 'seating_capacity' },
      { key: 'payload_capacity', label: t('vehicles.specs_payload_capacity'), fieldname: 'payload_capacity' },
      { key: 'towing_capacity', label: t('vehicles.specs_towing_capacity'), fieldname: 'towing_capacity' },
      { key: 'gross_vehicle_weight', label: t('vehicles.specs_gvw'), fieldname: 'gross_vehicle_weight' },
    ]
  },
  { 
    id: 'ownership_registration', 
    title: t('vehicles.specs_ownership'),
    fields: [
      { key: 'ownership_type', label: t('vehicles.specs_ownership_type'), fieldname: 'ownership_type' },
      { key: 'registration_authority', label: t('vehicles.specs_registration_authority'), fieldname: 'registration_authority' },
      { key: 'registration_expiry', label: t('vehicles.specs_registration_expiry'), fieldname: 'registration_expiry' },
      { key: 'insurance_policy', label: t('vehicles.specs_insurance_policy'), fieldname: 'insurance_policy' },
      { key: 'insurance_company', label: t('vehicles.specs_insurance_company'), fieldname: 'insurance_company' },
      { key: 'insurance_expiry', label: t('vehicles.specs_insurance_expiry'), fieldname: 'insurance_expiry' },
    ]
  },
])

async function loadSpecs() {
  isLoading.value = true
  try {
    specs.value = await apiCall('car_repair_management.api.vehicle.get_vehicle_specs_full', {
      vehicle_name: props.vehicleId,
    })
  } catch (e) {
    console.error('Failed to load specs', e)
  } finally {
    isLoading.value = false
  }
}

function startEditing() {
  editForm.value = {}
  sections.value.forEach(section => {
    section.fields.forEach(field => {
      editForm.value[field.fieldname] = specs.value[section.id]?.data?.[field.key] || ''
    })
  })
  isEditing.value = true
}

async function saveSpecs() {
  isSaving.value = true
  try {
    await apiUpdate('Vehicle', props.vehicleId, editForm.value)
    await loadSpecs()
    isEditing.value = false
  } catch (e) {
    console.error('Failed to save specs', e)
  } finally {
    isSaving.value = false
  }
}

function toggleSection(id: string) {
  if (expandedSections.value.has(id)) {
    expandedSections.value.delete(id)
  } else {
    expandedSections.value.add(id)
  }
}

function formatValue(value: any): string {
  if (value === null || value === undefined || value === '') return '—'
  return String(value)
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

onMounted(loadSpecs)
</script>

<template>
  <div class="space-y-4">
    <!-- Header with Actions -->
    <div class="flex justify-between items-center mb-2">
      <h2 class="text-lg font-semibold">{{ $t('vehicles.specs') }}</h2>
      <div class="flex gap-2">
        <template v-if="!isEditing">
          <Button variant="outline" size="sm" @click="startEditing">
            <LucideEdit class="size-4" />
            {{ $t('common.edit') }}
          </Button>
        </template>
        <template v-else>
          <Button variant="ghost" size="sm" @click="isEditing = false" :disabled="isSaving">
            <LucideX class="size-4" />
            {{ $t('common.cancel') }}
          </Button>
          <Button variant="primary" size="sm" @click="saveSpecs" :disabled="isSaving">
            <LucideLoader2 v-if="isSaving" class="size-4 animate-spin" />
            <LucideSave v-else class="size-4" />
            {{ isSaving ? $t('common.saving') : $t('common.save') }}
          </Button>
        </template>
      </div>
    </div>

    <!-- Loading State -->
    <template v-if="isLoading">
      <Card v-for="i in 4" :key="i">
        <Skeleton height="150px" />
      </Card>
    </template>

    <!-- Specs Sections -->
    <template v-else-if="specs">
      <Card v-for="section in sections" :key="section.id" padding="none">
        <!-- Section Header -->
        <button
          @click="toggleSection(section.id)"
          class="w-full flex items-center justify-between p-4 text-left transition-colors hover:opacity-80"
        >
          <h3 class="text-lg font-semibold" style="color: var(--text-primary);">
            {{ section.title }}
          </h3>
          <div class="flex items-center gap-3">
            <div v-if="specs[section.id]?.last_updated" class="flex items-center gap-2 text-xs" style="color: var(--text-muted);">
              <LucideClock class="size-3" />
              <span>{{ formatDate(specs[section.id].last_updated) }}</span>
            </div>
            <component 
              :is="expandedSections.has(section.id) ? LucideChevronUp : LucideChevronDown" 
              class="size-5" 
              style="color: var(--text-muted);"
            />
          </div>
        </button>

        <!-- Section Content -->
        <div 
          v-if="expandedSections.has(section.id)"
          class="px-4 pb-4 border-t"
          style="border-color: var(--border-color);"
        >
          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2 pt-4">
            <div 
              v-for="field in section.fields" 
              :key="field.key"
              class="flex flex-col py-2 border-b last:border-0"
              style="border-color: var(--border-subtle);"
            >
              <label class="text-xs font-medium mb-1" style="color: var(--text-muted);">{{ field.label }}</label>
              
              <template v-if="isEditing">
                <input 
                  v-model="editForm[field.fieldname]"
                  type="text"
                  class="w-full h-8 px-2 text-sm rounded border focus:outline-none focus:ring-1 focus:ring-accent"
                  style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
                />
              </template>
              <template v-else>
                <span class="text-sm font-medium" style="color: var(--text-primary);">
                  {{ formatValue(specs[section.id]?.data?.[field.key]) }}
                </span>
              </template>
            </div>
          </div>
        </div>
      </Card>
    </template>

    <Card v-else class="py-12 text-center">
      <p style="color: var(--text-muted);">{{ $t('vehicles.unable_to_load_specs') }}</p>
    </Card>
  </div>
</template>
