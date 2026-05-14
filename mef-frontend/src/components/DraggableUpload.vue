<script setup>
import { onBeforeUnmount, ref } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  modelValue: { type: File, default: null }
})
const emit = defineEmits(['update:modelValue'])

const preview = ref('')
const isDragging = ref(false)

const handleFile = (file) => {
  if (file && file.type.startsWith('image/')) {
    emit('update:modelValue', file)
    if (preview.value) URL.revokeObjectURL(preview.value)
    preview.value = URL.createObjectURL(file)
  }
}

const onFileChange = (e) => {
  const file = e.target.files?.[0]
  if (file) handleFile(file)
}

const onDrop = (e) => {
  isDragging.value = false
  const file = e.dataTransfer.files?.[0]
  if (file) handleFile(file)
}

const onDragOver = () => { isDragging.value = true }
const onDragLeave = () => { isDragging.value = false }

onBeforeUnmount(() => {
  if (preview.value) URL.revokeObjectURL(preview.value)
})
</script>

<template>
  <div class="upload-item">
    <label class="upload-label">{{ label }}</label>
    <div
      class="upload-box"
      :class="{ 'is-dragging': isDragging, 'has-image': preview }"
      @drop.prevent="onDrop"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @click="$refs.fileInput.click()"
    >
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="file-input"
        @change="onFileChange"
      />
      <img v-if="preview" :src="preview" class="preview-img" />
      <Transition name="placeholder-fade" mode="out-in">
        <div v-if="!preview" class="upload-placeholder">
          <el-icon class="upload-icon" :class="{ 'icon-bounce': isDragging }">
            <Upload />
          </el-icon>
          <span class="upload-text">点击或拖拽上传</span>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.upload-item {
  flex: 1;
  min-width: 0;
}

.upload-label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.upload-box {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  background: var(--color-card);
  box-shadow: var(--shadow-xs);
}

.upload-box:hover {
  border-color: var(--color-border-hover);
  background: var(--color-primary-light);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.upload-box:active {
  transform: translateY(0);
  box-shadow: var(--shadow-xs);
}

.upload-box.is-dragging {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  transform: scale(1.01);
}

.upload-box.has-image {
  border-style: solid;
  border-color: var(--color-border);
  box-shadow: var(--shadow-sm);
}

.upload-box.has-image:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.file-input {
  display: none;
}

.upload-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
}

.upload-icon {
  font-size: 24px;
  color: var(--color-text-tertiary);
  transition: all 0.25s ease;
}

.upload-box:hover .upload-icon {
  color: var(--color-primary);
  transform: scale(1.1);
}

.upload-box.is-dragging .upload-icon {
  color: var(--color-primary);
  transform: scale(1.2);
}

.icon-bounce {
  animation: icon-bounce 0.5s ease;
}

@keyframes icon-bounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.3); }
}

.upload-text {
  font-size: 12px;
  font-weight: 500;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.3s ease;
}

.upload-box.has-image:hover .preview-img {
  transform: scale(1.02);
}

.placeholder-fade-enter-active {
  transition: opacity 0.2s ease;
}
.placeholder-fade-leave-active {
  transition: opacity 0.15s ease;
}
.placeholder-fade-enter-from,
.placeholder-fade-leave-to {
  opacity: 0;
}
</style>
