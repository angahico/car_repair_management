<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { LucideSearch, LucideX, LucideLoader2 } from 'lucide-vue-next'
import { apiSearchLink } from '@/api'

interface Props {
  modelValue: string
  doctype: string
  label?: string
  placeholder?: string
  required?: boolean
  filters?: Record<string, unknown>
  titleField?: string
}

interface Option {
  value: string
  label: string
  description?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Search...',
  required: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const isOpen = ref(false)
const searchQuery = ref('')
const options = ref<Option[]>([])
const isLoading = ref(false)
const inputRef = ref<HTMLInputElement>()
const dropdownRef = ref<HTMLDivElement>()

const displayValue = ref(props.modelValue || '')

watch(() => props.modelValue, (val) => {
  displayValue.value = val || ''
})

async function search(txt: string = '') {
  isLoading.value = true
  try {
    options.value = await apiSearchLink(props.doctype, txt, props.filters, props.titleField)
  } finally {
    isLoading.value = false
  }
}

function handleFocus() {
  isOpen.value = true
  search(searchQuery.value)
}

function handleInput(e: Event) {
  const target = e.target as HTMLInputElement
  searchQuery.value = target.value
  displayValue.value = target.value
  search(target.value)
}

function selectOption(option: Option) {
  displayValue.value = option.label
  emit('update:modelValue', option.value)
  isOpen.value = false
  searchQuery.value = ''
}

function clear() {
  displayValue.value = ''
  emit('update:modelValue', '')
  searchQuery.value = ''
  options.value = []
}

function handleClickOutside(e: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="relative" ref="dropdownRef">
    <label v-if="label" class="block text-sm font-medium mb-1" style="color: var(--text-primary);">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    
    <div class="relative">
      <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4" style="color: var(--text-muted);" />
      <input
        ref="inputRef"
        type="text"
        :value="displayValue"
        :placeholder="placeholder"
        class="w-full h-10 pl-10 pr-10 rounded-lg border focus:outline-none focus:ring-2 focus:ring-gray-400"
        style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
        @focus="handleFocus"
        @input="handleInput"
      />
      <button
        v-if="displayValue"
        type="button"
        class="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded hover:opacity-70"
        style="color: var(--text-muted);"
        @click.stop="clear"
      >
        <LucideX class="size-4" />
      </button>
    </div>

    <!-- Dropdown -->
    <div
      v-if="isOpen"
      class="absolute z-50 w-full mt-1 rounded-lg border shadow-lg overflow-hidden"
      style="background-color: var(--bg-elevated); border-color: var(--border-color);"
    >
      <div v-if="isLoading" class="flex items-center justify-center py-4">
        <LucideLoader2 class="size-5 animate-spin" style="color: var(--text-muted);" />
      </div>
      
      <div v-else-if="options.length === 0" class="py-4 text-center text-sm" style="color: var(--text-muted);">
        No results found
      </div>
      
      <ul v-else class="max-h-60 overflow-y-auto">
        <li
          v-for="option in options"
          :key="option.value"
          class="px-4 py-2.5 cursor-pointer transition-colors hover:opacity-80"
          :style="{
            backgroundColor: option.value === modelValue ? 'var(--bg-tertiary)' : 'transparent',
          }"
          @click="selectOption(option)"
        >
          <p class="text-sm font-medium" style="color: var(--text-primary);">{{ option.label }}</p>
          <p v-if="option.description" class="text-xs" style="color: var(--text-muted);">{{ option.description }}</p>
        </li>
      </ul>
    </div>
  </div>
</template>
