# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FILM** (Image Fusion via Vision-Language Model) — ICML 2024. A PyTorch deep learning research project for multi-modal image fusion (infrared-visible, medical, multi-exposure, multi-focus). Also includes a Vue 3 + FastAPI web application for interactive multi-exposure image (MEF) fusion demos.

## Tech Stack

| Component | Stack |
|-----------|-------|
| Backend (training/inference) | Python 3.8.17, PyTorch 1.8.1+cu111, NumPy, OpenCV, h5py |
| API server | FastAPI + Uvicorn |
| Frontend | Vue 3 + Vite + Element Plus + ECharts |
| Comparison methods | FFMEF (CVPRW 2023) — git submodule at `compare_methods/FFMEF/` |

## Directory Structure (Key Paths)

- `net/Film.py` — Main FILM model (`Net` class) with CrossAttention and Restormer blocks
- `net/restormer.py` — Restormer TransformerBlock and auxiliary blocks (DropPath, AttentionBase, InvertedResidualBlock, LayerNorm variants)
- `utils/H5_read.py` — H5 dataset loader (PyTorch `Dataset`)
- `utils/Evaluator.py` — Comprehensive evaluation: 12 metrics (EN, SD, SF, AG, MI, MSE, CC, PSNR, SCD, VIF, Qabf, SSIM)
- `utils/lossfun.py` — Loss functions (Fusionloss, LpLssimLossweight, MEFSSIM, Sobelxy)
- `utils/Logger.py` — Training logger classes (`Logger`, `Logger1`) that create timestamped output dirs with `log.txt` and `param.json`
- `utils/img_read_save.py` — Image I/O via OpenCV and skimage (`image_read_cv2`, `img_save`, `text_read`)
- `utils/plot_fun.py` — Metric plotting utility (`draw_epoch_metric`)
- `utils/save_code.py` — Code snapshot utility for training experiments
- `VLFDataset/` — Vision-Language dataset (images, text descriptions, BLIP2 text features)
- `VLFDataset_h5/` — Preprocessed HDF5 datasets
- `models/*.pth` — Pretrained checkpoints (IVF, MEF, MFF, MIF, ~25 MB each)
- `mef-frontend/` — Vue 3 web application
  - `src/App.vue` — Layout shell (~80 lines), assembles sub-components
  - `src/config/api.js` — API base URL (`VITE_API_BASE_URL` env var, defaults to `http://127.0.0.1:8000`)
  - `src/composables/` — Shared logic: `useFusion.js` (API + state), `useHistory.js` (history + CSV export)
  - `src/components/` — `AppHeader.vue`, `DraggableUpload.vue`, `AlgorithmSelector.vue`, `FusionViewer.vue`, `MetricsDashboard.vue`, `HistoryDrawer.vue`
  - `src/style.css` — Global CSS variables (color system, spacing, radius, fonts)
- `api_server.py` — FastAPI REST API server (port 8000)
- `mef_engine.py` — MEF fusion inference engine (YCbCr color space: neural net processes Y channel only, Cb/Cr blended at 50/50)
- `mef_metrics.py` — Image quality metrics (EN, SD, SF, AG) implemented directly via numpy/OpenCV, used by API evaluate endpoint
- `data_process.py` — Dataset preprocessing from VLFDataset to HDF5 (relies on `train.txt` file listing sample names)
- `data_process_MEFB.py` — Variant of `data_process.py` that auto-scans the OVER directory instead of relying on a `.txt` file
- `compare_methods/FFMEF/` — FFMEF git submodule (CVPRW 2023), pre-trained weights in `ckp/`, model in `model/FFMEF.py`
- `compare_methods/run_ffmef.py` — Standalone script for FFMEF inference on MEFB test set with full metric evaluation
- `compare_methods.py` — Top-level comparison script: runs Average, Max, Mertens from H5 dataset, then generates radar/bar charts comparing all methods (FILM/FFMEF/traditional) on MEFB test set
- `storage/results/` — Server output: fused images (`fused_*.jpg`), evaluation results (`eval_*.jpg`), server logs (`api_server.err.log`, `api_server.out.log`)
- `mef_history.db` — SQLite database with schema: `history(id, algo, img_url, time, en, sd, sf, ag, vif, qabf)`
- `test_api.py`, `test_eval2.py`, `test_evaluate.py`, `test_evaluate2.py` — Ad-hoc test scripts for API endpoints and evaluation logic

## Development Commands

### Python Backend

```bash
# Setup environment
conda create -n FILM python=3.8.17
conda activate FILM
pip install -r requirements.txt

# Preprocess datasets (VLFDataset -> VLFDataset_h5)
python data_process.py          # Uses train.txt/test.txt file lists (4 tasks)
python data_process_MEFB.py     # Auto-scans OVER directory (MEFB-only, more robust)

# Train model (default: 150 epochs, batch size 2, lr=1e-5, multi-GPU on 0-7)
python train.py

# Train with custom hyperparameters
python train.py --hidden_dim 256 --i2t_dim 32 --numepochs 150 --lr 1e-5 --batch_size 2 --loss_grad_weight 20 --dataset_path "VLFDataset_h5\MSRS_train.h5"
# Available CLI arguments:
#   --hidden_dim 256     — Text feature hidden dimension
#   --i2t_dim 32         — Image-to-text projection dimension
#   --numepochs 150      — Number of training epochs
#   --lr 1e-5            — Learning rate
#   --gamma 0.6          — LR scheduler decay factor (StepLR)
#   --step_size 50       — LR scheduler step interval (epochs)
#   --batch_size 2       — Batch size
#   --loss_grad_weight 20 — Gradient loss weight
#   --loss_ssim 0        — Enable SSIM loss (1=enabled, 0=disabled)
#   --dataset_path       — Path to HDF5 training dataset (default: VLFDataset_h5\MSRS_train.h5)

# Monitor training with TensorBoard
tensorboard --logdir exp/

# Run inference (hardcoded to MEF task on MEFB dataset)
python test.py

# Generate architecture diagrams (matplotlib)
python generate_arch_diagram.py      # System architecture diagram
python generate_system_arch.py       # FILM network architecture diagram

# Run FFMEF benchmark on MEFB test set
python compare_methods/run_ffmef.py  # Reports EN/SD/SF/AG/VIF/Qabf for FFMEF

# Compare all methods (FILM vs Average/Max/Mertens/FFMEF) on MEFB
python compare_methods.py  # Generates radar/bar charts from H5 dataset
```

### FastAPI Server

```bash
python api_server.py
# On Windows PowerShell, use: & "D:\anaconda\envs\FILM\python.exe" api_server.py
# Server runs on 0.0.0.0:8000 with endpoints:
#   POST /api/fuse          — AI fusion via FILM model (YCbCr: Y through net, Cb/Cr 50/50 blend)
#   POST /api/fuse/ffmef    — FFMEF deep learning fusion (CVPRW 2023, CPU mode)
#   POST /api/fuse/traditional — Traditional algorithms (avg, max, mertens via algo_type form field)
#   POST /api/evaluate      — Two-phase evaluation: fast metrics (EN/SD/SF/AG) returned immediately; VIF/Qabf computed in background task when source images provided, then DB record updated. `algo` form field defaults to "AI".
#   GET  /api/history       — Query processing history (SQLite, last 20 records)
# All POST endpoints validate: file type (jpeg/png/bmp/webp), file size (<=20MB)
# Starlette form parser limits are overridden to 50MB (MAX_PART_SIZE, MAX_FILE_SIZE) to allow large base64 image fields
# Server logs: storage/api_server.out.log, storage/api_server.err.log
```

### Vue Frontend

```bash
cd mef-frontend
npm install
npm run dev       # Vite dev server
npm run build     # Production build
npm run preview   # Preview production build
```

## Architecture

### Two-Component System

1. **Research backend**: PyTorch model for image fusion guided by text semantics. Four fusion tasks (IVF/MIF/MEF/MFF) share the same `Net` architecture, with separate pretrained checkpoints.
2. **Web application**: The `mef-frontend` (Vue 3 SPA, plain JavaScript — no TypeScript) communicates with `api_server.py` (FastAPI) over HTTP. The frontend uses a two-column layout: left panel (320px) for source image uploads + algorithm selection, right panel for fusion viewer with before/after slider and ECharts metrics visualization. The API loads the PyTorch FILM model at startup via `MEFFusionEngine`, performs inference, saves results to `storage/results/`, and logs history to `mef_history.db` (SQLite table: `history(id, algo, img_url, time, en, sd, sf, ag, vif, qabf)`).

### FFMEF Comparison Engine

The `compare_methods/FFMEF/` submodule adds a competing deep learning method (FFMEF, CVPRW 2023) for benchmarking. Key details:
- Loaded at server startup in `api_server.py` lifespan, runs on **CPU** to save VRAM (FILM uses GPU)
- Model weights: `compare_methods/FFMEF/ckp/mef.pth` (also has `mff.pth`, `vif.pth` for other tasks)
- Uses same YCbCr pipeline as FILM: Y channel through network, Cb/Cr averaged
- Available as a standalone evaluation script: `python compare_methods/run_ffmef.py` — runs inference on the full MEFB test set and reports EN/SD/SF/AG/VIF/Qabf metrics
- The submodule has its own `.git` directory and `train.py`/`test.py` — treat it as a nested project

### Model Architecture

`Net` in `net/Film.py`:
- 3 cascaded `restormer_cablock` stages (first takes 1-channel input, others take `mid_channel`)
- Each `restormer_cablock`: processes image A and B through separate Restormer TransformerBlocks → projects to text-feature space → cross-attention with text as query, image features as key/value → pools + normalizes + reshapes back to spatial → concatenates original + text-guided features through 1x1 conv + PReLU
- Concatenates features from A and B, then 3 Restormer TransformerBlocks for fusion
- Two 1x1 conv layers for dimension reduction and output, sigmoid activation for final fusion mask

Key supporting classes in `net/Film.py`:
- `CrossAttention` — wraps `nn.MultiheadAttention` with transpose handling for NLP-style `(seq_len, batch, dim)` input
- `ChannelAttention` — SE-block style channel attention with avg/max pooling + 2-layer Conv1d
- `imagefeature2textfeature` — 1x1 Conv + nearest-neighbor interpolation to 288x384 + reshape to `(batch, seq_len, hidden_dim)`
- `text_preprocess` — 1D conv to transform 768-dim BLIP2 text features to `hidden_dim`

Supporting blocks in `net/restormer.py`:
- `TransformerBlock` — core Restormer block (LayerNorm + MDTA + LayerNorm + FFN with residual connections)
- `DropPath` — stochastic depth, `AttentionBase` — multi-head attention with 1x1 + 3x3 QKV convs
- `InvertedResidualBlock` — MobileNet-v2 style, `DetailFeatureExtraction` — INN-style detail extraction
- Custom LayerNorm variants (`BiasFree_LayerNorm`, `WithBias_LayerNorm`) that work with 4D tensors `(B, C, H, W)`

### MEF Inference Pipeline (mef_engine.py)

1. Convert RGB source images to YCbCr color space
2. Send only Y (luminance) channel through the neural network
3. Min-max normalize the network output
4. Blend Cb/Cr channels with 0.5 alpha (classical weighted average)
5. Merge Y+Cb+Cr back to YCbCr, convert to RGB, save as JPEG

### Data Pipeline

```
Raw Images (PNG) --> [data_process.py] --> HDF5 (imageA, imageB, text groups)
ChatGPT Text Descriptions                  ^
BLIP2 Text Embeddings (.npy, 768-dim) ----/
                                               |
                                    [H5ImageTextDataset]
                                               |
                                    [train.py / test.py]
                                               |
                                    [MEFFusionEngine] (for API)
```

The VLF Dataset covers 8 datasets across 4 tasks:
- **IVF**: MSRS, M3FD, RoadScene (subfolders: IR / VI)
- **MIF**: Harvard (subfolders: MRI / T)
- **MEF**: SICE, MEFB (subfolders: OVER / UNDER)
- **MFF**: RealMFF, Lytro (subfolders: NEAR / FAR)

Raw images + text descriptions in `VLFDataset/Image/{task}/{dataset}/{subdir}/` and `VLFDataset/TextFeature/{task}/{dataset}/{name}.npy` → preprocessed to HDF5 in `VLFDataset_h5/{dataset}_{mode}.h5` via `data_process.py` or `data_process_MEFB.py` → loaded by `H5ImageTextDataset` in training/testing.

`data_process.py` relies on `train.txt` / `test.txt` file lists. `data_process_MEFB.py` auto-scans the OVER directory and wraps sample processing in try/except to skip failing samples — it is the more robust variant for MEFB specifically.

Training mode with `size='small'` resizes images to 384x288 (landscape) or 288x384 (portrait).

**Important**: `H5ImageTextDataset` opens the HDF5 file on every `__getitem__` and `__len__` call. This is I/O-inefficient for large datasets but avoids file handle leaks.

The VLF Dataset images exceed 4GB and are not included in the repo — they must be downloaded from the Google Drive link in the README.

### Training Configuration

- Default hyperparameters: `hidden_dim=256`, `i2t_dim=32`, `numepochs=150`, `lr=1e-5`, `batch_size=2`
- Loss: `Fusionloss` (gradient L1 + intensity L1) + optional `LpLssimLossweight` (L2 + SSIM, **disabled by default** with `loss_ssim=0`)
- Multi-GPU: `CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7` with `DataParallel`
- Training outputs: `./exp/{timestamp}_epochs_.../` with subfolders `code/`, `model/`, `pic_fusion/`, plus `log.txt` and `param.json`
- Saves full checkpoint (state dict + optimizer + scheduler) every epoch
- TensorBoard logs are written to the experiment directory. Scalars tracked: total loss, gradient loss, LpLssim loss (A/B), learning rate

## Important Notes

- PyTorch version pinned to 1.8.1+cu111 (CUDA 11.1). If your system CUDA version differs, you may need to adjust the torch/torchvision versions in `requirements.txt`. `torch.load()` calls use the legacy format without `weights_only=True`, which produces warnings on newer PyTorch.
- `train.py` sets `KMP_DUPLICATE_LIB_OK=True` to avoid OpenMP library conflicts between PyTorch and scikit-image.
- Hardcoded CUDA device: `train.py` sets `CUDA_VISIBLE_DEVICES="0,1,2,3,4,5,6,7"` and `test.py` sets `"0"`. The API server auto-detects CUDA availability.
- `test.py` is hardcoded to `task_name='MEF'` and `dataset_name='MEFB'`. Modify these variables at the top to test other tasks.
- `test.py` computes 6 metrics (EN/SD/SF/AG/VIF/Qabf) using `utils/Evaluator.py`. VIF and Qabf require source image pairs, which `test.py` reads from the same HDF5 dataset (`imageA`/`imageB` groups).
- `mef_metrics.py` implements EN/SD/SF/AG directly via numpy/OpenCV — it does **not** delegate to `utils/Evaluator.py`. It's a simpler, self-contained module used by the API.
- No formal test framework (no pytest/jest). Testing is done via `python test.py` for inference and manual metric computation via `utils/Evaluator.py`.
- The frontend and backend communicate over HTTP (CORS enabled with `allow_origins=["*"]`).
- The API validates uploaded files: type must be image/jpeg|png|bmp|webp, size <= 20MB.
- `mef_engine.py` uses absolute paths for model and dataset files. If you move the project, update the paths in `mef_engine.py`.
- Conda environment path: `D:\anaconda\envs\FILM\python.exe`. Run with `& "D:\anaconda\envs\FILM\python.exe" api_server.py` on Windows PowerShell.
- The MEF engine loads the text tensor from the first test sample only (`VLFDataset_h5/MEFB_test.h5`), assuming all MEF text prompts are identical. This works for MEFB but may break for other datasets.
- Training output structure: experiments saved in `exp/{timestamp}_epochs_{N}_lr_{lr}_.../` — the `save_path` variable in `train.py` (line 89) controls the base directory. Subfolders: `code/` (model snapshot), `model/` (epoch checkpoints), `pic_fusion/` (visual results), plus `log.txt` and `param.json`.
- No TypeScript in frontend — plain JavaScript (`.js` files), no `tsconfig.json`.
- No existing AI assistant config: no `.cursorrules`, `.cursor/rules/`, or `.github/copilot-instructions.md`.
- **Server logs**: stdout/stderr are redirected to `storage/api_server.out.log` and `storage/api_server.err.log`.
- **SQLite schema extended**: The history table now includes `vif` and `qabf` columns (beyond the original EN/SD/SF/AG). The `/api/evaluate` endpoint writes a placeholder record immediately (VIF=0, Qabf=0) with fast metrics, then the background task updates those fields in-place. The frontend polls for updated values.
- **FFMEF submodule**: `compare_methods/FFMEF/` is a git submodule — run `git submodule update --init --recursive` after cloning to fetch it. It has its own dependencies and training scripts; the main project only uses its pretrained inference model.
- **Storage directory**: `storage/results/` holds both fusion outputs (`fused_*.jpg`) and evaluation snapshots (`eval_*.jpg`). Results are served as static files at `/static/`.