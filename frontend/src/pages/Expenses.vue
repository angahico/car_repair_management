<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { LucideReceipt, LucidePlus } from 'lucide-vue-next'
import { apiList, apiGetCount } from '@/api'
import { Card, Button, EmptyState, Skeleton } from '@/components/ui'

interface Expense {
  name: string
  expense_type?: string
  amount?: number
  vehicle?: string
  posting_date?: string
  modified: string
}

const { t } = useI18n()

const expenses = ref<Expense[]>([])
const total = ref(0)
const isLoading = ref(true)

async function loadExpenses() {
  isLoading.value = true
  try {
    const [list, count] = await Promise.all([
      apiList<Expense>({
        doctype: 'Expense Claim',
        fields: ['name', 'expense_type', 'total_claimed_amount as amount', 'posting_date', 'modified'],
        orderBy: 'modified desc',
        limitPageLength: 20,
      }),
      apiGetCount('Expense Claim'),
    ])
    expenses.value = list
    total.value = count
  } catch (e) {
    console.warn('Failed to load expenses', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(loadExpenses)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-page-title text-ink">Expenses</h1>
        <p class="text-sm text-ink-muted mt-1">{{ total }} total expenses</p>
      </div>
      <Button variant="primary">
        <LucidePlus class="size-4" />
        New Expense
      </Button>
    </div>

    <Card>
      <div v-if="isLoading" class="space-y-3">
        <Skeleton v-for="i in 5" :key="i" height="56px" />
      </div>

      <EmptyState
        v-else-if="expenses.length === 0"
        :icon="LucideReceipt"
        title="No expenses found"
        description="Track vehicle and repair expenses here"
      />

      <div v-else class="divide-y divide-border-light dark:divide-border-dark">
        <div
          v-for="expense in expenses"
          :key="expense.name"
          class="flex items-center justify-between py-4"
        >
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-500/20 flex items-center justify-center">
              <LucideReceipt class="size-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p class="text-sm font-medium text-ink">{{ expense.name }}</p>
              <p class="text-xs text-ink-muted">
                {{ expense.expense_type || 'General' }} • {{ expense.posting_date || new Date(expense.modified).toLocaleDateString() }}
              </p>
            </div>
          </div>
          <div class="text-right">
            <p class="text-sm font-semibold text-ink">
              {{ expense.amount?.toLocaleString() || 0 }}
            </p>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>
