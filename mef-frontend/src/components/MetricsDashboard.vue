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
      radius: '65%',
      axisName: { color: '#64748B', fontSize: 11, fontWeight: 600 },
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
    grid: { top: 16, bottom: 28, left: 35, right: 10 },
    xAxis: {
      type: 'category',
      data: ['EN', 'SD', 'SF', 'AG', 'VIF', 'Qabf'],
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisLabel: { color: '#64748B', fontSize: 11, fontWeight: 600 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F1F5F9' } },
      axisLabel: { color: '#94A3B8', fontSize: 10 }
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
      barWidth: 20,
      itemStyle: { borderRadius: '6px 6px 0 0' },
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
    <div v-if="metrics" class="metrics-dashboard">
      <div class="metrics-grid">
        <div class="metrics-table">
          <div class="table-title">
            <el-icon class="title-icon"><DataAnalysis /></el-icon>
            评价指标
          </div>
          <table class="data-table">
            <tbody>
              <tr>
                <td class="label-cell">EN (信息熵)</td>
                <td class="value-cell">{{ metrics.EN.toFixed(4) }}</td>
              </tr>
              <tr>
                <td class="label-cell">SD (标准差)</td>
                <td class="value-cell">{{ metrics.SD.toFixed(4) }}</td>
              </tr>
              <tr>
                <td class="label-cell">SF (空间频率)</td>
                <td class="value-cell">{{ metrics.SF.toFixed(4) }}</td>
              </tr>
              <tr>
                <td class="label-cell">AG (平均梯度)</td>
                <td class="value-cell">{{ metrics.AG.toFixed(4) }}</td>
              </tr>
              <tr>
                <td class="label-cell">VIF (视觉信息保真度)</td>
                <td class="value-cell">{{ metrics.VIF != null ? metrics.VIF.toFixed(4) : '--' }}</td>
              </tr>
              <tr>
                <td class="label-cell">Qabf (边缘信息保持度)</td>
                <td class="value-cell">{{ metrics.Qabf != null ? metrics.Qabf.toFixed(4) : '--' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="chart-box">
          <div class="chart-title">
            <el-icon class="title-icon"><PieChart /></el-icon>
            雷达图
          </div>
          <div ref="chartRef" class="radar-container"></div>
        </div>
      </div>

      <div class="chart-box full-width">
        <div class="chart-title">
          <el-icon class="title-icon"><Histogram /></el-icon>
          指标柱状图
        </div>
        <div ref="barChartRef" class="bar-container"></div>
      </div>

      <div class="perf-info">
        <span class="perf-item">
          <el-icon class="perf-icon"><Timer /></el-icon>
          <span class="perf-label">推理耗时</span>
          <span class="perf-value">{{ fusionTime ? fusionTime + ' ms' : '--' }}</span>
        </span>
        <span class="perf-divider"></span>
        <span class="perf-item">
          <el-icon class="perf-icon"><Crop /></el-icon>
          <span class="perf-label">图像尺寸</span>
          <span class="perf-value">{{ imageWidth }} × {{ imageHeight }}</span>
        </span>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.metrics-dashboard {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-glass);
  transition: opacity 0.4s ease;
}

.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  min-width: 220px;
  flex-shrink: 0;
}

.table-title,
.chart-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-3);
}

.title-icon {
  font-size: 14px;
  color: var(--color-primary);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: var(--color-card);
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.data-table tr {
  border-bottom: 1px solid var(--color-border);
  transition: background 0.15s ease;
}

.data-table tr:last-child {
  border-bottom: none;
}

.data-table tr:hover {
  background: var(--color-bg-subtle);
}

.label-cell {
  padding: var(--space-3) var(--space-4);
  color: var(--color-text-secondary);
  font-weight: 500;
  background: var(--color-bg);
  width: 50%;
}

.value-cell {
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-primary);
  font-size: 13px;
}

.chart-box {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  box-shadow: var(--shadow-xs);
  min-width: 220px;
  flex-shrink: 0;
}

.chart-box.full-width {
  flex: 1;
  min-width: 0;
}

.radar-container {
  height: 220px;
  width: 100%;
}

.bar-container {
  height: 180px;
  width: 100%;
}

.perf-info {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 12px;
  box-shadow: var(--shadow-xs);
}

.perf-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.perf-icon {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.perf-label {
  color: var(--color-text-secondary);
}

.perf-value {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-text);
}

.perf-divider {
  width: 1px;
  height: 16px;
  background: var(--color-border);
}

.slide-up-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(16px);
}

/* Responsive: stack on small screens */
@media (max-width: 1199px) {
  .metrics-dashboard {
    flex-direction: column;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-4);
  }

  .chart-box {
    min-width: 0;
  }
}

@media (max-width: 767px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
