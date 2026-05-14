"""
MEF 融合方法对比 - 生成图 2.6
对比: Average, Max, Mertens, FFMEF, FILM
数据集: MEFB (40 张测试图像均值)
指标: EN, SD, SF, AG, VIF, Qabf

数据来源:
- Average, Max, Mertens: 本脚本从 H5 数据集直接计算
- FFMEF: compare_methods/run_ffmef.py 实际运行 (CVPRW 2023)
- FILM: test.py 实际运行 (TCSVT 2024)
"""
import os
import sys
import warnings
warnings.filterwarnings("ignore")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import numpy as np
import cv2
from torch.utils.data import DataLoader
from utils.H5_read import H5ImageTextDataset
from utils.Evaluator import Evaluator
from tqdm import tqdm

# ============================================================
# 1. 加载数据集
# ============================================================
H5_PATH = os.path.join(BASE_DIR, "VLFDataset_h5", "MEFB_test.h5")
testloader = DataLoader(H5ImageTextDataset(H5_PATH), batch_size=1, shuffle=False, num_workers=0)

names = []
data_list = []
for imgA, imgB, text, idx in testloader:
    names.append(str(idx[0]))
    data_list.append((imgA, imgB))

metric_funcs = ["EN", "SD", "SF", "AG", "VIF", "Qabf"]
results = {}

def get_metrics(fused, imgA, imgB):
    return [
        Evaluator.EN(fused),
        Evaluator.SD(fused),
        Evaluator.SF(fused),
        Evaluator.AG(fused),
        Evaluator.VIF(fused, imgA, imgB),
        Evaluator.Qabf(fused, imgA, imgB),
    ]

# --- Average (Y通道等权平均) ---
avg_acc = {m: [] for m in metric_funcs}
for i in tqdm(range(len(names)), desc="Average"):
    imgA_y = (np.squeeze(data_list[i][0].numpy()) * 255).astype(np.float64)
    imgB_y = (np.squeeze(data_list[i][1].numpy()) * 255).astype(np.float64)
    fused_y = 0.5 * imgA_y + 0.5 * imgB_y
    vals = get_metrics(fused_y, imgA_y, imgB_y)
    for j, m in enumerate(metric_funcs):
        avg_acc[m].append(vals[j])
results["Average"] = [np.mean(avg_acc[m]) for m in metric_funcs]

# --- Max (Y通道像素最大值) ---
max_acc = {m: [] for m in metric_funcs}
for i in tqdm(range(len(names)), desc="Max"):
    imgA_y = (np.squeeze(data_list[i][0].numpy()) * 255).astype(np.float64)
    imgB_y = (np.squeeze(data_list[i][1].numpy()) * 255).astype(np.float64)
    fused_y = np.maximum(imgA_y, imgB_y)
    vals = get_metrics(fused_y, imgA_y, imgB_y)
    for j, m in enumerate(metric_funcs):
        max_acc[m].append(vals[j])
results["Max"] = [np.mean(max_acc[m]) for m in metric_funcs]

# --- Mertens (拉普拉斯金字塔融合) ---
mertens_acc = {m: [] for m in metric_funcs}
merge_mertens = cv2.createMergeMertens()
for i in tqdm(range(len(names)), desc="Mertens"):
    imgA_y = (np.squeeze(data_list[i][0].numpy()) * 255).astype(np.uint8)
    imgB_y = (np.squeeze(data_list[i][1].numpy()) * 255).astype(np.uint8)
    imgA_rgb = np.stack([imgA_y] * 3, axis=2)
    imgB_rgb = np.stack([imgB_y] * 3, axis=2)
    fused_rgb_float = merge_mertens.process([imgA_rgb, imgB_rgb])
    fused_rgb = np.clip(fused_rgb_float * 255, 0, 255).astype(np.uint8)
    fused_y = cv2.cvtColor(fused_rgb, cv2.COLOR_RGB2YCrCb)[:, :, 0].astype(np.float64)
    imgA_y_f = imgA_y.astype(np.float64)
    imgB_y_f = imgB_y.astype(np.float64)
    vals = get_metrics(fused_y, imgA_y_f, imgB_y_f)
    for j, m in enumerate(metric_funcs):
        mertens_acc[m].append(vals[j])
results["Mertens"] = [np.mean(mertens_acc[m]) for m in metric_funcs]

# --- FFMEF (CVPRW 2023, 实际运行结果) ---
results["FFMEF"] = [6.89, 56.85, 12.93, 3.72, 1.46, 0.62]

# --- FILM (TCSVT 2024, 实际运行结果) ---
results["FILM"] = [7.32, 68.97, 20.96, 6.11, 1.52, 0.77]

# ============================================================
# 2. 汇总输出
# ============================================================
print("=" * 70)
print("MEFB 数据集融合方法对比 (40 张测试图像均值)")
print("=" * 70)
header = f"{'Method':<12}" + "".join(f"{m:>10}" for m in metric_funcs)
print(header)
print("-" * 70)
for name in ["Average", "Max", "Mertens", "FFMEF", "FILM"]:
    vals = "".join(f"{v:>10.2f}" for v in results[name])
    print(f"{name:<12}{vals}")
print("=" * 70)

# 保存 CSV
csv_path = os.path.join(BASE_DIR, "test_output", "metrics_comparison.csv")
os.makedirs(os.path.join(BASE_DIR, "test_output"), exist_ok=True)
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("Method," + ",".join(metric_funcs) + "\n")
    for name in ["Average", "Max", "Mertens", "FFMEF", "FILM"]:
        f.write(f"{name}," + ",".join(f"{v:.4f}" for v in results[name]) + "\n")
print(f"CSV 已保存: {csv_path}")

# ============================================================
# 3. 绘图
# ============================================================
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 归一化到 [0, 1] 用于雷达图
metric_ranges = {
    "EN": (0, 12),
    "SD": (0, 80),
    "SF": (0, 25),
    "AG": (0, 10),
    "VIF": (0, 5),
    "Qabf": (0, 1.0),
}

norm_results = {}
for name in ["Average", "Max", "Mertens", "FFMEF", "FILM"]:
    norm_results[name] = []
    for j, m in enumerate(metric_funcs):
        lo, hi = metric_ranges[m]
        norm_val = (results[name][j] - lo) / (hi - lo)
        norm_results[name].append(max(0, min(1, norm_val)))

fig = plt.figure(figsize=(16, 6))

# --- 雷达图 ---
ax1 = fig.add_subplot(121, projection='polar')
angles = np.linspace(0, 2 * np.pi, len(metric_funcs), endpoint=False).tolist()
angles += angles[:1]

colors = {"Average": "#95a5a6", "Max": "#e67e22", "Mertens": "#3498db", "FFMEF": "#9b59b6", "FILM": "#2ecc71"}

for method_name, color in colors.items():
    vals = norm_results[method_name] + [norm_results[method_name][0]]
    ax1.fill(angles, vals, alpha=0.15, color=color, label=method_name)
    ax1.plot(angles, vals, linewidth=2, color=color)

ax1.set_xticks(angles[:-1])
ax1.set_xticklabels(metric_funcs, fontsize=10)
ax1.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
ax1.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=8)
ax1.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)
ax1.set_title("Radar Chart of Evaluation Metrics (Normalized)", fontsize=12, pad=20)
ax1.grid(True, alpha=0.3)

# --- 分组柱状图 ---
ax2 = fig.add_subplot(122)
x = np.arange(len(metric_funcs))
width = 0.14
method_names = ["Average", "Max", "Mertens", "FFMEF", "FILM"]

for idx, method_name in enumerate(method_names):
    offset = (idx - 2) * width
    vals = results[method_name]
    bars = ax2.bar(x + offset, vals, width, label=method_name, color=colors[method_name])
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax2.text(bar.get_x() + bar.get_width()/2., h,
                     f'{h:.1f}', ha='center', va='bottom', fontsize=5)

ax2.set_xlabel("Metrics", fontsize=11)
ax2.set_ylabel("Metric Value", fontsize=11)
ax2.set_xticks(x)
ax2.set_xticklabels(metric_funcs, fontsize=10)
ax2.legend(fontsize=10)
ax2.set_title("Grouped Bar Chart of Evaluation Metrics (Raw Values)", fontsize=12)
ax2.grid(True, axis='y', alpha=0.3)

plt.tight_layout()
save_path = os.path.join(BASE_DIR, "test_output", "fig2_6_metrics_comparison.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"图表已保存: {save_path}")
plt.close()

# 复制到论文 img 目录
import shutil
dst_path = os.path.join(BASE_DIR, "毕业论文", "img", "fig2_6_metrics_comparison.png")
shutil.copy2(save_path, dst_path)
print(f"已复制到: {dst_path}")

print("\n完成！")
