<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { algorithms } from '../data/algorithms.js'
import { useFusion } from '../composables/useFusion'

const { comparisonResults, isComparing, startComparison, imageFiles, quality, maxDim } = useFusion()

const ALGO_COLORS = {
  ai: '#2563EB',
  ffmef: '#059669',
  avg: '#D97706',
  max: '#DC2626',
  mertens: '#8B5CF6',
}

const ALGO_NAMES = {
  ai: 'IF-FILM',
  ffmef: 'FFMEF',
  avg: '加权平均',
  max: '最大值',
  mertens: 'Mertens',
}

const METRIC_KEYS = ['en', 'sd', 'sf', 'ag']
const METRIC_LABELS = { en: 'EN', sd: 'SD', sf: 'SF', ag: 'AG' }

const barChartRef = ref(null)
const radarChartRef = ref(null)
let barChart = null
let radarChart = null

const handleResize = () => {
  barChart?.resize()
  radarChart?.resize()
}

onMounted(() => window.addEventListener('resize', handleResize))
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  barChart?.dispose()
  radarChart?.dispose()
})

function getAlgoInfo(slug) {
  return algorithms[slug] || { fullName: slug, principle: '' }
}

function fmt(val) {
  if (val === null || val === undefined) return '--'
  return typeof val === 'number' ? val.toFixed(4) : '--'
}

async function handleRun() {
  await startComparison(imageFiles.value, quality.value, maxDim.value)
}

const hasResults = computed(() => comparisonResults.value && comparisonResults.value.length > 0)
const validResults = computed(() =>
  (comparisonResults.value || []).filter((r) => !r.error)
)

watch(validResults, (results) => {
  if (results.length > 0) {
    nextTick(() => {
      initBarChart(results)
      initRadarChart(results)
    })
  }
})

function initBarChart(results) {
  if (!barChartRef.value) return
  if (barChart) barChart.dispose()
  barChart = echarts.init(barChartRef.value)

  const series = results.map((r) => ({
    name: ALGO_NAMES[r.algo] || r.algo,
    type: 'bar',
    data: METRIC_KEYS.map((k) => r[k] ?? 0),
    itemStyle: { color: ALGO_COLORS[r.algo] || '#2563EB', borderRadius: '3px 3px 0 0' },
    barMaxWidth: 28,
    label: {
      show: true,
      position: 'top',
      fontSize: 9,
      color: '#64748B',
      formatter: (p) => p.value.toFixed(2),
    },
  }))

  barChart.setOption({
    title: {
      text: '指标对比柱状图',
      left: 'center',
      textStyle: { fontSize: 13, color: '#0F172A', fontWeight: 600 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E2E8F0',
      textStyle: { color: '#0F172A' },
    },
    legend: {
      data: results.map((r) => ALGO_NAMES[r.algo] || r.algo),
      bottom: 0,
      textStyle: { fontSize: 10 },
    },
    grid: { top: 36, bottom: 36, left: 48, right: 12 },
    xAxis: {
      type: 'category',
      data: METRIC_KEYS.map((k) => METRIC_LABELS[k]),
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisLabel: { color: '#64748B', fontSize: 11, fontWeight: 600 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F1F5F9' } },
      axisLabel: { color: '#94A3B8', fontSize: 10 },
    },
    series,
    animationDuration: 600,
    animationEasing: 'cubicOut',
  })
}

function initRadarChart(results) {
  if (!radarChartRef.value) return
  if (radarChart) radarChart.dispose()
  radarChart = echarts.init(radarChartRef.value)

  const maxes = {}
  for (const k of METRIC_KEYS) {
    maxes[k] = Math.max(...results.map((r) => r[k] ?? 0), 0.01)
    maxes[k] = Math.ceil(maxes[k] * 10) / 10
  }

  const indicator = METRIC_KEYS.map((k) => ({ name: METRIC_LABELS[k], max: maxes[k] }))

  const radarData = results.map((r) => ({
    name: ALGO_NAMES[r.algo] || r.algo,
    value: METRIC_KEYS.map((k) => r[k] ?? 0),
    lineStyle: { color: ALGO_COLORS[r.algo] || '#2563EB', width: 2 },
    itemStyle: { color: ALGO_COLORS[r.algo] || '#2563EB' },
    areaStyle: {
      color: ALGO_COLORS[r.algo]
        ? ALGO_COLORS[r.algo] + '22'
        : 'rgba(37,99,235,0.1)',
    },
  }))

  radarChart.setOption({
    title: {
      text: '算法雷达图',
      left: 'center',
      textStyle: { fontSize: 13, color: '#0F172A', fontWeight: 600 },
    },
    tooltip: {
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E2E8F0',
      textStyle: { color: '#0F172A' },
    },
    legend: {
      data: results.map((r) => ALGO_NAMES[r.algo] || r.algo),
      bottom: 0,
      textStyle: { fontSize: 10 },
    },
    radar: {
      indicator,
      radius: '55%',
      axisName: { color: '#64748B', fontSize: 11, fontWeight: 600 },
      splitArea: {
        areaStyle: {
          color: ['rgba(248,250,252,0.5)', 'rgba(241,245,249,0.3)'],
        },
      },
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      splitLine: { lineStyle: { color: '#E2E8F0' } },
    },
    series: [{ type: 'radar', data: radarData }],
    animationDuration: 600,
    animationEasing: 'cubicOut',
  })
}

function fmtMetric(result, key) {
  return fmt(result[key])
}
</script>

<template>
  <div class="comparison-view">
    <!-- Header -->
    <div class="comp-header">
      <span class="comp-title">多算法对比</span>
      <el-button
        type="primary"
        size="large"
        :loading="isComparing"
        :disabled="imageFiles.length < 2"
        @click="handleRun"
      >
        {{ isComparing ? '对比中...' : '运行全部算法' }}
      </el-button>
    </div>

    <!-- Loading -->
    <div v-if="isComparing" class="comp-loading">
      <div class="spinner"></div>
      <p>正在运行 5 种算法，请稍候...</p>
    </div>

    <!-- Results -->
    <template v-else-if="hasResults">
      <!-- Charts -->
      <div class="charts-row">
        <div class="chart-card">
          <div ref="barChartRef" class="chart-container"></div>
        </div>
        <div class="chart-card">
          <div ref="radarChartRef" class="chart-container"></div>
        </div>
      </div>

      <!-- Result cards -->
      <div class="comp-grid">
        <div
          v-for="(result, index) in comparisonResults"
          :key="result.algo"
          class="comp-card"
          :style="{
            '--delay': index * 0.08 + 's',
            '--algo-color': ALGO_COLORS[result.algo] || '#2563EB',
          }"
        >
          <!-- Error -->
          <template v-if="result.error">
            <div class="card-header error">
              <span class="algo-name">{{ getAlgoInfo(result.algo).fullName }}</span>
            </div>
            <div class="card-image error-placeholder">
              <span class="error-icon">!</span>
              <p class="error-msg">{{ result.error }}</p>
            </div>
          </template>

          <!-- Success -->
          <template v-else>
            <div class="card-header">
              <span
                class="algo-name"
                :style="{ color: ALGO_COLORS[result.algo] || '#2563EB' }"
              >
                {{ ALGO_NAMES[result.algo] || result.algo }}
              </span>
            </div>
            <div class="card-image">
              <img :src="result.image_url" :alt="getAlgoInfo(result.algo).fullName" />
            </div>
            <div class="card-metrics">
              <div class="metric-item" v-for="k in METRIC_KEYS" :key="k">
                <span class="m-label">{{ METRIC_LABELS[k] }}</span>
                <span class="m-value">{{ fmtMetric(result, k) }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>

    <!-- Empty -->
    <div v-else class="comp-empty">
      <p>上传源图像后点击「运行全部算法」进行多算法对比</p>
    </div>
  </div>
</template>

<style scoped>
.comparison-view {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.comp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-md);
}

.comp-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.comp-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-md);
  gap: 12px;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.comp-loading p {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* Charts */
.charts-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 10px;
}

.chart-card {
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-md);
  padding: 8px;
  box-shadow: var(--shadow-glass);
}

.chart-container {
  width: 100%;
  height: 280px;
}

/* Grid */
.comp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}

/* Card */
.comp-card {
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-glass);
  transition: var(--transition-smooth);
  animation: card-in 0.4s cubic-bezier(0.16, 1, 0.3, 1) var(--delay) both;
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.comp-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-header {
  padding: 6px 10px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-subtle);
}

.card-header.error {
  border-bottom-color: var(--color-error);
  background: rgba(220, 38, 38, 0.05);
}

.algo-name {
  font-size: 12px;
  font-weight: 700;
}

.card-image {
  width: 100%;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: var(--color-bg-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.error-placeholder {
  flex-direction: column;
  gap: 6px;
}

.error-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(220, 38, 38, 0.1);
  color: var(--color-error);
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-msg {
  font-size: 11px;
  color: var(--color-error);
  text-align: center;
  padding: 0 12px 8px;
}

.card-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3px 8px;
  padding: 6px 10px;
  border-top: 1px solid var(--color-border);
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 11px;
}

.m-label {
  color: var(--color-text-secondary);
  font-weight: 500;
}

.m-value {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--algo-color, var(--color-primary));
  font-size: 11px;
}

/* Empty */
.comp-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-md);
  color: var(--color-text-tertiary);
  font-size: 13px;
}

/* Responsive */
@media (max-width: 1199px) {
  .charts-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .comp-grid {
    grid-template-columns: 1fr;
  }
  .chart-container {
    height: 240px;
  }
}
</style>
