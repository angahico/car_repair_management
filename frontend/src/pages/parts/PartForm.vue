<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LucideArrowLeft,
  LucideSave,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Skeleton } from '@/components/ui'

interface PartFormData {
  item_name: string
  item_group: string
  stock_uom: string
  is_stock_item: boolean
  item_code: string
  description: string
  standard_rate: number | null
  reorder_level: number | null
  reorder_qty: number | null
  image: string
}

const props = defineProps<{ id?: string; isNew?: boolean }>()
const router = useRouter()

const isLoading = ref(false)
const isSaving = ref(false)
const form = ref<PartFormData>({
  item_name: '',
  item_group: '',
  stock_uom: 'Nos',
  is_stock_item: true,
  item_code: '',
  description: '',
  standard_rate: null,
  reorder_level: null,
  reorder_qty: null,
  image: '',
})

function goBack() {
  router.push('/parts')
}

async function loadItem() {
  if (!props.id || props.isNew) return
  isLoading.value = true
  try {
    const data = await apiCall<{
      doc: {
        item_name: string
        item_group: string
        stock_uom: string
        is_stock_item: number
        item_code: string
        description: string | null
        standard_rate: number
        reorder_level: number
        reorder_qty: number
        image: string | null
      }
    }>(
      'car_repair_management.api.parts.get_part_detail',
      { name: props.id },
    )
    const doc = data.doc
    form.value = {
      item_name: doc.item_name || '',
      item_group: doc.item_group || '',
      stock_uom: doc.stock_uom || 'Nos',
      is_stock_item: !!doc.is_stock_item,
      item_code: doc.item_code || '',
      description: doc.description || '',
      standard_rate: doc.standard_rate || null,
      reorder_level: doc.reorder_level || null,
      reorder_qty: doc.reorder_qty || null,
      image: doc.image || '',
    }
  } catch (e) {
    console.warn('Failed to load item', e)
  } finally {
    isLoading.value = false
  }
}

async function saveItem() {
  if (!form.value.item_name.trim()) return
  isSaving.value = true
  try {
    const payload: Record<string, unknown> = {
      item_name: form.value.item_name,
      item_group: form.value.item_group,
      stock_uom: form.value.stock_uom,
      is_stock_item: form.value.is_stock_item ? 1 : 0,
      description: form.value.description,
      standard_rate: form.value.standard_rate || 0,
      image: form.value.image,
    }
    if (form.value.item_code) payload.item_code = form.value.item_code
    if (form.value.is_stock_item) {
      payload.reorder_level = form.value.reorder_level || 0
      payload.reorder_qty = form.value.reorder_qty || 0
    }

    if (props.id && !props.isNew) {
      payload.name = props.id
      await apiCall(
        'car_repair_management.api.parts.update_part',
        payload,
      )
      router.push(`/parts/${props.id}`)
    } else {
      const result = await apiCall<{ name: string }>(
        'car_repair_management.api.parts.create_part',
        payload,
      )
      router.push(`/parts/${result.name}`)
    }
  } catch (e) {
    console.warn('Failed to save item', e)
  } finally {
    isSaving.value = false
  }
}

onMounted(loadItem)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <div v-if="isLoading" class="space-y-6">
      <Skeleton height="48px" />
      <Skeleton height="400px" />
    </div>

    <template v-else>
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <button
            class="w-9 h-9 flex items-center justify-center rounded-lg transition-colors"
            style="background: var(--bg-tertiary); color: var(--text-secondary)"
            @click="goBack"
          >
            <LucideArrowLeft class="size-5" />
          </button>
          <h1 class="text-page-title">
            {{ props.isNew ? 'New Item' : 'Edit Item' }}
          </h1>
        </div>
        <Button variant="primary" :disabled="isSaving || !form.item_name.trim()" @click="saveItem">
          <LucideSave class="size-4" />
          {{ isSaving ? 'Saving...' : 'Save' }}
        </Button>
      </div>

      <!-- Form -->
      <Card>
        <h2 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">Item Details</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
          <!-- Item Name -->
          <div>
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">
              Item Name <span style="color: #ef4444">*</span>
            </label>
            <input
              v-model="form.item_name"
              type="text"
              placeholder="Enter item name"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            />
          </div>

          <!-- Item Group -->
          <div>
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Item Group</label>
            <input
              v-model="form.item_group"
              type="text"
              placeholder="e.g. Consumable, Raw Material"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            />
          </div>

          <!-- Stock UOM -->
          <div>
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Stock UOM</label>
            <input
              v-model="form.stock_uom"
              type="text"
              placeholder="e.g. Nos, Kg, Ltr"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            />
          </div>

          <!-- Item Code -->
          <div>
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Item Code</label>
            <input
              v-model="form.item_code"
              type="text"
              placeholder="Auto-generated if empty"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
              :disabled="!!props.id && !props.isNew"
            />
          </div>

          <!-- Standard Rate -->
          <div>
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Standard Rate</label>
            <input
              v-model.number="form.standard_rate"
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            />
          </div>

          <!-- Image URL -->
          <div>
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Image URL</label>
            <input
              v-model="form.image"
              type="text"
              placeholder="https://..."
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            />
          </div>

          <!-- Is Stock Item -->
          <div class="flex items-center gap-2 md:col-span-2">
            <input
              v-model="form.is_stock_item"
              type="checkbox"
              class="w-4 h-4 rounded border"
              style="border-color: var(--border-color); accent-color: var(--accent)"
            />
            <label class="text-sm font-medium" style="color: var(--text-primary)">Is Stock Item</label>
          </div>

          <!-- Reorder Level (shown if is_stock_item) -->
          <div v-if="form.is_stock_item">
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Reorder Level</label>
            <input
              v-model.number="form.reorder_level"
              type="number"
              step="1"
              min="0"
              placeholder="0"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            />
          </div>

          <!-- Reorder Qty (shown if is_stock_item) -->
          <div v-if="form.is_stock_item">
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Reorder Qty</label>
            <input
              v-model.number="form.reorder_qty"
              type="number"
              step="1"
              min="0"
              placeholder="0"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            />
          </div>

          <!-- Description (full width) -->
          <div class="md:col-span-2">
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Description</label>
            <textarea
              v-model="form.description"
              rows="4"
              placeholder="Enter item description..."
              class="w-full px-3 py-2 text-sm rounded border resize-y"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color)"
            />
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>
