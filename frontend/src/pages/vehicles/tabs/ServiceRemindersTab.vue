<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  LucideBell,
  LucidePlus,
  LucideClock,
  LucideX,
  LucideAlarmClockPlus,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Skeleton } from '@/components/ui'

const props = defineProps<{ vehicleId: string }>()

const isLoading = ref(true)
const remindersData = ref<any>(null)
const showAddForm = ref(false)
const isSaving = ref(false)

const newReminder = ref({
  reminder_type: 'General Service',
  description: '',
  remind_at: '',
})

const reminderTypes = [
  'Oil Change',
  'Tire Rotation',
  'Brake Inspection',
  'General Service',
  'Filter Replacement',
  'Fluid Change',
  'Belt/Chain',
  'Other',
]

const statusColors: Record<string, string> = {
  'Overdue': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  'Due': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  'Upcoming': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  'Completed': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  'Notified': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
}

async function loadReminders() {
  isLoading.value = true
  try {
    remindersData.value = await apiCall('car_repair_management.api.vehicle.get_vehicle_reminders_full', {
      vehicle_name: props.vehicleId,
    })
  } catch (e) {
    console.error('Failed to load reminders', e)
  } finally {
    isLoading.value = false
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString()
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}

async function handleAddReminder() {
  if (!newReminder.value.description || !newReminder.value.remind_at) return
  isSaving.value = true
  try {
    await apiCall('car_repair_management.api.vehicle.create_vehicle_reminder', {
      vehicle_name: props.vehicleId,
      remind_at: newReminder.value.remind_at,
      description: newReminder.value.description,
      reminder_type: newReminder.value.reminder_type,
    })
    showAddForm.value = false
    newReminder.value = { reminder_type: 'General Service', description: '', remind_at: '' }
    await loadReminders()
  } catch (e) {
    console.error('Failed to create reminder', e)
  } finally {
    isSaving.value = false
  }
}

async function handleDismiss(reminderName: string) {
  try {
    await apiCall('car_repair_management.api.vehicle.dismiss_vehicle_reminder', {
      reminder_name: reminderName,
    })
    await loadReminders()
  } catch (e) {
    console.error('Failed to dismiss reminder', e)
  }
}

async function handleSnooze(reminderName: string) {
  try {
    await apiCall('car_repair_management.api.vehicle.snooze_vehicle_reminder', {
      reminder_name: reminderName,
      days: 7,
    })
    await loadReminders()
  } catch (e) {
    console.error('Failed to snooze reminder', e)
  }
}

onMounted(loadReminders)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <template v-if="isLoading">
      <div class="grid grid-cols-3 gap-4">
        <Card v-for="i in 3" :key="i"><Skeleton height="80px" /></Card>
      </div>
      <Card><Skeleton height="300px" /></Card>
    </template>

    <template v-else-if="remindersData">
      <!-- Status Counts -->
      <div class="grid grid-cols-3 gap-4">
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Overdue</p>
          <p class="text-3xl font-bold text-red-500">{{ remindersData.counts?.overdue || 0 }}</p>
        </Card>
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Due Soon</p>
          <p class="text-3xl font-bold text-amber-500">{{ remindersData.counts?.due || 0 }}</p>
        </Card>
        <Card class="text-center">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Upcoming</p>
          <p class="text-3xl font-bold" style="color: var(--text-primary);">{{ remindersData.counts?.upcoming || 0 }}</p>
        </Card>
      </div>

      <!-- Active Reminders -->
      <Card>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold" style="color: var(--text-primary);">
            <LucideBell class="inline size-5 mr-2" />
            Active Reminders
          </h3>
          <Button @click="showAddForm = !showAddForm">
            <LucidePlus class="size-4" />
            Add Reminder
          </Button>
        </div>

        <!-- Add Reminder Form -->
        <div
          v-if="showAddForm"
          class="mb-6 p-4 rounded-lg border"
          style="background-color: var(--bg-tertiary); border-color: var(--border-color);"
        >
          <h4 class="text-sm font-semibold mb-4" style="color: var(--text-primary);">New Reminder</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Reminder Type</label>
              <select
                v-model="newReminder.reminder_type"
                class="w-full px-3 py-2 rounded-lg border text-sm"
                style="background-color: var(--bg-secondary); border-color: var(--border-color); color: var(--text-primary);"
              >
                <option v-for="rt in reminderTypes" :key="rt" :value="rt">{{ rt }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Due Date/Time</label>
              <input
                v-model="newReminder.remind_at"
                type="datetime-local"
                class="w-full px-3 py-2 rounded-lg border text-sm"
                style="background-color: var(--bg-secondary); border-color: var(--border-color); color: var(--text-primary);"
              />
            </div>
            <div class="md:col-span-2">
              <label class="block text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Description</label>
              <textarea
                v-model="newReminder.description"
                rows="2"
                placeholder="e.g., Change engine oil and replace oil filter"
                class="w-full px-3 py-2 rounded-lg border text-sm"
                style="background-color: var(--bg-secondary); border-color: var(--border-color); color: var(--text-primary);"
              />
            </div>
          </div>
          <div class="flex justify-end gap-2 mt-4">
            <Button variant="outline" @click="showAddForm = false">Cancel</Button>
            <Button
              @click="handleAddReminder"
              :disabled="isSaving || !newReminder.description || !newReminder.remind_at"
            >
              {{ isSaving ? 'Saving...' : 'Save Reminder' }}
            </Button>
          </div>
        </div>

        <!-- Active Reminders List -->
        <div v-if="remindersData.active?.length" class="space-y-3">
          <div
            v-for="reminder in remindersData.active"
            :key="reminder.name"
            class="flex items-center justify-between p-4 rounded-lg"
            style="background-color: var(--bg-tertiary);"
          >
            <div class="flex items-center gap-4">
              <div
                class="w-10 h-10 rounded-full flex items-center justify-center"
                :class="reminder.status === 'Overdue' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-gray-100 dark:bg-gray-800'"
              >
                <LucideClock
                  class="size-5"
                  :class="reminder.status === 'Overdue' ? 'text-red-600' : ''"
                  :style="reminder.status !== 'Overdue' ? { color: 'var(--text-muted)' } : {}"
                />
              </div>
              <div>
                <p class="text-sm font-medium" style="color: var(--text-primary);">{{ reminder.reminder_type }}</p>
                <p class="text-xs mt-0.5" style="color: var(--text-muted);">{{ reminder.description }}</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="text-right">
                <p class="text-sm" style="color: var(--text-secondary);">Due</p>
                <p class="text-sm font-medium" style="color: var(--text-primary);">{{ formatDateTime(reminder.remind_at) }}</p>
              </div>
              <span :class="['px-2.5 py-1 rounded-full text-xs font-medium', statusColors[reminder.status] || statusColors['Upcoming']]">
                {{ reminder.status }}
              </span>
              <div class="flex items-center gap-1 ml-2">
                <button
                  @click="handleSnooze(reminder.name)"
                  class="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  title="Snooze 7 days"
                >
                  <LucideAlarmClockPlus class="size-4" style="color: var(--text-muted);" />
                </button>
                <button
                  @click="handleDismiss(reminder.name)"
                  class="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  title="Dismiss"
                >
                  <LucideX class="size-4" style="color: var(--text-muted);" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-8">
          <LucideBell class="size-12 mx-auto mb-4" style="color: var(--text-muted);" />
          <p class="text-sm" style="color: var(--text-muted);">No active reminders</p>
        </div>
      </Card>

      <!-- Reminder History -->
      <Card>
        <h3 class="text-lg font-semibold mb-4" style="color: var(--text-primary);">Reminder History</h3>

        <div v-if="remindersData.history?.length" class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Reminder</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Description</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Due At</th>
                <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in remindersData.history"
                :key="item.name"
                class="border-b"
                style="border-color: var(--border-subtle);"
              >
                <td class="px-4 py-3 text-sm font-medium" style="color: var(--text-primary);">{{ item.reminder_type }}</td>
                <td class="px-4 py-3 text-sm" style="color: var(--text-secondary);">{{ item.description }}</td>
                <td class="px-4 py-3 text-sm" style="color: var(--text-secondary);">{{ formatDateTime(item.remind_at) }}</td>
                <td class="px-4 py-3">
                  <span :class="['px-2 py-1 rounded-full text-xs font-medium', statusColors[item.action_taken] || 'bg-gray-100 text-gray-700']">
                    {{ item.action_taken }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="text-center py-8">
          <p class="text-sm" style="color: var(--text-muted);">No reminder history</p>
        </div>
      </Card>
    </template>
  </div>
</template>
