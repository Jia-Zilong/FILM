# Plan 1: 后端代码修复

**Context:** 后端存在三个问题：(1) test.py 中 VIFF/Qabf 指标硬编码为假值 (2) 评估指标在 3 个文件重复实现，api_server.py 有重复 import (3) API 端点缺少输入验证。

**Goal:** 修复硬编码指标、消除代码重复、添加输入验证。

**Scope:** 仅后端 Python 代码，不影响前端。

---

### Task 1: 修复 api_server.py 重复 import

**File:** `api_server.py`

重复项：
- Line 4: `from fastapi import FastAPI`（line 1 已导入）
- Line 15: `from mef_metrics import ImageMetrics`（line 8 已导入）
- Line 7/114/160: `import traceback`（只需保留 line 7）

删除 line 4、7、15 的重复导入。

### Task 2: 统一评估指标到 utils/Evaluator.py

**Files:**
- Modify: `mef_metrics.py` — 改为导入 `utils/Evaluator.py` 并委托调用
- Modify: `test.py` — 内联 `Metrics` 类改为导入 `utils/Evaluator.py`，修复 VIFF/Qabf 硬编码

`utils/Evaluator.py` 已有完整的 EN/SD/SF/AG/VIFF/Qabf/SSIM 等实现。`mef_metrics.py` 和 `test.py` 中的重复实现应删除，改为委托。

### Task 3: 添加 API 输入验证

**File:** `api_server.py`

在三个 POST 端点添加：
- 文件类型验证（仅允许 image/jpeg, image/png, image/bmp, image/webp）
- 文件大小限制（最大 20MB）
- 图像内容验证（确保能成功解码为图像）
- `/api/fuse/traditional` 的 algo_type 无效值应返回 400 而非 500
