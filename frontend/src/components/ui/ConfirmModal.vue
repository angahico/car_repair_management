<script setup lang="ts">
import { ref } from 'vue'
import { LucideAlertTriangle, LucideX } from 'lucide-vue-next'
import Card from './Card.vue'
import Button from './Button.vue'

const props = withDefaults(defineProps<{
  title?: string
  message?: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'warning' | 'default'
  showReason?: boolean
  reasonLabel?: string
  loading?: boolean
}>(), {
  title: 'Confirm Action',
  message: 'Are you sure you want to proceed?',
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  variant: 'danger',
  showReason: false,
  reasonLabel: 'Reason (optional)',
  loading: false,
})

const emit = defineEmits<{
  confirm: [reason: string]
  cancel: []
}>()

const reason = ref('')

function handleConfirm() {
  emit('confirm', reason.value)
}

function handleCancel() {
  reason.value = ''
  emit('cancel')
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      style="background: rgba(0, 0, 0, 0.4);"
      @click.self="handleCancel"
    >
      <Card class="w-full max-w-md">
        <div class="flex items-start gap-3 mb-4">
          <div
            class="p-2 rounded-lg shrink-0"
            :style="{
              backgroundColor: variant === 'danger' ? 'var(--bg-danger, #fef2f2)' : variant === 'warning' ? 'var(--bg-warning, #fffbeb)' : 'var(--bg-tertiary)',
            }"
          >
            <LucideAlertTriangle
              class="size-5"
              :style="{
                color: variant === 'danger' ? 'var(--text-danger, #dc2626)' : variant === 'warning' ? 'var(--text-warning, #d97706)' : 'var(--text-muted)',
              }"
            />
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="text-base font-semibold" style="color: var(--text-primary);">{{ title }}</h3>
            <p class="text-sm mt-1" style="color: var(--text-muted);">{{ message }}</p>
          </div>
          <button @click="handleCancel" class="p-1 rounded shrink-0" style="color: var(--text-muted);">
            <LucideX class="size-4" />
          </button>
        </div>

        <div v-if="showReason" class="mb-4">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">{{ reasonLabel }}</label>
          <textarea
            v-model="reason"
            rows="2"
            class="w-full px-3 py-2 text-sm rounded border resize-none"
            style="background: var(--bg-tertiary); color: var(--text-primary); border-color: var(--border-color);"
            placeholder="Enter a reason..."
          />
        </div>

        <div class="flex justify-end gap-2">
          <Button variant="ghost" size="sm" @click="handleCancel" :disabled="loading">
            {{ cancelLabel }}
          </Button>
          <Button
            :variant="variant === 'danger' ? 'danger' : 'primary'"
            size="sm"
            :loading="loading"
            @click="handleConfirm"
          >
            {{ confirmLabel }}
          </Button>
        </div>
      </Card>
    </div>
  </Teleport>
</template>
