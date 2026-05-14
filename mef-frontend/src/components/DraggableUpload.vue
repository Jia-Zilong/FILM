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
  <div class="upload-item" :class="{ 'has-image': preview }">
    <div
      class="upload-box"
      :class="{ 'is-dragging': isDragging }"
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
          <el-icon class="upload-icon">
            <Upload />
          </el-icon>
          <span class="upload-label-text">{{ label }}</span>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.upload-item {
  width: 160px;
  flex-shrink: 0;
}

.upload-box {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 80px;
  border: 2px dashed var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.2s ease;
  background: var(--color-card);
}

.upload-box:hover {
  border-color: var(--color-primary);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}

.upload-box.is-dragging {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.upload-item.has-image .upload-box {
  border-style: solid;
  border-width: 1px;
}

.file-input {
  display: none;
}

.upload-placeholder {
  height: 100%;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 4px;
  color: var(--color-text-tertiary);
}

.upload-icon {
  font-size: 20px;
  transition: all 0.2s ease;
}

.upload-box:hover .upload-icon {
  color: var(--color-primary);
  transform: scale(1.1);
}

.upload-label-text {
  font-size: 11px;
  font-weight: 500;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
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
