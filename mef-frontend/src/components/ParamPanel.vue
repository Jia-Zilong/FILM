<script setup>
const props = defineProps({
  quality: { type: Number, default: 95 },
  maxDim: { type: Number, default: 1024 },
})
const emit = defineEmits(['update:quality', 'update:maxDim'])
</script>

<template>
  <div class="param-panel">
    <div class="param-header">
      <span class="param-title">融合参数</span>
    </div>
    <div class="param-body">
      <div class="param-row">
        <span class="param-label">
          JPEG 质量
          <span class="param-value">{{ quality }}</span>
        </span>
        <input
          type="range"
          min="50"
          max="100"
          step="5"
          :value="quality"
          @input="emit('update:quality', Number($event.target.value))"
          class="param-slider"
        />
      </div>
      <div class="param-row">
        <span class="param-label">
          最大尺寸
          <span class="param-value">{{ maxDim }}px</span>
        </span>
        <input
          type="range"
          min="512"
          max="4096"
          step="256"
          :value="maxDim"
          @input="emit('update:maxDim', Number($event.target.value))"
          class="param-slider"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.param-panel {
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: 12px;
  padding: 10px 14px;
}

.param-header {
  margin-bottom: 6px;
}

.param-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.param-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.param-row {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.param-label {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.param-value {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-primary);
  font-size: 11px;
}

.param-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: var(--color-border);
  outline: none;
  cursor: pointer;
}

.param-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.3);
}

.param-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: none;
}
</style>
