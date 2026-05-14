<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  metrics: { type: Object, default: null },
  fusionTime: { type: Number, default: null },
  fusedImageUrl: { type: String, default: '' }
})

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

const initRadarChart = () => {
  if (!chartRef.value || !props.metrics) return
  if (radarChart) radarChart.dispose()
  radarChart = echarts.init(chartRef.value)
  radarChart.setOption({
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#E2E8F0',
      textStyle: { color: '#0F172A' }
    },
    radar: {
      indicator: [
        { name: 'EN', max: 8 },
        { name: 'SD', max: 80 },
        { name: 'SF', max: 25 },
        { name: 'AG', max: 10 },
        { name: 'VIF', max: 2 },
        { name: 'Qabf', max: 1.0 }
      ],
      radius: '60%',
      axisName: { color: '#64748B', fontSize: 10, fontWeight: 600 },
      splitArea: { areaStyle: { color: ['rgba(248, 250, 252, 0.5)', 'rgba(241, 245, 249, 0.3)'] } },
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      splitLine: { lineStyle: { color: '#E2E8F0' } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          props.metrics.EN,
          props.metrics.SD,
          props.metrics.SF,
          props.metrics.AG,
          props.metrics.VIF ?? 0,
          props.metrics.Qabf ?? 0
        ],
        name: '评估得分',
        areaStyle: { color: 'rgba(37, 99, 235, 0.1)' },
        lineStyle: { color: '#2563EB', width: 2 },
        itemStyle: { color: '#2563EB', borderWidth: 2, borderColor: '#fff' }
      }]
    }]
  })
}

const initBarChart = () => {
  if (!barChartRef.value || !props.metrics) return
  if (barChart) barChart.dispose()
  barChart = echarts.init(barChartRef.value)

  const vifVal = props.metrics.VIF != null ? props.metrics.VIF : 0
  const qabfVal = props.metrics.Qabf != null ? props.metrics.Qabf : 0

  barChart.setOption({
    grid: { top: 12, bottom: 22, left: 30, right: 8 },
    xAxis: {
      type: 'category',
      data: ['EN', 'SD', 'SF', 'AG', 'VIF', 'Qabf'],
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisLabel: { color: '#64748B', fontSize: 10, fontWeight: 600 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F1F5F9' } },
      axisLabel: { color: '#94A3B8', fontSize: 9 }
    },
    series: [{
      type: 'bar',
      data: [
        { value: props.metrics.EN, itemStyle: { color: '#2563EB' } },
        { value: props.metrics.SD, itemStyle: { color: '#059669' } },
        { value: props.metrics.SF, itemStyle: { color: '#D97706' } },
        { value: props.metrics.AG, itemStyle: { color: '#DC2626' } },
        { value: vifVal, itemStyle: { color: '#8B5CF6' } },
        { value: qabfVal, itemStyle: { color: '#06B6D4' } }
      ],
      barWidth: 18,
      itemStyle: { borderRadius: '4px 4px 0 0' },
      animationDuration: 600,
      animationEasing: 'cubicOut'
    }]
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
    <div v-if="metrics" class="metrics-bar">
      <div class="metrics-values">
        <div class="metric-row" v-for="m in [
          { label: 'EN', value: metrics.EN.toFixed(4) },
          { label: 'SD', value: metrics.SD.toFixed(4) },
          { label: 'SF', value: metrics.SF.toFixed(4) },
          { label: 'AG', value: metrics.AG.toFixed(4) },
          { label: 'VIF', value: metrics.VIF != null ? metrics.VIF.toFixed(4) : '--' },
          { label: 'Qabf', value: metrics.Qabf != null ? metrics.Qabf.toFixed(4) : '--' },
        ]" :key="m.label">
          <span class="metric-label">{{ m.label }}</span>
          <span class="metric-value">{{ m.value }}</span>
        </div>
      </div>

      <div class="chart-section">
        <div ref="chartRef" class="radar-chart"></div>
      </div>

      <div class="chart-section flex-grow">
        <div ref="barChartRef" class="bar-chart"></div>
      </div>

      <div class="perf-info">
        <span class="perf-item">
          <span class="perf-label">耗时</span>
          <span class="perf-value">{{ fusionTime ? fusionTime + 'ms' : '--' }}</span>
        </span>
        <span class="perf-item">
          <span class="perf-label">尺寸</span>
          <span class="perf-value">{{ imageWidth }}×{{ imageHeight }}</span>
        </span>
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
