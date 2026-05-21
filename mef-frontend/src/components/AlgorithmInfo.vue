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
        <a :href="getAlgo(algo).citation.link" target="_blank" rel="noopener" class="citation-link" v-if="getAlgo(algo).citation.link">查看论文</a>
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
