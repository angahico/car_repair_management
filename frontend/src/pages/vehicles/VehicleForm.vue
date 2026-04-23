<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { 
  LucideArrowLeft, 
  LucideSave, 
  LucideLoader2, 
  LucideChevronRight, 
  LucideChevronLeft,
  LucideInfo,
  LucideSettings,
  LucideDollarSign
} from 'lucide-vue-next'
import { apiGet, apiCreate, apiUpdate } from '@/api'
import { Card, Button } from '@/components/ui'

interface Props {
  id?: string
  isNew?: boolean
}

const props = defineProps<Props>()
const router = useRouter()
const { t } = useI18n()

const isLoading = ref(false)
const isSaving = ref(false)
const error = ref('')
const currentStep = ref(1)

const form = ref({
  license_plate: '',
  make: '',
  model: '',
  year: '',
  variant: '',
  color: '',
  chassis_no: '',
  transmission: '',
  fuel_type: '',
  last_odometer: '' as string | number,
  uom: 'Kilometer',
  // New Specification Fields
  acquisition_cost: '' as string | number,
  acquisition_date: '',
  engine_number: '',
  engine_type: '',
  engine_capacity: '' as string | number,
  cylinders: '' as string | number,
  drivetrain: '',
  fuel_tank_capacity: '',
  battery_capacity: '',
  seating_capacity: '' as string | number,
  payload_capacity: '',
  towing_capacity: '',
  gross_vehicle_weight: '',
  vehicle_type: '',
  country_of_origin: '',
  ownership_type: 'Owned',
  registration_authority: '',
  registration_expiry: '',
  insurance_policy: '',
  insurance_expiry: '',
  insurance_company: '',
  insured_value: '' as string | number,
  insurance_start_date: '',
  comprehensive_insurance: '',
  depreciation_method: 'Straight Line',
  depreciation_months: 60 as string | number,
  // Fuel quota fields
  custom_fuel_capacity_liters: '' as string | number,
  custom_km_per_liter: '' as string | number,
  custom_monthly_fuel_quota: '' as string | number,
})

const pageTitle = computed(() => props.isNew ? t('vehicles.new_vehicle') : t('vehicles.edit_vehicle'))

const steps = [
  { id: 1, label: t('vehicles.step_basic'), icon: LucideInfo },
  { id: 2, label: t('vehicles.step_specs'), icon: LucideSettings },
  { id: 3, label: t('vehicles.step_acquisition'), icon: LucideDollarSign },
]

async function loadData() {
  isLoading.value = true
  error.value = ''
  
  try {
    if (props.id && !props.isNew) {
      const data = await apiGet<any>('Vehicle', props.id)
      if (data) {
        form.value = {
          license_plate: data.license_plate || '',
          make: data.make || '',
          model: data.model || '',
          year: data.year || '',
          variant: data.variant || '',
          color: data.color || '',
          chassis_no: data.chassis_no || '',
          transmission: data.transmission || '',
          fuel_type: data.fuel_type || '',
          last_odometer: data.last_odometer ?? '',
          uom: data.uom || 'Kilometer',
          // Extended fields
          acquisition_cost: data.acquisition_cost ?? '',
          acquisition_date: data.acquisition_date || '',
          engine_number: data.engine_number || data.custom_engine_number || '',
          engine_type: data.engine_type || data.custom_engine_type || '',
          engine_capacity: data.engine_capacity ?? data.custom_engine_capacity ?? '',
          cylinders: data.cylinders ?? data.custom_cylinders ?? '',
          drivetrain: data.drivetrain || data.custom_drivetrain || '',
          fuel_tank_capacity: data.fuel_tank_capacity || data.custom_fuel_tank_capacity || '',
          battery_capacity: data.battery_capacity || data.custom_battery_capacity || '',
          seating_capacity: data.seating_capacity ?? data.custom_seating_capacity ?? '',
          payload_capacity: data.payload_capacity || data.custom_payload_capacity || '',
          towing_capacity: data.towing_capacity || data.custom_towing_capacity || '',
          gross_vehicle_weight: data.gross_vehicle_weight || data.custom_gvw || '',
          vehicle_type: data.vehicle_type || data.custom_vehicle_type || '',
          country_of_origin: data.country_of_origin || data.custom_country_of_origin || '',
          ownership_type: data.ownership_type || data.custom_ownership_type || 'Owned',
          registration_authority: data.registration_authority || data.custom_registration_authority || '',
          registration_expiry: data.registration_expiry || data.custom_registration_expiry || '',
          insurance_policy: data.insurance_policy || data.policy_no || '',
          insurance_expiry: data.insurance_expiry || data.end_date || '',
          insurance_company: data.insurance_company || '',
          insured_value: data.insured_value ?? '',
          insurance_start_date: data.insurance_start_date || data.start_date || '',
          comprehensive_insurance: data.comprehensive_insurance || '',
          depreciation_method: data.depreciation_method || 'Straight Line',
          depreciation_months: data.depreciation_months ?? 60,
          custom_fuel_capacity_liters: data.custom_fuel_capacity_liters ?? '',
          custom_km_per_liter: data.custom_km_per_liter ?? '',
          custom_monthly_fuel_quota: data.custom_monthly_fuel_quota ?? '',
        }
      }
    }
  } catch (e: any) {
    error.value = e.message || t('common.failed_to_load')
  } finally {
    isLoading.value = false
  }
}

function nextStep() {
  if (currentStep.value === 1) {
    if (!form.value.license_plate) {
      error.value = t('vehicles.license_plate_required')
      return
    }
  }
  error.value = ''
  if (currentStep.value < 3) currentStep.value++
}

function prevStep() {
  error.value = ''
  if (currentStep.value > 1) currentStep.value--
}

async function handleSubmit() {
  if (!form.value.license_plate) {
    error.value = t('vehicles.license_plate_required')
    currentStep.value = 1
    return
  }
  if (form.value.last_odometer === '' || form.value.last_odometer === null) {
    error.value = t('vehicles.odometer_required')
    currentStep.value = 1
    return
  }
  
  isSaving.value = true
  error.value = ''
  
  try {
    const payload = {
      ...form.value,
      last_odometer: Number(form.value.last_odometer) || 0,
      acquisition_cost: Number(form.value.acquisition_cost) || 0,
      
      // Map to standard or custom fields
      engine_number: form.value.engine_number,
      engine_type: form.value.engine_type,
      engine_capacity: Number(form.value.engine_capacity) || 0,
      cylinders: Number(form.value.cylinders) || 0,
      drivetrain: form.value.drivetrain,
      fuel_tank_capacity: form.value.fuel_tank_capacity,
      battery_capacity: form.value.battery_capacity,
      seating_capacity: Number(form.value.seating_capacity) || 0,
      payload_capacity: form.value.payload_capacity,
      towing_capacity: form.value.towing_capacity,
      gross_vehicle_weight: form.value.gross_vehicle_weight,
      vehicle_type: form.value.vehicle_type,
      country_of_origin: form.value.country_of_origin,
      ownership_type: form.value.ownership_type,
      registration_authority: form.value.registration_authority,
      registration_expiry: form.value.registration_expiry,
      insurance_policy: form.value.insurance_policy,
      insurance_expiry: form.value.insurance_expiry,
      insurance_company: form.value.insurance_company,
      insured_value: Number(form.value.insured_value) || 0,
      insurance_start_date: form.value.insurance_start_date,
      comprehensive_insurance: form.value.comprehensive_insurance,
      depreciation_method: form.value.depreciation_method,
      depreciation_months: Number(form.value.depreciation_months) || 60,
      custom_fuel_capacity_liters: Number(form.value.custom_fuel_capacity_liters) || 0,
      custom_km_per_liter: Number(form.value.custom_km_per_liter) || 0,
      custom_monthly_fuel_quota: form.value.custom_monthly_fuel_quota ? Number(form.value.custom_monthly_fuel_quota) : null,
    }
    
    if (props.isNew) {
      const result = await apiCreate<{ name: string }>('Vehicle', payload)
      router.push(`/vehicles/${result.name}`)
    } else if (props.id) {
      await apiUpdate('Vehicle', props.id, payload)
      router.push(`/vehicles/${props.id}`)
    }
  } catch (e: any) {
    error.value = e.message || t('common.failed_to_save')
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
      
      <div v-if="currentStep === 3" class="flex items-center gap-2">
        <Button variant="primary" :disabled="isSaving" @click="handleSubmit">
          <LucideLoader2 v-if="isSaving" class="size-4 animate-spin" />
          <LucideSave v-else class="size-4" />
          {{ isSaving ? $t('common.saving') : $t('common.save') }}
        </Button>
      </div>
    </div>

    <!-- Step Progress -->
    <div class="flex items-center justify-between px-4 py-2 bg-surface-bg border border-default rounded-xl">
      <div 
        v-for="step in steps" 
        :key="step.id"
        class="flex items-center gap-2"
      >
        <div 
          :class="[
            'size-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors',
            currentStep === step.id ? 'bg-accent text-accent-text' : 
            currentStep > step.id ? 'bg-green-500 text-white' : 'bg-surface-tertiary text-ink-muted'
          ]"
        >
          <component :is="step.icon" class="size-4" />
        </div>
        <span 
          class="text-xs font-medium hidden sm:block"
          :class="currentStep === step.id ? 'text-ink' : 'text-ink-muted'"
        >
          {{ step.label }}
        </span>
        <LucideChevronRight v-if="step.id < 3" class="size-4 text-ink-muted mx-2" />
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
        <!-- Step 1: Basic Information -->
        <div v-if="currentStep === 1" class="space-y-6">
          <h2 class="text-xl font-semibold">{{ $t('vehicles.step_basic') }}</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('vehicles.license_plate') }} *</label>
              <input v-model="form.license_plate" type="text" class="form-input" placeholder="ABC-1234" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('vehicles.make') }}</label>
              <input v-model="form.make" type="text" class="form-input" placeholder="Toyota" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('vehicles.model') }}</label>
              <input v-model="form.model" type="text" class="form-input" placeholder="Camry" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('vehicles.year') }}</label>
              <input v-model="form.year" type="number" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('vehicles.variant') }}</label>
              <input v-model="form.variant" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('vehicles.color') }}</label>
              <input v-model="form.color" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('vehicles.chassis_number') }}</label>
              <input v-model="form.chassis_no" type="text" class="form-input" />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-sm font-medium mb-1">{{ $t('vehicles.current_odometer') }} *</label>
                <input v-model="form.last_odometer" type="number" class="form-input" />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">{{ $t('vehicles.odometer_uom') }}</label>
                <select v-model="form.uom" class="form-select">
                  <option value="Kilometer">Kilometer</option>
                  <option value="Mile">Mile</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: Technical Specifications -->
        <div v-if="currentStep === 2" class="space-y-6">
          <h2 class="text-xl font-semibold">{{ $t('vehicles.step_specs') }}</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('vehicles.transmission') }}</label>
              <select v-model="form.transmission" class="form-select">
                <option value="Manual">Manual</option>
                <option value="Automatic">Automatic</option>
                <option value="CVT">CVT</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('vehicles.fuel_type') }}</label>
              <select v-model="form.fuel_type" class="form-select">
                <option value="Petrol">Petrol</option>
                <option value="Diesel">Diesel</option>
                <option value="Electric">Electric</option>
                <option value="Hybrid">Hybrid</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('vehicles.specs_engine_number') || 'Engine Number' }}</label>
              <input v-model="form.engine_number" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Engine Type</label>
              <input v-model="form.engine_type" type="text" class="form-input" placeholder="v6, Inline-4" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Engine Capacity (cc)</label>
              <input v-model="form.engine_capacity" type="number" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Cylinders</label>
              <input v-model="form.cylinders" type="number" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Drivetrain</label>
              <input v-model="form.drivetrain" type="text" class="form-input" placeholder="FWD, RWD, AWD" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Seating Capacity</label>
              <input v-model="form.seating_capacity" type="number" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Fuel Tank Capacity</label>
              <input v-model="form.fuel_tank_capacity" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('fuel.tank_capacity_liters') }}</label>
              <input v-model="form.custom_fuel_capacity_liters" type="number" step="0.1" min="0" class="form-input" placeholder="e.g. 80" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('fuel.km_per_liter') }}</label>
              <input v-model="form.custom_km_per_liter" type="number" step="0.1" min="0" class="form-input" placeholder="e.g. 10" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">{{ $t('fuel.monthly_quota_override') }}</label>
              <input v-model="form.custom_monthly_fuel_quota" type="number" step="1" min="0" class="form-input" placeholder="0 = auto (capacity × 2)" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Battery Capacity</label>
              <input v-model="form.battery_capacity" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Payload Capacity</label>
              <input v-model="form.payload_capacity" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Towing Capacity</label>
              <input v-model="form.towing_capacity" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Gross Vehicle Weight (GVW)</label>
              <input v-model="form.gross_vehicle_weight" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Vehicle Type</label>
              <input v-model="form.vehicle_type" type="text" class="form-input" placeholder="Truck, Sedan, SUV" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Country of Origin</label>
              <input v-model="form.country_of_origin" type="text" class="form-input" />
            </div>
          </div>
        </div>

        <!-- Step 3: Acquisition & Ownership -->
        <div v-if="currentStep === 3" class="space-y-6">
          <h2 class="text-xl font-semibold">{{ $t('vehicles.step_acquisition') }}</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1">Acquisition Cost</label>
              <input v-model="form.acquisition_cost" type="number" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Acquisition Date</label>
              <input v-model="form.acquisition_date" type="date" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Ownership Type</label>
              <select v-model="form.ownership_type" class="form-select">
                <option value="Owned">Owned</option>
                <option value="Leased">Leased</option>
                <option value="Rented">Rented</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Registration Authority</label>
              <input v-model="form.registration_authority" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Registration Expiry</label>
              <input v-model="form.registration_expiry" type="date" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Insurance Policy Ref</label>
              <input v-model="form.insurance_policy" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Insurance Expiry</label>
              <input v-model="form.insurance_expiry" type="date" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Insurance Company</label>
              <input v-model="form.insurance_company" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Insured Value</label>
              <input v-model="form.insured_value" type="number" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Insurance Start Date</label>
              <input v-model="form.insurance_start_date" type="date" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Comprehensive Insurance</label>
              <input v-model="form.comprehensive_insurance" type="text" class="form-input" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Depreciation Method</label>
              <select v-model="form.depreciation_method" class="form-select">
                <option value="Straight Line">Straight Line</option>
                <option value="Double Declining Balance">Double Declining Balance</option>
                <option value="Written Down Value">Written Down Value</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Useful Life (Months)</label>
              <input v-model="form.depreciation_months" type="number" class="form-input" placeholder="60" />
            </div>
          </div>
          <div class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg text-xs leading-relaxed" style="color: var(--text-secondary);">
            <LucideInfo class="size-4 inline mr-1 text-blue-500" />
            Entering acquisition cost and date will automatically create a linked ERPNext Asset for depreciation tracking using the selected method.
          </div>
        </div>

        <!-- Navigation Buttons -->
        <div class="flex items-center justify-between mt-12 pt-6 border-t border-default">
          <Button 
            variant="outline" 
            :disabled="currentStep === 1" 
            @click="prevStep"
          >
            <LucideChevronLeft class="size-4" />
            {{ $t('common.previous') }}
          </Button>
          
          <Button 
            v-if="currentStep < 3"
            variant="primary" 
            @click="nextStep"
          >
            {{ $t('common.next') }}
            <LucideChevronRight class="size-4" />
          </Button>

          <Button 
            v-else
            variant="primary" 
            :disabled="isSaving" 
            @click="handleSubmit"
          >
            <LucideLoader2 v-if="isSaving" class="size-4 animate-spin" />
            <LucideSave v-else class="size-4" />
            {{ isSaving ? $t('common.saving') : $t('common.save') }}
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
