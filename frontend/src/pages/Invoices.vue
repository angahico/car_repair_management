<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { LucideFileText, LucideRefreshCw } from 'lucide-vue-next'
import { apiList } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState } from '@/components/ui'

const { t } = useI18n()

const invoices = ref<any[]>([])
const isLoading = ref(true)

async function loadInvoices() {
  isLoading.value = true
  try {
    invoices.value = await apiList({
      doctype: 'Sales Invoice',
      fields: ['name', 'customer', 'status', 'grand_total', 'posting_date', 'modified'],
      orderBy: 'modified desc',
      limitPageLength: 50,
    })
  } catch (e) {
    console.error('Failed to load invoices', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(loadInvoices)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-page-title text-ink">Invoices</h1>
        <p class="text-sm text-ink-muted mt-1">Sales invoices</p>
      </div>
      <Button variant="outline" @click="loadInvoices">
        <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
      </Button>
    </div>

    <Card>
      <template v-if="isLoading">
        <div class="space-y-3"><Skeleton v-for="i in 5" :key="i" height="48px" /></div>
      </template>

      <template v-else-if="invoices.length === 0">
        <EmptyState title="No invoices" description="Invoices will appear here" />
      </template>

      <div v-else class="divide-y divide-border-light dark:divide-border-dark">
        <a
          v-for="inv in invoices"
          :key="inv.name"
          :href="`/app/sales-invoice/${inv.name}`"
          target="_blank"
          class="flex items-center justify-between py-3 hover:bg-gray-50 dark:hover:bg-gray-800 -mx-4 px-4 transition-colors"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-500/20 flex items-center justify-center">
              <LucideFileText class="size-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p class="text-sm font-medium text-ink">{{ inv.name }}</p>
              <p class="text-xs text-ink-muted">{{ inv.customer }}</p>
            </div>
          </div>
          <div class="text-right">
            <p class="text-sm font-semibold text-ink">{{ inv.grand_total?.toLocaleString() }}</p>
            <Badge :variant="inv.status === 'Paid' ? 'success' : inv.status === 'Overdue' ? 'danger' : 'default'" size="sm">{{ inv.status }}</Badge>
          </div>
        </a>
      </div>
    </Card>
  </div>
</template>
