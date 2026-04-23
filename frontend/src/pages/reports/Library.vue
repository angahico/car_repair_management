<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideArrowLeft,
  LucideSearch,
  LucideFileBarChart,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState, ViewToggle, Input } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface ReportItem {
  id: string
  title: string
  category: string
  report_type: string
  description: string
  module: string
}

interface LibraryResponse {
  reports: ReportItem[]
  total: number
  categories: string[]
}

type ViewMode = 'table' | 'card'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const isLoading = ref(true)
const reports = ref<ReportItem[]>([])
const total = ref(0)
const categories = ref<string[]>([])

const search = ref('')
const category = ref<string>((route.query.category as string) || '')
const reportType = ref('')
const viewMode = ref<ViewMode>('table')

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const REPORT_TYPE_OPTIONS = ['Chart', 'Table', 'Pivot', 'KPI', 'Dashboard']

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
  debounceTimer = setTimeout(() => {
    updateQueryParams()
    loadData()
  }, 300)
}

function onCategoryChange(e: Event) {
  category.value = (e.target as HTMLSelectElement).value
  updateQueryParams()
  loadData()
}

function onTypeChange(e: Event) {
  reportType.value = (e.target as HTMLSelectElement).value
  updateQueryParams()
  loadData()
}

function updateQueryParams() {
  const query: Record<string, string> = {}
  if (category.value) query.category = category.value
  if (reportType.value) query.report_type = reportType.value
  if (search.value) query.search = search.value
  router.replace({ query })
}

async function loadData() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {}
    if (search.value) args.search = search.value
    if (category.value) args.category = category.value
    if (reportType.value) args.report_type = reportType.value

    const data = await apiCall<LibraryResponse>(
      'car_repair_management.api.reports.get_reports_library',
      args,
    )
    reports.value = data.reports
    total.value = data.total
    categories.value = data.categories
  } catch (e) {
    console.warn('Failed to load reports library', e)
  } finally {
    isLoading.value = false
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
        <h1 class="text-page-title" style="color: var(--text-primary)">{{ $t('reports.library') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">
          Browse and search all available reports
        </p>
      </div>
    </div>

    <!-- Control Bar -->
    <Card>
      <div class="flex flex-wrap items-end gap-3">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('common.search') }}</label>
          <Input
            :model-value="search"
            type="search"
            placeholder="Search reports..."
            size="md"
            @update:model-value="onSearchInput"
          />
        </div>

        <div class="min-w-[160px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">{{ $t('issues.category') }}</label>
          <select
            :value="category"
            class="w-full h-10 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @change="onCategoryChange"
          >
            <option value="">{{ $t('issues.all_categories') }}</option>
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>

        <div class="min-w-[140px]">
          <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Report Type</label>
          <select
            :value="reportType"
            class="w-full h-10 px-3 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            @change="onTypeChange"
          >
            <option value="">All Types</option>
            <option v-for="t in REPORT_TYPE_OPTIONS" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>

        <ViewToggle v-model="viewMode" :show-table="true" :show-card="true" :show-list="false" />
      </div>
    </Card>

    <!-- Results Count -->
    <p v-if="!isLoading" class="text-xs" style="color: var(--text-muted)">
      {{ total }} report{{ total !== 1 ? 's' : '' }} found
    </p>

    <!-- Table View -->
    <Card v-if="viewMode === 'table'" padding="none">
      <div v-if="isLoading" class="p-4 space-y-3">
        <Skeleton v-for="i in 6" :key="i" height="48px" />
      </div>

      <EmptyState
        v-else-if="reports.length === 0"
        :icon="LucideFileBarChart"
        title="No reports found"
        description="Try adjusting your search or filters"
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm" style="color: var(--text-primary)">
          <thead>
            <tr class="border-b" style="border-color: var(--border-subtle)">
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Report Name</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Category</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Type</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Description</th>
              <th class="text-left px-4 py-3 text-xs font-medium" style="color: var(--text-muted)">Module</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in reports"
              :key="r.id"
              class="border-b cursor-pointer transition-colors"
              style="border-color: var(--border-subtle)"
              @click="router.push(`/reports/view/${r.id}`)"
              @mouseenter="($event.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-tertiary)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.backgroundColor = ''"
            >
              <td class="px-4 py-3 font-medium whitespace-nowrap">
                <RouterLink
                  :to="`/reports/view/${r.id}`"
                  style="color: var(--accent)"
                  class="hover:underline"
                  @click.stop
                >
                  {{ r.title }}
                </RouterLink>
              </td>
              <td class="px-4 py-3 whitespace-nowrap">{{ r.category }}</td>
              <td class="px-4 py-3">
                <Badge :variant="TYPE_VARIANTS[r.report_type] || 'default'" size="sm">{{ r.report_type }}</Badge>
              </td>
              <td class="px-4 py-3 max-w-xs truncate" style="color: var(--text-secondary)">{{ r.description }}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-secondary)">{{ r.module }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Card View -->
    <div v-if="viewMode === 'card'">
      <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card v-for="i in 6" :key="i">
          <div class="space-y-3">
            <Skeleton height="20px" width="60%" />
            <Skeleton height="14px" />
            <Skeleton height="14px" width="40%" />
          </div>
        </Card>
      </div>

      <EmptyState
        v-else-if="reports.length === 0"
        :icon="LucideFileBarChart"
        title="No reports found"
        description="Try adjusting your search or filters"
      />

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <RouterLink
          v-for="r in reports"
          :key="r.id"
          :to="`/reports/view/${r.id}`"
          class="block"
        >
          <Card hoverable class="h-full">
            <div class="space-y-2">
              <h3 class="text-base font-semibold" style="color: var(--text-primary)">{{ r.title }}</h3>
              <p class="text-sm line-clamp-2" style="color: var(--text-muted)">{{ r.description }}</p>
              <div class="flex items-center gap-2 pt-1">
                <Badge variant="default" size="sm">{{ r.category }}</Badge>
                <Badge :variant="TYPE_VARIANTS[r.report_type] || 'default'" size="sm">{{ r.report_type }}</Badge>
              </div>
            </div>
          </Card>
        </RouterLink>
      </div>
    </div>
  </div>
</template>
