# Frontend Layout Redesign Spec

**Date:** 2026-05-14
**Status:** Approved by user

## Problem

Current layout uses a 320px fixed left panel (upload + algorithm + button) and a 1fr right panel (viewer + metrics). The input area is too cramped, making the analysis portion dominate the screen. The layout feels unbalanced.

## Solution Overview

Switch to a **three-row workstation layout** with modern glass-morphism styling, increased max-width (1400px), and equal visual weight between input, display, and analysis areas.

## Layout Architecture

### Row 1: Input Row (top horizontal)
- Two upload boxes side-by-side, each `200px` wide
- Algorithm selector chips in remaining space
- Full-width fusion button below

### Row 2: Image Display Row (middle)
- Left column (1fr): Source images side-by-side (over-exposed + under-exposed)
- Right column (2fr): Fused result with comparison slider

### Row 3: Metrics Row (bottom)
- Three columns: `220px` metrics table | `220px` radar chart | `1fr` bar chart + performance info

### Overall constraints
- `max-width: 1400px`
- Card border-radius: `12px`
- Gap between rows: `16px`
- Glass-effect cards with `backdrop-filter: blur(12px)`

## Component Changes

| Component | Change |
|-----------|--------|
| `App.vue` | Rewrite template: three-row layout with CSS Grid. Remove old left/right panel structure. |
| `style.css` | Add glass-morphism variables, smooth transition variables, enhanced hover effects. |
| `DraggableUpload.vue` | No internal changes. Only adjust external container width. |
| `AlgorithmSelector.vue` | Change to flex horizontal (remove `flex-wrap`), fit chips in one row. |
| `FusionViewer.vue` | Add source image comparison sub-area (side-by-side originals). Result area keeps comparison slider. Receives `overPreview` and `underPreview` props (already exist). |
| `MetricsDashboard.vue` | Change to horizontal three-column layout (table + radar + bar). Remove vertical stacking. |

No new files. No component count changes.

## Data Flow & State

Data flow unchanged. All state managed by `useFusion()` composable. Only addition: `FusionViewer.vue` receives `overPreview` and `underPreview` for side-by-side original display (props already exist).

## Responsive Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| `>= 1200px` | Full three-row layout |
| `768px - 1199px` | Display row stacks vertically (source above, fused below). Metrics row becomes 2 columns (table + merged charts). |
| `< 768px` | Input row stacks vertically (single column). All sections full-width. |

## Empty & Loading States

- No images: Input row shows upload boxes, display row shows empty placeholder, metrics row hidden
- Loading: FusionViewer skeleton loader (unchanged)

## CSS Variables to Add

```css
--color-glass: rgba(255, 255, 255, 0.85);
--color-glass-border: rgba(226, 232, 240, 0.6);
--shadow-glass: 0 4px 24px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
--transition-smooth: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
```

## Animation Enhancements

- Upload box hover: slight lift + shadow deepen
- Algorithm chip: gradient fill animation on select
- Fusion result: fade-in + scale on appear
- Metrics panel: staggered fade-in on reveal
