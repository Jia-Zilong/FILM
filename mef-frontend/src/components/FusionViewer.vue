<script setup>
import { ref } from 'vue'

defineProps({
  fusedImageUrl: { type: String, default: '' },
  underPreview: { type: String, default: '' },
  overPreview: { type: String, default: '' },
  isFusing: { type: Boolean, default: false }
})
const emit = defineEmits(['download'])

const sliderValue = ref(50)
</script>

<template>
  <div class="fusion-viewer">
    <div class="viewer-header">
      <span class="viewer-title">融合结果</span>
      <el-button
        v-if="fusedImageUrl"
        type="primary"
        size="small"
        plain
        @click="emit('download')"
      >
        <el-icon><Download /></el-icon>
        下载
      </el-button>
    </div>

    <!-- Source images side-by-side -->
    <div v-if="overPreview || underPreview" class="source-preview-row">
      <div class="source-thumb" :class="{ empty: !overPreview }">
        <img v-if="overPreview" :src="overPreview" alt="过曝" />
        <span v-else class="source-label">过曝</span>
      </div>
      <div class="source-thumb" :class="{ empty: !underPreview }">
        <img v-if="underPreview" :src="underPreview" alt="欠曝" />
        <span v-else class="source-label">欠曝</span>
      </div>
    </div>

    <div class="viewer-area">
      <Transition name="image-fade" mode="out-in">
        <template v-if="fusedImageUrl && !isFusing">
          <div class="compare-container">
            <div class="compare-after">
              <img :src="fusedImageUrl" alt="融合后" />
            </div>
            <div
              class="compare-before"
              :style="{ clipPath: `inset(0 ${100 - sliderValue}% 0 0)` }"
            >
              <img :src="underPreview" alt="对比基准" />
            </div>
            <div
              class="compare-divider"
              :style="{ left: sliderValue + '%' }"
            >
              <div class="divider-handle">
                <el-icon><DArrowLeft /></el-icon>
              </div>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              v-model="sliderValue"
              class="compare-slider"
            />
            <Transition name="label-fade">
              <span class="compare-label-left" v-show="sliderValue > 15">原图</span>
            </Transition>
            <Transition name="label-fade">
              <span class="compare-label-right" v-show="sliderValue < 85">融合</span>
            </Transition>
          </div>
        </template>

        <div v-else-if="isFusing" class="skeleton-loader">
          <div class="skeleton-grid">
            <div class="skeleton-block" v-for="n in 4" :key="n"></div>
          </div>
          <div class="skeleton-text">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line long"></div>
          </div>
        </div>

        <div v-else class="empty-state">
          <el-icon class="empty-icon"><Picture /></el-icon>
          <span>上传图像并点击融合</span>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.fusion-viewer {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.viewer-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}

/* Source preview row */
.source-preview-row {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.source-thumb {
  flex: 1;
  aspect-ratio: 4 / 3;
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
}

.source-thumb.empty {
  border-style: dashed;
}

.source-thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.source-label {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.viewer-area {
  width: 100%;
  aspect-ratio: 4 / 3;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  position: relative;
  box-shadow: var(--shadow-sm);
}

.compare-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.compare-after,
.compare-before {
  position: absolute;
  inset: 0;
}

.compare-after img,
.compare-before img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.compare-divider {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(255, 255, 255, 0.9);
  z-index: 10;
  pointer-events: none;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
}

.divider-handle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  color: #374151;
  font-size: 14px;
  transition: all 0.2s ease;
}

.divider-handle:hover {
  transform: translate(-50%, -50%) scale(1.1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.compare-slider {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: ew-resize;
  z-index: 20;
}

.compare-label-left,
.compare-label-right {
  position: absolute;
  top: var(--space-3);
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  color: #fff;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 500;
  z-index: 5;
}

.compare-label-left { left: var(--space-3); }
.compare-label-right { right: var(--space-3); }

.label-fade-enter-active,
.label-fade-leave-active {
  transition: opacity 0.3s ease;
}
.label-fade-enter-from,
.label-fade-leave-to {
  opacity: 0;
}

.image-fade-enter-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.image-fade-enter-from {
  opacity: 0;
  transform: scale(0.98);
}
.image-fade-leave-active {
  transition: opacity 0.2s ease;
}
.image-fade-leave-to {
  opacity: 0;
}

/* Upgraded skeleton loader */
.skeleton-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--space-5);
  padding: var(--space-6);
}

.skeleton-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  width: 80%;
}

.skeleton-block {
  aspect-ratio: 4 / 3;
  background: linear-gradient(
    90deg,
    var(--color-bg-subtle) 25%,
    var(--color-border) 50%,
    var(--color-bg-subtle) 75%
  );
  background-size: 200% 100%;
  border-radius: var(--radius-sm);
  animation: shimmer 1.5s ease-in-out infinite;
}

.skeleton-text {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}

.skeleton-line {
  height: 12px;
  background: linear-gradient(
    90deg,
    var(--color-bg-subtle) 25%,
    var(--color-border) 50%,
    var(--color-bg-subtle) 75%
  );
  background-size: 200% 100%;
  border-radius: 6px;
  animation: shimmer 1.5s ease-in-out infinite;
}

.skeleton-line.short { width: 40%; animation-delay: 0.1s; }
.skeleton-line.long { width: 60%; animation-delay: 0.2s; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--space-3);
  color: var(--color-text-tertiary);
  font-size: 13px;
}

.empty-icon {
  font-size: 32px;
  color: var(--color-text-tertiary);
}
</style>
