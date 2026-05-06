<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import {
  LucideLayoutDashboard,
  LucideCar,
  LucideClipboardList,
  LucideClipboardCheck,
  LucideAlertTriangle,
  LucideReceipt,
  LucidePackage,
  LucideUsers,
  LucideFileText,
  LucideBarChart3,
  LucideSettings,
  LucideChevronLeft,
  LucideChevronRight,
  LucideChevronDown,
  LucideWrench,
  LucideList,
  LucideUserCheck,
  LucideGauge,
  LucideHistory,
  LucideRefreshCw,
  LucideClock,
  LucideXCircle,
  LucideCalendar,
  LucideFileCheck,
  LucideBug,
  LucideBell,
  LucidePieChart,
  LucideUserCog,
  LucideBookmark,
  LucideSun,
  LucideMoon,
  LucideMonitor,
  LucideFuel,
} from 'lucide-vue-next'
import { useThemeStore } from '@/stores'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const { t } = useI18n()

const themeStore = useThemeStore()

const themeOptions = computed(() => [
  { id: 'light' as const, icon: LucideSun, title: t('settings.light') },
  { id: 'dark' as const, icon: LucideMoon, title: t('settings.dark') },
  { id: 'system' as const, icon: LucideMonitor, title: t('settings.system') },
])

const currentThemeIcon = computed(() => {
  const opt = themeOptions.value.find((o) => o.id === themeStore.mode)
  return opt?.icon || LucideMonitor
})

function cycleTheme() {
  const modes = ['light', 'dark', 'system'] as const
  const idx = modes.indexOf(themeStore.mode)
  themeStore.setTheme(modes[(idx + 1) % modes.length])
}

const isCollapsed = ref(false)
const expandedMenu = ref<string | null>(null)

interface NavChild {
  id: string
  label: string
  route: string
  icon?: any
}

interface NavItem {
  id: string
  label: string
  icon: any
  route?: string
  children?: NavChild[]
}

const navItems = computed<NavItem[]>(() => [
  { id: 'dashboard', label: t('nav.dashboard'), icon: LucideLayoutDashboard, route: '/' },
  {
    id: 'vehicles',
    label: t('nav.vehicles'),
    icon: LucideCar,
    children: [
      { id: 'vehicle-list', label: t('nav.vehicle_list'), route: '/vehicles', icon: LucideList },
      { id: 'vehicle-assignments', label: t('nav.vehicle_assignments'), route: '/vehicles/assignments', icon: LucideUserCheck },
      { id: 'meter-history', label: t('nav.meter_history'), route: '/vehicles/meter-history', icon: LucideGauge },
      { id: 'expense-history', label: t('nav.expense_history'), route: '/vehicles/expense-history', icon: LucideHistory },
      { id: 'replacement-analysis', label: t('nav.replacement_analysis'), route: '/vehicles/replacement-analysis', icon: LucideRefreshCw },
      { id: 'vehicle-aging', label: t('nav.aging_analysis'), route: '/vehicles/aging-analysis', icon: LucideClock },
    ],
  },
  { id: 'work-orders', label: t('nav.work_orders'), icon: LucideClipboardList, route: '/repair-orders' },
  {
    id: 'inspections',
    label: t('nav.inspections'),
    icon: LucideClipboardCheck,
    children: [
      { id: 'inspection-history', label: t('nav.inspection_history'), route: '/inspections', icon: LucideHistory },
      { id: 'item-failures', label: t('nav.item_failures'), route: '/inspections/item-failures', icon: LucideXCircle },
      { id: 'inspection-schedules', label: t('nav.schedules'), route: '/inspections/schedules', icon: LucideCalendar },
      { id: 'inspection-forms', label: t('nav.forms'), route: '/inspections/forms', icon: LucideFileCheck },
    ],
  },
  {
    id: 'issues',
    label: t('nav.issues'),
    icon: LucideAlertTriangle,
    children: [
      { id: 'issues-list', label: t('nav.issues'), route: '/issues', icon: LucideAlertTriangle },
      { id: 'faults', label: t('nav.faults'), route: '/issues/faults', icon: LucideBug },
      { id: 'recalls', label: t('nav.recalls'), route: '/issues/recalls', icon: LucideBell },
    ],
  },
  {
    id: 'fuel',
    label: t('nav.fuel'),
    icon: LucideFuel,
    children: [
      { id: 'fuel-records', label: t('fuel.refueling_records'), route: '/fuel', icon: LucideFuel },
      { id: 'fuel-quotas', label: t('fuel.quotas_title'), route: '/fuel/quotas', icon: LucideGauge },
    ],
  },
  { id: 'expenses', label: t('nav.expenses'), icon: LucideReceipt, route: '/expenses' },
  { id: 'parts', label: t('nav.parts'), icon: LucidePackage, route: '/parts' },
  { id: 'customers', label: t('nav.customers'), icon: LucideUsers, route: '/customers' },
  { id: 'employees', label: t('nav.employees'), icon: LucideUserCog, route: '/employees' },
  { id: 'invoices', label: t('nav.invoices'), icon: LucideFileText, route: '/invoices' },
  {
    id: 'reports',
    label: t('nav.reports'),
    icon: LucideBarChart3,
    children: [
      { id: 'report-overview', label: t('nav.report_dashboard'), route: '/reports', icon: LucidePieChart },
      { id: 'report-library', label: t('nav.report_library'), route: '/reports/library', icon: LucideList },
      { id: 'report-saved', label: t('nav.saved_reports'), route: '/reports/saved', icon: LucideBookmark },
      { id: 'report-scheduled', label: t('nav.scheduled_reports'), route: '/reports/scheduled', icon: LucideCalendar },
    ],
  },
  { id: 'settings', label: t('nav.settings'), icon: LucideSettings, route: '/settings' },
])

function isActive(itemRoute: string): boolean {
  if (itemRoute === '/') return route.path === '/'
  return route.path === itemRoute
}

function isParentActive(item: NavItem): boolean {
  if (item.children) {
    return item.children.some(child => route.path === child.route)
  }
  return false
}

function toggleMenu(id: string) {
  if (isCollapsed.value) {
    isCollapsed.value = false
  }
  expandedMenu.value = expandedMenu.value === id ? null : id
}

function isExpanded(id: string): boolean {
  return expandedMenu.value === id
}

function handleSimpleNavClick() {
  expandedMenu.value = null
}
</script>

<template>
  <aside
    :class="[
      'h-full flex flex-col border-r transition-all duration-300',
      isCollapsed ? 'w-16' : 'w-60',
    ]"
    style="background-color: var(--bg-secondary); border-color: var(--border-color);"
  >
    <!-- Logo -->
    <div class="h-16 flex items-center px-4 border-b" style="border-color: var(--border-color);">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background-color: var(--accent);">
          <LucideWrench class="size-4" style="color: var(--accent-text);" />
        </div>
        <span v-if="!isCollapsed" class="font-semibold font-heading" style="color: var(--text-primary);">
          Workshop
        </span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 py-4 overflow-y-auto">
      <ul class="space-y-1 px-2">
        <li v-for="item in navItems" :key="item.id">
          <!-- Simple link (no children) -->
          <RouterLink
            v-if="item.route && !item.children"
            :to="item.route"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
              isActive(item.route) ? 'font-medium' : 'hover:opacity-80',
            ]"
            :style="{
              backgroundColor: isActive(item.route) ? 'var(--bg-tertiary)' : 'transparent',
              color: isActive(item.route) ? 'var(--text-primary)' : 'var(--text-muted)',
            }"
            @click="handleSimpleNavClick"
          >
            <component :is="item.icon" class="size-5 flex-shrink-0" />
            <span v-if="!isCollapsed" class="text-sm">{{ item.label }}</span>
          </RouterLink>

          <!-- Expandable menu (has children) -->
          <template v-else-if="item.children">
            <button
              @click="toggleMenu(item.id)"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                isParentActive(item) ? 'font-medium' : 'hover:opacity-80',
              ]"
              :style="{
                backgroundColor: isParentActive(item) ? 'var(--bg-tertiary)' : 'transparent',
                color: isParentActive(item) ? 'var(--text-primary)' : 'var(--text-muted)',
              }"
            >
              <component :is="item.icon" class="size-5 flex-shrink-0" />
              <span v-if="!isCollapsed" class="text-sm flex-1 text-left">{{ item.label }}</span>
              <LucideChevronDown
                v-if="!isCollapsed"
                :class="[
                  'size-4 transition-transform duration-200',
                  isExpanded(item.id) ? 'rotate-180' : '',
                ]"
              />
            </button>

            <!-- Submenu -->
            <ul
              v-if="!isCollapsed && isExpanded(item.id)"
              class="mt-1 ml-4 pl-4 space-y-1 border-l"
              style="border-color: var(--border-color);"
            >
              <li v-for="child in item.children" :key="child.id">
                <RouterLink
                  :to="child.route"
                  :class="[
                    'flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
                    isActive(child.route) ? 'font-medium' : 'hover:opacity-80',
                  ]"
                  :style="{
                    backgroundColor: isActive(child.route) ? 'var(--bg-tertiary)' : 'transparent',
                    color: isActive(child.route) ? 'var(--text-primary)' : 'var(--text-muted)',
                  }"
                >
                  <component v-if="child.icon" :is="child.icon" class="size-4 flex-shrink-0" />
                  <span>{{ child.label }}</span>
                </RouterLink>
              </li>
            </ul>
          </template>
        </li>
      </ul>
    </nav>

    <!-- Theme toggle — icon-only switch -->
    <div class="px-2 pt-2 pb-1 border-t" style="border-color: var(--border-color);">
      <template v-if="!isCollapsed">
        <!-- 3-button icon-only segmented control -->
        <div
          class="flex items-center gap-0.5 p-1 rounded-lg"
          style="background-color: var(--bg-tertiary);"
          :title="themeStore.mode"
        >
          <button
            v-for="option in themeOptions"
            :key="option.id"
            @click="themeStore.setTheme(option.id)"
            :title="option.title"
            class="flex-1 flex items-center justify-center py-1.5 rounded-md transition-all duration-150"
            :style="{
              backgroundColor: themeStore.mode === option.id ? 'var(--bg-secondary)' : 'transparent',
              color: themeStore.mode === option.id ? 'var(--accent)' : 'var(--text-muted)',
              boxShadow: themeStore.mode === option.id ? '0 1px 3px rgba(0,0,0,0.15)' : 'none',
            }"
          >
            <component :is="option.icon" class="size-4" />
          </button>
        </div>
      </template>
      <template v-else>
        <button
          @click="cycleTheme"
          class="w-full flex items-center justify-center p-2 rounded-lg transition-colors hover:opacity-80"
          style="color: var(--text-muted);"
          :title="`Theme: ${themeStore.mode}`"
        >
          <component :is="currentThemeIcon" class="size-5" />
        </button>
      </template>
    </div>

    <!-- Collapse toggle -->
    <div class="p-2 border-t" style="border-color: var(--border-color);">
      <button
        @click="isCollapsed = !isCollapsed"
        class="w-full flex items-center justify-center p-2 rounded-lg transition-colors hover:opacity-80"
        style="color: var(--text-muted);"
      >
        <LucideChevronLeft v-if="!isCollapsed" class="size-5" />
        <LucideChevronRight v-else class="size-5" />
      </button>
    </div>

    <!-- Credit footer -->
    <div
      v-if="!isCollapsed"
      class="px-3 py-3 border-t text-center space-y-1"
      style="border-color: var(--border-color);"
    >
      <p class="text-xs" style="color: var(--text-muted);">
        Developed by
        <a
          href="https://natnaeltilaye.com"
          target="_blank"
          rel="noopener noreferrer"
          class="font-medium hover:underline"
          style="color: var(--accent);"
        >Natnael Tilaye</a>
      </p>
      <p class="text-xs" style="color: var(--text-muted);">
        Powered by
        <a
          href="https://selfmadecs.com"
          target="_blank"
          rel="noopener noreferrer"
          class="font-medium hover:underline"
          style="color: var(--accent);"
        >SelfmadeERP</a>
      </p>
    </div>
  </aside>
</template>
