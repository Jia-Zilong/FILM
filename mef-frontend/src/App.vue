<script setup>
import { onBeforeUnmount, ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import DraggableUpload from './components/DraggableUpload.vue'
import AlgorithmSelector from './components/AlgorithmSelector.vue'
import FusionViewer from './components/FusionViewer.vue'
import MetricsDashboard from './components/MetricsDashboard.vue'
import HistoryDrawer from './components/HistoryDrawer.vue'
import { useFusion } from './composables/useFusion'

const {
  overFile, underFile, overPreview, underPreview,
  isFusing, fusedImageUrl, metrics, selectedAlgo, fusionTime,
  setOverImage, setUnderImage, startFusion, downloadImage, clearPreviews
} = useFusion()

const showHistory = ref(false)

const handleFuse = async () => {
  await startFusion()
}

onBeforeUnmount(clearPreviews)
</script>

<template>
  <div class="app-layout">
    <AppHeader @open-history="showHistory = true" />

    <main class="app-main">
      <div class="workspace">
        <!-- Row 1: Input Row (horizontal) -->
        <section class="input-row">
          <div class="upload-group">
            <DraggableUpload
              label="过曝图像 (Over)"
              v-model="overFile"
              @update:model-value="setOverImage"
            />
            <DraggableUpload
              label="欠曝图像 (Under)"
              v-model="underFile"
              @update:model-value="setUnderImage"
            />
          </div>

          <div class="algo-section">
            <AlgorithmSelector v-model="selectedAlgo" />
          </div>

          <el-button
            type="primary"
            size="large"
            class="fuse-button"
            :loading="isFusing"
            @click="handleFuse"
          >
            {{ isFusing ? '融合中...' : '执行融合' }}
          </el-button>
        </section>

        <!-- Row 2: Display Row -->
        <section class="display-row">
          <div class="source-panel">
            <div class="panel-header">
              <h3 class="panel-title">源图像</h3>
              <div class="source-labels">
                <span class="source-tag">过曝</span>
                <span class="source-tag">欠曝</span>
              </div>
            </div>
            <div class="source-images">
              <div class="source-image-wrapper" :class="{ empty: !overPreview }">
                <img v-if="overPreview" :src="overPreview" alt="过曝" class="source-img" />
                <div v-else class="source-empty">
                  <el-icon><Picture /></el-icon>
                  <span>过曝</span>
                </div>
              </div>
              <div class="source-image-wrapper" :class="{ empty: !underPreview }">
                <img v-if="underPreview" :src="underPreview" alt="欠曝" class="source-img" />
                <div v-else class="source-empty">
                  <el-icon><Picture /></el-icon>
                  <span>欠曝</span>
                </div>
              </div>
            </div>
          </div>

          <div class="result-panel">
            <FusionViewer
              :fused-image-url="fusedImageUrl"
              :under-preview="underPreview"
              :over-preview="overPreview"
              :is-fusing="isFusing"
              @download="downloadImage"
            />
          </div>
        </section>

        <!-- Row 3: Metrics Row -->
        <section class="metrics-row">
          <MetricsDashboard
            :metrics="metrics"
            :fusion-time="fusionTime"
            :fused-image-url="fusedImageUrl"
          />
        </section>
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
  padding: var(--space-5);
  display: flex;
  justify-content: center;
}

.workspace {
  width: 100%;
  max-width: 1400px;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ===== Row 1: Input Row ===== */
.input-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-glass);
}

.upload-group {
  display: flex;
  gap: var(--space-3);
  flex-shrink: 0;
  width: 420px;
}

.algo-section {
  flex: 1;
  min-width: 0;
}

.fuse-button {
  flex-shrink: 0;
  width: 160px;
  height: 44px;
  font-size: 14px;
  font-weight: 600;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
  transition: var(--transition-smooth);
  align-self: center;
}

.fuse-button:hover {
  background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.3);
  transform: translateY(-1px);
}

.fuse-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.fuse-button:disabled {
  background: linear-gradient(135deg, #94A3B8 0%, #64748B 100%);
  box-shadow: none;
  transform: none;
}

/* ===== Row 2: Display Row ===== */
.display-row {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--space-4);
}

.source-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-glass);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: 0.3px;
}

.source-labels {
  display: flex;
  gap: var(--space-2);
}

.source-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: var(--color-bg-subtle);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.source-images {
  display: flex;
  gap: var(--space-3);
  flex: 1;
  min-height: 0;
}

.source-image-wrapper {
  flex: 1;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-bg-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.source-image-wrapper.empty {
  border: 2px dashed var(--color-border);
}

.source-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.source-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.result-panel {
  min-height: 0;
}

/* ===== Row 3: Metrics Row ===== */
.metrics-row {
  min-height: 0;
}

/* ===== Responsive: 768px - 1199px ===== */
@media (max-width: 1199px) {
  .display-row {
    grid-template-columns: 1fr;
  }

  .source-panel {
    order: 1;
  }

  .result-panel {
    order: 2;
  }
}

/* ===== Responsive: < 768px ===== */
@media (max-width: 767px) {
  .app-main {
    padding: var(--space-3);
  }

  .input-row {
    flex-direction: column;
    align-items: stretch;
  }

  .upload-group {
    width: 100%;
    flex-direction: column;
  }

  .fuse-button {
    width: 100%;
  }

  .display-row {
    grid-template-columns: 1fr;
  }
}
</style>
