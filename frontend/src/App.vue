<script setup lang="ts">
import { onMounted, computed, defineAsyncComponent } from 'vue'
import { useRoute } from 'vue-router'
import { FrappeUIProvider } from 'frappe-ui'
import { useSessionStore, useThemeStore, useSchemaStore } from '@/stores'

const route = useRoute()
const sessionStore = useSessionStore()
const themeStore = useThemeStore()
const schemaStore = useSchemaStore()

const AppLayout = defineAsyncComponent(() => import('@/components/layouts/AppLayout.vue'))

const isAuthRoute = computed(() => route.path.startsWith('/auth'))
const isReady = computed(() => !sessionStore.isLoggedIn || schemaStore.isReady || schemaStore.error)

onMounted(async () => {
  // Initialize theme
  themeStore.setTheme(themeStore.mode)
  
  // Initialize schema if logged in
  if (sessionStore.isLoggedIn) {
    await schemaStore.initialize()
  }
})
</script>

<template>
  <FrappeUIProvider>
    <!-- Auth routes - no layout -->
    <router-view v-if="isAuthRoute" />
    
    <!-- Protected routes with layout -->
    <template v-else-if="sessionStore.isLoggedIn">
      <!-- Loading state -->
      <div v-if="!isReady" class="h-screen flex items-center justify-center bg-surface-bg">
        <div class="flex flex-col items-center gap-4">
          <div class="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
          <p class="text-ink-muted">Loading...</p>
        </div>
      </div>
      
      <!-- App ready -->
      <AppLayout v-else>
        <router-view :key="route.fullPath" />
      </AppLayout>
    </template>
    
    <!-- Not logged in - redirect handled by router -->
    <div v-else class="h-screen flex items-center justify-center bg-surface-bg">
      <p class="text-ink-muted">Redirecting to login...</p>
    </div>
  </FrappeUIProvider>
</template>
