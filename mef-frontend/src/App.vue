<script setup>
import { onBeforeUnmount, ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import ImageList from './components/ImageList.vue'
import AlgorithmSelector from './components/AlgorithmSelector.vue'
import FusionViewer from './components/FusionViewer.vue'
import MetricsDashboard from './components/MetricsDashboard.vue'
import HistoryDrawer from './components/HistoryDrawer.vue'
import ParamPanel from './components/ParamPanel.vue'
import AlgorithmInfo from './components/AlgorithmInfo.vue'
import { useFusion } from './composables/useFusion'

const {
  imageFiles, previews, isFusing, fusedImageUrl, metrics,
  selectedAlgo, fusionTime, quality, maxDim, selectedMetrics,
  isComparing, startComparison,
  setImageFiles, clearPreviews, startFusion,
} = useFusion()

const showHistory = ref(false)
const imageListRef = ref(null)
const viewMode = ref('fusion')

const handleFuse = async () => {
  await startFusion()
}

const handleClear = () => {
  imageListRef.value?.clearAll()
  clearPreviews()
}

onBeforeUnmount(clearPreviews)
</script>

<template>
  <div class="app-layout">
    <AppHeader @open-history="showHistory = true" />

    <!-- View mode toggle -->
    <div class="view-toggle">
      <button :class="{ active: viewMode === 'fusion' }" @click="viewMode = 'fusion'">融合</button>
      <button :class="{ active: viewMode === 'compare' }" @click="viewMode = 'compare'">对比</button>
    </div>

    <!-- Fusion view -->
    <main v-if="viewMode === 'fusion'" class="app-main">
      <div class="workspace">
        <!-- Top: image uploads + controls -->
        <section class="top-bar">
          <ImageList
            ref="imageListRef"
            v-model="imageFiles"
            @update:model-value="setImageFiles"
          />

          <div class="controls">
            <AlgorithmSelector v-model="selectedAlgo" />
            <div class="action-row">
              <el-button
                type="primary"
                size="large"
                class="fuse-button"
                :loading="isFusing"
                @click="handleFuse"
                :disabled="imageFiles.length < 2"
              >
                {{ isFusing ? `融合中 (${imageFiles.length}张)...` : '执行融合' }}
              </el-button>
              <el-button
                size="large"
                class="clear-button"
                @click="handleClear"
                :disabled="isFusing"
              >
                清空
              </el-button>
            </div>
          </div>
        </section>

        <!-- Middle: image previews + algorithm info -->
        <section class="image-area">
          <div class="source-col">
            <div class="source-label">源图像 ({{ previews.length }}张)</div>
            <div class="source-grid">
              <div
                v-for="(src, index) in previews"
                :key="index"
                class="img-container has-img"
              >
                <div class="thumb-label">图{{ index + 1 }}</div>
                <img :src="src" :alt="imageFiles[index]?.name || `Image ${index + 1}`" />
              </div>
            </div>
          </div>
          <div class="result-col">
            <div class="source-label">融合结果</div>
            <FusionViewer
              :fused-image-url="fusedImageUrl"
              :under-preview="previews.length > 0 ? previews[previews.length - 1] : ''"
              :over-preview="previews.length > 0 ? previews[0] : ''"
              :is-fusing="isFusing"
            />
          </div>
          <!-- Algorithm info sidebar -->
          <div v-if="fusedImageUrl && !isFusing" class="algo-info-col">
            <AlgorithmInfo :algo="selectedAlgo" />
          </div>
        </section>

        <!-- Bottom: parameters + metrics -->
        <div class="bottom-area">
          <ParamPanel
            v-model:quality="quality"
            v-model:max-dim="maxDim"
          />
          <MetricsDashboard
            :metrics="metrics"
            :fusion-time="fusionTime"
            :fused-image-url="fusedImageUrl"
            :selected-metrics="selectedMetrics"
          />
        </div>
      </div>
    </main>

    <!-- Comparison view -->
    <main v-else class="app-main">
      <div class="workspace">
        <section class="top-bar">
          <ImageList
            ref="imageListRef"
            v-model="imageFiles"
            @update:model-value="setImageFiles"
          />
          <div class="controls">
            <ParamPanel
              v-model:quality="quality"
              v-model:max-dim="maxDim"
            />
            <el-button
              type="primary"
              size="large"
              :loading="isComparing"
              @click="startComparison"
              :disabled="imageFiles.length < 2"
            >
              {{ isComparing ? '对比中...' : '运行全部算法对比' }}
            </el-button>
          </div>
        </section>
        <div class="comparison-placeholder">
          <p>对比功能将在下一步添加</p>
        </div>
      </div>
    </main>

    <HistoryDrawer v-model:visible="showHistory" />
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-main {
  flex: 1;
  padding: 12px;
  display: flex;
  justify-content: center;
}

.workspace {
  width: 100%;
  max-width: 1600px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* View toggle */
.view-toggle {
  display: flex;
  gap: 4px;
  padding: 8px 12px 0;
  justify-content: center;
}

.view-toggle button {
  padding: 6px 20px;
  border: 1px solid var(--color-border);
  border-radius: 8px 8px 0 0;
  background: var(--color-card);
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.view-toggle button.active {
  background: var(--color-glass);
  border-bottom-color: var(--color-glass);
  color: var(--color-primary);
  font-weight: 600;
}

/* ===== Top Bar ===== */
.top-bar {
  display: flex;
  align-items: stretch;
  gap: 12px;
  padding: 12px;
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: 12px;
}

.controls {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
  min-width: 0;
}

.action-row {
  display: flex;
  gap: 8px;
}

.fuse-button {
  flex: 1;
  height: 38px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
  transition: var(--transition-smooth);
}

.fuse-button:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.3);
  transform: translateY(-1px);
}

.fuse-button:disabled {
  background: linear-gradient(135deg, #94A3B8 0%, #64748B 100%);
}

.clear-button {
  height: 38px;
  min-width: 70px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

.clear-button:hover:not(:disabled) {
  border-color: var(--color-error);
  color: var(--color-error);
}

/* ===== Image Area ===== */
.image-area {
  display: grid;
  grid-template-columns: 1.2fr 1.5fr auto;
  gap: 12px;
  height: 50vh;
  min-height: 260px;
  max-height: 580px;
}

.source-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.source-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.source-grid {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-content: flex-start;
  overflow-y: auto;
}

.img-container {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  min-width: 0;
}

.img-container .thumb-label {
  font-size: 9px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  padding: 2px 6px;
  background: var(--color-glass);
}

.img-container img {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
  display: block;
}

.result-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.algo-info-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-self: flex-start;
  padding-top: 20px;
}

/* ===== Bottom Area ===== */
.bottom-area {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

/* Comparison placeholder */
.comparison-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: 12px;
  color: var(--color-text-tertiary);
  font-size: 14px;
}

/* ===== Responsive ===== */
@media (max-width: 1199px) {
  .image-area {
    grid-template-columns: 1fr 1fr;
    min-height: 260px;
  }
  .result-col {
    grid-column: 1 / -1;
  }
  .algo-info-col {
    display: none;
  }
}

@media (max-width: 767px) {
  .top-bar {
    flex-direction: column;
  }
  .image-area {
    grid-template-columns: 1fr;
  }
}
</style>
