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
      </div>

      <div v-else class="empty-state">
        <el-icon class="empty-icon"><Picture /></el-icon>
        <span>上传图像并点击融合</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.viewer-area {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
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
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  color: #374151;
  font-size: 12px;
}

.divider-handle:hover {
  transform: translate(-50%, -50%) scale(1.1);
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
  top: 8px;
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  color: #fff;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 500;
  z-index: 5;
}

.compare-label-left { left: 8px; }
.compare-label-right { right: 8px; }

.label-fade-enter-active,
.label-fade-leave-active {
  transition: opacity 0.3s ease;
}
.label-fade-enter-from,
.label-fade-leave-to {
  opacity: 0;
}

.image-fade-enter-active {
  transition: opacity 0.4s ease, transform 0.4s ease;
}
.image-fade-enter-from {
  opacity: 0;
  transform: scale(0.97);
}
.image-fade-leave-active {
  transition: opacity 0.2s ease;
}
.image-fade-leave-to {
  opacity: 0;
}

.skeleton-loader {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 16px;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  width: 80%;
}

.skeleton-block {
  aspect-ratio: 4 / 3;
  background: linear-gradient(90deg, var(--color-bg-subtle) 25%, var(--color-border) 50%, var(--color-bg-subtle) 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.empty-icon {
  font-size: 28px;
}
</style>
