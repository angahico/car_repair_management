<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideArrowLeft,
  LucideSave,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, LinkField } from '@/components/ui'

const router = useRouter()
const { t } = useI18n()

const isSaving = ref(false)
const error = ref('')
const quotaWarning = ref('')

const form = ref({
  vehicle: '',
  liters: 0,
  refuel_date: new Date().toISOString().slice(0, 10),
  odometer_reading: 0,
  cost_per_liter: 0,
  fuel_station: '',
  notes: '',
})

async function handleSubmit() {
  if (!form.value.vehicle) {
    error.value = t('issues.vehicle_required')
    return
  }
  if (!form.value.liters || form.value.liters <= 0) {
    error.value = t('fuel.liters_required')
    return
  }

  isSaving.value = true
  error.value = ''
  quotaWarning.value = ''
  try {
    const result = await apiCall<{ name: string; needs_approval: boolean; approval_status: string }>(
      'car_repair_management.api.fuel.create_refueling_record',
      {
        vehicle: form.value.vehicle,
        liters: form.value.liters,
        refuel_date: form.value.refuel_date || undefined,
        odometer_reading: form.value.odometer_reading || undefined,
        cost_per_liter: form.value.cost_per_liter || undefined,
        fuel_station: form.value.fuel_station || undefined,
        notes: form.value.notes || undefined,
      },
    )
    if (result.needs_approval) {
      quotaWarning.value = t('fuel.over_quota_warning')
    }
    router.push(`/fuel/${result.name}`)
  } catch (e: any) {
    error.value = e.message || t('common.failed_to_save')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <Button variant="outline" @click="router.push('/fuel')">
        <LucideArrowLeft class="size-4" />
      </Button>
      <div>
        <h1 class="text-page-title">{{ $t('fuel.new_record') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">{{ $t('fuel.new_record_desc') }}</p>
      </div>
    </div>

    <div v-if="error" class="p-3 rounded-lg text-sm" style="background: rgba(239, 68, 68, 0.1); color: #ef4444;">{{ error }}</div>

    <Card>
      <div class="space-y-4">
        <LinkField v-model="form.vehicle" doctype="Vehicle" :label="$t('common.vehicle')" title-field="license_plate" :required="true" />

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">{{ $t('fuel.liters') }} <span class="text-red-500">*</span></label>
            <input v-model.number="form.liters" type="number" step="0.1" min="0" class="w-full h-10 px-3 rounded-lg border" style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">{{ $t('fuel.cost_per_liter') }}</label>
            <input v-model.number="form.cost_per_liter" type="number" step="0.01" min="0" class="w-full h-10 px-3 rounded-lg border" style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);" />
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">{{ $t('common.date') }}</label>
            <input v-model="form.refuel_date" type="date" class="w-full h-10 px-3 rounded-lg border" style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">{{ $t('fuel.odometer') }}</label>
            <input v-model.number="form.odometer_reading" type="number" min="0" class="w-full h-10 px-3 rounded-lg border" style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);" />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">{{ $t('fuel.station') }}</label>
          <input v-model="form.fuel_station" type="text" class="w-full h-10 px-3 rounded-lg border" style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);" />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--text-primary)">{{ $t('common.notes') }}</label>
          <textarea v-model="form.notes" rows="3" class="w-full px-3 py-2 rounded-lg border resize-none" style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);" />
        </div>
      </div>
    </Card>

    <div class="flex justify-end gap-3">
      <Button variant="outline" @click="router.push('/fuel')">{{ $t('common.cancel') }}</Button>
      <Button variant="primary" :loading="isSaving" @click="handleSubmit">
        <LucideSave class="size-4" /> {{ $t('fuel.create_record') }}
      </Button>
    </div>
  </div>
</template>
