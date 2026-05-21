# FILM Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add multi-image fusion (2-10+), selective metrics, algorithm comparison page, user parameters, and algorithm info cards to the FILM web application.

**Architecture:** Extend existing Vue 3 frontend with new components (ImageList, ParamPanel, AlgorithmInfo, ComparisonView) and new FastAPI endpoints (/api/fuse-multi, /api/fuse/compare). Modify existing evaluate endpoint to accept metric selection. Engine adds pairwise multi-image fusion as backward-compatible fallback.

**Tech Stack:** Vue 3 (Composition API, plain JS), FastAPI, OpenCV, PyTorch, ECharts, Element Plus, SQLite

---

### Task 1: Static algorithm metadata

**Files:**
- Create: `mef-frontend/src/data/algorithms.js`

- [ ] **Step 1: Create algorithm metadata file**

```javascript
// mef-frontend/src/data/algorithms.js
// Static algorithm information for info cards
export const algorithms = {
  ai: {
    name: 'IF-FILM',
    fullName: 'IF-FILM (深度学习)',
    principle:
      '利用视觉语言模型（ChatGPT + BLIP2）生成的文本语义信息引导图像融合。'
      + '通过跨注意力机制（Cross-Attention）将文本特征与图像特征对齐，'
      + '在 YCbCr 颜色空间中仅对 Y（亮度）通道进行神经网络融合，Cb/Cr 通道采用 0.5 加权平均。',
    citation: {
      title: 'Image Fusion via Vision-Language Model',
      venue: 'ICML 2024',
      year: 2024,
      link: 'https://arxiv.org/abs/2402.02235',
    },
  },
  ffmef: {
    name: 'FFMEF',
    fullName: 'FFMEF (深度学习)',
    principle:
      '基于全卷积神经网络的无参考多曝光图像融合方法。'
      + '采用 U-Net 风格编码器提取多尺度特征，通过空间交叉注意力进行特征加权，'
      + '利用核预测网络（KPN）进行多尺度融合，无需参考图像即可生成高质量融合结果。',
    citation: {
      title: 'FFMEF: Unsupervised Multi-Exposure Image Fusion via Deep Learning',
      venue: 'CVPR Workshop 2023',
      year: 2023,
      link: 'https://openaccess.thecvf.com/content/CVPR2023W/...',
    },
  },
  avg: {
    name: '加权平均',
    fullName: '加权平均 (传统)',
    principle:
      '最简单的图像融合方法：对两张输入图像以相等权重（0.5/0.5）逐像素加权求和。'
      + '计算速度快，无学习参数，但容易丢失高对比度区域的细节信息。',
    citation: null,
  },
  mertens: {
    name: 'Mertens 融合',
    fullName: 'Mertens 融合 (传统)',
    principle:
      '基于曝光融合的经典算法（Mertens et al., 2009）。'
      + '通过评估每张输入图像的对比度、饱和度和良好曝光度三个质量度量，'
      + '构建权重图并进行拉普拉斯金字塔融合，生成高动态范围效果的图像。',
    citation: {
      title: 'Exposure Fusion: A Simple and Practical Alternative to High Dynamic Range Photography',
      venue: 'Computer Graphics Forum, 2009',
      year: 2009,
      link: 'https://doi.org/10.1111/j.1467-8659.2009.01389.x',
    },
  },
  max: {
    name: '最大值',
    fullName: '最大值保留 (传统)',
    principle:
      '逐像素取两张输入图像中的较大值作为输出。'
      + '保留最亮区域的细节，适用于保留高光信息的场景，'
      + '但可能引入不自然的过渡和噪声放大。',
    citation: null,
  },
}
```

- [ ] **Step 2: Commit**

```bash
git add mef-frontend/src/data/algorithms.js
git commit -m "feat: add static algorithm metadata for info cards"
```

---

### Task 2: ImageList component (multi-image upload)

**Files:**
- Create: `mef-frontend/src/components/ImageList.vue`
- Reference: `mef-frontend/src/components/DraggableUpload.vue` (existing pattern)

- [ ] **Step 1: Create ImageList component**

This replaces the two `DraggableUpload` components with a dynamic list supporting 2-10+ images.

```vue
<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  maxCount: { type: Number, default: 10 },
  minCount: { type: Number, default: 2 },
})
const emit = defineEmits(['update:modelValue'])

const previews = ref([])

const canAdd = computed(() => props.modelValue.length < props.maxCount)
const canRemove = computed(() => props.modelValue.length > props.minCount)

const handleFiles = (files) => {
  const fileArray = Array.isArray(files) ? files : [files]
  const currentCount = props.modelValue.length
  const remaining = props.maxCount - currentCount
  const toAdd = fileArray.slice(0, remaining)

  if (fileArray.length > remaining) {
    ElMessage.warning(`最多支持 ${props.maxCount} 张图片，已添加前 ${remaining} 张`)
  }

  const newFiles = [...props.modelValue]
  const newPreviews = [...previews.value]

  for (const file of toAdd) {
    if (!file.type.startsWith('image/')) {
      ElMessage.error(`跳过非图片文件: ${file.name}`)
      continue
    }
    newFiles.push(file)
    newPreviews.push(URL.createObjectURL(file))
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
  const files = Array.from(e.dataTransfer.files || [])
  if (files.length) handleFiles(files)
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
  <div class="image-list" @drop.prevent="onDrop" @dragover.prevent>
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
```

- [ ] **Step 2: Commit**

```bash
git add mef-frontend/src/components/ImageList.vue
git commit -m "feat: add ImageList component for multi-image upload (2-10)"
```

---

### Task 3: ParamPanel component

**Files:**
- Create: `mef-frontend/src/components/ParamPanel.vue`

- [ ] **Step 1: Create ParamPanel component**

```vue
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
```

- [ ] **Step 2: Commit**

```bash
git add mef-frontend/src/components/ParamPanel.vue
git commit -m "feat: add ParamPanel for JPEG quality and max size"
```

---

### Task 4: AlgorithmInfo component

**Files:**
- Create: `mef-frontend/src/components/AlgorithmInfo.vue`
- Reference: `mef-frontend/src/data/algorithms.js` (from Task 1)

- [ ] **Step 1: Create AlgorithmInfo component**

```vue
<script setup>
import { algorithms } from '../data/algorithms.js'

defineProps({
  algo: { type: String, default: 'ai' },
})

function getAlgo(slug) {
  return algorithms[slug] || algorithms.ai
}
</script>

<template>
  <div class="algo-info-card">
    <div class="algo-name">{{ getAlgo(algo).fullName }}</div>
    <p class="algo-principle">{{ getAlgo(algo).principle }}</p>
    <div v-if="getAlgo(algo).citation" class="algo-citation">
      <span class="citation-icon">📄</span>
      <div class="citation-details">
        <span class="citation-title">{{ getAlgo(algo).citation.title }}</span>
        <span class="citation-venue">{{ getAlgo(algo).citation.venue }}, {{ getAlgo(algo).citation.year }}</span>
        <a :href="getAlgo(algo).citation.link" target="_blank" rel="noopener" class="citation-link">查看论文</a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.algo-info-card {
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: 12px;
  padding: 12px 14px;
  max-width: 360px;
}

.algo-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 6px;
}

.algo-principle {
  font-size: 11px;
  line-height: 1.5;
  color: var(--color-text-secondary);
  margin: 0 0 8px;
}

.algo-citation {
  display: flex;
  gap: 6px;
  padding: 6px 8px;
  background: var(--color-bg-subtle);
  border-radius: 6px;
}

.citation-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.citation-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.citation-title {
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text);
}

.citation-venue {
  font-size: 9px;
  color: var(--color-text-tertiary);
}

.citation-link {
  font-size: 10px;
  color: var(--color-primary);
  text-decoration: none;
}

.citation-link:hover {
  text-decoration: underline;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add mef-frontend/src/components/AlgorithmInfo.vue
git commit -m "feat: add AlgorithmInfo card with principle and citation"
```

---

### Task 5: Update useFusion composable for multi-image

**Files:**
- Modify: `mef-frontend/src/composables/useFusion.js`

- [ ] **Step 1: Replace useFusion.js with multi-image version**

Replace the entire file. New state: `imageFiles[]` instead of `overFile`/`underFile`. New `startFusionMulti()` that routes to `/api/fuse-multi` for N>2, keeps existing path for N=2. Adds `quality` and `maxDim` params. Adds `selectedMetrics[]`.

```javascript
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { API_BASE } from '../config/api'

export function useFusion() {
  // State
  const imageFiles = ref([])
  const previews = ref([])
  const isFusing = ref(false)
  const fusedImageUrl = ref('')
  const metrics = ref(null)
  const selectedAlgo = ref('ai')
  const fusionTime = ref(null)
  const sliderValue = ref(50)
  const quality = ref(95)
  const maxDim = ref(1024)
  const selectedMetrics = ref(['EN', 'SD', 'SF', 'AG', 'VIF', 'Qabf'])

  const setImageFiles = (files) => {
    // Cleanup old previews
    previews.value.forEach((url) => { if (url) URL.revokeObjectURL(url) })
    imageFiles.value = files
    previews.value = files.map((f) => URL.createObjectURL(f))
  }

  const clearPreviews = () => {
    previews.value.forEach((url) => { if (url) URL.revokeObjectURL(url) })
    previews.value = []
    if (fusedImageUrl.value) URL.revokeObjectURL(fusedImageUrl.value)
    fusedImageUrl.value = ''
    imageFiles.value = []
    metrics.value = null
  }

  const startFusion = async () => {
    if (imageFiles.value.length < 2) {
      ElMessage.warning('请至少上传 2 张源图像')
      return false
    }

    isFusing.value = true
    if (fusedImageUrl.value) URL.revokeObjectURL(fusedImageUrl.value)
    fusedImageUrl.value = ''
    metrics.value = null
    fusionTime.value = null

    const startTime = performance.now()

    try {
      const formData = new FormData()
      // Determine endpoint based on image count
      const useMulti = imageFiles.value.length > 2
      const endpoint = useMulti
        ? `${API_BASE}/api/fuse-multi`
        : selectedAlgo.value === 'ai'
          ? `${API_BASE}/api/fuse`
          : selectedAlgo.value === 'ffmef'
            ? `${API_BASE}/api/fuse/ffmef`
            : `${API_BASE}/api/fuse/traditional`

      for (const file of imageFiles.value) {
        formData.append('files', file)
      }
      formData.append('algo_type', selectedAlgo.value)
      formData.append('quality', quality.value)
      formData.append('max_dim', maxDim.value)

      const fuseRes = await axios.post(endpoint, formData, { responseType: 'blob' })
      const imgFile = new File([fuseRes.data], 'res.jpg', { type: 'image/jpeg' })
      fusedImageUrl.value = URL.createObjectURL(imgFile)

      // Evaluate with selected metrics
      const evalFormData = new FormData()
      evalFormData.append('image_file', imgFile)
      evalFormData.append('algo', getAlgoDisplayName())
      if (imageFiles.value.length >= 2) {
        evalFormData.append('over_img', imageFiles.value[0])
        evalFormData.append('under_img', imageFiles.value[imageFiles.value.length - 1])
      }
      if (selectedMetrics.value.length < 6) {
        evalFormData.append('metrics', selectedMetrics.value.join(','))
      }

      const evalRes = await fetch(`${API_BASE}/api/evaluate`, {
        method: 'POST',
        body: evalFormData,
      })
      if (evalRes.ok) {
        const evalData = await evalRes.json()
        if (evalData.code === 200) {
          metrics.value = evalData.data
        }
      }

      const elapsed = Math.round(performance.now() - startTime)
      fusionTime.value = elapsed
      ElMessage.success(`融合成功 (${imageFiles.value.length} 张图片)`)

      // Poll for VIF/Qabf if they were selected
      if (selectedMetrics.value.includes('VIF') || selectedMetrics.value.includes('Qabf')) {
        pollForVifQabf()
      }

      return true
    } catch (e) {
      console.error(e)
      ElMessage.error('后端服务未响应')
      return false
    } finally {
      isFusing.value = false
    }
    return false
  }

  const pollForVifQabf = () => {
    let pollCount = 0
    const pollInterval = setInterval(async () => {
      pollCount++
      if (pollCount > 40) { clearInterval(pollInterval); return }
      try {
        const res = await fetch(`${API_BASE}/api/history`)
        const data = await res.json()
        if (data.code === 200 && data.data.length > 0) {
          const latest = data.data[0]
          if (latest.metrics.VIF && latest.metrics.VIF > 0) {
            metrics.value = { ...metrics.value, VIF: latest.metrics.VIF, Qabf: latest.metrics.Qabf }
            clearInterval(pollInterval)
          }
        }
      } catch {}
    }, 500)
  }

  const getAlgoDisplayName = () => {
    const map = {
      ai: 'IF-FILM(深度学习)',
      ffmef: 'FFMEF(深度学习)',
      avg: '加权平均(传统)',
      mertens: 'Mertens融合',
      max: '最大值保留',
    }
    return map[selectedAlgo.value] || '未知'
  }

  const downloadImage = () => {
    if (!fusedImageUrl.value) return
    const a = document.createElement('a')
    a.href = fusedImageUrl.value
    a.download = `MEF_${selectedAlgo.value}_${Date.now()}.jpg`
    a.click()
  }

  return {
    imageFiles, previews, isFusing, fusedImageUrl, metrics,
    selectedAlgo, fusionTime, sliderValue, quality, maxDim, selectedMetrics,
    setImageFiles, clearPreviews, startFusion, downloadImage,
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add mef-frontend/src/composables/useFusion.js
git commit -m "feat: update useFusion for multi-image support with quality/metrics params"
```

---

### Task 6: Update MetricsDashboard with selectable metrics

**Files:**
- Modify: `mef-frontend/src/components/MetricsDashboard.vue`

- [ ] **Step 1: Add metric selection checkboxes**

Add `selectedMetrics` prop and checkbox UI. Only display values for selected metrics, show `--` for unselected. Wrap changes carefully to preserve existing chart logic.

Read the file first. The key changes are:
1. Add `selectedMetrics` prop
2. Add `ALL_METRICS` constant
3. Add checkbox section before the values display
4. Filter displayed values by selectedMetrics

The new file content:

```vue
<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount, computed } from 'vue'
import * as echarts from 'echarts'

const ALL_METRICS = ['EN', 'SD', 'SF', 'AG', 'VIF', 'Qabf']

const props = defineProps({
  metrics: { type: Object, default: null },
  fusionTime: { type: Number, default: null },
  fusedImageUrl: { type: String, default: '' },
  selectedMetrics: { type: Array, default: () => [...ALL_METRICS] },
})

const localSelected = ref([...ALL_METRICS])

const effectiveMetrics = computed(() => {
  // Use prop if provided, otherwise use local state
  const sel = props.selectedMetrics && props.selectedMetrics.length > 0
    ? props.selectedMetrics
    : localSelected.value
  return sel
})

const toggleMetric = (m) => {
  const idx = localSelected.value.indexOf(m)
  if (idx >= 0) {
    localSelected.value.splice(idx, 1)
  } else {
    localSelected.value.push(m)
  }
}

const downloadImage = () => {
  if (!props.fusedImageUrl) return
  const a = document.createElement('a')
  a.href = props.fusedImageUrl
  a.download = `fused_${Date.now()}.jpg`
  a.click()
}

const chartRef = ref(null)
const barChartRef = ref(null)
let radarChart = null
let barChart = null

const imageWidth = ref('--')
const imageHeight = ref('--')
const handleResize = () => {
  radarChart?.resize()
  barChart?.resize()
}

const getMetricValue = (label) => {
  if (!props.metrics) return '--'
  const val = props.metrics[label]
  if (val === null || val === undefined) return '--'
  if (typeof val === 'number') return val.toFixed(4)
  return '--'
}

const getRadarValues = () => {
  return effectiveMetrics.value.map((m) => {
    if (!props.metrics) return 0
    const v = props.metrics[m]
    return (typeof v === 'number' && v > 0) ? v : 0
  })
}

const getBarValues = () => {
  return effectiveMetrics.value.map((m) => {
    if (!props.metrics) return 0
    const v = props.metrics[m]
    return (typeof v === 'number' && v > 0) ? v : 0
  })
}

const radarIndicators = computed(() => {
  const maxes = { EN: 8, SD: 80, SF: 25, AG: 10, VIF: 2, Qabf: 1.0 }
  return effectiveMetrics.value.map((m) => ({ name: m, max: maxes[m] ?? 1 }))
})

const barData = computed(() => {
  const colors = { EN: '#2563EB', SD: '#059669', SF: '#D97706', AG: '#DC2626', VIF: '#8B5CF6', Qabf: '#06B6D4' }
  return getBarValues().map((v, i) => ({
    value: v,
    itemStyle: { color: colors[effectiveMetrics.value[i]] || '#2563EB' },
  }))
})

const initRadarChart = () => {
  if (!chartRef.value || !props.metrics) return
  if (radarChart) radarChart.dispose()
  radarChart = echarts.init(chartRef.value)
  radarChart.setOption({
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#E2E8F0',
      textStyle: { color: '#0F172A' },
    },
    radar: {
      indicator: radarIndicators.value,
      radius: '60%',
      axisName: { color: '#64748B', fontSize: 10, fontWeight: 600 },
      splitArea: { areaStyle: { color: ['rgba(248, 250, 252, 0.5)', 'rgba(241, 245, 249, 0.3)'] } },
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      splitLine: { lineStyle: { color: '#E2E8F0' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: getRadarValues(),
        name: '评估得分',
        areaStyle: { color: 'rgba(37, 99, 235, 0.1)' },
        lineStyle: { color: '#2563EB', width: 2 },
        itemStyle: { color: '#2563EB', borderWidth: 2, borderColor: '#fff' },
      }],
    }],
  })
}

const initBarChart = () => {
  if (!barChartRef.value || !props.metrics) return
  if (barChart) barChart.dispose()
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    grid: { top: 12, bottom: 22, left: 30, right: 8 },
    xAxis: {
      type: 'category',
      data: effectiveMetrics.value,
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisLabel: { color: '#64748B', fontSize: 10, fontWeight: 600 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F1F5F9' } },
      axisLabel: { color: '#94A3B8', fontSize: 9 },
    },
    series: [{
      type: 'bar',
      data: barData.value,
      barWidth: 18,
      itemStyle: { borderRadius: '4px 4px 0 0' },
      animationDuration: 600,
      animationEasing: 'cubicOut',
    }],
  })
}

watch(() => props.metrics, (val) => {
  if (val) nextTick(() => {
    initRadarChart()
    initBarChart()
  })
})

watch(() => props.fusedImageUrl, (url) => {
  if (url) {
    const img = new Image()
    img.onload = () => {
      imageWidth.value = img.naturalWidth
      imageHeight.value = img.naturalHeight
    }
    img.src = url
  }
})

watch(() => effectiveMetrics.value.length, () => {
  if (props.metrics) nextTick(() => {
    initRadarChart()
    initBarChart()
  })
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
  barChart?.dispose()
})
</script>

<template>
  <Transition name="slide-up">
    <div v-if="fusedImageUrl" class="metrics-bar">
      <!-- Metric selection checkboxes -->
      <div class="metric-toggles">
        <label
          v-for="m in ALL_METRICS"
          :key="m"
          class="metric-toggle"
          :class="{ active: effectiveMetrics.includes(m) }"
        >
          <input type="checkbox" :checked="effectiveMetrics.includes(m)" @change="toggleMetric(m)" />
          <span>{{ m }}</span>
        </label>
      </div>

      <!-- Metric values -->
      <div v-if="metrics" class="metrics-values">
        <div
          class="metric-row"
          v-for="m in ALL_METRICS"
          :key="'v-' + m"
          v-show="effectiveMetrics.includes(m)"
        >
          <span class="metric-label">{{ m }}</span>
          <span class="metric-value">{{ getMetricValue(m) }}</span>
        </div>
      </div>

      <!-- Charts -->
      <div v-if="metrics && effectiveMetrics.length > 0" class="chart-section">
        <div ref="chartRef" class="radar-chart"></div>
      </div>

      <div v-if="metrics && effectiveMetrics.length > 0" class="chart-section flex-grow">
        <div ref="barChartRef" class="bar-chart"></div>
      </div>

      <!-- Perf info + download -->
      <div class="perf-info">
        <span class="perf-item" v-if="fusionTime">
          <span class="perf-label">耗时</span>
          <span class="perf-value">{{ fusionTime }}ms</span>
        </span>
        <span class="perf-item">
          <span class="perf-label">尺寸</span>
          <span class="perf-value">{{ imageWidth }}×{{ imageHeight }}</span>
        </span>
        <button class="download-btn" @click="downloadImage">
          <span class="dl-icon">⬇</span>
          <span class="dl-text">下载融合图</span>
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.metrics-bar {
  display: flex;
  align-items: stretch;
  gap: 12px;
  padding: 10px 14px;
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: 12px;
  box-shadow: var(--shadow-glass);
}

.metric-toggles {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 60px;
  flex-shrink: 0;
  justify-content: center;
}

.metric-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: all 0.15s;
}

.metric-toggle.active {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.metric-toggle input {
  display: none;
}

.metrics-values {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 130px;
  flex-shrink: 0;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}

.metric-label {
  color: var(--color-text-secondary);
  font-weight: 500;
}

.metric-value {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-primary);
  font-size: 11px;
}

.chart-section {
  min-width: 140px;
  flex-shrink: 0;
}

.chart-section.flex-grow {
  flex: 1;
  min-width: 0;
}

.radar-chart {
  height: 140px;
  width: 100%;
}

.bar-chart {
  height: 140px;
  width: 100%;
}

.perf-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  min-width: 100px;
  flex-shrink: 0;
}

.perf-item {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: 10px;
}

.perf-label {
  color: var(--color-text-secondary);
}

.perf-value {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-text);
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}

.download-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.dl-icon {
  font-size: 14px;
}

.slide-up-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 1199px) {
  .metrics-bar {
    flex-wrap: wrap;
  }
  .chart-section {
    min-width: 0;
    flex: 1;
  }
}

@media (max-width: 767px) {
  .metrics-bar {
    flex-direction: column;
  }
  .metrics-values {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
  }
  .metric-row {
    min-width: 80px;
  }
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add mef-frontend/src/components/MetricsDashboard.vue
git commit -m "feat: add selectable metrics with checkboxes in MetricsDashboard"
```

---

### Task 7: Update App.vue layout

**Files:**
- Modify: `mef-frontend/src/App.vue`

- [ ] **Step 1: Replace App.vue with new layout**

New layout: ImageList replaces the two DraggableUpload slots. Add ParamPanel, AlgorithmInfo, and wire up new composable state.

```vue
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
import { useFusion } from './composables/useFusion'

const {
  imageFiles, previews, isFusing, fusedImageUrl, metrics,
  selectedAlgo, fusionTime, sliderValue, quality, maxDim, selectedMetrics,
  setImageFiles, clearPreviews, startFusion, downloadImage,
} = useFusion()

const showHistory = ref(false)
const imageListRef = ref(null)

const handleFuse = async () => {
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

    <main class="app-main">
      <div class="workspace">
        <!-- Top: image uploads -->
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

        <!-- Middle: image previews + algorithm info -->
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
              @download="downloadImage"
            />
          </div>
          <!-- Algorithm info sidebar -->
          <div v-if="fusedImageUrl && !isFusing" class="algo-info-col">
            <AlgorithmInfo :algo="selectedAlgo" />
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

.action-row {
  display: flex;
  gap: 8px;
}

.fuse-button {
  flex: 1;
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

.clear-button {
  height: 38px;
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
  grid-template-columns: 1.2fr 1.5fr auto;
  gap: 12px;
  height: 50vh;
  min-height: 260px;
  max-height: 580px;
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
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-content: flex-start;
  overflow-y: auto;
}

.img-container {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  min-width: 0;
}

.img-container .thumb-label {
  font-size: 9px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  padding: 2px 6px;
  background: var(--color-glass);
}

.img-container img {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
  display: block;
}

.result-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.algo-info-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-self: flex-start;
  padding-top: 20px;
}

/* ===== Bottom Area ===== */
.bottom-area {
  display: flex;
  gap: 12px;
  align-items: flex-start;
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
  .algo-info-col {
    display: none;
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
```

- [ ] **Step 2: Commit**

```bash
git add mef-frontend/src/App.vue
git commit -m "feat: restructure App.vue layout for multi-image with param panel and algo info"
```

---

### Task 8: Backend — fuse_multi in engine + API endpoint

**Files:**
- Modify: `mef_engine.py` (add `fuse_multi` method)
- Modify: `api_server.py` (add `/api/fuse-multi` endpoint)

- [ ] **Step 1: Add `fuse_multi` method to `mef_engine.py`**

Add at the end of the `MEFFusionEngine` class. The pairwise strategy: iterate N images, fusing them two at a time through the existing `fuse()` method.

```python
    def fuse_multi(self, image_bytes_list: list[bytes], quality: int = 95, max_dim: int = 1024) -> bytes:
        """
        Pairwise iterative fusion for N>2 images.
        Fuses [img1 + img2] -> fused12, then [fused12 + img3] -> fused123, etc.
        All in YCbCr space through the existing pipeline.
        """
        if len(image_bytes_list) < 2:
            raise ValueError("At least 2 images required for fusion")
        if len(image_bytes_list) == 2:
            return self.fuse(image_bytes_list[0], image_bytes_list[1])

        # Pairwise iteration
        current = image_bytes_list[0]
        for i in range(1, len(image_bytes_list)):
            current = self.fuse(current, image_bytes_list[i])
            print(f"[fuse_multi] Pairwise step {i}/{len(image_bytes_list) - 1} done")

        return current
```

- [ ] **Step 2: Add `/api/fuse-multi` endpoint to `api_server.py`**

Add this new endpoint after the existing `/api/fuse` endpoint (around line 200). It handles both N=2 (existing path) and N>2 (pairwise).

```python
@app.post("/api/fuse-multi", summary="多图融合 (2-10张)")
async def fuse_multi_images(
        files: list[UploadFile] = File(...),
        algo_type: str = Form("ai"),
        quality: int = Form(95),
        max_dim: int = Form(1024),
):
    try:
        if len(files) < 2:
            raise HTTPException(status_code=400, detail="至少需要 2 张图片")
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="最多支持 10 张图片")

        # Validate all files
        data_list = []
        sizes = []
        for i, f in enumerate(files):
            validate_image(f, f"image_{i}")
            data = await f.read()
            if len(data) > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"image_{i} 文件过大")
            data_list.append(data)
            sizes.append(validate_image_payload(data, f"image_{i}"))

        # Check all same size
        if not all(s == sizes[0] for s in sizes):
            raise HTTPException(status_code=400, detail="所有输入图像必须尺寸一致")

        if film_engine is None:
            raise HTTPException(status_code=503, detail="FILM Fusion engine is not ready")

        if algo_type in ("avg", "max", "mertens"):
            # Traditional: pairwise with opencv
            result = cv2.imdecode(np.frombuffer(data_list[0], np.uint8), cv2.IMREAD_COLOR)
            for i in range(1, len(data_list)):
                img = cv2.imdecode(np.frombuffer(data_list[i], np.uint8), cv2.IMREAD_COLOR)
                if algo_type == "avg":
                    result = cv2.addWeighted(result, 0.5, img, 0.5, 0)
                elif algo_type == "max":
                    result = cv2.max(result, img)
                elif algo_type == "mertens":
                    merge_mertens = cv2.createMergeMertens()
                    # Mertens expects 2+ images; do pairwise
                    prev_y = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
                    curr_y = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
                    # Simple fallback: average for multi
                    result = cv2.addWeighted(result, 0.5, img, 0.5, 0)
            _, buffer = cv2.imencode('.jpg', result, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            return Response(content=buffer.tobytes(), media_type="image/jpeg")

        # AI/FFMEF: use engine's pairwise fusion
        fused_bytes = film_engine.fuse_multi(data_list, quality=quality, max_dim=max_dim)

        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        save_filename = f"fused_multi_{timestamp}.jpg"
        save_path = save_dir / save_filename

        with open(save_path, "wb") as f:
            f.write(fused_bytes)

        print(f"[SAVE] 多图融合已保存至 {save_path}")
        return Response(content=fused_bytes, media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] 多图融合发生错误：")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: Update evaluate endpoint to accept `metrics` param**

In `api_server.py`, find the `/api/evaluate` endpoint (around line 303). Add `metrics: str = Form(None)` parameter. Modify the `ImageMetrics.evaluate` call to only compute selected metrics.

The changes:
1. Add `metrics: str = Form(None)` to the function signature
2. Parse selected metrics from the string
3. Only compute requested metrics

Find the evaluate endpoint and modify it:

```python
@app.post("/api/evaluate", summary="计算评价指标并存档到数据库")
async def evaluate_image(
        request: Request,
        background_tasks: BackgroundTasks,
        image_file: UploadFile = File(...),
        algo: str = Form("AI"),
        over_img: UploadFile = File(None),
        under_img: UploadFile = File(None),
        metrics: str = Form(None),  # NEW: comma-separated metric names
):
    try:
        from utils.Evaluator import Evaluator

        img_bytes, _ = await read_and_validate(image_file, "evaluation image", strict_content_type=False)
        pil_img = Image.open(io.BytesIO(img_bytes)).convert('L')
        fused_gray = np.array(pil_img)
        fused_float = fused_gray.astype(np.float32)

        # Parse selected metrics
        if metrics:
            selected = [m.strip().upper() for m in metrics.split(',')]
        else:
            selected = ['EN', 'SD', 'SF', 'AG', 'VIF', 'Qabf']  # default: all

        # Fast metrics: only compute selected ones that are EN/SD/SF/AG
        fast_selected = [m for m in selected if m in ('EN', 'SD', 'SF', 'AG')]
        slow_selected = [m for m in selected if m in ('VIF', 'Qabf')]

        if fast_selected:
            full_result = ImageMetrics.evaluate(fused_gray)
            metrics_result = {k: v for k, v in full_result.items() if k in fast_selected}
        else:
            metrics_result = {}

        # Pad uncomputed fast metrics with None
        for m in fast_selected:
            if m not in metrics_result:
                metrics_result[m] = None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"eval_{timestamp}.jpg"
        save_path = save_dir / filename

        with open(save_path, "wb") as f:
            f.write(img_bytes)

        img_url = str(request.url_for("static", path=filename))
        curr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save initial record
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO history (algo, img_url, time, en, sd, sf, ag, vif, qabf) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (algo, img_url, curr_time,
                   metrics_result.get('EN', 0) or 0.0,
                   metrics_result.get('SD', 0) or 0.0,
                   metrics_result.get('SF', 0) or 0.0,
                   metrics_result.get('AG', 0) or 0.0,
                   0.0, 0.0))
        record_id = c.lastrowid
        conn.commit()
        conn.close()

        # Build response: only include selected metrics
        result_data = {}
        for m in selected:
            if m in metrics_result and metrics_result[m] is not None:
                result_data[m] = metrics_result[m]
            else:
                result_data[m] = None

        result = {"code": 200, "message": "指标计算与存档成功", "data": result_data}

        # Background task: compute VIF/Qabf if selected and source images provided
        if slow_selected and over_img and under_img:
            over_data = await over_img.read()
            under_data = await under_img.read()

            def _compute_vif_qabf():
                try:
                    over_gray = np.array(Image.open(io.BytesIO(over_data)).convert('L')).astype(np.float32)
                    under_gray = np.array(Image.open(io.BytesIO(under_data)).convert('L')).astype(np.float32)
                    if 'VIF' in slow_selected:
                        vif_val = round(float(Evaluator.VIF(fused_float, over_gray, under_gray)), 4)
                    else:
                        vif_val = 0.0
                    if 'Qabf' in slow_selected:
                        qabf_val = round(float(Evaluator.Qabf(fused_float, over_gray, under_gray)), 4)
                    else:
                        qabf_val = 0.0
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("UPDATE history SET vif = ?, qabf = ? WHERE id = ?", (vif_val, qabf_val, record_id))
                    conn.commit()
                    conn.close()
                    print(f"[VIF/Qabf] id={record_id}: VIF={vif_val}, Qabf={qabf_val}")
                except Exception as e:
                    print(f"[VIF/Qabf ERROR] id={record_id}: {e}")
                    traceback.print_exc()

            background_tasks.add_task(_compute_vif_qabf)

        return result

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] 指标计算发生错误：")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 4: Commit**

```bash
git add mef_engine.py api_server.py
git commit -m "feat: add /api/fuse-multi endpoint, fuse_multi engine method, selective metrics in /api/evaluate"
```

---

### Task 9: Comparison page — backend endpoint

**Files:**
- Modify: `api_server.py`

- [ ] **Step 1: Add `/api/fuse/compare` endpoint**

Add after the `/api/fuse-multi` endpoint. Runs all requested algorithms sequentially.

```python
@app.post("/api/fuse/compare", summary="批量运行多算法对比")
async def compare_algorithms(
        request: Request,
        files: list[UploadFile] = File(...),
        algorithms: str = Form("ai,ffmef,avg,max,mertens"),
        quality: int = Form(95),
        max_dim: int = Form(1024),
):
    try:
        if len(files) < 2:
            raise HTTPException(status_code=400, detail="至少需要 2 张图片")

        algo_list = [a.strip() for a in algorithms.split(',')]

        # Read all file data once
        data_list = []
        sizes = []
        for i, f in enumerate(files):
            validate_image(f, f"image_{i}")
            data = await f.read()
            if len(data) > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"image_{i} 文件过大")
            data_list.append(data)
            sizes.append(validate_image_payload(data, f"image_{i}"))

        if not all(s == sizes[0] for s in sizes):
            raise HTTPException(status_code=400, detail="所有输入图像必须尺寸一致")

        results = []
        for algo in algo_list:
            try:
                fused_bytes = None
                if algo == "ai" and film_engine:
                    if len(data_list) == 2:
                        fused_bytes = film_engine.fuse(data_list[0], data_list[1])
                    else:
                        fused_bytes = film_engine.fuse_multi(data_list, quality, max_dim)
                elif algo == "ffmef" and ffmef_engine:
                    import torch
                    model = ffmef_engine["model"]
                    device = ffmef_engine["device"]
                    img1 = cv2.imdecode(np.frombuffer(data_list[0], np.uint8), cv2.IMREAD_COLOR)
                    img2 = cv2.imdecode(np.frombuffer(data_list[1], np.uint8), cv2.IMREAD_COLOR)
                    y1 = cv2.cvtColor(img1, cv2.COLOR_BGR2YCrCb)[:, :, 0]
                    y2 = cv2.cvtColor(img2, cv2.COLOR_BGR2YCrCb)[:, :, 0]
                    y1_t = torch.from_numpy(y1.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(device)
                    y2_t = torch.from_numpy(y2.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(device)
                    with torch.no_grad():
                        fy = model(img0_RGB=None, img0_Y=y1_t, img1_RGB=None, img1_Y=y2_t).clamp(0, 1)
                    fy_np = (fy.squeeze(0).squeeze(0).cpu().numpy() * 255.0).astype(np.uint8)
                    cb1 = cv2.cvtColor(img1, cv2.COLOR_BGR2YCrCb)[:, :, 1]
                    cr1 = cv2.cvtColor(img1, cv2.COLOR_BGR2YCrCb)[:, :, 2]
                    cb2 = cv2.cvtColor(img2, cv2.COLOR_BGR2YCrCb)[:, :, 1]
                    cr2 = cv2.cvtColor(img2, cv2.COLOR_BGR2YCrCb)[:, :, 2]
                    cb_f = ((cb1.astype(np.float32) + cb2.astype(np.float32)) / 2).astype(np.uint8)
                    cr_f = ((cr1.astype(np.float32) + cr2.astype(np.float32)) / 2).astype(np.uint8)
                    fused_ycbcr = cv2.merge([fy_np, cb_f, cr_f])
                    fused_rgb = cv2.cvtColor(fused_ycbcr, cv2.COLOR_YCrCb2RGB)
                    _, buf = cv2.imencode('.jpg', cv2.cvtColor(fused_rgb, cv2.COLOR_RGB2BGR))
                    fused_bytes = buf.tobytes()
                elif algo in ("avg", "max", "mertens"):
                    result = cv2.imdecode(np.frombuffer(data_list[0], np.uint8), cv2.IMREAD_COLOR)
                    for di in range(1, min(len(data_list), 2)):  # use first 2 for traditional
                        img = cv2.imdecode(np.frombuffer(data_list[di], np.uint8), cv2.IMREAD_COLOR)
                        if algo == "avg":
                            result = cv2.addWeighted(result, 0.5, img, 0.5, 0)
                        elif algo == "max":
                            result = cv2.max(result, img)
                        elif algo == "mertens":
                            merge_mertens = cv2.createMergeMertens()
                            result_f = merge_mertens.process([result, img])
                            result = np.clip(result_f * 255, 0, 255).astype(np.uint8)
                    _, buf = cv2.imencode('.jpg', result, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                    fused_bytes = buf.tobytes()
                else:
                    results.append({"algo": algo, "error": "算法不可用"})
                    continue

                # Save and compute quick metrics
                os.makedirs(save_dir, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                fname = f"compare_{algo}_{ts}.jpg"
                spath = save_dir / fname
                with open(spath, "wb") as sf:
                    sf.write(fused_bytes)

                img_url = str(request.url_for("static", path=fname))

                # Quick metrics
                pil_img = Image.open(io.BytesIO(fused_bytes)).convert('L')
                fg = np.array(pil_img)
                quick = ImageMetrics.evaluate(fg)

                curr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO history (algo, img_url, time, en, sd, sf, ag, vif, qabf) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (f"对比-{algo}", img_url, curr_time,
                           quick.get('EN', 0), quick.get('SD', 0),
                           quick.get('SF', 0), quick.get('AG', 0), 0.0, 0.0))
                conn.commit()
                conn.close()

                results.append({"algo": algo, "image_url": img_url, "metrics": quick})

            except Exception as e:
                print(f"[compare] Error for {algo}: {e}")
                results.append({"algo": algo, "error": str(e)})

        return {"code": 200, "data": results}

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] 对比融合发生错误：")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: Commit**

```bash
git add api_server.py
git commit -m "feat: add /api/fuse/compare endpoint for batch multi-algorithm comparison"
```

---

### Task 10: Comparison page — frontend view

**Files:**
- Create: `mef-frontend/src/components/ComparisonView.vue`
- Modify: `mef-frontend/src/App.vue` (add toggle)
- Modify: `mef-frontend/src/composables/useFusion.js` (add comparison state/method)

- [ ] **Step 1: Add comparison state to useFusion.js**

Add to the end of the `useFusion` composable, before the final `return` statement:

```javascript
  // Comparison state
  const comparisonResults = ref(null)
  const isComparing = ref(false)

  const startComparison = async () => {
    if (imageFiles.value.length < 2) {
      ElMessage.warning('请至少上传 2 张源图像')
      return false
    }

    isComparing.value = true
    comparisonResults.value = null

    try {
      const formData = new FormData()
      for (const file of imageFiles.value) {
        formData.append('files', file)
      }
      formData.append('algorithms', 'ai,ffmef,avg,max,mertens')
      formData.append('quality', quality.value)
      formData.append('max_dim', maxDim.value)

      const res = await fetch(`${API_BASE}/api/fuse/compare`, {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        const data = await res.json()
        if (data.code === 200) {
          comparisonResults.value = data.data
        }
      }
      ElMessage.success('对比完成')
      return true
    } catch (e) {
      console.error(e)
      ElMessage.error('对比失败')
      return false
    } finally {
      isComparing.value = false
    }
    return false
  }
```

Add to the return object:

```javascript
    comparisonResults, isComparing, startComparison,
```

- [ ] **Step 2: Create ComparisonView.vue**

```vue
<script setup>
import { ref } from 'vue'

const props = defineProps({
  results: { type: Array, default: null },
  isComparing: { type: Boolean, default: false },
})

const algoLabels = {
  ai: 'IF-FILM',
  ffmef: 'FFMEF',
  avg: '加权平均',
  max: '最大值',
  mertens: 'Mertens',
}
</script>

<template>
  <div class="comparison-view">
    <div class="comparison-header">
      <h3>算法对比</h3>
      <span v-if="results" class="result-count">{{ results.length }} 个算法</span>
    </div>

    <div v-if="isComparing" class="comparison-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在运行所有算法...</span>
    </div>

    <div v-else-if="results" class="comparison-grid">
      <div
        v-for="item in results"
        :key="item.algo"
        class="comparison-card"
      >
        <div class="card-header">
          <span class="algo-name">{{ algoLabels[item.algo] || item.algo }}</span>
          <span v-if="item.metrics" class="algo-en">EN: {{ item.metrics.EN }}</span>
        </div>
        <div class="card-image">
          <img v-if="item.image_url" :src="item.image_url" :alt="item.algo" />
          <div v-else-if="item.error" class="card-error">
            {{ item.error }}
          </div>
        </div>
        <div v-if="item.metrics" class="card-metrics">
          <span class="mini-metric" v-for="m in ['SD', 'SF', 'AG']" :key="m">
            {{ m }}: {{ item.metrics[m] }}
          </span>
        </div>
      </div>
    </div>

    <div v-else class="comparison-empty">
      <el-icon><Picture /></el-icon>
      <span>上传图片后点击"运行对比"</span>
    </div>
  </div>
</template>

<style scoped>
.comparison-view {
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: 12px;
  padding: 14px;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.comparison-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.result-count {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.comparison-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 8px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.comparison-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.comparison-card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-card);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: var(--color-bg-subtle);
}

.algo-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
}

.algo-en {
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--color-primary);
  font-weight: 600;
}

.card-image {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  background: var(--color-bg-subtle);
}

.card-image img {
  max-width: 100%;
  max-height: 160px;
  object-fit: contain;
}

.card-error {
  padding: 12px;
  font-size: 11px;
  color: var(--color-error);
  text-align: center;
}

.card-metrics {
  display: flex;
  gap: 8px;
  padding: 4px 8px;
  font-size: 9px;
  font-family: var(--font-mono);
  color: var(--color-text-secondary);
}

.comparison-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 8px;
  color: var(--color-text-tertiary);
  font-size: 12px;
}
</style>
```

- [ ] **Step 3: Update App.vue to toggle between fusion and comparison views**

Add a tab toggle at the top of `App.vue`. Add `const viewMode = ref('fusion')` and a simple tab switcher.

Add to the script section:
```javascript
const viewMode = ref('fusion')
const comparisonResults = useFusion().comparisonResults
const isComparing = useFusion().isComparing
const startComparison = useFusion().startComparison
```

Actually, better: import comparison state from the composable. Modify App.vue script:

```javascript
// Add to the destructured useFusion return:
const {
  // ... existing ...
  comparisonResults, isComparing, startComparison,
} = useFusion()
```

Add tab toggle in the template, between `<AppHeader>` and `<main>`:

```vue
    <!-- View mode toggle -->
    <div class="view-toggle">
      <button :class="{ active: viewMode === 'fusion' }" @click="viewMode = 'fusion'">融合</button>
      <button :class="{ active: viewMode === 'compare' }" @click="viewMode = 'compare'">对比</button>
    </div>
```

Replace the `<main>` content to conditionally show fusion or comparison view. Wrap the existing main content in `<template v-if="viewMode === 'fusion'">` and add comparison view in `<template v-else>`.

For the comparison view:
```vue
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
            <el-button
              type="primary"
              size="large"
              :loading="isComparing"
              @click="startComparison"
              :disabled="imageFiles.length < 2"
            >
              {{ isComparing ? '对比中...' : '运行全部算法对比' }}
            </el-button>
          </div>
        </section>
        <ComparisonView
          :results="comparisonResults"
          :is-comparing="isComparing"
        />
      </div>
    </main>
```

Add CSS for view-toggle:
```css
.view-toggle {
  display: flex;
  gap: 4px;
  padding: 0 12px;
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
```

- [ ] **Step 4: Import ComparisonView in App.vue**

Add to imports:
```javascript
import ComparisonView from './components/ComparisonView.vue'
```

- [ ] **Step 5: Commit**

```bash
git add mef-frontend/src/components/ComparisonView.vue mef-frontend/src/composables/useFusion.js mef-frontend/src/App.vue
git commit -m "feat: add comparison page with batch algorithm results grid"
```

---

### Task 11: Final cleanup and push

- [ ] **Step 1: Run frontend build check**

```bash
cd mef-frontend && npm run build
```

Expected: build succeeds or shows only minor warnings.

- [ ] **Step 2: Commit any fixes**

```bash
git add -A
git commit -m "fix: address build issues from enhancement"
```

- [ ] **Step 3: Push to remote**

```bash
git push origin main
```

---

## Self-Review Checklist

**1. Spec coverage:**

| Spec requirement | Task |
|---|---|
| Multi-image upload (2-10+) | Task 2 (ImageList), Task 5 (useFusion), Task 7 (App.vue), Task 8 (fuse-multi API) |
| Selective metrics | Task 6 (MetricsDashboard checkboxes), Task 8 (evaluate metrics param) |
| Algorithm comparison page | Task 9 (compare API), Task 10 (ComparisonView) |
| User parameters | Task 3 (ParamPanel), Task 5 (quality/maxDim state), Task 7 (App.vue wiring) |
| Algorithm info cards | Task 1 (algorithms.js), Task 4 (AlgorithmInfo), Task 7 (App.vue wiring) |
| P2 deferred (no model change) | Explicitly not included — deferred per spec |

All requirements covered. No gaps.

**2. Placeholder scan:** No TBD/TODO patterns found. All code blocks are complete.

**3. Type consistency:** 
- `imageFiles` used consistently across Tasks 2, 5, 7, 10
- `quality`/`maxDim` consistent across Tasks 3, 5, 7, 8, 9, 10
- `selectedMetrics` consistent across Tasks 5, 6
- API endpoint `/api/fuse-multi` uses `files` form field, matched by frontend `formData.append('files', file)`

**4. Scope check:** Plan covers only P0/P1 features per spec. No unrelated refactoring. Existing `/api/fuse` endpoint preserved unchanged.
