<script setup lang="ts">
import { watch } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import {
  LucideX,
  LucideLayoutDashboard,
  LucideCar,
  LucideClipboardList,
  LucideClipboardCheck,
  LucideAlertTriangle,
  LucideFuel,
  LucideReceipt,
  LucidePackage,
  LucideUsers,
  LucideFileText,
  LucideBarChart3,
  LucideSettings,
  LucideWrench,
} from 'lucide-vue-next'

interface Props {
  open: boolean
}

defineProps<Props>()
const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const route = useRoute()

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LucideLayoutDashboard, route: '/' },
  { id: 'vehicles', label: 'Vehicles', icon: LucideCar, route: '/vehicles' },
  { id: 'work-orders', label: 'Work Orders', icon: LucideClipboardList, route: '/repair-orders' },
  { id: 'inspections', label: 'Inspections', icon: LucideClipboardCheck, route: '/inspections' },
  { id: 'issues', label: 'Issues', icon: LucideAlertTriangle, route: '/issues' },
  { id: 'fuel', label: 'Fuel', icon: LucideFuel, route: '/fuel' },
  { id: 'expenses', label: 'Expenses', icon: LucideReceipt, route: '/expenses' },
  { id: 'parts', label: 'Parts / Inventory', icon: LucidePackage, route: '/parts' },
  { id: 'customers', label: 'Customers', icon: LucideUsers, route: '/customers' },
  { id: 'invoices', label: 'Invoices', icon: LucideFileText, route: '/invoices' },
  { id: 'reports', label: 'Reports', icon: LucideBarChart3, route: '/reports' },
  { id: 'settings', label: 'Settings', icon: LucideSettings, route: '/settings' },
]

// Close on route change
watch(() => route.path, () => {
  emit('update:open', false)
})

function isActive(itemRoute: string): boolean {
  if (itemRoute === '/') return route.path === '/'
  return route.path.startsWith(itemRoute)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 bg-black/50 z-40"
        @click="$emit('update:open', false)"
      />
    </Transition>

    <Transition name="slide">
      <aside
        v-if="open"
        class="fixed inset-y-0 left-0 w-72 z-50 flex flex-col shadow-xl"
        style="background-color: var(--bg-secondary);"
      >
        <!-- Header -->
        <div class="h-16 flex items-center justify-between px-4 border-b" style="border-color: var(--border-color);">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background-color: var(--accent);">
              <LucideWrench class="size-4" style="color: var(--accent-text);" />
            </div>
            <span class="font-semibold font-heading" style="color: var(--text-primary);">
              Workshop
            </span>
          </div>
          <button
            @click="$emit('update:open', false)"
            class="p-2 rounded-lg transition-colors hover:opacity-80"
            style="color: var(--text-muted);"
          >
            <LucideX class="size-5" />
          </button>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 py-4 overflow-y-auto">
          <ul class="space-y-1 px-3">
            <li v-for="item in navItems" :key="item.id">
              <RouterLink
                :to="item.route"
                :class="[
                  'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                  isActive(item.route) ? 'font-medium' : 'hover:opacity-80',
                ]"
                :style="{
                  backgroundColor: isActive(item.route) ? 'var(--bg-tertiary)' : 'transparent',
                  color: isActive(item.route) ? 'var(--text-primary)' : 'var(--text-muted)',
                }"
              >
                <component :is="item.icon" class="size-5" />
                <span class="text-sm">{{ item.label }}</span>
              </RouterLink>
            </li>
          </ul>
        </nav>
      </aside>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}
</style>
