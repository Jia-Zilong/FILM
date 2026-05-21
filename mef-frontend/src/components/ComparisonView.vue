<script setup>
import { computed } from 'vue'
import { algorithms } from '../data/algorithms.js'
import { useFusion } from '../composables/useFusion'

const { comparisonResults, isComparing, startComparison, imageFiles, quality, maxDim } = useFusion()

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
</script>

<template>
  <div class="comparison-view">
    <!-- Header with run button -->
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

    <!-- Loading state -->
    <div v-if="isComparing" class="comp-loading">
      <div class="spinner"></div>
      <p>正在运行 5 种算法，请稍候...</p>
    </div>

    <!-- Results grid -->
    <div v-else-if="hasResults" class="comp-grid">
      <div
        v-for="(result, index) in comparisonResults"
        :key="result.algo"
        class="comp-card"
        :style="{ '--delay': index * 0.08 + 's' }"
      >
        <!-- Error card -->
        <template v-if="result.error">
          <div class="card-header error">
            <span class="algo-name">{{ getAlgoInfo(result.algo).fullName }}</span>
          </div>
          <div class="card-image error-placeholder">
            <span class="error-icon">!</span>
            <p class="error-msg">{{ result.error }}</p>
          </div>
        </template>

        <!-- Success card -->
        <template v-else>
          <div class="card-header">
            <span class="algo-name">{{ getAlgoInfo(result.algo).fullName }}</span>
          </div>
          <div class="card-image">
            <img :src="result.image_url" :alt="getAlgoInfo(result.algo).fullName" />
          </div>
          <div class="card-metrics">
            <div class="metric-item">
              <span class="m-label">EN</span>
              <span class="m-value">{{ fmt(result.en) }}</span>
            </div>
            <div class="metric-item">
              <span class="m-label">SD</span>
              <span class="m-value">{{ fmt(result.sd) }}</span>
            </div>
            <div class="metric-item">
              <span class="m-label">SF</span>
              <span class="m-value">{{ fmt(result.sf) }}</span>
            </div>
            <div class="metric-item">
              <span class="m-label">AG</span>
              <span class="m-value">{{ fmt(result.ag) }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="comp-empty">
      <p>上传源图像后点击「运行全部算法」进行多算法对比</p>
    </div>
  </div>
</template>

<style scoped>
.comparison-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Header */
.comp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
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

/* Loading */
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

/* Grid */
.comp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
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
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.comp-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-header {
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-subtle);
}

.card-header.error {
  border-bottom-color: var(--color-error);
  background: rgba(220, 38, 38, 0.05);
}

.algo-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
}

/* Image */
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

/* Metrics */
.card-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 8px;
  padding: 8px 12px;
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
  color: var(--color-primary);
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
@media (max-width: 767px) {
  .comp-grid {
    grid-template-columns: 1fr;
  }
}
</style>
