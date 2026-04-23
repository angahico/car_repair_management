<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

interface Props {
  option: echarts.EChartsOption
  height?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '300px',
  loading: false,
})

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

function getThemeColors() {
  const style = getComputedStyle(document.documentElement)
  return {
    textPrimary: style.getPropertyValue('--text-primary').trim() || '#1f2937',
    textMuted: style.getPropertyValue('--text-muted').trim() || '#6b7280',
    borderColor: style.getPropertyValue('--border-color').trim() || '#e5e7eb',
    bgSecondary: style.getPropertyValue('--bg-secondary').trim() || '#f9fafb',
  }
}

onMounted(() => {
  if (!chartRef.value) return

  const colors = getThemeColors()

  chart = echarts.init(chartRef.value, undefined, { renderer: 'canvas' })

  const baseOption: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    textStyle: {
      color: colors.textMuted,
    },
    legend: {
      textStyle: { color: colors.textMuted },
    },
    xAxis: {
      axisLine: { lineStyle: { color: colors.borderColor } },
      axisLabel: { color: colors.textMuted },
      splitLine: { lineStyle: { color: colors.borderColor } },
    },
    yAxis: {
      axisLine: { lineStyle: { color: colors.borderColor } },
      axisLabel: { color: colors.textMuted },
      splitLine: { lineStyle: { color: colors.borderColor } },
    },
  }

  chart.setOption(baseOption)

  if (props.option) {
    chart.setOption(props.option, true)
  }

  if (props.loading) {
    chart.showLoading()
  }

  resizeObserver = new ResizeObserver(() => {
    chart?.resize()
  })
  resizeObserver.observe(chartRef.value)
})

watch(
  () => props.option,
  (newOption) => {
    if (chart && newOption) {
      chart.setOption(newOption, true)
    }
  },
  { deep: true },
)

watch(
  () => props.loading,
  (isLoading) => {
    if (!chart) return
    if (isLoading) {
      chart.showLoading()
    } else {
      chart.hideLoading()
    }
  },
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="chartRef" :style="{ height, width: '100%' }" />
</template>
