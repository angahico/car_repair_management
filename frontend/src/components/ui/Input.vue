<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue?: string | number
  type?: 'text' | 'email' | 'password' | 'number' | 'search' | 'tel'
  placeholder?: string
  disabled?: boolean
  error?: string
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  size: 'md',
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

const sizes = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-3 text-sm',
  lg: 'h-12 px-4 text-base',
}

const inputClasses = computed(() => [
  'w-full rounded-input border bg-surface-card transition-colors',
  'text-ink placeholder:text-ink-faint',
  'focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500',
  'disabled:opacity-50 disabled:cursor-not-allowed',
  props.error
    ? 'border-danger-DEFAULT focus:border-danger-DEFAULT focus:ring-danger-DEFAULT/50'
    : 'border-default',
  sizes[props.size],
])
</script>

<template>
  <div class="space-y-1">
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="inputClasses"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="error" class="text-xs text-danger-DEFAULT">{{ error }}</p>
  </div>
</template>
