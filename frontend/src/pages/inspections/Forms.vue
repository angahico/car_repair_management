<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideFileText,
  LucidePlus,
  LucideSearch,
  LucideRefreshCw,
} from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { apiCall } from '@/api'
import { Card, Button, EmptyState, Skeleton, Badge, Input } from '@/components/ui'
import type { StatusVariant } from '@/types'

interface FormRecord {
  name: string
  title: string
  category: string | null
  description: string | null
  status: string
  version: number
  usage_count: number
  item_count: number
  owner: string
  creation: string
  modified: string
}

interface FormsData {
  records: FormRecord[]
  total: number
}

const router = useRouter()
const { t } = useI18n()

const records = ref<FormRecord[]>([])
const total = ref(0)
const isLoading = ref(true)
const searchQuery = ref('')
const categoryFilter = ref('All')
const statusFilter = ref('All')

const categories = ['All', 'Pre-Trip', 'Post-Trip', 'Safety', 'Regulatory', 'Custom']
const statuses = ['All', 'Draft', 'Active', 'Archived']

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Draft: 'default',
  Active: 'success',
  Archived: 'warning',
}

function parseDateSafe(dateStr: string): Date {
  const parts = dateStr.split(/[- T:]/)
  return new Date(
    parseInt(parts[0], 10),
    parseInt(parts[1], 10) - 1,
    parseInt(parts[2], 10),
    parseInt(parts[3] || '0', 10),
    parseInt(parts[4] || '0', 10),
    parseInt(parts[5] || '0', 10),
  )
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return 'Never'
  const d = parseDateSafe(dateStr)
  return d.toLocaleDateString()
}

async function loadForms() {
  isLoading.value = true
  try {
    const args: Record<string, unknown> = {
      limit_start: 0,
      limit_page_length: 20,
    }
    if (searchQuery.value) args.search = searchQuery.value
    if (categoryFilter.value !== 'All') args.category = categoryFilter.value
    if (statusFilter.value !== 'All') args.status = statusFilter.value

    const result = await apiCall<FormsData>(
      'car_repair_management.api.inspection.get_form_templates',
      args,
    )
    records.value = result?.records || []
    total.value = result?.total || 0
  } catch (e) {
    console.warn('Failed to load form templates', e)
  } finally {
    isLoading.value = false
  }
}

function navigateToDetail(name: string) {
  router.push(`/inspections/forms/${name}`)
}

watch([categoryFilter, statusFilter], () => loadForms())

onMounted(loadForms)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-page-title">{{ $t('inspections.forms_title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted)">{{ total }} form templates</p>
      </div>
      <a href="/app/inspection-form-template/new">
        <Button variant="primary">
          <LucidePlus class="size-4" />
          {{ $t('inspections.new_form') }}
        </Button>
      </a>
    </div>

    <!-- Control Bar -->
    <Card>
      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div class="flex-1 w-full sm:w-auto">
          <Input
            v-model="searchQuery"
            placeholder="Search form templates..."
            @keyup.enter="loadForms"
          >
            <template #prefix>
              <LucideSearch class="size-4" style="color: var(--text-muted)" />
            </template>
          </Input>
        </div>
        <div class="flex items-center gap-2 flex-wrap">
          <select
            v-model="categoryFilter"
            class="h-10 px-3 text-sm rounded-input border bg-surface-card text-ink"
            style="border-color: var(--border-color)"
          >
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat === 'All' ? $t('issues.all_categories') : cat }}</option>
          </select>
          <select
            v-model="statusFilter"
            class="h-10 px-3 text-sm rounded-input border bg-surface-card text-ink"
            style="border-color: var(--border-color)"
          >
            <option v-for="s in statuses" :key="s" :value="s">{{ s === 'All' ? $t('issues.all_statuses') : s }}</option>
          </select>
          <Button variant="ghost" size="sm" @click="loadForms">
            <LucideRefreshCw class="size-4" />
          </Button>
        </div>
      </div>
    </Card>

    <!-- Loading -->
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card v-for="i in 6" :key="i">
        <div class="space-y-3">
          <Skeleton height="20px" width="70%" />
          <Skeleton height="14px" width="40%" />
          <Skeleton height="14px" />
          <div class="flex gap-2 pt-2">
            <Skeleton height="24px" width="60px" />
            <Skeleton height="24px" width="60px" />
          </div>
        </div>
      </Card>
    </div>

    <!-- Empty state -->
    <Card v-else-if="records.length === 0">
      <EmptyState
        :icon="LucideFileText"
        :title="$t('inspections.no_forms')"
        :description="$t('inspections.no_forms_desc')"
        actionLabel="New Form"
        actionRoute="/app/inspection-form-template/new"
      />
    </Card>

    <!-- Card Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card
        v-for="record in records"
        :key="record.name"
        hoverable
        @click="navigateToDetail(record.name)"
      >
        <div class="space-y-3">
          <!-- Title & Status -->
          <div class="flex items-start justify-between gap-2">
            <h3 class="text-sm font-semibold" style="color: var(--text-primary)">
              {{ record.title || record.name }}
            </h3>
            <Badge :variant="STATUS_VARIANTS[record.status] || 'default'" size="sm">
              {{ record.status }}
            </Badge>
          </div>

          <!-- Description -->
          <p
            v-if="record.description"
            class="text-xs line-clamp-2"
            style="color: var(--text-muted)"
          >
            {{ record.description }}
          </p>

          <!-- Category -->
          <div v-if="record.category" class="flex items-center gap-2">
            <Badge variant="info" size="sm">{{ record.category }}</Badge>
          </div>

          <!-- Stats row -->
          <div class="flex items-center gap-4 text-xs" style="color: var(--text-muted)">
            <span>{{ record.item_count }} items</span>
            <span>{{ record.usage_count }} uses</span>
            <span>v{{ record.version }}</span>
          </div>

          <!-- Footer -->
          <p class="text-xs" style="color: var(--text-muted)">
            Updated {{ formatDate(record.modified) }}
          </p>
        </div>
      </Card>
    </div>
  </div>
</template>
