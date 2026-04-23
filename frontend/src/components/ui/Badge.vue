<script setup lang="ts">
import { computed } from 'vue'
import type { StatusVariant } from '@/types'

interface Props {
  variant?: StatusVariant
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'md',
})

const classes = computed(() => {
  const base = 'inline-flex items-center font-medium rounded-pill'
  
  const variants = {
    default: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
    primary: 'bg-primary-100 text-primary-700 dark:bg-primary-500/20 dark:text-primary-400',
    success: 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400',
    warning: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400',
    danger: 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400',
    info: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-500/20 dark:text-cyan-400',
  }
  
  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
  }

  return [base, variants[props.variant], sizes[props.size]].join(' ')
})
</script>

<template>
  <span :class="classes">
    <slot />
  </span>
</template>
