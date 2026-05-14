<script setup>
import { computed } from 'vue'
import { useHistory } from '../composables/useHistory'

const props = defineProps({
  visible: { type: Boolean, default: false }
})
const emit = defineEmits(['update:visible'])

const { historyList, loadingHistory, fetchHistory, exportToCSV } = useHistory()

const drawerVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const onOpen = () => {
  fetchHistory()
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    title="历史记录"
    size="400px"
    @open="onOpen"
  >
    <template #header>
      <div class="drawer-header">
        <span class="drawer-title">历史记录</span>
        <el-button
          type="warning"
          size="small"
          round
          class="export-btn"
          @click="exportToCSV"
          :disabled="historyList.length === 0"
        >
          <el-icon><Download /></el-icon>
          导出 CSV
        </el-button>
      </div>
    </template>

    <Transition name="fade" mode="out-in">
      <div v-if="historyList.length === 0" key="empty" class="history-empty">
        <el-icon class="empty-icon"><Document /></el-icon>
        <span>暂无历史记录</span>
      </div>

      <div v-else key="list" class="history-list" v-loading="loadingHistory">
        <TransitionGroup name="card-slide">
          <div v-for="item in historyList" :key="item.id" class="history-card">
            <div class="card-header">
              <span class="card-time">
                <el-icon><Clock /></el-icon>
                {{ item.time }}
              </span>
              <el-tag size="small" class="algo-tag" round>
                {{ item.algo || '未知' }}
              </el-tag>
            </div>
            <div class="card-image-wrapper">
              <img :src="item.fused" class="card-image" />
            </div>
            <div class="card-metrics">
              <span class="metric">
                <span class="metric-label">EN</span>
                {{ item.metrics.EN?.toFixed(2) }}
              </span>
              <span class="metric metric-success">
                <span class="metric-label">SD</span>
                {{ item.metrics.SD?.toFixed(2) }}
              </span>
              <span class="metric metric-warning">
                <span class="metric-label">AG</span>
                {{ item.metrics.AG?.toFixed(2) }}
              </span>
            </div>
          </div>
        </TransitionGroup>
      </div>
    </Transition>
  </el-drawer>
</template>

<style scoped>
.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.drawer-title {
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.export-btn {
  transition: all 0.2s ease;
}

.export-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.history-list {
  padding: var(--space-4) 0;
}

.history-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-tertiary);
  font-size: 13px;
  padding: var(--space-8) 0;
}

.history-empty .empty-icon {
  font-size: 40px;
  color: var(--color-text-tertiary);
}

.history-card {
  margin-bottom: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-card);
  box-shadow: var(--shadow-xs);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.history-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-subtle);
  border-bottom: 1px solid var(--color-border);
}

.card-time {
  font-size: 11px;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-time .el-icon {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.algo-tag {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  color: #fff;
  border: none;
  font-weight: 600;
}

.card-image-wrapper {
  overflow: hidden;
}

.card-image {
  width: 100%;
  height: 160px;
  object-fit: cover;
  display: block;
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.history-card:hover .card-image {
  transform: scale(1.03);
}

.card-metrics {
  display: flex;
  justify-content: space-around;
  padding: var(--space-2) var(--space-3);
  gap: var(--space-2);
  background: var(--color-card);
}

.metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-primary);
  background: #EFF6FF;
  transition: all 0.15s ease;
  flex: 1;
}

.metric:hover {
  transform: scale(1.05);
}

.metric-label {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.7;
}

.metric-success {
  color: var(--color-success);
  background: #ECFDF5;
}

.metric-warning {
  color: var(--color-warning);
  background: #FFFBEB;
}

/* Slide-in/out for cards */
.card-slide-enter-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.card-slide-leave-active {
  transition: all 0.2s ease;
}
.card-slide-enter-from,
.card-slide-leave-to {
  opacity: 0;
  transform: translateX(16px);
}
.card-slide-move {
  transition: transform 0.3s ease;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
