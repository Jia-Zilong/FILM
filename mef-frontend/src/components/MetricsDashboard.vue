<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount, computed } from 'vue'
import * as echarts from 'echarts'

const ALL_METRICS = ['EN', 'SD', 'SF', 'AG', 'VIF', 'Qabf']

const props = defineProps({
  metrics: { type: Object, default: null },
  fusionTime: { type: Number, default: null },
  fusedImageUrl: { type: String, default: '' },
  selectedMetrics: { type: Array, default: () => ['EN', 'SD', 'SF', 'AG', 'VIF', 'Qabf'] },
})

const localSelected = ref([...ALL_METRICS])

const effectiveMetrics = computed(() => {
  // Use prop if provided, otherwise use local state
  const sel = props.selectedMetrics && props.selectedMetrics.length > 0
    ? props.selectedMetrics
    : localSelected.value
  return sel
})

const toggleMetric = (m) => {
  const idx = localSelected.value.indexOf(m)
  if (idx >= 0) {
    localSelected.value.splice(idx, 1)
  } else {
    localSelected.value.push(m)
  }
}

const downloadImage = () => {
  if (!props.fusedImageUrl) return
  const a = document.createElement('a')
  a.href = props.fusedImageUrl
  a.download = `fused_${Date.now()}.jpg`
  a.click()
}

const chartRef = ref(null)
const barChartRef = ref(null)
let radarChart = null
let barChart = null

const imageWidth = ref('--')
const imageHeight = ref('--')
const handleResize = () => {
  radarChart?.resize()
  barChart?.resize()
}

const getMetricValue = (label) => {
  if (!props.metrics) return '--'
  const val = props.metrics[label]
  if (val === null || val === undefined) return '--'
  if (typeof val === 'number') return val.toFixed(4)
  return '--'
}

const getRadarValues = () => {
  return effectiveMetrics.value.map((m) => {
    if (!props.metrics) return 0
    const v = props.metrics[m]
    return (typeof v === 'number' && v > 0) ? v : 0
  })
}

const getBarValues = () => {
  return effectiveMetrics.value.map((m) => {
    if (!props.metrics) return 0
    const v = props.metrics[m]
    return (typeof v === 'number' && v > 0) ? v : 0
  })
}

const radarIndicators = computed(() => {
  const maxes = { EN: 8, SD: 80, SF: 25, AG: 10, VIF: 2, Qabf: 1.0 }
  return effectiveMetrics.value.map((m) => ({ name: m, max: maxes[m] ?? 1 }))
})

const barData = computed(() => {
  const colors = { EN: '#2563EB', SD: '#059669', SF: '#D97706', AG: '#DC2626', VIF: '#8B5CF6', Qabf: '#06B6D4' }
  return getBarValues().map((v, i) => ({
    value: v,
    itemStyle: { color: colors[effectiveMetrics.value[i]] || '#2563EB' },
  }))
})

const initRadarChart = () => {
  if (!chartRef.value || !props.metrics) return
  if (radarChart) radarChart.dispose()
  radarChart = echarts.init(chartRef.value)
  radarChart.setOption({
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#E2E8F0',
      textStyle: { color: '#0F172A' },
    },
    radar: {
      indicator: radarIndicators.value,
      radius: '60%',
      axisName: { color: '#64748B', fontSize: 10, fontWeight: 600 },
      splitArea: { areaStyle: { color: ['rgba(248, 250, 252, 0.5)', 'rgba(241, 245, 249, 0.3)'] } },
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      splitLine: { lineStyle: { color: '#E2E8F0' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: getRadarValues(),
        name: '评估得分',
        areaStyle: { color: 'rgba(37, 99, 235, 0.1)' },
        lineStyle: { color: '#2563EB', width: 2 },
        itemStyle: { color: '#2563EB', borderWidth: 2, borderColor: '#fff' },
      }],
    }],
  })
}

const initBarChart = () => {
  if (!barChartRef.value || !props.metrics) return
  if (barChart) barChart.dispose()
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    grid: { top: 12, bottom: 22, left: 30, right: 8 },
    xAxis: {
      type: 'category',
      data: effectiveMetrics.value,
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisLabel: { color: '#64748B', fontSize: 10, fontWeight: 600 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F1F5F9' } },
      axisLabel: { color: '#94A3B8', fontSize: 9 },
    },
    series: [{
      type: 'bar',
      data: barData.value,
      barWidth: 18,
      itemStyle: { borderRadius: '4px 4px 0 0' },
      animationDuration: 600,
      animationEasing: 'cubicOut',
    }],
  })
}

watch(() => props.metrics, (val) => {
  if (val) nextTick(() => {
    initRadarChart()
    initBarChart()
  })
})

watch(() => props.fusedImageUrl, (url) => {
  if (url) {
    const img = new Image()
    img.onload = () => {
      imageWidth.value = img.naturalWidth
      imageHeight.value = img.naturalHeight
    }
    img.src = url
  }
})

watch(() => effectiveMetrics.value.length, () => {
  if (props.metrics) nextTick(() => {
    initRadarChart()
    initBarChart()
  })
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
  barChart?.dispose()
})
</script>

<template>
  <Transition name="slide-up">
    <div v-if="fusedImageUrl" class="metrics-bar">
      <!-- Metric selection checkboxes -->
      <div class="metric-toggles">
        <label
          v-for="m in ALL_METRICS"
          :key="m"
          class="metric-toggle"
          :class="{ active: effectiveMetrics.includes(m) }"
        >
          <input type="checkbox" :checked="effectiveMetrics.includes(m)" @change="toggleMetric(m)" />
          <span>{{ m }}</span>
        </label>
      </div>

      <!-- Metric values -->
      <div v-if="metrics" class="metrics-values">
        <div
          class="metric-row"
          v-for="m in ALL_METRICS"
          :key="'v-' + m"
          v-show="effectiveMetrics.includes(m)"
        >
          <span class="metric-label">{{ m }}</span>
          <span class="metric-value">{{ getMetricValue(m) }}</span>
        </div>
      </div>

      <!-- Charts -->
      <div v-if="metrics && effectiveMetrics.length > 0" class="chart-section">
        <div ref="chartRef" class="radar-chart"></div>
      </div>

      <div v-if="metrics && effectiveMetrics.length > 0" class="chart-section flex-grow">
        <div ref="barChartRef" class="bar-chart"></div>
      </div>

      <!-- Perf info + download -->
      <div class="perf-info">
        <span class="perf-item" v-if="fusionTime">
          <span class="perf-label">耗时</span>
          <span class="perf-value">{{ fusionTime }}ms</span>
        </span>
        <span class="perf-item">
          <span class="perf-label">尺寸</span>
          <span class="perf-value">{{ imageWidth }}x{{ imageHeight }}</span>
        </span>
        <button class="download-btn" @click="downloadImage">
          <span class="dl-icon">⬇</span>
          <span class="dl-text">下载融合图</span>
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.metrics-bar {
  display: flex;
  align-items: stretch;
  gap: 12px;
  padding: 10px 14px;
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: 12px;
  box-shadow: var(--shadow-glass);
}

.metric-toggles {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 60px;
  flex-shrink: 0;
  justify-content: center;
}

.metric-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: all 0.15s;
}

.metric-toggle.active {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.metric-toggle input {
  display: none;
}

.metrics-values {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 130px;
  flex-shrink: 0;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}

.metric-label {
  color: var(--color-text-secondary);
  font-weight: 500;
}

.metric-value {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-primary);
  font-size: 11px;
}

.chart-section {
  min-width: 140px;
  flex-shrink: 0;
}

.chart-section.flex-grow {
  flex: 1;
  min-width: 0;
}

.radar-chart {
  height: 140px;
  width: 100%;
}

.bar-chart {
  height: 140px;
  width: 100%;
}

.perf-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  min-width: 100px;
  flex-shrink: 0;
}

.perf-item {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: 10px;
}

.perf-label {
  color: var(--color-text-secondary);
}

.perf-value {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-text);
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}

.download-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.dl-icon {
  font-size: 14px;
}

.slide-up-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 1199px) {
  .metrics-bar {
    flex-wrap: wrap;
  }
  .chart-section {
    min-width: 0;
    flex: 1;
  }
}

@media (max-width: 767px) {
  .metrics-bar {
    flex-direction: column;
  }
  .metrics-values {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
  }
  .metric-row {
    min-width: 80px;
  }
}
</style>
