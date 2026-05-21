# FILM Enhancement Design

**Date**: 2026-05-14
**Status**: Approved

## Problem Statement

Current FILM system only supports 2-image fusion (over/under), no algorithm comparison view, no user-configurable parameters, no selective metrics computation, and no algorithm documentation. Additionally, the model architecture (fixed 2-input, pure Restormer blocks) needs exploration for multi-image scenarios.

## Scope

| Priority | Feature | Scope |
|----------|---------|-------|
| P0 | Multi-image upload (2-10+) | Frontend + API + Engine (pairwise fallback) |
| P0 | Selective metrics computation | Frontend checkboxes + API params |
| P1 | Algorithm comparison page | Dedicated view, batch-run all algorithms |
| P1 | User parameters | JPEG quality, max image size |
| P1 | Algorithm info cards | Static frontend data, principle + paper citation |
| P2 | Architecture innovation | Deferred — requires baseline first, data-backed |

**P2 Deferred Policy**: No model architecture change without:
1. Baseline metrics from current model on MEFB test set
2. Clear bottleneck identification
3. Literature/theory justification for proposed change
4. Post-change metrics ≥ baseline (5/6 items at minimum, overall improvement)

## Architecture

### Multi-Image Fusion Pipeline

```
Frontend (2-10 images)
    │
    ├── Upload as list (FormData: files[])
    │
    ▼
POST /api/fuse-multi (new endpoint)
    │
    ├── N=2: route to existing /api/fuse (no change)
    │
    ├── N>2 (old model): pairwise iterative fusion
    │   [img1 + img2] → fused_12 → [fused_12 + img3] → fused_123 → ...
    │   All in YCbCr space, only Y through network
    │
    └── N>2 (new model, future): N-channel direct fusion
        After retraining with multi-input architecture
```

### Pairwise Fusion Rationale

The existing `MEFFusionEngine.fuse()` already handles 2-image YCbCr fusion. For N>2:
- No retraining needed — existing MEF.pth checkpoint works
- Baseline-preserving: each pairwise step is identical to current pipeline
- If pairwise metrics drift significantly from 2-input baseline, it signals the need for architectural change (not a band-aid workaround)

### Selective Metrics

Current `/api/evaluate` always computes EN/SD/SF/AG immediately, then VIF/Qabf in background. New behavior:
- Accept `metrics` form parameter: comma-separated list (e.g., `EN,SD,VIF`)
- Only compute requested metrics
- DB record updated with 0.0 for uncomputed metrics
- Frontend shows `--` for uncomputed values

### Algorithm Info Cards

Static frontend data file (`mef-frontend/src/data/algorithms.js`):
- Key: algorithm slug (`ai`, `ffmef`, `avg`, `max`, `mertens`)
- Value: `{ name, principle (2-3 sentences), citation: { title, venue, year, link } }`
- Displayed alongside fusion result when algorithm is selected

### Comparison Page

- New route or standalone view showing same source images fused by different algorithms
- API endpoint: `POST /api/fuse/compare` — accepts images + algorithm list, returns results sequentially
- UI: grid layout, each cell = algorithm name + fused result + mini metrics
- Stored in DB with `algo` field distinguishing each run

## Component Changes

### Frontend

| Component | Change |
|-----------|--------|
| `DraggableUpload.vue` | Convert to `ImageList.vue` — dynamic add/remove, thumbnail grid |
| `App.vue` | Layout: replace 2 upload slots with image list; add parameter drawer; add compare page toggle |
| `useFusion.js` | New state: `imageFiles[]`, `fusionParams`, `selectedMetrics`; new `startFusionMulti()` |
| `MetricsDashboard.vue` | Add checkboxes for EN/SD/SF/AG/VIF/Qabf; only show computed values |
| NEW: `AlgorithmInfo.vue` | Static info card: principle + citation |
| NEW: `ParamPanel.vue` | JPEG quality slider (50-100), max size slider (512-4096) |
| NEW: `ComparisonView.vue` | Grid view for multi-algorithm comparison |
| NEW: `data/algorithms.js` | Static algorithm metadata |

### Backend

| Endpoint | Change |
|----------|--------|
| `POST /api/fuse` | No change (2-image path) |
| `POST /api/fuse-multi` | **NEW**: accepts N images, pairwise fusion for N>2 |
| `POST /api/evaluate` | Accept `metrics` param; only compute selected |
| `POST /api/fuse/compare` | **NEW**: batch-run algorithms, return all results |

### Engine

| File | Change |
|------|--------|
| `mef_engine.py` | Add `fuse_multi(files_bytes, quality, max_dim)` method |
| `api_server.py` | Wire up new endpoints |

## Data Flow

### Multi-Image Fusion

```
User uploads N images → Frontend shows thumbnails
User clicks "融合" → POST /api/fuse-multi with FormData:
  - files[]: N image files
  - algo_type: ai/ffmef/avg/max/mertens
  - quality: 95
  - max_dim: 1024
  - algo: display name

Backend:
  1. Validate all files (type, size, same dimensions)
  2. If N==2: call existing fuse path
  3. If N>2: call fuse_multi (pairwise iteration)
  4. Save result to storage/results/
  5. Return fused image as JPEG

Evaluate (optional):
  POST /api/evaluate with:
  - image_file: fused result
  - metrics: "EN,SD,AG,VIF"
  - over_img, under_img: source images (for VIF/Qabf)
```

### Comparison

```
User clicks "对比" → opens ComparisonView
User uploads images → clicks "运行全部算法"
POST /api/fuse/compare:
  - files[]: images
  - algorithms: ["ai", "ffmef", "avg", "max", "mertens"]

Backend runs each algorithm sequentially, saves results
Returns: [{ algo, image_url, metrics }, ...]

Frontend renders grid: each cell = algo name + image + metrics
```

## Error Handling

- N>10 images: reject with message "最多支持10张图片"
- Mismatched dimensions: reject with "所有输入图像必须尺寸一致"
- Pairwise fusion quality degradation: log warning if intermediate result differs significantly from inputs (future monitoring)
- Algorithm failure in comparison mode: show error for that cell, continue with others

## Testing Strategy

**Before any model change**:
1. Run `python test.py` on MEFB — record EN/SD/SF/AG/VIF/Qabf as baseline
2. Save to `docs/baseline_metrics.json`

**After pairwise multi-image support**:
1. Test with 3, 5, 8 images from MEFB
2. Compare metrics against 2-input baseline (should be close for 2 images, may vary for N>2)

**After architecture change**:
1. Train new model on 3090
2. Run `test.py` — compare against `docs/baseline_metrics.json`
3. If < 5/6 metrics match or exceed baseline, rollback

## Migration Path

1. Phase 1 (Day 1-2): Frontend + API features (P0, P1) — existing model, no risk
2. Phase 2: Establish baseline + pairwise multi-image — functional, metrics verified
3. Phase 3 (deferred): Architecture innovation — data-driven, rigorous comparison
