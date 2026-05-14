<script setup>
const emit = defineEmits(['open-history'])
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <div class="logo-text">
        <span class="logo-mark">IF</span>
        <span class="logo-name">FILM</span>
      </div>
      <span class="header-divider"></span>
      <span class="header-subtitle">多曝光图像融合系统</span>
    </div>
    <div class="header-right">
      <span class="status-badge">
        <span class="status-dot"></span> 服务就绪
      </span>
      <el-button class="history-btn" @click="emit('open-history')">
        <el-icon><Clock /></el-icon>
        历史记录
      </el-button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  height: 56px;
  padding: 0 var(--space-6);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow-xs);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.logo-text {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.logo-mark {
  font-size: 20px;
  font-weight: 800;
  background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: 0.5px;
}

.header-divider {
  width: 1px;
  height: 16px;
  background: var(--color-border);
  border-radius: 1px;
}

.header-subtitle {
  font-size: 12px;
  color: var(--color-text-secondary);
  letter-spacing: 0.3px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.status-badge {
  font-size: 12px;
  color: var(--color-success);
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  background: var(--color-success);
  border-radius: 50%;
  display: inline-block;
  animation: status-pulse 2s ease-in-out infinite;
}

@keyframes status-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.4); }
  50% { box-shadow: 0 0 0 4px rgba(5, 150, 105, 0); }
}

.history-btn {
  font-size: 13px;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.history-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}
</style>
