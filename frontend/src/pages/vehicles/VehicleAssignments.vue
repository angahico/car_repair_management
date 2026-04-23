<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  LucideRefreshCw,
  LucideChevronLeft,
  LucideChevronRight,
  LucideUserCheck,
  LucideCar,
  LucideCalendar,
  LucideTable,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton, EmptyState } from '@/components/ui'

interface AssignmentBlock {
  id: string
  kind: 'custodian' | 'repair'
  start: string
  end: string
  title: string
  subtitle?: string
  color: string
  reference?: { doctype: string; name: string }
}

interface VehicleRow {
  name: string
  license_plate: string
  make: string
  model: string
  year: number
  thumbnail_url?: string
  status: string
  vehicle_type: string
  assignments: AssignmentBlock[]
}

type ViewMode = 'calendar' | 'table'
type ScaleMode = 'month' | 'week' | 'day'

const router = useRouter()
const { t } = useI18n()

const VEHICLE_COL_WIDTH = 220
const MIN_COL_WIDTH_MONTH = 28
const MIN_COL_WIDTH_WEEK = 60
const MIN_COL_WIDTH_DAY = 80

const viewMode = ref<ViewMode>('calendar')
const scaleMode = ref<ScaleMode>('month')
const isLoading = ref(true)
const vehicles = ref<VehicleRow[]>([])
const anchorDate = ref(new Date())
const hoveredBar = ref<{ id: string; x: number; y: number; title: string; subtitle?: string } | null>(null)
const calendarWrapperRef = ref<HTMLElement | null>(null)
const containerWidth = ref(1000)
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  loadData()
  nextTick(() => measureContainer())
  resizeObserver = new ResizeObserver(() => measureContainer())
  if (calendarWrapperRef.value) {
    resizeObserver.observe(calendarWrapperRef.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})

function measureContainer() {
  if (calendarWrapperRef.value) {
    containerWidth.value = calendarWrapperRef.value.clientWidth
  }
}

watch(calendarWrapperRef, (el) => {
  if (el && resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver.observe(el)
    measureContainer()
  }
})

const rangeStart = computed(() => {
  const d = new Date(anchorDate.value)
  if (scaleMode.value === 'month') {
    return new Date(d.getFullYear(), d.getMonth(), 1)
  } else if (scaleMode.value === 'week') {
    const day = d.getDay()
    const diff = day === 0 ? -6 : 1 - day
    const monday = new Date(d)
    monday.setDate(d.getDate() + diff)
    return monday
  }
  return new Date(d.getFullYear(), d.getMonth(), d.getDate())
})

const rangeEnd = computed(() => {
  const d = new Date(anchorDate.value)
  if (scaleMode.value === 'month') {
    return new Date(d.getFullYear(), d.getMonth() + 1, 0)
  } else if (scaleMode.value === 'week') {
    const sunday = new Date(rangeStart.value)
    sunday.setDate(rangeStart.value.getDate() + 6)
    return sunday
  }
  return new Date(d.getFullYear(), d.getMonth(), d.getDate())
})

const days = computed(() => {
  const result: Date[] = []
  const cur = new Date(rangeStart.value)
  while (cur <= rangeEnd.value) {
    result.push(new Date(cur))
    cur.setDate(cur.getDate() + 1)
  }
  return result
})

const columnWidth = computed(() => {
  const available = containerWidth.value - VEHICLE_COL_WIDTH
  const count = days.value.length || 1
  const ideal = available / count

  if (scaleMode.value === 'month') return Math.max(ideal, MIN_COL_WIDTH_MONTH)
  if (scaleMode.value === 'week') return Math.max(ideal, MIN_COL_WIDTH_WEEK)
  return Math.max(ideal, MIN_COL_WIDTH_DAY)
})

const trackWidth = computed(() => days.value.length * columnWidth.value)
const gridTotalWidth = computed(() => VEHICLE_COL_WIDTH + trackWidth.value)
const gridFillsContainer = computed(() => gridTotalWidth.value <= containerWidth.value)

const periodLabel = computed(() => {
  const d = anchorDate.value
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
  if (scaleMode.value === 'month') {
    return `${months[d.getMonth()]} ${d.getFullYear()}`
  } else if (scaleMode.value === 'week') {
    const s = rangeStart.value
    const e = rangeEnd.value
    const fmt = (dt: Date) => `${dt.getDate()} ${months[dt.getMonth()].slice(0, 3)}`
    return `${fmt(s)} – ${fmt(e)} ${e.getFullYear()}`
  }
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
})

const scaleModeLabels = computed<Record<ScaleMode, string>>(() => ({
  month: t('vehicle_assignments.month'),
  week: t('vehicle_assignments.week'),
  day: t('vehicle_assignments.day'),
}))

const todayStr = computed(() => formatDate(new Date()))

function formatDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function isWeekend(d: Date): boolean {
  return d.getDay() === 0 || d.getDay() === 6
}

function isToday(d: Date): boolean {
  return formatDate(d) === todayStr.value
}

function navigate(direction: -1 | 1) {
  const d = new Date(anchorDate.value)
  if (scaleMode.value === 'month') {
    d.setMonth(d.getMonth() + direction)
  } else if (scaleMode.value === 'week') {
    d.setDate(d.getDate() + direction * 7)
  } else {
    d.setDate(d.getDate() + direction)
  }
  anchorDate.value = d
}

function goToday() {
  anchorDate.value = new Date()
}

function dayLabel(d: Date): string {
  if (scaleMode.value === 'day') return formatDate(d)
  return String(d.getDate())
}

function dayHeaderSub(d: Date): string {
  const names = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
  return names[d.getDay()]
}

function parseDate(str: string): Date {
  const [y, m, d] = str.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function daysBetween(a: Date, b: Date): number {
  const utcA = Date.UTC(a.getFullYear(), a.getMonth(), a.getDate())
  const utcB = Date.UTC(b.getFullYear(), b.getMonth(), b.getDate())
  return Math.round((utcB - utcA) / 86400000)
}

function barStyle(assignment: AssignmentBlock) {
  const start = parseDate(assignment.start)
  const end = parseDate(assignment.end)
  const rStart = rangeStart.value
  const rEnd = rangeEnd.value

  const clampedStart = start < rStart ? rStart : start
  const clampedEnd = end > rEnd ? rEnd : end

  const totalDays = days.value.length
  const startOffset = daysBetween(rangeStart.value, clampedStart)
  const duration = daysBetween(clampedStart, clampedEnd) + 1

  const leftPct = (startOffset / totalDays) * 100
  const widthPct = (duration / totalDays) * 100
  const gapPct = totalDays > 1 ? 0.3 : 0

  const bg = assignment.kind === 'custodian'
    ? 'rgba(59, 130, 246, 0.25)'
    : 'rgba(245, 158, 11, 0.35)'
  const border = assignment.kind === 'custodian'
    ? 'rgba(59, 130, 246, 0.6)'
    : 'rgba(245, 158, 11, 0.7)'
  const textColor = assignment.kind === 'custodian'
    ? '#3b82f6'
    : '#d97706'

  return {
    left: `${leftPct + gapPct}%`,
    width: `max(20px, calc(${widthPct - gapPct * 2}%))`,
    backgroundColor: bg,
    borderLeft: `3px solid ${border}`,
    color: textColor,
  }
}

function todayOffset(): string {
  const today = new Date()
  const rStart = rangeStart.value
  const rEnd = rangeEnd.value
  if (today < rStart || today > rEnd) return '-9999px'
  const offset = daysBetween(rStart, today)
  const totalDays = days.value.length
  const pct = ((offset + 0.5) / totalDays) * 100
  return `${pct}%`
}

function showTooltip(event: MouseEvent, assignment: AssignmentBlock) {
  hoveredBar.value = {
    id: assignment.id,
    x: event.clientX,
    y: event.clientY - 10,
    title: assignment.title,
    subtitle: assignment.subtitle,
  }
}

function hideTooltip() {
  hoveredBar.value = null
}

function navigateToVehicle(vehicleName: string) {
  router.push(`/vehicles/${vehicleName}`)
}

function navigateToAssignment(assignment: AssignmentBlock) {
  if (!assignment.reference) return
  const { doctype, name } = assignment.reference
  if (doctype === 'Repair Order') {
    router.push(`/repair-orders/${name}`)
  } else if (doctype === 'Employee') {
    router.push(`/employees/${name}`)
  }
}

const allAssignments = computed(() => {
  const result: (AssignmentBlock & { vehicle_label: string; vehicle_name: string })[] = []
  for (const v of vehicles.value) {
    for (const a of v.assignments) {
      result.push({
        ...a,
        vehicle_label: `${v.license_plate} – ${v.make} ${v.model}`,
        vehicle_name: v.name,
      })
    }
  }
  result.sort((a, b) => a.start.localeCompare(b.start))
  return result
})

async function loadData() {
  isLoading.value = true
  try {
    const data = await apiCall<{ range: { start: string; end: string }; vehicles: VehicleRow[] }>(
      'car_repair_management.api.vehicle_assignments.get_vehicle_assignments',
      {
        range_start: formatDate(rangeStart.value),
        range_end: formatDate(rangeEnd.value),
      },
    )
    vehicles.value = data?.vehicles || []
  } catch (e) {
    console.error('Failed to load vehicle assignments', e)
    vehicles.value = []
  } finally {
    isLoading.value = false
  }
}

watch([rangeStart, rangeEnd], () => loadData(), { immediate: false })
</script>

<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-page-title" style="color: var(--text-primary);">{{ $t('vehicles.assignments_title') }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted);">{{ $t('vehicle_assignments.resource_scheduling') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <Button variant="outline" @click="loadData">
          <LucideRefreshCw class="size-4" :class="{ 'animate-spin': isLoading }" />
        </Button>
      </div>
    </div>

    <!-- Controls Row -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
      <!-- View mode toggle -->
      <div class="inline-flex rounded-lg overflow-hidden" style="border: 1px solid var(--border-color);">
        <button
          class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium transition-colors"
          :style="{
            backgroundColor: viewMode === 'calendar' ? 'var(--accent)' : 'transparent',
            color: viewMode === 'calendar' ? 'var(--accent-text)' : 'var(--text-secondary)',
          }"
          @click="viewMode = 'calendar'"
        >
          <LucideCalendar class="size-3.5" />
          {{ $t('vehicle_assignments.calendar') }}
        </button>
        <button
          class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium transition-colors"
          :style="{
            backgroundColor: viewMode === 'table' ? 'var(--accent)' : 'transparent',
            color: viewMode === 'table' ? 'var(--accent-text)' : 'var(--text-secondary)',
            borderLeft: '1px solid var(--border-color)',
          }"
          @click="viewMode = 'table'"
        >
          <LucideTable class="size-3.5" />
          {{ $t('vehicle_assignments.table') }}
        </button>
      </div>

      <!-- Date navigator -->
      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" @click="navigate(-1)">
          <LucideChevronLeft class="size-4" />
        </Button>
        <button
          class="px-3 py-1 text-sm font-medium rounded-md transition-colors"
          style="color: var(--text-primary);"
          @click="goToday"
        >
          {{ periodLabel }}
        </button>
        <Button variant="outline" size="sm" @click="navigate(1)">
          <LucideChevronRight class="size-4" />
        </Button>
        <Button variant="ghost" size="sm" @click="goToday" style="color: var(--text-muted);">
          {{ $t('vehicle_assignments.today') }}
        </Button>
      </div>

      <!-- Scale toggle (calendar only) -->
      <div v-if="viewMode === 'calendar'" class="inline-flex rounded-lg overflow-hidden" style="border: 1px solid var(--border-color);">
        <button
          v-for="s in (['month', 'week', 'day'] as ScaleMode[])"
          :key="s"
          class="px-3 py-1.5 text-xs font-medium transition-colors"
          :style="{
            backgroundColor: scaleMode === s ? 'var(--accent)' : 'transparent',
            color: scaleMode === s ? 'var(--accent-text)' : 'var(--text-secondary)',
            borderLeft: s !== 'month' ? '1px solid var(--border-color)' : 'none',
          }"
          @click="scaleMode = s"
        >
          {{ scaleModeLabels[s] }}
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <Card v-if="isLoading" padding="none">
      <div class="p-4 space-y-3">
        <Skeleton height="40px" />
        <Skeleton v-for="i in 6" :key="i" height="64px" />
      </div>
    </Card>

    <!-- Empty state -->
    <Card v-else-if="vehicles.length === 0">
      <EmptyState
        :icon="LucideUserCheck"
        :title="$t('vehicle_assignments.no_vehicle_assignments')"
        :description="$t('vehicle_assignments.no_vehicle_assignments_desc')"
      />
    </Card>

    <!-- Calendar View -->
    <Card v-else-if="viewMode === 'calendar'" padding="none">
      <div
        ref="calendarWrapperRef"
        class="calendar-wrapper"
        :class="gridFillsContainer ? '' : 'overflow-x-auto'"
        style="overflow-y: auto; max-height: 75vh;"
      >
        <div
          class="calendar-grid"
          :style="{ width: gridFillsContainer ? '100%' : `${gridTotalWidth}px` }"
        >
          <!-- Header row -->
          <div class="calendar-header" style="position: sticky; top: 0; z-index: 20; display: flex;">
            <!-- Corner cell -->
            <div
              class="calendar-corner"
              :style="{
                position: 'sticky',
                left: 0,
                zIndex: 30,
                width: `${VEHICLE_COL_WIDTH}px`,
                minWidth: `${VEHICLE_COL_WIDTH}px`,
                backgroundColor: 'var(--bg-elevated)',
                borderBottom: '1px solid var(--border-color)',
                borderRight: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center',
              }"
            >
              <span class="px-4 py-2 text-xs font-medium" style="color: var(--text-muted);">{{ $t('vehicle_assignments.vehicle_col') }}</span>
            </div>
            <!-- Day columns header -->
            <div class="flex flex-1 min-w-0">
              <div
                v-for="d in days"
                :key="formatDate(d)"
                class="flex flex-col items-center justify-center py-1.5"
                :style="{
                  flex: gridFillsContainer ? '1 1 0%' : `0 0 ${columnWidth}px`,
                  minWidth: gridFillsContainer ? '0' : `${columnWidth}px`,
                  backgroundColor: isToday(d) ? 'rgba(59, 130, 246, 0.1)' : isWeekend(d) ? 'var(--bg-tertiary)' : 'var(--bg-elevated)',
                  borderBottom: '1px solid var(--border-color)',
                  borderRight: '1px solid var(--border-subtle)',
                }"
              >
                <span class="text-[10px] font-medium" :style="{ color: isToday(d) ? '#3b82f6' : 'var(--text-muted)' }">{{ dayHeaderSub(d) }}</span>
                <span
                  class="text-xs font-semibold leading-tight"
                  :style="{ color: isToday(d) ? '#3b82f6' : 'var(--text-primary)' }"
                >{{ dayLabel(d) }}</span>
              </div>
            </div>
          </div>

          <!-- Vehicle rows -->
          <div
            v-for="(vehicle, vIdx) in vehicles"
            :key="vehicle.name"
            class="calendar-row flex"
            :style="{ backgroundColor: vIdx % 2 === 0 ? 'transparent' : 'var(--bg-tertiary)' }"
          >
            <!-- Vehicle info (sticky, clickable) -->
            <div
              class="flex items-center gap-3 px-3 cursor-pointer group"
              :style="{
                position: 'sticky',
                left: 0,
                zIndex: 10,
                width: `${VEHICLE_COL_WIDTH}px`,
                minWidth: `${VEHICLE_COL_WIDTH}px`,
                height: '64px',
                borderRight: '1px solid var(--border-color)',
                borderBottom: '1px solid var(--border-subtle)',
                backgroundColor: vIdx % 2 === 0 ? 'var(--bg-elevated)' : 'var(--bg-tertiary)',
              }"
              @click="navigateToVehicle(vehicle.name)"
            >
              <div
                v-if="vehicle.thumbnail_url"
                class="w-9 h-9 rounded-md overflow-hidden flex-shrink-0"
                style="border: 1px solid var(--border-subtle);"
              >
                <img :src="vehicle.thumbnail_url" :alt="vehicle.license_plate" class="w-full h-full object-cover" />
              </div>
              <div v-else class="w-9 h-9 rounded-md flex items-center justify-center flex-shrink-0" style="background-color: var(--bg-tertiary);">
                <LucideCar class="size-4" style="color: var(--text-muted);" />
              </div>
              <div class="min-w-0">
                <p class="text-sm font-semibold truncate group-hover:underline" style="color: var(--text-primary);">{{ vehicle.license_plate }}</p>
                <p class="text-[11px] truncate" style="color: var(--text-muted);">{{ vehicle.make }} {{ vehicle.model }}</p>
              </div>
            </div>

            <!-- Track area -->
            <div
              class="relative flex-1 min-w-0"
              :style="{ height: '64px', minWidth: gridFillsContainer ? '0' : `${trackWidth}px` }"
            >
              <!-- Day grid lines & weekend shading -->
              <div class="absolute inset-0 flex">
                <div
                  v-for="d in days"
                  :key="formatDate(d)"
                  class="h-full"
                  :style="{
                    flex: gridFillsContainer ? '1 1 0%' : `0 0 ${columnWidth}px`,
                    backgroundColor: isWeekend(d) ? 'rgba(128,128,128,0.04)' : 'transparent',
                    borderRight: '1px solid var(--border-subtle)',
                    borderBottom: '1px solid var(--border-subtle)',
                  }"
                />
              </div>

              <!-- Today marker -->
              <div
                v-if="todayOffset() !== '-9999px'"
                class="absolute top-0 bottom-0"
                :style="{
                  left: todayOffset(),
                  width: '2px',
                  backgroundColor: 'rgba(59, 130, 246, 0.5)',
                  zIndex: 5,
                }"
              />

              <!-- Assignment bars -->
              <div
                v-for="assignment in vehicle.assignments"
                :key="assignment.id"
                class="absolute rounded-sm cursor-pointer transition-opacity hover:opacity-90 flex items-center px-1.5 overflow-hidden"
                :style="{
                  ...barStyle(assignment),
                  top: assignment.kind === 'custodian' ? '6px' : '34px',
                  height: '24px',
                  zIndex: 6,
                  fontSize: '11px',
                  fontWeight: 500,
                  whiteSpace: 'nowrap',
                }"
                @mouseenter="showTooltip($event, assignment)"
                @mouseleave="hideTooltip"
                @click="navigateToAssignment(assignment)"
              >
                <span class="truncate underline-offset-2 hover:underline">{{ assignment.title }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>

    <!-- Table View -->
    <Card v-else padding="none">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b" style="background-color: var(--bg-tertiary); border-color: var(--border-color);">
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicle_assignments.vehicle_col') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicle_assignments.type_label') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicle_assignments.assignee') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicle_assignments.start') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicle_assignments.end') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ $t('vehicle_assignments.reference') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y" style="border-color: var(--border-color);">
            <tr v-if="allAssignments.length === 0">
              <td colspan="6" class="px-4 py-8">
                <EmptyState
                  :icon="LucideUserCheck"
                  :title="$t('vehicle_assignments.no_assignments_period')"
                  :description="$t('vehicle_assignments.no_assignments_period_desc')"
                />
              </td>
            </tr>
            <tr
              v-for="row in allAssignments"
              :key="row.id"
              class="transition-colors hover:opacity-80"
            >
              <td class="px-4 py-3">
                <div
                  class="flex items-center gap-2 cursor-pointer hover:underline"
                  @click="router.push(`/vehicles/${row.vehicle_name}`)"
                >
                  <LucideCar class="size-4 flex-shrink-0" style="color: var(--text-muted);" />
                  <span class="text-sm font-medium" style="color: var(--text-primary);">{{ row.vehicle_label }}</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <Badge :variant="row.kind === 'custodian' ? 'info' : 'warning'" size="sm">
                  {{ row.kind === 'custodian' ? $t('vehicle_assignments.custodian') : $t('vehicle_assignments.repair') }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-sm" style="color: var(--text-primary);">
                {{ row.title }}
              </td>
              <td class="px-4 py-3 text-sm" style="color: var(--text-secondary);">
                {{ row.start }}
              </td>
              <td class="px-4 py-3 text-sm" style="color: var(--text-secondary);">
                {{ row.kind === 'custodian' && !row.end ? $t('vehicle_assignments.ongoing') : row.end }}
              </td>
              <td class="px-4 py-3 text-sm">
                <span
                  v-if="row.reference"
                  class="cursor-pointer hover:underline"
                  style="color: var(--accent);"
                  @click="navigateToAssignment(row)"
                >
                  {{ row.reference.name }}
                </span>
                <span v-else style="color: var(--text-muted);">–</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Tooltip -->
    <Teleport to="body">
      <div
        v-if="hoveredBar"
        class="fixed rounded-lg px-3 py-2 shadow-lg pointer-events-none"
        style="
          z-index: 9999;
          background-color: var(--bg-elevated);
          border: 1px solid var(--border-color);
          transform: translate(-50%, -100%);
          max-width: 250px;
        "
        :style="{ left: `${hoveredBar.x}px`, top: `${hoveredBar.y}px` }"
      >
        <p class="text-sm font-medium" style="color: var(--text-primary);">{{ hoveredBar.title }}</p>
        <p v-if="hoveredBar.subtitle" class="text-xs mt-0.5" style="color: var(--text-muted);">{{ hoveredBar.subtitle }}</p>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.calendar-wrapper {
  scrollbar-width: thin;
}
</style>
