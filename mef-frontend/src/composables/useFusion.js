import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { API_BASE } from '../config/api'

export function useFusion() {
  // State
  const overFile = ref(null)
  const underFile = ref(null)
  const overPreview = ref('')
  const underPreview = ref('')
  const isFusing = ref(false)
  const fusedImageUrl = ref('')
  const metrics = ref(null)
  const selectedAlgo = ref('ai')
  const fusionTime = ref(null)
  const sliderValue = ref(50)

  const setOverImage = (file) => {
    overFile.value = file
    if (overPreview.value) URL.revokeObjectURL(overPreview.value)
    overPreview.value = URL.createObjectURL(file)
  }

  const setUnderImage = (file) => {
    underFile.value = file
    if (underPreview.value) URL.revokeObjectURL(underPreview.value)
    underPreview.value = URL.createObjectURL(file)
  }

  const clearPreviews = () => {
    if (overPreview.value) URL.revokeObjectURL(overPreview.value)
    if (underPreview.value) URL.revokeObjectURL(underPreview.value)
    if (fusedImageUrl.value) URL.revokeObjectURL(fusedImageUrl.value)
  }

  const startFusion = async () => {
    if (!overFile.value || !underFile.value) {
      ElMessage.warning('请先上传源图像')
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
      formData.append('over_img', overFile.value)
      formData.append('under_img', underFile.value)
      if (selectedAlgo.value === 'avg' || selectedAlgo.value === 'max' || selectedAlgo.value === 'mertens') {
        formData.append('algo_type', selectedAlgo.value)
      }

      const endpoint = selectedAlgo.value === 'ai'
        ? `${API_BASE}/api/fuse`
        : selectedAlgo.value === 'ffmef'
        ? `${API_BASE}/api/fuse/ffmef`
        : `${API_BASE}/api/fuse/traditional`

      const fuseRes = await axios.post(endpoint, formData, { responseType: 'blob' })
      // Use File instead of Blob for reliable multipart upload
      const imgFile = new File([fuseRes.data], 'res.jpg', { type: 'image/jpeg' })
      fusedImageUrl.value = URL.createObjectURL(imgFile)

      const evalFormData = new FormData()
      evalFormData.append('image_file', imgFile)
      evalFormData.append('over_img', overFile.value)
      evalFormData.append('under_img', underFile.value)
      const algoNameMap = {
        'ai': 'IF-FILM(深度学习)',
        'ffmef': 'FFMEF(深度学习)',
        'avg': '加权平均(传统)',
        'mertens': 'Mertens融合',
        'max': '最大值保留'
      }
      evalFormData.append('algo', algoNameMap[selectedAlgo.value])

      // Use native fetch for reliable multipart FormData serialization
      const evalRes = await fetch(`${API_BASE}/api/evaluate`, {
        method: 'POST',
        body: evalFormData
      })
      if (evalRes.ok) {
        const evalData = await evalRes.json()
        if (evalData.code === 200) {
          metrics.value = evalData.data
        }
      }
      const elapsed = Math.round(performance.now() - startTime)
      fusionTime.value = elapsed
      ElMessage.success('融合成功')

      // Poll history for VIF/Qabf (computed in background)
      let pollCount = 0
      const pollInterval = setInterval(async () => {
        pollCount++
        if (pollCount > 40) { clearInterval(pollInterval); return } // timeout after 20s
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

      return true
    } catch (e) {
      ElMessage.error('后端服务未响应')
      return false
    } finally {
      isFusing.value = false
    }
    return false
  }

  const downloadImage = () => {
    if (!fusedImageUrl.value) return
    const a = document.createElement('a')
    a.href = fusedImageUrl.value
    a.download = `MEF_${selectedAlgo.value}_${Date.now()}.jpg`
    a.click()
  }

  return {
    overFile, underFile, overPreview, underPreview,
    isFusing, fusedImageUrl, metrics, selectedAlgo, fusionTime, sliderValue,
    setOverImage, setUnderImage, clearPreviews,
    startFusion, downloadImage
  }
}
