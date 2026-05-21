import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { API_BASE } from '../config/api'

export function useHistory() {
  const historyList = ref([])
  const loadingHistory = ref(false)

  const fetchHistory = async () => {
    loadingHistory.value = true
    try {
      const res = await axios.get(`${API_BASE}/api/history`)
      if (res.data.code === 200) {
        historyList.value = res.data.data
      }
    } catch (e) {
      ElMessage.error('无法获取历史记录')
    } finally {
      loadingHistory.value = false
    }
  }

  const exportToCSV = () => {
    if (historyList.value.length === 0) {
      ElMessage.warning('暂无数据可导出')
      return
    }
    let csvContent = "时间,算法,EN(信息熵),SD(标准差),SF(空间频率),AG(平均梯度),VIF,Qabf\n"
    historyList.value.forEach(item => {
      const row = `${item.time},${item.algo || '未知'},${item.metrics.EN},${item.metrics.SD},${item.metrics.SF},${item.metrics.AG},${item.metrics.VIF ?? '--'},${item.metrics.Qabf ?? '--'}\n`
      csvContent += row
    })
    const blob = new Blob(["﻿" + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.setAttribute("href", url)
    link.setAttribute("download", `实验数据报表_${new Date().getTime()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('实验数据已导出')
  }

  return { historyList, loadingHistory, fetchHistory, exportToCSV }
}
