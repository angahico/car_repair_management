<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideArrowLeft,
  LucideSave,
  LucideLoader2,
  LucideSearch,
  LucideX,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button } from '@/components/ui'

const router = useRouter()
const { t } = useI18n()

const isSaving = ref(false)
const error = ref('')

const form = ref({
  subject: '',
  vehicle: '',
  severity: '',
  category: '',
  source: 'Driver Report',
  description: '',
})

const severities = ['Low', 'Medium', 'High', 'Critical']
const categories = ['Mechanical', 'Electrical', 'Body/Paint', 'Interior', 'Safety', 'Compliance', 'Other']
const sources = ['Inspection', 'Driver Report', 'Mechanic', 'Customer', 'Sensor', 'Other']

// Vehicle search state
const vehicleSearchOpen = ref(false)
const vehicleSearchQuery = ref('')
const vehicleDisplay = ref('')
const vehicleOptions = ref<{ name: string; license_plate: string; make: string; model: string }[]>([])
const vehicleLoading = ref(false)
const vehicleDropdownRef = ref<HTMLDivElement>()

async function searchVehicles(txt: string = '') {
  vehicleLoading.value = true
  try {
    vehicleOptions.value = await apiCall<any[]>(
      'car_repair_management.api.issue.search_vehicles',
      { txt, limit_page_length: 20 },
    )
  } catch {
    vehicleOptions.value = []
  } finally {
    vehicleLoading.value = false
  }
}

function handleVehicleFocus() {
  vehicleSearchOpen.value = true
  searchVehicles(vehicleSearchQuery.value)
}

function handleVehicleInput(e: Event) {
  const target = e.target as HTMLInputElement
  vehicleSearchQuery.value = target.value
  vehicleDisplay.value = target.value
  searchVehicles(target.value)
}

function selectVehicle(v: typeof vehicleOptions.value[0]) {
  form.value.vehicle = v.name
  vehicleDisplay.value = v.license_plate || v.name
  vehicleSearchOpen.value = false
  vehicleSearchQuery.value = ''
}

function clearVehicle() {
  form.value.vehicle = ''
  vehicleDisplay.value = ''
  vehicleSearchQuery.value = ''
  vehicleOptions.value = []
}

function handleVehicleClickOutside(e: MouseEvent) {
  if (vehicleDropdownRef.value && !vehicleDropdownRef.value.contains(e.target as Node)) {
    vehicleSearchOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleVehicleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleVehicleClickOutside))

async function handleSubmit() {
  if (!form.value.subject.trim()) {
    error.value = t('issues.subject_required')
    return
  }
  if (!form.value.vehicle) {
    error.value = t('issues.vehicle_required')
    return
  }

  isSaving.value = true
  error.value = ''
  try {
    const result = await apiCall<{ name: string; workflow_state: string }>(
      'car_repair_management.api.issue.create_issue',
      {
        subject: form.value.subject,
        vehicle: form.value.vehicle,
        severity: form.value.severity || undefined,
        category: form.value.category || undefined,
        source: form.value.source || undefined,
        description: form.value.description || undefined,
      },
    )
    router.push(`/issues/${result.name}`)
  } catch (e: any) {
    error.value = e.message || t('common.failed_to_save')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-4">
      <Button variant="outline" @click="router.push('/issues')">
        <LucideArrowLeft class="size-4" />
      </Button>
      <div>
        <h1 class="text-page-title">{{ $t('issues.new_issue') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">{{ $t('issues.new_issue_desc') }}</p>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="p-3 rounded-lg text-sm" style="background: rgba(239, 68, 68, 0.1); color: #ef4444;">
      {{ error }}
    </div>

    <!-- Form -->
    <Card>
      <div class="space-y-4">
        <!-- Subject -->
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">
            {{ $t('issues.subject') }} <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.subject"
            type="text"
            class="w-full h-10 px-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
            style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            :placeholder="$t('issues.subject_placeholder')"
          />
        </div>

        <!-- Vehicle -->
        <div class="relative" ref="vehicleDropdownRef">
          <label class="block text-sm font-medium mb-1" style="color: var(--text-primary);">
            {{ $t('common.vehicle') }} <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4" style="color: var(--text-muted);" />
            <input
              type="text"
              :value="vehicleDisplay"
              :placeholder="$t('issues.search_vehicle')"
              class="w-full h-10 pl-10 pr-10 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
              @focus="handleVehicleFocus"
              @input="handleVehicleInput"
            />
            <button
              v-if="vehicleDisplay"
              type="button"
              class="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded hover:opacity-70"
              style="color: var(--text-muted);"
              @click.stop="clearVehicle"
            >
              <LucideX class="size-4" />
            </button>
          </div>
          <div
            v-if="vehicleSearchOpen"
            class="absolute z-50 w-full mt-1 rounded-lg border shadow-lg overflow-hidden"
            style="background-color: var(--bg-elevated); border-color: var(--border-color);"
          >
            <div v-if="vehicleLoading" class="flex items-center justify-center py-4">
              <LucideLoader2 class="size-5 animate-spin" style="color: var(--text-muted);" />
            </div>
            <div v-else-if="vehicleOptions.length === 0" class="py-4 text-center text-sm" style="color: var(--text-muted);">
              No vehicles found
            </div>
            <ul v-else class="max-h-60 overflow-y-auto">
              <li
                v-for="v in vehicleOptions"
                :key="v.name"
                class="px-4 py-2.5 cursor-pointer transition-colors hover:opacity-80"
                :style="{ backgroundColor: v.name === form.vehicle ? 'var(--bg-tertiary)' : 'transparent' }"
                @click="selectVehicle(v)"
              >
                <p class="text-sm font-medium" style="color: var(--text-primary);">{{ v.license_plate || v.name }}</p>
                <p class="text-xs" style="color: var(--text-muted);">{{ [v.make, v.model].filter(Boolean).join(' ') || v.name }}</p>
              </li>
            </ul>
          </div>
        </div>

        <!-- Severity + Category row -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">{{ $t('inspections.severity') }}</label>
            <select
              v-model="form.severity"
              class="w-full h-10 px-3 rounded-lg border"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            >
              <option value="">{{ $t('common.select') }}</option>
              <option v-for="s in severities" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">{{ $t('issues.category') }}</label>
            <select
              v-model="form.category"
              class="w-full h-10 px-3 rounded-lg border"
              style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            >
              <option value="">{{ $t('common.select') }}</option>
              <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>

        <!-- Source -->
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">{{ $t('issues.source') }}</label>
          <select
            v-model="form.source"
            class="w-full h-10 px-3 rounded-lg border"
            style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
          >
            <option v-for="s in sources" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

        <!-- Description -->
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">{{ $t('common.description') }}</label>
          <textarea
            v-model="form.description"
            rows="4"
            class="w-full px-3 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-gray-400"
            style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
            :placeholder="$t('issues.description_placeholder')"
          />
        </div>
      </div>
    </Card>

    <!-- Submit Button -->
    <div class="flex justify-end gap-3">
      <Button variant="outline" @click="router.push('/issues')">{{ $t('common.cancel') }}</Button>
      <Button variant="primary" :loading="isSaving" @click="handleSubmit">
        <LucideSave class="size-4" />
        {{ $t('issues.create_issue') }}
      </Button>
    </div>
  </div>
</template>
