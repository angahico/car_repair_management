<script setup lang="ts">
interface Props {
  variant?: 'text' | 'circle' | 'rect'
  width?: string
  height?: string
}

withDefaults(defineProps<Props>(), {
  variant: 'text',
})
</script>

<template>
  <div
    :class="[
      'animate-pulse bg-gray-200 dark:bg-gray-700',
      variant === 'circle' ? 'rounded-full' : 'rounded',
      variant === 'text' ? 'h-4' : '',
    ]"
    :style="{ width, height }"
  />
</template>
