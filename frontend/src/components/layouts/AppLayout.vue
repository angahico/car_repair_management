<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'
import MobileSidebar from './MobileSidebar.vue'

const isMobile = ref(window.innerWidth < 768)
const showMobileSidebar = ref(false)

function handleResize() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) {
    showMobileSidebar.value = false
  }
}

onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => window.removeEventListener('resize', handleResize))
</script>

<template>
  <div class="flex h-screen w-screen overflow-hidden bg-surface-bg">
    <!-- Desktop sidebar -->
    <Sidebar v-if="!isMobile" />

    <!-- Mobile sidebar overlay -->
    <MobileSidebar v-model:open="showMobileSidebar" />

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <Topbar @toggle-sidebar="showMobileSidebar = true" />
      <main class="flex-1 overflow-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
