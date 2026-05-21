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
    <div class="algo-left">
      <div class="algo-name">{{ getAlgo(algo).fullName }}</div>
      <p class="algo-principle">{{ getAlgo(algo).principle }}</p>
    </div>
    <div class="algo-right">
      <div v-if="getAlgo(algo).citation" class="algo-citation">
        <span class="citation-icon">📄</span>
        <div class="citation-details">
          <span class="citation-title">{{ getAlgo(algo).citation.title }}</span>
          <span class="citation-venue">{{ getAlgo(algo).citation.venue }}, {{ getAlgo(algo).citation.year }}</span>
          <a :href="getAlgo(algo).citation.link" target="_blank" rel="noopener" class="citation-link" v-if="getAlgo(algo).citation.link">查看论文</a>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.algo-info-card {
  background: transparent;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-start;
}

.algo-left {
  flex: 1;
  min-width: 280px;
}

.algo-right {
  flex-shrink: 0;
  min-width: 220px;
}

.algo-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 8px;
}

.algo-principle {
  font-size: 13px;
  line-height: 1.7;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
}

.algo-citation {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-bg-subtle);
  border-radius: 8px;
}

.citation-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.citation-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.citation-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
}

.citation-venue {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.citation-link {
  font-size: 11px;
  color: var(--color-primary);
  text-decoration: none;
}

.citation-link:hover {
  text-decoration: underline;
}
</style>
