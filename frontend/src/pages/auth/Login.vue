<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { LucideWrench, LucideEye, LucideEyeOff } from 'lucide-vue-next'
import { frappeRequest } from 'frappe-ui'
import { useSessionStore } from '@/stores'
import { Button, Input, Card } from '@/components/ui'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const sessionStore = useSessionStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const error = ref('')

const isValid = computed(() => email.value.length > 0 && password.value.length > 0)

async function handleLogin() {
  if (!isValid.value) return
  
  isLoading.value = true
  error.value = ''
  
  try {
    await frappeRequest({
      url: '/api/method/login',
      method: 'POST',
      body: {
        usr: email.value,
        pwd: password.value,
      },
    })
    sessionStore.refreshUser()
    window.location.href = '/workshop'
  } catch (e: any) {
    error.value = e.message || 'Invalid email or password'
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
          {{ $t('auth.workshop_management') }}
        </h1>
        <p class="text-sm text-ink-muted mt-1">
          {{ $t('auth.sign_in_subtitle') }}
        </p>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-ink mb-1.5">
            {{ $t('auth.email') }}
          </label>
          <Input
            v-model="email"
            type="email"
            placeholder="you@example.com"
            :error="error && !email ? t('auth.email_required') : undefined"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-ink mb-1.5">
            {{ $t('auth.password') }}
          </label>
          <div class="relative">
            <Input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-ink-faint hover:text-ink-muted"
            >
              <LucideEyeOff v-if="showPassword" class="size-4" />
              <LucideEye v-else class="size-4" />
            </button>
          </div>
        </div>

        <!-- Error -->
        <p v-if="error" class="text-sm text-danger-DEFAULT">{{ error }}</p>

        <!-- Submit -->
        <Button type="submit" variant="primary" full-width :loading="isLoading" :disabled="!isValid">
          {{ $t('auth.sign_in') }}
        </Button>

        <!-- Forgot password -->
        <div class="text-center">
          <RouterLink to="/auth/forgot" class="text-sm text-primary-500 hover:text-primary-600">
            {{ $t('auth.forgot_password') }}
          </RouterLink>
        </div>
      </form>
    </Card>
  </div>
</template>
