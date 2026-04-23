<script setup lang="ts">
import { LucideInbox } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import Button from './Button.vue'

interface Props {
  title?: string
  description?: string
  actionLabel?: string
  actionRoute?: string
  icon?: any
}

defineProps<Props>()
defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-12 text-center">
    <div class="rounded-full p-4 mb-4" style="background-color: var(--bg-tertiary);">
      <slot name="icon">
        <component :is="icon" v-if="icon" class="size-8" style="color: var(--text-muted);" />
        <LucideInbox v-else class="size-8" style="color: var(--text-muted);" />
      </slot>
    </div>
    <h3 class="text-lg font-semibold mb-1" style="color: var(--text-primary);">
      {{ title || 'No data' }}
    </h3>
    <p v-if="description" class="text-sm max-w-sm mb-4" style="color: var(--text-muted);">
      {{ description }}
    </p>
    <RouterLink v-if="actionLabel && actionRoute" :to="actionRoute">
      <Button variant="primary">
        {{ actionLabel }}
      </Button>
    </RouterLink>
    <Button v-else-if="actionLabel" variant="primary" @click="$emit('action')">
      {{ actionLabel }}
    </Button>
    <slot name="action" />
  </div>
</template>
