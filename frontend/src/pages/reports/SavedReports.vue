<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import {
  LucideArrowLeft,
  LucideBookmark,
  LucideSearch,
  LucideExternalLink,
  LucideCopy,
  LucideTrash2,
} from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, Input, ConfirmModal } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface SavedReport {
  name: string
  title: string
  report_id: string
  report_title: string
  category: string
  report_type: string
  filters_json: string
  date_from: string
  date_to: string
  shared_with: string
  last_run: string
  owner: string
  creation: string
  modified: string
}

interface SavedReportsResponse {
  reports: SavedReport[]
  total: number
}

const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const reports = ref<SavedReport[]>([])
const total = ref(0)
const search = ref('')
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const showDeleteConfirm = ref(false)
const deleteTarget = ref<SavedReport | null>(null)
const deleteLoading = ref(false)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const TYPE_VARIANTS: Record<string, StatusVariant> = {
  Chart: 'info',
  Table: 'default',
  KPI: 'success',
  Pivot: 'warning',
  Dashboard: 'primary',
}

function onSearchInput(val: string | number) {
  search.value = String(val)
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => loadData(), 300)
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function showMessage(text: string, type: 'success' | 'error') {
  message.value = text
  messageType.value = type
  setTimeout(() => { message.value = '' }, 4000)
}

async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {}
    if (search.value) args.search = search.value

    const data = await apiCall<SavedReportsResponse>(
      'car_repair_management.api.reports.get_saved_reports',
      args,
    )
    reports.value = data.reports
    total.value = data.total
  } catch (e) {
    console.warn('Failed to load saved reports', e)
  } finally {
    isLoading.value = false
  }
}

async function handleDuplicate(report: SavedReport) {
  try {
    const res = await apiCall<{ name: string; title: string }>(
      'car_repair_management.api.reports.duplicate_saved_report',
      { name: report.name },
    )
    showMessage(`Duplicated as "${res.title}"`, 'success')
    await loadData()
  } catch (e: any) {
    showMessage(e?.message || 'Failed to duplicate report', 'error')
  }
}

function promptDelete(report: SavedReport) {
  deleteTarget.value = report
  showDeleteConfirm.value = true
}

async function handleDelete(reason: string) {
  if (!deleteTarget.value) return
  deleteLoading.value = true
  try {
    await apiCall('car_repair_management.api.reports.delete_saved_report', { name: deleteTarget.value.name })
    showMessage(`"${deleteTarget.value.title}" deleted successfully`, 'success')
    showDeleteConfirm.value = false
    deleteTarget.value = null
    await loadData()
  } catch (e: any) {
    showMessage(e?.message || 'Failed to delete report', 'error')
  } finally {
    deleteLoading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-3">
      <RouterLink to="/reports">
        <Button variant="ghost" size="sm">
          <LucideArrowLeft class="size-4" />
        </Button>
      </RouterLink>
      <div>
        <h1 class="text-page-title" style="color: var(--text-primary)">{{ $t('reports.saved') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">
          Manage your saved report variants with custom filters
        </p>
      </div>
    </div>

    <!-- Message Banner -->
    <div
      v-if="message"
      class="px-4 py-3 rounded text-sm font-medium"
      :style="{
        backgroundColor: messageType === 'success' ? 'var(--bg-success, #ecfdf5)' : 'var(--bg-danger, #fef2f2)',
        color: messageType === 'success' ? 'var(--text-success, #065f46)' : 'var(--text-danger, #991b1b)',
      }"
    >
      {{ message }}
    </div>

    <!-- Search Bar -->
    <Card>
      <div class="flex items-end gap-3">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('common.search') }}</label>
          <Input
            :model-value="search"
            type="search"
            placeholder="Search saved reports..."
            size="md"
            @update:model-value="onSearchInput"
          />
        </div>
      </div>
    </Card>

    <!-- Results Count -->
    <p v-if="!isLoading" class="text-xs" style="color: var(--text-muted)">
      {{ total }} saved report{{ total !== 1 ? 's' : '' }} found
    </p>

    <!-- Table -->
    <Card padding="none">
      <div v-if="isLoading" class="p-4 space-y-3">
        <Skeleton v-for="i in 5" :key="i" height="48px" />
      </div>

      <EmptyState
        v-else-if="reports.length === 0"
        :icon="LucideBookmark"
        title="No Saved Reports"
        :description="
          search
            ? 'No saved reports match your search. Try a different term.'
            : 'Save report variants with custom filters and layouts. Your saved reports will appear here.'
        "
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm" style="color: var(--text-primary)">
          <thead>
            <tr class="border-b" style="border-color: var(--border-subtle)">
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Saved Report</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Based On</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Category</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Type</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Owner</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Last Run</th>
              <th class="text-right px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">{{ $t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in reports"
              :key="r.name"
              class="border-b cursor-pointer transition-colors"
              style="border-color: var(--border-subtle)"
              @click="router.push(`/reports/view/${r.report_id}`)"
              @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
            >
              <td class="px-4 py-3 font-medium whitespace-nowrap">
                <RouterLink
                  :to="`/reports/view/${r.report_id}`"
                  style="color: var(--accent)"
                  class="hover:underline"
                  @click.stop
                >
                  {{ r.title }}
                </RouterLink>
              </td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">
                {{ r.report_title || '—' }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                {{ r.category || '—' }}
              </td>
              <td class="px-4 py-3">
                <Badge v-if="r.report_type" :variant="TYPE_VARIANTS[r.report_type] || 'default'" size="sm">
                  {{ r.report_type }}
                </Badge>
                <span v-else style="color: var(--text-muted)">—</span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">
                {{ r.owner || '—' }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">
                {{ formatDate(r.last_run) }}
              </td>
              <td class="px-4 py-3 text-right whitespace-nowrap" @click.stop>
                <div class="inline-flex items-center gap-1">
                  <RouterLink :to="`/reports/view/${r.report_id}`">
                    <Button variant="ghost" size="sm" title="Open report">
                      <LucideExternalLink class="size-4" />
                    </Button>
                  </RouterLink>
                  <Button variant="ghost" size="sm" title="Duplicate" @click="handleDuplicate(r)">
                    <LucideCopy class="size-4" />
                  </Button>
                  <Button variant="ghost" size="sm" title="Delete" @click="promptDelete(r)">
                    <LucideTrash2 class="size-4" style="color: var(--text-danger, #dc2626)" />
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <ConfirmModal
      v-if="showDeleteConfirm"
      :title="$t('reports.delete_saved_report')"
      :message="`Are you sure you want to delete &quot;${deleteTarget?.title}&quot;? This action cannot be undone.`"
      confirm-label="Delete"
      variant="danger"
      :show-reason="true"
      reason-label="Reason for deletion (optional)"
      :loading="deleteLoading"
      @confirm="handleDelete"
      @cancel="showDeleteConfirm = false; deleteTarget = null"
    />
  </div>
</template>
