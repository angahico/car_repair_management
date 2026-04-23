<script setup lang="ts">
interface Tab {
  id: string
  label: string
  badge?: string | number
}

interface Props {
  tabs: Tab[]
  modelValue: string
}

defineProps<Props>()
defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="border-b border-default">
    <nav class="-mb-px flex gap-6" aria-label="Tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="[
          'whitespace-nowrap border-b-2 py-3 px-1 text-sm font-medium transition-colors',
          modelValue === tab.id
            ? 'border-primary-500 text-primary-500'
            : 'border-transparent text-ink-muted hover:text-ink hover:border-gray-300',
        ]"
        @click="$emit('update:modelValue', tab.id)"
      >
        {{ tab.label }}
        <span
          v-if="tab.badge !== undefined"
          :class="[
            'ml-2 rounded-pill px-2 py-0.5 text-xs',
            modelValue === tab.id ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
          ]"
        >
          {{ tab.badge }}
        </span>
      </button>
    </nav>
  </div>
</template>
