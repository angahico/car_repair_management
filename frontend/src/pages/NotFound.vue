<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { LucideHome } from 'lucide-vue-next'
import { Button } from '@/components/ui'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="flex flex-col items-center justify-center min-h-[60vh] text-center">
    <div class="text-8xl font-bold text-gray-200 dark:text-gray-700 mb-4">404</div>
    <h1 class="text-2xl font-semibold text-ink mb-2">
      {{ $t('not_found.title') }}
    </h1>
    <p class="text-ink-muted mb-6 max-w-md">
      {{ $t('not_found.description') }}
    </p>
    <div class="flex gap-3">
      <RouterLink to="/">
        <Button variant="primary">
          <LucideHome class="size-4" />
          {{ $t('not_found.go_to_dashboard') }}
        </Button>
      </RouterLink>
    </div>
  </div>
</template>
