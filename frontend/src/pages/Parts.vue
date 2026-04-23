<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { LucidePackage, LucidePlus, LucideSearch } from 'lucide-vue-next'
import { apiList, apiGetCount } from '@/api'
import { Card, Button, EmptyState, Skeleton, Input } from '@/components/ui'

interface Part {
  name: string
  item_name?: string
  item_code?: string
  stock_uom?: string
  modified: string
}

const { t } = useI18n()

const parts = ref<Part[]>([])
const total = ref(0)
const isLoading = ref(true)
const searchQuery = ref('')

async function loadParts() {
  isLoading.value = true
  try {
    const filters: Record<string, unknown> = { is_stock_item: 1 }
    if (searchQuery.value) {
      filters.item_name = ['like', `%${searchQuery.value}%`]
    }
    
    const [list, count] = await Promise.all([
      apiList<Part>({
        doctype: 'Item',
        fields: ['name', 'item_name', 'item_code', 'stock_uom', 'modified'],
        filters,
        orderBy: 'item_name asc',
        limitPageLength: 50,
      }),
      apiGetCount('Item', filters),
    ])
    parts.value = list
    total.value = count
  } catch (e) {
    console.warn('Failed to load parts', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(loadParts)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-page-title text-ink">Parts & Inventory</h1>
        <p class="text-sm text-ink-muted mt-1">{{ total }} items in stock</p>
      </div>
      <Button variant="primary">
        <LucidePlus class="size-4" />
        Add Part
      </Button>
    </div>

    <Card>
      <div class="mb-4">
        <div class="relative">
          <LucideSearch class="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-muted" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search parts..."
            class="w-full pl-10 pr-4 py-2 rounded-input border border-default bg-surface-card text-ink text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            @input="loadParts"
          />
        </div>
      </div>

      <div v-if="isLoading" class="space-y-3">
        <Skeleton v-for="i in 5" :key="i" height="56px" />
      </div>

      <EmptyState
        v-else-if="parts.length === 0"
        :icon="LucidePackage"
        title="No parts found"
        description="Add parts to track inventory"
      />

      <div v-else class="divide-y divide-border-light dark:divide-border-dark">
        <div
          v-for="part in parts"
          :key="part.name"
          class="flex items-center justify-between py-4"
        >
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center">
              <LucidePackage class="size-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p class="text-sm font-medium text-ink">{{ part.item_name || part.name }}</p>
              <p class="text-xs text-ink-muted">
                {{ part.item_code }} • {{ part.stock_uom || 'Nos' }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>
