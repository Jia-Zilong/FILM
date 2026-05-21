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

  return {
    imageFiles, previews, isFusing, fusedImageUrl, metrics,
    selectedAlgo, fusionTime, sliderValue, quality, maxDim, selectedMetrics,
    comparisonResults, isComparing, startComparison,
    setImageFiles, clearPreviews, startFusion, downloadImage,
  }
}
