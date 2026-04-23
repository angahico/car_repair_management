<script setup lang="ts">
import { LucideLayoutGrid, LucideList, LucideTable } from 'lucide-vue-next'

type ViewMode = 'table' | 'card' | 'list'

interface Props {
  modelValue: ViewMode
  showTable?: boolean
  showCard?: boolean
  showList?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showTable: true,
  showCard: true,
  showList: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: ViewMode]
}>()

const viewOptions = [
  { id: 'table' as ViewMode, icon: LucideTable, label: 'Table', show: () => props.showTable },
  { id: 'card' as ViewMode, icon: LucideLayoutGrid, label: 'Cards', show: () => props.showCard },
  { id: 'list' as ViewMode, icon: LucideList, label: 'List', show: () => props.showList },
]
</script>

<template>
  <div class="flex items-center rounded-lg border overflow-hidden" style="border-color: var(--border-color);">
    <button
      v-for="option in viewOptions.filter(o => o.show())"
      :key="option.id"
      @click="emit('update:modelValue', option.id)"
      :class="[
        'flex items-center justify-center p-2 transition-colors',
        modelValue === option.id ? 'bg-opacity-100' : 'hover:opacity-80',
      ]"
      :style="{
        backgroundColor: modelValue === option.id ? 'var(--bg-tertiary)' : 'transparent',
        color: modelValue === option.id ? 'var(--text-primary)' : 'var(--text-muted)',
      }"
      :title="option.label"
    >
      <component :is="option.icon" class="size-4" />
    </button>
  </div>
</template>
