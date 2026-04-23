<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import {
  LucideUser,
  LucideClock,
  LucideMessageSquare,
  LucideEdit,
  LucidePlus,
  LucideInfo,
  LucideLoader2,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card } from '@/components/ui'

const props = defineProps<{
  doctype: string
  name: string
}>()

interface ActivityEntry {
  type: string
  timestamp: string
  user: string
  user_fullname: string
  content: string
  details?: Record<string, any>
}

const activities = ref<ActivityEntry[]>([])
const isLoading = ref(true)

const typeIcons: Record<string, any> = {
  created: LucidePlus,
  comment: LucideMessageSquare,
  info: LucideInfo,
  field_change: LucideEdit,
  workflow: LucideInfo,
  assignment: LucideUser,
  default: LucideClock,
}

const typeColors: Record<string, string> = {
  created: 'var(--accent, #3b82f6)',
  comment: 'var(--text-muted)',
  info: 'var(--text-muted)',
  field_change: 'var(--text-muted)',
  workflow: 'var(--accent, #3b82f6)',
  default: 'var(--text-muted)',
}

function getIcon(type: string) {
  return typeIcons[type] || typeIcons.default
}

function getColor(type: string) {
  return typeColors[type] || typeColors.default
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—'
  const parts = dateStr.substring(0, 10).split('-')
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
    const time = dateStr.substring(11, 16)
    return `${d.toLocaleDateString()} ${time || ''}`
  }
  return dateStr
}

async function loadActivities() {
  isLoading.value = true
  try {
    const result = await apiCall<ActivityEntry[]>(
      'car_repair_management.api.activity.get_document_activity',
      { doctype: props.doctype, name: props.name, limit: 50 },
    )
    activities.value = result || []
  } catch (e) {
    console.warn('Failed to load activity', e)
    activities.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(loadActivities)

watch(() => [props.doctype, props.name], loadActivities)
</script>

<template>
  <Card>
    <div class="flex items-center gap-2 mb-4">
      <LucideClock class="size-5" style="color: var(--text-muted)" />
      <h2 class="text-section-title">Activity Timeline</h2>
    </div>

    <div v-if="isLoading" class="flex items-center justify-center py-8">
      <LucideLoader2 class="size-5 animate-spin" style="color: var(--text-muted)" />
    </div>

    <div v-else-if="activities.length === 0" class="text-sm py-4" style="color: var(--text-muted)">
      No activity recorded
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="(activity, idx) in activities"
        :key="idx"
        class="flex items-start gap-3 p-3 rounded-lg"
        style="background: var(--bg-tertiary);"
      >
        <component
          :is="getIcon(activity.type)"
          class="size-4 mt-0.5 shrink-0"
          :style="{ color: getColor(activity.type) }"
        />
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-sm font-medium" style="color: var(--text-primary)">
              {{ activity.user_fullname || activity.user }}
            </span>
            <span class="text-xs" style="color: var(--text-muted)">
              {{ formatDateTime(activity.timestamp) }}
            </span>
          </div>
          <p class="text-sm mt-0.5" style="color: var(--text-secondary)">
            {{ activity.content }}
          </p>
        </div>
      </div>
    </div>
  </Card>
</template>
