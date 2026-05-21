<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  maxCount: { type: Number, default: 10 },
  minCount: { type: Number, default: 2 },
})
const emit = defineEmits(['update:modelValue'])

const previews = ref([])
const isDragging = ref(false)

const canAdd = computed(() => props.modelValue.length < props.maxCount)
const canRemove = computed(() => props.modelValue.length > props.minCount)

// Sync previews when modelValue changes from outside (e.g., view mode switch)
const syncPreviews = () => {
  previews.value.forEach((url) => { if (url) URL.revokeObjectURL(url) })
  previews.value = props.modelValue.map((f) => URL.createObjectURL(f))
}
watch(() => props.modelValue.length, syncPreviews)
onMounted(syncPreviews)

const handleFiles = (files) => {
  const fileArray = Array.isArray(files) ? files : [files]
  const currentCount = props.modelValue.length
  const remaining = props.maxCount - currentCount
  const toAdd = fileArray.slice(0, remaining)

  if (fileArray.length > remaining) {
    ElMessage.warning(`最多支持 ${props.maxCount} 张图片，已添加前 ${remaining} 张`)
  }

  // Revoke old preview URLs to prevent memory leaks when adding files
  const oldPreviews = [...previews.value]
  const newFiles = []
  const newPreviews = []
  let rejectedCount = 0

  for (const url of oldPreviews) {
    URL.revokeObjectURL(url)
  }

  for (const file of [...props.modelValue, ...toAdd]) {
    if (!file.type.startsWith('image/')) {
      rejectedCount++
      continue
    }
    newFiles.push(file)
    newPreviews.push(URL.createObjectURL(file))
  }

  if (rejectedCount > 0) {
    ElMessage.error(`${rejectedCount} 个非图片文件已跳过`)
  }

  if (newFiles.length > props.modelValue.length) {
    emit('update:modelValue', newFiles)
    previews.value = newPreviews
  }
}

const onFileChange = (e) => {
  const files = Array.from(e.target.files || [])
  if (files.length) handleFiles(files)
  e.target.value = ''
}

const onDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files || [])
  if (files.length) handleFiles(files)
}

const onDragOver = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const onDragLeave = (e) => {
  // Only reset if we actually left the container (not entering a child)
  if (!e.currentTarget.contains(e.relatedTarget)) {
    isDragging.value = false
  }
}

const removeImage = (index) => {
  if (props.modelValue.length <= props.minCount) {
    ElMessage.warning(`至少需要 ${props.minCount} 张图片`)
    return
  }
  if (previews.value[index]) URL.revokeObjectURL(previews.value[index])
  const newFiles = props.modelValue.filter((_, i) => i !== index)
  const newPreviews = previews.value.filter((_, i) => i !== index)
  emit('update:modelValue', newFiles)
  previews.value = newPreviews
}

const clearAll = () => {
  previews.value.forEach((url) => { if (url) URL.revokeObjectURL(url) })
  previews.value = []
  emit('update:modelValue', [])
}

onBeforeUnmount(() => {
  previews.value.forEach((url) => { if (url) URL.revokeObjectURL(url) })
})

defineExpose({ clearAll })
</script>

<template>
  <div class="image-list" :class="{ 'is-dragging': isDragging }"
       @drop.prevent="onDrop" @dragover.prevent="onDragOver" @dragleave.prevent="onDragLeave">
    <div class="image-grid">
      <div
        v-for="(file, index) in modelValue"
        :key="index"
        class="image-card"
      >
        <img :src="previews[index]" :alt="file?.name || `Image ${index + 1}`" />
        <button
          v-if="canRemove"
          class="remove-btn"
          @click.stop="removeImage(index)"
        >
          <el-icon><Close /></el-icon>
        </button>
        <div class="image-index">{{ index + 1 }}</div>
      </div>

      <button
        v-if="canAdd"
        class="add-card"
        @click="$refs.fileInput.click()"
      >
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          multiple
          class="file-input"
          @change="onFileChange"
        />
        <el-icon class="add-icon"><Plus /></el-icon>
        <span class="add-label">
          {{ modelValue.length === 0 ? '点击或拖拽上传图片' : '添加图片' }}
        </span>
        <span v-if="modelValue.length > 0" class="add-hint">
          已上传 {{ modelValue.length }}/{{ maxCount }} 张
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.image-list {
  width: 100%;
}

.image-list.is-dragging .image-grid {
  outline: 2px dashed var(--color-primary);
  outline-offset: 4px;
  border-radius: 8px;
  background: var(--color-primary-light);
}

.image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.image-card {
  position: relative;
  width: 100px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  flex-shrink: 0;
}

.image-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(220, 38, 38, 0.85);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-card:hover .remove-btn {
  opacity: 1;
}

.image-index {
  position: absolute;
  bottom: 2px;
  left: 4px;
  font-size: 9px;
  font-weight: 600;
  color: #fff;
  background: rgba(0, 0, 0, 0.5);
  padding: 1px 4px;
  border-radius: 4px;
}

.add-card {
  width: 100px;
  height: 80px;
  border: 2px dashed var(--color-border);
  border-radius: 8px;
  background: var(--color-card);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  transition: all 0.2s;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.add-card:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.file-input {
  display: none;
}

.add-icon {
  font-size: 18px;
}

.add-label {
  font-size: 10px;
  font-weight: 500;
  text-align: center;
  line-height: 1.1;
}

.add-hint {
  font-size: 9px;
  color: var(--color-text-tertiary);
}
</style>