<script setup lang="ts">
interface Props {
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hoverable?: boolean
}

withDefaults(defineProps<Props>(), {
  padding: 'md',
  hoverable: false,
})

const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
}
</script>

<template>
  <div
    :class="[
      'card',
      paddingClasses[padding],
      hoverable ? 'card-hoverable cursor-pointer' : '',
    ]"
  >
    <slot />
  </div>
</template>
