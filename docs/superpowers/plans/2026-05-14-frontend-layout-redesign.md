# Frontend Layout Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the MEF frontend from a cramped left-right panel layout to a balanced three-row workstation layout with modern glass-morphism styling.

**Architecture:** Three-row CSS Grid layout (input row → display row → metrics row). Existing Vue components retained but repositioned. Glass-morphism effects via CSS variables and backdrop-filter. Responsive breakpoints at 1200px and 768px.

**Tech Stack:** Vue 3 (Composition API), Vite, Element Plus, ECharts, CSS Grid/Flexbox

---

## File Responsibility Map

| File | Responsibility |
|------|---------------|
| `mef-frontend/src/style.css` | Add glass-morphism CSS variables, enhanced transitions |
| `mef-frontend/src/App.vue` | Rewrite template: three-row grid layout. Update styles for new layout. |
| `mef-frontend/src/components/AlgorithmSelector.vue` | Change from flex-wrap to single-row horizontal flex layout |
| `mef-frontend/src/components/FusionViewer.vue` | Add source image side-by-side sub-area. Keep existing comparison slider. Add props for over/under previews (already exists: `underPreview`). |
| `mef-frontend/src/components/MetricsDashboard.vue` | Change from vertical stacking to horizontal three-column layout (table + radar + bar) |

**Files NOT modified:** `DraggableUpload.vue`, `AppHeader.vue`, `HistoryDrawer.vue`, `useFusion.js`, `useHistory.js`

---

### Task 1: Add CSS Variables & Global Enhancements

**Files:**
- Modify: `mef-frontend/src/style.css`

- [ ] **Step 1: Add glass-morphism CSS variables**

Append these new variables to the `:root` block in `style.css` (after the existing `--font-mono` line, before the closing `}`):

```css
  /* Glass-morphism */
  --color-glass: rgba(255, 255, 255, 0.85);
  --color-glass-border: rgba(226, 232, 240, 0.6);
  --shadow-glass: 0 4px 24px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
  --transition-smooth: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
```

- [ ] **Step 2: Verify no syntax errors**

Run: `cd mef-frontend && npx vite build`
Expected: Build succeeds with no errors

- [ ] **Step 3: Commit**

```bash
cd mef-frontend
git add src/style.css
git commit -m "style: add glass-morphism CSS variables for layout redesign"
```

---

### Task 2: Rewrite App.vue Layout to Three-Row Grid

**Files:**
- Modify: `mef-frontend/src/App.vue`

- [ ] **Step 1: Replace the entire `<template>` section**

Replace the current `<template>` block (lines 26-80) with:

```vue
<template>
  <div class="app-layout">
    <AppHeader @open-history="showHistory = true" />

    <main class="app-main">
      <div class="workspace">
        <!-- Row 1: Input Row (horizontal) -->
        <section class="input-row">
          <div class="upload-group">
            <DraggableUpload
              label="过曝图像 (Over)"
              v-model="overFile"
              @update:model-value="setOverImage"
            />
            <DraggableUpload
              label="欠曝图像 (Under)"
              v-model="underFile"
              @update:model-value="setUnderImage"
            />
          </div>

          <div class="algo-section">
            <AlgorithmSelector v-model="selectedAlgo" />
          </div>

          <el-button
            type="primary"
            size="large"
            class="fuse-button"
            :loading="isFusing"
            @click="handleFuse"
          >
            {{ isFusing ? '融合中...' : '执行融合' }}
          </el-button>
        </section>

        <!-- Row 2: Display Row -->
        <section class="display-row">
          <div class="source-panel glass-card">
            <div class="panel-header">
              <h3 class="panel-title">源图像</h3>
              <div class="source-labels">
                <span class="source-tag">过曝</span>
                <span class="source-tag">欠曝</span>
              </div>
            </div>
            <div class="source-images">
              <div class="source-image-wrapper" :class="{ empty: !overPreview }">
                <img v-if="overPreview" :src="overPreview" alt="过曝" class="source-img" />
                <div v-else class="source-empty">
                  <el-icon><Picture /></el-icon>
                  <span>过曝</span>
                </div>
              </div>
              <div class="source-image-wrapper" :class="{ empty: !underPreview }">
                <img v-if="underPreview" :src="underPreview" alt="欠曝" class="source-img" />
                <div v-else class="source-empty">
                  <el-icon><Picture /></el-icon>
                  <span>欠曝</span>
                </div>
              </div>
            </div>
          </div>

          <div class="result-panel">
            <FusionViewer
              :fused-image-url="fusedImageUrl"
              :under-preview="underPreview"
              :over-preview="overPreview"
              :is-fusing="isFusing"
              @download="downloadImage"
            />
          </div>
        </section>

        <!-- Row 3: Metrics Row -->
        <section class="metrics-row">
          <MetricsDashboard
            :metrics="metrics"
            :fusion-time="fusionTime"
            :fused-image-url="fusedImageUrl"
          />
        </section>
      </div>
    </main>

    <HistoryDrawer v-model:visible="showHistory" />
  </div>
</template>
```

- [ ] **Step 2: Replace the entire `<style>` section**

Replace the current `<style scoped>` block (lines 82-169) with:

```vue
<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-main {
  flex: 1;
  padding: var(--space-5);
  display: flex;
  justify-content: center;
}

.workspace {
  width: 100%;
  max-width: 1400px;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ===== Row 1: Input Row ===== */
.input-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-glass);
}

.upload-group {
  display: flex;
  gap: var(--space-3);
  flex-shrink: 0;
  width: 420px;
}

.algo-section {
  flex: 1;
  min-width: 0;
}

.fuse-button {
  flex-shrink: 0;
  width: 160px;
  height: 44px;
  font-size: 14px;
  font-weight: 600;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
  transition: var(--transition-smooth);
  align-self: center;
}

.fuse-button:hover {
  background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.3);
  transform: translateY(-1px);
}

.fuse-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.fuse-button:disabled {
  background: linear-gradient(135deg, #94A3B8 0%, #64748B 100%);
  box-shadow: none;
  transform: none;
}

/* ===== Row 2: Display Row ===== */
.display-row {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--space-4);
}

.source-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: 0.3px;
}

.source-labels {
  display: flex;
  gap: var(--space-2);
}

.source-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: var(--color-bg-subtle);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.source-images {
  display: flex;
  gap: var(--space-3);
  flex: 1;
  min-height: 0;
}

.source-image-wrapper {
  flex: 1;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-bg-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.source-image-wrapper.empty {
  border: 2px dashed var(--color-border);
}

.source-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.source-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.result-panel {
  min-height: 0;
}

/* ===== Row 3: Metrics Row ===== */
.metrics-row {
  min-height: 0;
}

/* ===== Responsive: 768px - 1199px ===== */
@media (max-width: 1199px) {
  .display-row {
    grid-template-columns: 1fr;
  }

  .source-panel {
    order: 1;
  }

  .result-panel {
    order: 2;
  }
}

/* ===== Responsive: < 768px ===== */
@media (max-width: 767px) {
  .app-main {
    padding: var(--space-3);
  }

  .input-row {
    flex-direction: column;
    align-items: stretch;
  }

  .upload-group {
    width: 100%;
    flex-direction: column;
  }

  .fuse-button {
    width: 100%;
  }

  .display-row {
    grid-template-columns: 1fr;
  }
}
</style>
```

- [ ] **Step 3: Add `overPreview` to FusionViewer props usage**

The FusionViewer component needs to accept `overPreview` as a new prop. We'll add it in Task 4. For now, the template passes it via `:over-preview="overPreview"`.

- [ ] **Step 4: Verify build**

Run: `cd mef-frontend && npx vite build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
cd mef-frontend
git add src/App.vue
git commit -m "feat: rewrite App.vue layout to three-row workstation design"
```

---

### Task 3: Update AlgorithmSelector to Single-Row Horizontal

**Files:**
- Modify: `mef-frontend/src/components/AlgorithmSelector.vue`

- [ ] **Step 1: Change `.algo-options` from flex-wrap to single row**

Replace the `.algo-options` CSS rule (around line 48-52):

```css
.algo-options {
  display: flex;
  flex-wrap: nowrap;
  gap: var(--space-2);
  align-items: center;
}
```

- [ ] **Step 2: Make chips shrink gracefully**

Add `white-space: nowrap` and `flex-shrink: 0` to `.algo-chip`:

```css
.algo-chip {
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-card);
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  font-weight: 500;
  box-shadow: var(--shadow-xs);
  position: relative;
  overflow: hidden;
  white-space: nowrap;
  flex-shrink: 0;
}
```

- [ ] **Step 3: Verify build**

Run: `cd mef-frontend && npx vite build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
cd mef-frontend
git add src/components/AlgorithmSelector.vue
git commit -m "style: make algorithm selector single-row horizontal layout"
```

---

### Task 4: Add Source Image Display to FusionViewer

**Files:**
- Modify: `mef-frontend/src/components/FusionViewer.vue`

- [ ] **Step 1: Add `overPreview` prop**

Update the `defineProps` block (lines 4-8):

```vue
defineProps({
  fusedImageUrl: { type: String, default: '' },
  underPreview: { type: String, default: '' },
  overPreview: { type: String, default: '' },
  isFusing: { type: Boolean, default: false }
})
```

- [ ] **Step 2: Add source image display above the fusion result**

Replace the `<div class="viewer-area">` section (lines 30-82) with:

```vue
    <!-- Source images side-by-side -->
    <div v-if="overPreview || underPreview" class="source-preview-row">
      <div class="source-thumb" :class="{ empty: !overPreview }">
        <img v-if="overPreview" :src="overPreview" alt="过曝" />
        <span v-else class="source-label">过曝</span>
      </div>
      <div class="source-thumb" :class="{ empty: !underPreview }">
        <img v-if="underPreview" :src="underPreview" alt="欠曝" />
        <span v-else class="source-label">欠曝</span>
      </div>
    </div>

    <div class="viewer-area">
      <Transition name="image-fade" mode="out-in">
        <template v-if="fusedImageUrl && !isFusing">
          <div class="compare-container">
            <div class="compare-after">
              <img :src="fusedImageUrl" alt="融合后" />
            </div>
            <div
              class="compare-before"
              :style="{ clipPath: `inset(0 ${100 - sliderValue}% 0 0)` }"
            >
              <img :src="underPreview" alt="对比基准" />
            </div>
            <div
              class="compare-divider"
              :style="{ left: sliderValue + '%' }"
            >
              <div class="divider-handle">
                <el-icon><DArrowLeft /></el-icon>
              </div>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              v-model="sliderValue"
              class="compare-slider"
            />
            <Transition name="label-fade">
              <span class="compare-label-left" v-show="sliderValue > 15">原图</span>
            </Transition>
            <Transition name="label-fade">
              <span class="compare-label-right" v-show="sliderValue < 85">融合</span>
            </Transition>
          </div>
        </template>

        <div v-else-if="isFusing" class="skeleton-loader">
          <div class="skeleton-grid">
            <div class="skeleton-block" v-for="n in 4" :key="n"></div>
          </div>
          <div class="skeleton-text">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line long"></div>
          </div>
        </div>

        <div v-else class="empty-state">
          <el-icon class="empty-icon"><Picture /></el-icon>
          <span>上传图像并点击融合</span>
        </div>
      </Transition>
    </div>
```

- [ ] **Step 3: Add CSS for source preview row**

Append these CSS rules at the end of the `<style scoped>` block (after line 293, before `</style>`):

```vue
/* Source preview row */
.source-preview-row {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.source-thumb {
  flex: 1;
  aspect-ratio: 4 / 3;
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
}

.source-thumb.empty {
  border-style: dashed;
}

.source-thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.source-label {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

/* Result image fade-in + scale animation */
.image-fade-enter-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.image-fade-enter-from {
  opacity: 0;
  transform: scale(0.98);
}
```

- [ ] **Step 4: Verify build**

Run: `cd mef-frontend && npx vite build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
cd mef-frontend
git add src/components/FusionViewer.vue
git commit -m "feat: add source image side-by-side display to FusionViewer"
```

---

### Task 5: Update MetricsDashboard to Horizontal Three-Column Layout

**Files:**
- Modify: `mef-frontend/src/components/MetricsDashboard.vue`

- [ ] **Step 1: Change `.metrics-dashboard` layout to horizontal flex**

Replace the `.metrics-dashboard` CSS rule (line 210-215):

```css
.metrics-dashboard {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-glass);
  transition: opacity 0.4s ease;
}
```

- [ ] **Step 2: Change `.metrics-grid` to horizontal sub-layout**

Replace `.metrics-grid` CSS (lines 217-221):

```css
.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  min-width: 220px;
  flex-shrink: 0;
}
```

- [ ] **Step 3: Remove `gap` from `.metrics-dashboard` since items now use flex row**

Update `.chart-box` (lines 278-284) to add right margin:

```css
.chart-box {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  box-shadow: var(--shadow-xs);
  min-width: 220px;
  flex-shrink: 0;
}
```

- [ ] **Step 4: Make bar chart take remaining space**

Update `.chart-box.full-width` (lines 286-288):

```css
.chart-box.full-width {
  flex: 1;
  min-width: 0;
}
```

- [ ] **Step 5: Remove margin-top from metrics-dashboard**

Since the parent `.metrics-row` provides spacing, remove `margin-top: var(--space-4);` from `.metrics-dashboard` (already removed in Step 1's replacement).

- [ ] **Step 6: Add stagger animation for metric table rows**

Add these CSS rules at the end of `<style scoped>`:

```vue
/* Stagger animation for table rows */
.data-table tbody tr {
  opacity: 1;
}

/* Responsive: stack on small screens */
@media (max-width: 1199px) {
  .metrics-dashboard {
    flex-direction: column;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-4);
  }

  .chart-box {
    min-width: 0;
  }
}

@media (max-width: 767px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 7: Verify build**

Run: `cd mef-frontend && npx vite build`
Expected: Build succeeds

- [ ] **Step 8: Commit**

```bash
cd mef-frontend
git add src/components/MetricsDashboard.vue
git commit -m "style: change MetricsDashboard to horizontal three-column layout with glass effect"
```

---

### Task 6: Final Integration Test & Polish

**Files:**
- All modified files from Tasks 1-5

- [ ] **Step 1: Run full build**

Run: `cd mef-frontend && npx vite build`
Expected: Build succeeds with no errors or warnings

- [ ] **Step 2: Start dev server and verify layout**

Run: `cd mef-frontend && npm run dev`
Expected: Vite starts successfully on an available port

Open browser and verify:
1. Input row: Two upload boxes + algorithm chips + button on single horizontal line
2. Display row: Source images on left (1fr), fused result on right (2fr)
3. Metrics row: Table (220px) + Radar (220px) + Bar chart (remaining)
4. Glass effect visible on input row and metrics row
5. Responsive: resize browser to < 1200px and < 768px to verify breakpoints

- [ ] **Step 3: Test functionality end-to-end**

1. Upload two images
2. Select algorithm
3. Click "执行融合"
4. Verify fusion result displays
5. Verify metrics populate in all three sections
6. Verify history button works

- [ ] **Step 4: Final commit**

```bash
cd mef-frontend
git add -A
git commit -m "style: complete frontend layout redesign - three-row workstation with glass-morphism"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- [x] Three-row layout architecture → Task 2
- [x] Input row horizontal (200px upload boxes + algorithm + button) → Task 2
- [x] Display row (1fr source + 2fr result) → Task 2 + Task 4
- [x] Metrics row (220px table + 220px radar + 1fr bar) → Task 5
- [x] Glass-morphism CSS variables → Task 1
- [x] Glass effect cards → Task 2 + Task 5
- [x] AlgorithmSelector single-row → Task 3
- [x] FusionViewer source display → Task 4
- [x] MetricsDashboard horizontal → Task 5
- [x] Responsive breakpoints (1200px, 768px) → Task 2 + Task 5
- [x] Empty/loading states → Preserved from existing components
- [x] Animation enhancements → Task 2 + Task 4 + Task 5

**2. Placeholder scan:** No TBD/TODO/incomplete sections found.

**3. Type consistency:** `overPreview` prop added to FusionViewer in Task 4, passed from App.vue in Task 2. `underPreview` already exists. All props use String type with default ''. Component signatures match.
