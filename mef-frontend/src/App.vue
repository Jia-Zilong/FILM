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
import ComparisonView from './components/ComparisonView.vue'
import { useFusion } from './composables/useFusion'

const {
  imageFiles, previews, isFusing, fusedImageUrl, metrics,
  selectedAlgo, fusionTime, quality, maxDim, selectedMetrics,
  setImageFiles, clearPreviews, startFusion,
} = useFusion()

const showHistory = ref(false)
const imageListRef = ref(null)
const viewMode = ref('fusion')
const showAlgoInfo = ref(false)

const handleFuse = async () => {
  showAlgoInfo.value = false
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

        <!-- Middle: image previews (2 columns) -->
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

        <!-- Collapsible Algorithm Info -->
        <div v-if="fusedImageUrl && !isFusing" class="algo-info-collapsible">
          <button class="algo-info-toggle" @click="showAlgoInfo = !showAlgoInfo">
            <span>{{ showAlgoInfo ? '收起' : '展开' }}算法说明</span>
            <span class="toggle-arrow" :class="{ open: showAlgoInfo }">&#9660;</span>
          </button>
          <Transition name="slide-up">
            <div v-if="showAlgoInfo" class="algo-info-content">
              <AlgorithmInfo :algo="selectedAlgo" />
            </div>
          </Transition>
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
          </div>
        </section>
        <ComparisonView />
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
  padding: 8px;
  display: flex;
  justify-content: center;
}

.workspace {
  width: 100%;
  max-width: 1600px;
  display: flex;
  flex-direction: column;
  gap: 10px;
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
  gap: 10px;
  padding: 8px;
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
  gap: 8px;
  min-width: 0;
}

.action-row {
  display: flex;
  gap: 8px;
}

.fuse-button {
  flex: 1;
  height: 36px;
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
  height: 36px;
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
  grid-template-columns: 1.2fr 1.5fr;
  gap: 10px;
  height: 40vh;
  min-height: 220px;
  max-height: 480px;
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
  display: grid;
  grid-template-columns: repeat(auto-fill, 80px);
  gap: 4px;
  align-content: flex-start;
  overflow-y: auto;
}

.img-container {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
  width: 80px;
  height: 68px;
}

.img-container .thumb-label {
  font-size: 9px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  padding: 1px 6px;
  background: var(--color-glass);
  line-height: 1;
}

.img-container img {
  width: 80px;
  height: 54px;
  object-fit: cover;
  display: block;
}

.result-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ===== Bottom Area ===== */
.bottom-area {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 10px;
  align-items: start;
}

/* ===== Collapsible Algorithm Info ===== */
.algo-info-collapsible {
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.algo-info-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 8px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  transition: var(--transition-smooth);
}

.algo-info-toggle:hover {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.toggle-arrow {
  font-size: 10px;
  transition: transform 0.2s;
}

.toggle-arrow.open {
  transform: rotate(180deg);
}

.algo-info-content {
  padding: 12px 16px 16px;
}

/* ===== Responsive ===== */
@media (max-width: 1199px) {
  .image-area {
    grid-template-columns: 1fr 1fr;
    min-height: 220px;
  }
  .bottom-area {
    grid-template-columns: 1fr;
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
