<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { LucideWrench, LucideArrowLeft, LucideCheck } from 'lucide-vue-next'
import { frappeRequest } from 'frappe-ui'
import { Button, Input, Card } from '@/components/ui'
import { useI18n } from 'vue-i18n'

const email = ref('')
const isLoading = ref(false)
const error = ref('')
const success = ref(false)
const { t } = useI18n()

const isValid = computed(() => email.value.length > 0 && email.value.includes('@'))

async function handleSubmit() {
  if (!isValid.value) return
  
  isLoading.value = true
  error.value = ''
  
  try {
    await frappeRequest({
      url: '/api/method/frappe.core.doctype.user.user.reset_password',
      method: 'POST',
      body: { user: email.value },
    })
    success.value = true
  } catch (e: any) {
    error.value = e.message || 'Failed to send reset link'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-surface-bg p-4">
    <Card class="w-full max-w-md p-8">
      <!-- Logo -->
      <div class="flex flex-col items-center mb-8">
        <div class="w-14 h-14 rounded-xl bg-primary-500 flex items-center justify-center mb-4">
          <LucideWrench class="size-7 text-white" />
        </div>
        <h1 class="text-xl font-semibold text-ink">
          {{ $t('auth.reset_password') }}
        </h1>
        <p class="text-sm text-ink-muted mt-1 text-center">
          {{ $t('auth.reset_subtitle') }}
        </p>
      </div>

      <!-- Success state -->
      <div v-if="success" class="text-center">
        <div class="w-16 h-16 rounded-full bg-green-100 dark:bg-green-500/20 flex items-center justify-center mx-auto mb-4">
          <LucideCheck class="size-8 text-green-600 dark:text-green-400" />
        </div>
        <p class="text-ink mb-4">
          {{ $t('auth.check_email') }}
        </p>
        <RouterLink to="/auth/login">
          <Button variant="outline">
            <LucideArrowLeft class="size-4" />
            {{ $t('auth.back_to_login') }}
          </Button>
        </RouterLink>
      </div>

      <!-- Form -->
      <form v-else @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-ink mb-1.5">
            {{ $t('auth.email') }}
          </label>
          <Input
            v-model="email"
            type="email"
            placeholder="you@example.com"
          />
        </div>

        <!-- Error -->
        <p v-if="error" class="text-sm text-danger-DEFAULT">{{ error }}</p>

        <!-- Submit -->
        <Button type="submit" variant="primary" full-width :loading="isLoading" :disabled="!isValid">
          {{ $t('auth.send_reset_link') }}
        </Button>

        <!-- Back to login -->
        <div class="text-center">
          <RouterLink to="/auth/login" class="text-sm text-ink-muted hover:text-ink inline-flex items-center gap-1">
            <LucideArrowLeft class="size-3" />
            {{ $t('auth.back_to_login') }}
          </RouterLink>
        </div>
      </form>
    </Card>
  </div>
</template>
