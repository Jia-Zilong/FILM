<script setup>
const props = defineProps({
  modelValue: { type: String, default: 'ai' }
})
const emit = defineEmits(['update:modelValue'])

const algorithms = [
  { label: 'IF-FILM (深度学习)', value: 'ai' },
  { label: 'FFMEF (深度学习)', value: 'ffmef' },
  { label: '加权平均 (传统)', value: 'avg' },
  { label: 'Mertens 融合 (传统)', value: 'mertens' },
  { label: '最大值保留 (传统)', value: 'max' }
]
</script>

<template>
  <div class="algo-selector">
    <label class="algo-label">融合算法</label>
    <div class="algo-options">
      <TransitionGroup name="chip-list">
        <button
          v-for="algo in algorithms"
          :key="algo.value"
          class="algo-chip"
          :class="{ 'is-active': modelValue === algo.value }"
          @click="emit('update:modelValue', algo.value)"
        >
          <span class="chip-text">{{ algo.label }}</span>
        </button>
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.algo-selector {
  margin-bottom: 0;
}

.algo-label {
  display: none;
}

.algo-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.algo-chip {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-card);
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  white-space: nowrap;
}

.algo-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.algo-chip:active {
  transform: translateY(0) scale(0.98);
}

.algo-chip.is-active {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
  transform: translateY(0);
}

.chip-text {
  position: relative;
  z-index: 1;
}

/* Chip enter/leave animations */
.chip-list-enter-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.chip-list-leave-active {
  transition: all 0.2s ease;
}
.chip-list-enter-from,
.chip-list-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
.chip-list-move {
  transition: transform 0.3s ease;
}
</style>
