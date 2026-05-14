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
        <!-- Top: controls + sources -->
        <section class="top-bar">
          <DraggableUpload
            label="过曝 (Over)"
            v-model="overFile"
            @update:model-value="setOverImage"
          />
          <DraggableUpload
            label="欠曝 (Under)"
            v-model="underFile"
            @update:model-value="setUnderImage"
          />

          <div class="controls">
            <AlgorithmSelector v-model="selectedAlgo" />
            <el-button
              type="primary"
              size="large"
              class="fuse-button"
              :loading="isFusing"
              @click="handleFuse"
            >
              {{ isFusing ? '融合中...' : '执行融合' }}
            </el-button>
          </div>
        </section>

        <!-- Middle: images side by side -->
        <section class="image-area">
          <div class="source-col" :class="{ empty: !overPreview && !underPreview }">
            <div class="source-label">过曝</div>
            <div class="img-container" :class="{ 'has-img': overPreview }">
              <img v-if="overPreview" :src="overPreview" alt="过曝" />
            </div>
          </div>
          <div class="source-col" :class="{ empty: !overPreview && !underPreview }">
            <div class="source-label">欠曝</div>
            <div class="img-container" :class="{ 'has-img': underPreview }">
              <img v-if="underPreview" :src="underPreview" alt="欠曝" />
            </div>
          </div>
          <div class="result-col">
            <div class="source-label">融合结果</div>
            <FusionViewer
              :fused-image-url="fusedImageUrl"
              :under-preview="underPreview"
              :over-preview="overPreview"
              :is-fusing="isFusing"
              @download="downloadImage"
            />
          </div>
        </section>

        <!-- Bottom: metrics -->
        <MetricsDashboard
          :metrics="metrics"
          :fusion-time="fusionTime"
          :fused-image-url="fusedImageUrl"
        />
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

.fuse-button {
  width: 100%;
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

/* ===== Image Area ===== */
.image-area {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  gap: 12px;
  min-height: 340px;
}

.source-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.source-col.empty .img-container {
  display: none;
}

.source-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.img-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.img-container.has-img {
  background: transparent;
}

.img-container img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.result-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
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
