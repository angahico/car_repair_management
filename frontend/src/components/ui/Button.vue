<script setup lang="ts">
import { computed } from 'vue'
import { LucideLoader2 } from 'lucide-vue-next'

interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  loading: false,
  disabled: false,
  fullWidth: false,
})

const baseClasses = 'btn inline-flex items-center justify-center font-medium transition-all duration-150 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed'

const sizeClasses = {
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-12 px-6 text-base gap-2.5',
}

const classes = computed(() => {
  return [
    baseClasses,
    sizeClasses[props.size],
    props.fullWidth ? 'w-full' : '',
  ].join(' ')
})

const variantStyles = computed(() => {
  const styles: Record<string, Record<string, string>> = {
    primary: {
      backgroundColor: 'var(--accent)',
      color: 'var(--accent-text)',
    },
    secondary: {
      backgroundColor: 'var(--bg-tertiary)',
      color: 'var(--text-primary)',
      border: '1px solid var(--border-color)',
    },
    ghost: {
      backgroundColor: 'transparent',
      color: 'var(--text-primary)',
    },
    danger: {
      backgroundColor: '#ef4444',
      color: '#ffffff',
    },
    outline: {
      backgroundColor: 'transparent',
      color: 'var(--text-primary)',
      border: '1px solid var(--border-color)',
    },
  }
  return styles[props.variant] || styles.primary
})
</script>

<template>
  <button :class="classes" :style="variantStyles" :disabled="disabled || loading">
    <LucideLoader2 v-if="loading" class="size-4 animate-spin" />
    <slot />
  </button>
</template>
