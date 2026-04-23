<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { LucideWrench, LucideRefreshCw } from 'lucide-vue-next'
import { apiList } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState } from '@/components/ui'

const tasks = ref<any[]>([])
const isLoading = ref(true)

async function loadTasks() {
  isLoading.value = true
  try {
    tasks.value = await apiList({
      doctype: 'Task',
      fields: ['name', 'subject', 'status', 'priority', 'project', 'modified'],
      filters: [['project', 'is', 'set']],
      orderBy: 'modified desc',
      limitPageLength: 50,
    })
  } catch (e) {
    console.error('Failed to load tasks', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(loadTasks)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-page-title text-ink">Tasks</h1>
        <p class="text-sm text-ink-muted mt-1">Work tasks from repair orders</p>
      </div>
      <Button variant="outline" @click="loadTasks">
        <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
      </Button>
    </div>

    <Card>
      <template v-if="isLoading">
        <div class="space-y-3"><Skeleton v-for="i in 5" :key="i" height="48px" /></div>
      </template>

      <template v-else-if="tasks.length === 0">
        <EmptyState title="No tasks" description="Tasks are created from repair order operations" />
      </template>

      <div v-else class="divide-y divide-border-light dark:divide-border-dark">
        <a
          v-for="task in tasks"
          :key="task.name"
          :href="`/app/task/${task.name}`"
          target="_blank"
          class="flex items-center justify-between py-3 hover:bg-gray-50 dark:hover:bg-gray-800 -mx-4 px-4 transition-colors"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center">
              <LucideWrench class="size-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p class="text-sm font-medium text-ink">{{ task.subject || task.name }}</p>
              <p class="text-xs text-ink-muted">{{ task.project }}</p>
            </div>
          </div>
          <Badge :variant="task.status === 'Completed' ? 'success' : task.status === 'Working' ? 'primary' : 'default'" size="sm">
            {{ task.status }}
          </Badge>
        </a>
      </div>
    </Card>
  </div>
</template>
