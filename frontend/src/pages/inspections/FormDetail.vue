<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideArrowLeft,
  LucideEdit,
  LucideFileText,
  LucideCamera,
  LucidePenLine,
  LucideAsterisk,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'
import type { StatusVariant } from '@/types'

const props = defineProps<{ id: string }>()
const router = useRouter()

interface FormItem {
  name: string
  item_label: string
  item_type: string
  section_name: string | null
  is_required: number
  photo_required: number
  signature_required: number
  min_threshold: number | null
  max_threshold: number | null
  fail_severity: string | null
  idx: number
}

interface FormTemplate {
  name: string
  title: string
  description: string | null
  category: string | null
  status: string
  version: number
  usage_count: number
  owner: string
  creation: string
  modified: string
  items: FormItem[]
}

const doc = ref<FormTemplate | null>(null)
const isLoading = ref(true)

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  Draft: 'default',
  Active: 'success',
  Archived: 'warning',
}

const ITEM_TYPE_VARIANTS: Record<string, StatusVariant> = {
  'Pass/Fail/N-A': 'info',
  Rating: 'warning',
  Numeric: 'success',
  Text: 'default',
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
  if (!dateStr) return 'N/A'
  const d = parseDateSafe(dateStr)
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

const groupedItems = computed(() => {
  if (!doc.value?.items) return []
  const groups: { section: string; items: FormItem[] }[] = []
  const map = new Map<string, FormItem[]>()

  for (const item of doc.value.items) {
    const section = item.section_name || 'General'
    if (!map.has(section)) {
      map.set(section, [])
      groups.push({ section, items: map.get(section)! })
    }
    map.get(section)!.push(item)
  }

  return groups
})

async function loadTemplate() {
  isLoading.value = true
  try {
    const result = await apiCall<FormTemplate>(
      'car_repair_management.api.inspection.get_form_template_detail',
      { name: props.id },
    )
    doc.value = result
  } catch (e) {
    console.error('Failed to load form template', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(loadTemplate)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-start gap-4">
      <Button variant="ghost" size="sm" @click="router.push('/inspections/forms')">
        <LucideArrowLeft class="size-4" />
      </Button>

      <template v-if="isLoading">
        <div class="flex-1 space-y-2">
          <Skeleton width="250px" height="28px" />
          <Skeleton width="150px" height="16px" />
        </div>
      </template>

      <template v-else-if="doc">
        <div class="flex-1">
          <div class="flex items-center gap-3 flex-wrap">
            <h1 class="text-page-title" style="color: var(--text-primary)">
              {{ doc.title || doc.name }}
            </h1>
            <Badge :variant="STATUS_VARIANTS[doc.status] || 'default'">{{ doc.status }}</Badge>
            <Badge variant="default" size="sm">v{{ doc.version }}</Badge>
            <Badge v-if="doc.category" variant="info" size="sm">{{ doc.category }}</Badge>
          </div>
        </div>
        <a :href="`/app/inspection-form-template/${doc.name}`" target="_blank">
          <Button variant="outline">
            <LucideEdit class="size-4" />
            Edit in Desk
          </Button>
        </a>
      </template>
    </div>

    <template v-if="isLoading">
      <Card><Skeleton height="120px" /></Card>
      <Card><Skeleton height="200px" /></Card>
    </template>

    <template v-else-if="doc">
      <!-- Template Info Card -->
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary)">Template Info</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Title</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ doc.title || doc.name }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Category</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ doc.category || 'None' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Status</p>
            <Badge :variant="STATUS_VARIANTS[doc.status] || 'default'">{{ doc.status }}</Badge>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Version</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ doc.version }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted)">Usage Count</p>
            <p class="text-sm font-medium" style="color: var(--text-primary)">{{ doc.usage_count }}</p>
          </div>
          <div v-if="doc.description" class="sm:col-span-2 lg:col-span-3">
            <p class="text-xs" style="color: var(--text-muted)">Description</p>
            <p class="text-sm" style="color: var(--text-primary)">{{ doc.description }}</p>
          </div>
        </div>
      </Card>

      <!-- Items Card -->
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary)">
          Inspection Items
          <span class="text-xs font-normal ml-2" style="color: var(--text-muted)">
            {{ doc.items?.length || 0 }} items
          </span>
        </h3>

        <div v-if="!doc.items || doc.items.length === 0" class="py-8 text-center">
          <LucideFileText class="size-8 mx-auto mb-2" style="color: var(--text-muted)" />
          <p class="text-sm" style="color: var(--text-muted)">No items defined</p>
        </div>

        <div v-else class="space-y-6">
          <div v-for="group in groupedItems" :key="group.section">
            <!-- Section header -->
            <div
              class="px-3 py-2 rounded-md text-xs font-semibold uppercase tracking-wide"
              style="background-color: var(--bg-tertiary); color: var(--text-muted)"
            >
              {{ group.section }}
            </div>

            <!-- Items list -->
            <div class="divide-y" style="border-color: var(--border-color)">
              <div
                v-for="item in group.items"
                :key="item.name"
                class="py-3 px-3"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span class="text-sm font-medium" style="color: var(--text-primary)">
                        {{ item.item_label }}
                      </span>
                      <!-- Required indicator -->
                      <LucideAsterisk
                        v-if="item.is_required"
                        class="size-3"
                        style="color: #ef4444"
                      />
                    </div>

                    <!-- Metadata row -->
                    <div class="flex items-center gap-3 mt-1.5 flex-wrap">
                      <Badge
                        :variant="ITEM_TYPE_VARIANTS[item.item_type] || 'default'"
                        size="sm"
                      >
                        {{ item.item_type }}
                      </Badge>

                      <!-- Photo required -->
                      <span
                        v-if="item.photo_required"
                        class="inline-flex items-center gap-1 text-xs"
                        style="color: var(--text-muted)"
                      >
                        <LucideCamera class="size-3" />
                        Photo
                      </span>

                      <!-- Signature required -->
                      <span
                        v-if="item.signature_required"
                        class="inline-flex items-center gap-1 text-xs"
                        style="color: var(--text-muted)"
                      >
                        <LucidePenLine class="size-3" />
                        Signature
                      </span>

                      <!-- Numeric thresholds -->
                      <span
                        v-if="item.item_type === 'Numeric' && (item.min_threshold != null || item.max_threshold != null)"
                        class="text-xs"
                        style="color: var(--text-muted)"
                      >
                        Range: {{ item.min_threshold ?? '–' }} – {{ item.max_threshold ?? '–' }}
                      </span>

                      <!-- Fail severity -->
                      <Badge
                        v-if="item.fail_severity"
                        variant="danger"
                        size="sm"
                      >
                        {{ item.fail_severity }}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <!-- Audit Trail Card -->
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary)">Audit Trail</h3>
        <div class="space-y-2 text-sm" style="color: var(--text-muted)">
          <p>
            Created by <span style="color: var(--text-primary)" class="font-medium">{{ doc.owner }}</span>
            on {{ formatDate(doc.creation) }}
          </p>
          <p>
            Last modified on {{ formatDate(doc.modified) }}
          </p>
        </div>
      </Card>
    </template>
  </div>
</template>
