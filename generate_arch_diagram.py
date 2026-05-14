import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(1, 1, figsize=(22, 28))
ax.set_xlim(0, 220)
ax.set_ylim(0, 280)
ax.set_aspect('equal')
ax.axis('off')

# Color scheme
COLOR_INPUT = '#E8F5E9'
COLOR_INPUT_BORDER = '#4CAF50'
COLOR_TEXT = '#E3F2FD'
COLOR_TEXT_BORDER = '#2196F3'
COLOR_PROCESS = '#FFF3E0'
COLOR_PROCESS_BORDER = '#FF9800'
COLOR_RESTORMER = '#F3E5F5'
COLOR_RESTORMER_BORDER = '#9C27B0'
COLOR_CROSS_ATTN = '#E1F5FE'
COLOR_CROSS_ATTN_BORDER = '#03A9F4'
COLOR_FUSION = '#FBE9E7'
COLOR_FUSION_BORDER = '#FF5722'
COLOR_OUTPUT = '#FCE4EC'
COLOR_OUTPUT_BORDER = '#E91E63'
COLOR_ARROW = '#555555'
COLOR_BG_BLOCK = '#FAFAFA'

def draw_box(x, y, w, h, text, fontsize=9, facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER,
             bold=False, align='center', alpha=1.0, subtext=None, subfontsize=7):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", linewidth=1.5,
                         edgecolor=edgecolor, facecolor=facecolor, alpha=alpha)
    ax.add_patch(box)
    if bold:
        ax.text(x+w/2, y+h/2 if subtext is None else y+h/2+0.15, text, fontsize=fontsize,
                fontweight='bold', ha=align, va='center', family='sans-serif')
    else:
        ax.text(x+w/2, y+h/2 if subtext is None else y+h/2+0.15, text, fontsize=fontsize,
                ha=align, va='center', family='sans-serif')
    if subtext:
        ax.text(x+w/2, y+h/2-0.15, subtext, fontsize=subfontsize,
                ha=align, va='center', style='italic', color='#666', family='sans-serif')
    return box

def draw_arrow(x1, y1, x2, y2, color=COLOR_ARROW, lw=1.5, style='->'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw))

def draw_brace(x, y_top, y_bottom, text, xpos='left', fontsize=8):
    mid_y = (y_top + y_bottom) / 2
    brace_w = 3
    if xpos == 'left':
        ax.plot([x+brace_w, x, x, x+brace_w], [y_top, y_top, y_bottom, y_bottom], color='#888', lw=1.5)
        ax.text(x-1, mid_y, text, fontsize=fontsize, ha='right', va='center', fontweight='bold', color='#555')
    else:
        ax.plot([x-brace_w, x, x, x-brace_w], [y_top, y_top, y_bottom, y_bottom], color='#888', lw=1.5)
        ax.text(x+1, mid_y, text, fontsize=fontsize, ha='left', va='center', fontweight='bold', color='#555')

# ============= Title =============
ax.text(110, 275, 'FILM (Image Fusion via Vision-Language Model) Architecture',
        fontsize=16, fontweight='bold', ha='center', va='center', color='#333')

# ============= INPUT SECTION (top) =============
# Image A input
draw_box(10, 255, 30, 12, 'Image A', fontsize=10, bold=True,
         facecolor=COLOR_INPUT, edgecolor=COLOR_INPUT_BORDER, subtext='[H×W×1] Y channel')
# Image B input
draw_box(55, 255, 30, 12, 'Image B', fontsize=10, bold=True,
         facecolor=COLOR_INPUT, edgecolor=COLOR_INPUT_BORDER, subtext='[H×W×1] Y channel')
# BLIP2 + Text
draw_box(100, 255, 55, 12, 'BLIP2 (Frozen LLM)', fontsize=10, bold=True,
         facecolor=COLOR_TEXT, edgecolor=COLOR_TEXT_BORDER, subtext='768-dim text feature [N×768]')

# Arrows down from inputs
draw_arrow(25, 255, 25, 238)
draw_arrow(70, 255, 70, 238)
draw_arrow(127.5, 255, 127.5, 238)

# ============= Text Preprocessing =============
draw_box(105, 226, 45, 12, 'Text Preprocess', fontsize=10, bold=True,
         facecolor=COLOR_TEXT, edgecolor=COLOR_TEXT_BORDER, subtext='Conv1d: 768 → 256')

draw_arrow(127.5, 238, 127.5, 238)

# ============= Cascaded Stage Label =============
draw_brace(8, 226, 115, '3× Cascaded restormer_cablock', xpos='left', fontsize=10)

# ============= STAGE 1 =============
stage_y = 214
draw_box(3, stage_y, 47, 11, 'Stage 1: Image A/B → Restormer', fontsize=8, bold=True,
         facecolor='#F5F5F5', edgecolor='#999', subtext='Conv3×3+PReLU → Restormer Block')

# Split A and B paths
draw_arrow(25, 238, 15, 225)
draw_arrow(70, 238, 80, 225)

# Image A path in Stage 1
draw_box(3, 198, 22, 10, 'Image A Path', fontsize=8, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER, subtext='Restormer: [H×W×32]')
draw_box(3, 184, 22, 10, 'Image→Text Proj', fontsize=8, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='Conv1×1 + Interp 288×384')
draw_box(3, 170, 22, 10, 'Cross Attention', fontsize=8, bold=True,
         facecolor=COLOR_CROSS_ATTN, edgecolor=COLOR_CROSS_ATTN_BORDER, subtext='Q=Text, K/V=Image [N×256]')

draw_arrow(14, 225, 14, 208)
draw_arrow(14, 198, 14, 194)
draw_arrow(14, 184, 14, 180)

# Image B path in Stage 1
draw_box(28, 198, 22, 10, 'Image B Path', fontsize=8, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER, subtext='Restormer: [H×W×32]')
draw_box(28, 184, 22, 10, 'Image→Text Proj', fontsize=8, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='Conv1×1 + Interp 288×384')
draw_box(28, 170, 22, 10, 'Cross Attention', fontsize=8, bold=True,
         facecolor=COLOR_CROSS_ATTN, edgecolor=COLOR_CROSS_ATTN_BORDER, subtext='Q=Text, K/V=Image [N×256]')

draw_arrow(39, 225, 39, 208)
draw_arrow(39, 198, 39, 194)
draw_arrow(39, 184, 39, 180)

# Text query arrow into Cross Attention
draw_arrow(127.5, 226, 50, 175, style='->', color=COLOR_TEXT_BORDER, lw=1.2)

# Attention Pool + Reshape
draw_box(3, 155, 22, 10, 'Attn Pool + L1 Norm', fontsize=7, bold=False,
         facecolor=COLOR_CROSS_ATTN, edgecolor=COLOR_CROSS_ATTN_BORDER, subtext='AdaptiveAvgPool1d')
draw_box(3, 141, 22, 10, 'Reshape + Concat', fontsize=7, bold=False,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='Orig+Guided → Conv1×1')

draw_arrow(14, 170, 14, 165)
draw_arrow(14, 155, 14, 151)

draw_box(28, 155, 22, 10, 'Attn Pool + L1 Norm', fontsize=7, bold=False,
         facecolor=COLOR_CROSS_ATTN, edgecolor=COLOR_CROSS_ATTN_BORDER, subtext='AdaptiveAvgPool1d')
draw_box(28, 141, 22, 10, 'Reshape + Concat', fontsize=7, bold=False,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='Orig+Guided → Conv1×1')

draw_arrow(39, 170, 39, 165)
draw_arrow(39, 155, 39, 151)

# Outputs from Stage 1: Feature A, Feature B
draw_box(15, 126, 12, 8, 'F_A1', fontsize=8, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='[HxWx32]')
draw_box(28, 126, 12, 8, 'F_B1', fontsize=8, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='[HxWx32]')

draw_arrow(14, 141, 21, 134)
draw_arrow(39, 141, 34, 134)

# ============= STAGE 2 =============
stage2_y = 114
draw_box(3, stage2_y, 47, 11, 'Stage 2: Feature A/B → Restormer', fontsize=8, bold=True,
         facecolor='#F5F5F5', edgecolor='#999', subtext='Input: [H×W×32] → Same structure as Stage 1')

draw_arrow(21, 126, 21, 125)
draw_arrow(34, 126, 34, 125)

draw_box(3, 100, 22, 10, 'Image A Path', fontsize=8, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER, subtext='Restormer: [H×W×32]')
draw_box(3, 86, 22, 10, 'Cross Attention', fontsize=8, bold=True,
         facecolor=COLOR_CROSS_ATTN, edgecolor=COLOR_CROSS_ATTN_BORDER, subtext='Q=Text, K/V=Feature')
draw_box(3, 72, 22, 10, 'Attn Pool + Reshape', fontsize=7, bold=False,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='Conv1×1 → [H×W×32]')

draw_arrow(14, 125, 14, 110)
draw_arrow(14, 100, 14, 96)
draw_arrow(14, 86, 14, 82)

draw_box(28, 100, 22, 10, 'Image B Path', fontsize=8, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER, subtext='Restormer: [H×W×32]')
draw_box(28, 86, 22, 10, 'Cross Attention', fontsize=8, bold=True,
         facecolor=COLOR_CROSS_ATTN, edgecolor=COLOR_CROSS_ATTN_BORDER, subtext='Q=Text, K/V=Feature')
draw_box(28, 72, 22, 10, 'Attn Pool + Reshape', fontsize=7, bold=False,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='Conv1×1 → [H×W×32]')

draw_arrow(39, 125, 39, 110)
draw_arrow(39, 100, 39, 96)
draw_arrow(39, 86, 39, 82)

# Text query into Stage 2 cross-attn
draw_arrow(127.5, 226, 50, 90, style='->', color=COLOR_TEXT_BORDER, lw=1.2)

draw_box(15, 58, 12, 8, 'F_A2', fontsize=8, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='[HxWx32]')
draw_box(28, 58, 12, 8, 'F_B2', fontsize=8, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='[HxWx32]')

draw_arrow(14, 72, 21, 66)
draw_arrow(39, 72, 34, 66)

# ============= STAGE 3 =============
stage3_y = 46
draw_box(3, stage3_y, 47, 11, 'Stage 3: Feature A/B → Restormer', fontsize=8, bold=True,
         facecolor='#F5F5F5', edgecolor='#999', subtext='Input: [H×W×32] → Same structure as Stage 1')

draw_arrow(21, 58, 21, 57)
draw_arrow(34, 58, 34, 57)

draw_box(3, 32, 22, 10, 'Image A Path', fontsize=8, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER, subtext='Restormer: [H×W×32]')
draw_box(3, 18, 22, 10, 'Cross Attention', fontsize=8, bold=True,
         facecolor=COLOR_CROSS_ATTN, edgecolor=COLOR_CROSS_ATTN_BORDER, subtext='Q=Text, K/V=Feature')
draw_box(3, 4, 22, 10, 'Attn Pool + Reshape', fontsize=7, bold=False,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='Conv1×1 → [H×W×32]')

draw_arrow(14, 57, 14, 42)
draw_arrow(14, 32, 14, 28)
draw_arrow(14, 18, 14, 14)

draw_box(28, 32, 22, 10, 'Image B Path', fontsize=8, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER, subtext='Restormer: [H×W×32]')
draw_box(28, 18, 22, 10, 'Cross Attention', fontsize=8, bold=True,
         facecolor=COLOR_CROSS_ATTN, edgecolor=COLOR_CROSS_ATTN_BORDER, subtext='Q=Text, K/V=Feature')
draw_box(28, 4, 22, 10, 'Attn Pool + Reshape', fontsize=7, bold=False,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='Conv1×1 → [H×W×32]')

draw_arrow(39, 57, 39, 42)
draw_arrow(39, 32, 39, 28)
draw_arrow(39, 18, 39, 14)

# Text query into Stage 3 cross-attn
draw_arrow(127.5, 226, 50, 22, style='->', color=COLOR_TEXT_BORDER, lw=1.2)

draw_box(15, -4, 12, 8, 'F_A3', fontsize=8, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='[HxWx32]')
draw_box(28, -4, 12, 8, 'F_B3', fontsize=8, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='[HxWx32]')

draw_arrow(14, 4, 21, 4)
draw_arrow(39, 4, 34, 4)

# ============= FUSION & REFINEMENT (right side) =============
# Concatenate
draw_box(55, -2, 25, 10, 'Concat', fontsize=9, bold=True,
         facecolor=COLOR_FUSION, edgecolor=COLOR_FUSION_BORDER, subtext='[H×W×64]')

# Arrows from F_A³, F_B³ to Concat
draw_arrow(27, 0, 55, 3)
draw_arrow(40, 0, 55, 3)

# Restormer 1
draw_box(55, -16, 25, 10, 'Restormer Block', fontsize=9, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER, subtext='MDTA + GDFN, in=64')
draw_arrow(67.5, -2, 67.5, -6)

# Conv 1×1 (channel reduction)
draw_box(55, -30, 25, 10, 'Conv 1×1', fontsize=9, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER, subtext='64 → 32')
draw_arrow(67.5, -16, 67.5, -20)

# Restormer 2
draw_box(55, -44, 25, 10, 'Restormer Block', fontsize=9, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER, subtext='MDTA + GDFN, in=32')
draw_arrow(67.5, -30, 67.5, -34)

# Restormer 3
draw_box(55, -58, 25, 10, 'Restormer Block', fontsize=9, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER, subtext='MDTA + GDFN, in=32')
draw_arrow(67.5, -44, 67.5, -48)

# Conv 1×1 (output)
draw_box(55, -72, 25, 10, 'Conv 1×1 + Sigmoid', fontsize=9, bold=True,
         facecolor=COLOR_OUTPUT, edgecolor=COLOR_OUTPUT_BORDER, subtext='32 → 1, [0,1]')
draw_arrow(67.5, -58, 67.5, -62)

# Fusion Mask
draw_box(55, -86, 25, 10, 'Fusion Mask', fontsize=10, bold=True,
         facecolor=COLOR_FUSION, edgecolor=COLOR_FUSION_BORDER, subtext='[H×W×1]')
draw_arrow(67.5, -72, 67.5, -76)

# ============= YCbCr COMPOSITION (bottom right) =============
draw_box(55, -102, 40, 10, 'YCbCr Composition', fontsize=10, bold=True,
         facecolor=COLOR_INPUT, edgecolor=COLOR_INPUT_BORDER,
         subtext='Y=Mask·A+(1-Mask)·B, Cb/Cr=0.5avg')
draw_arrow(67.5, -86, 67.5, -92)

# Final Output
draw_box(55, -116, 40, 12, 'Fused RGB Image', fontsize=11, bold=True,
         facecolor=COLOR_INPUT, edgecolor=COLOR_INPUT_BORDER, subtext='Final Output')
draw_arrow(75, -102, 75, -104)

# ============= LEGEND (bottom left) =============
legend_y = -110
legend_x = 95
legend_w = 120
legend_h = 30

draw_box(legend_x, legend_y, legend_w, legend_h, '', fontsize=8,
         facecolor='#FAFAFA', edgecolor='#CCC')

legend_items = [
    ('Input / Output', COLOR_INPUT, COLOR_INPUT_BORDER),
    ('Text Feature', COLOR_TEXT, COLOR_TEXT_BORDER),
    ('Restormer Block', COLOR_RESTORMER, COLOR_RESTORMER_BORDER),
    ('Projection / Conv', COLOR_PROCESS, COLOR_PROCESS_BORDER),
    ('Cross Attention', COLOR_CROSS_ATTN, COLOR_CROSS_ATTN_BORDER),
    ('Fusion Operation', COLOR_FUSION, COLOR_FUSION_BORDER),
    ('Final Output', COLOR_OUTPUT, COLOR_OUTPUT_BORDER),
]

for i, (label, fc, ec) in enumerate(legend_items):
    ly = legend_y + legend_h - 3.5 - i * 3.5
    lx = legend_x + 5
    box = FancyBboxPatch((lx, ly), 5, 2.5, boxstyle="round,pad=0.01", linewidth=1,
                         edgecolor=ec, facecolor=fc)
    ax.add_patch(box)
    ax.text(lx + 7, ly + 1.25, label, fontsize=7.5, ha='left', va='center', family='sans-serif')

# ============= CROSS-ATTENTION DETAIL CALLOUT (right middle) =============
callout_x = 110
callout_y = 140
callout_w = 100
callout_h = 65

draw_box(callout_x, callout_y, callout_w, callout_h, 'Cross-Attention Detail', fontsize=9, bold=True,
         facecolor='#FAFAFA', edgecolor='#BBB')

# Q, K, V labels inside callout
draw_box(callout_x + 5, callout_y + callout_h - 20, 25, 8, 'Q: Text [N×256]', fontsize=7.5, bold=True,
         facecolor=COLOR_TEXT, edgecolor=COLOR_TEXT_BORDER)
draw_box(callout_x + 5, callout_y + callout_h - 34, 25, 8, 'K: Image [N×256]', fontsize=7.5, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER)
draw_box(callout_x + 5, callout_y + callout_h - 48, 25, 8, 'V: Image [N×256]', fontsize=7.5, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER)

# Attention computation
draw_box(callout_x + 35, callout_y + callout_h - 34, 58, 22,
         'softmax(QK^T / √d_k) · V', fontsize=8, bold=True,
         facecolor=COLOR_CROSS_ATTN, edgecolor=COLOR_CROSS_ATTN_BORDER,
         subtext='d_k = 256/8 = 32, 8 attention heads')

# Arrows Q,K,V to attention
draw_arrow(callout_x + 30, callout_y + callout_h - 16, callout_x + 35, callout_y + callout_h - 23)
draw_arrow(callout_x + 30, callout_y + callout_h - 30, callout_x + 35, callout_y + callout_h - 23)
draw_arrow(callout_x + 30, callout_y + callout_h - 44, callout_x + 35, callout_y + callout_h - 23)

# Output
draw_box(callout_x + 35, callout_y + callout_h - 58, 58, 8, 'Output: Text-guided feature [N×256]', fontsize=7.5, bold=True,
         facecolor=COLOR_PROCESS, edgecolor=COLOR_PROCESS_BORDER)
draw_arrow(callout_x + 64, callout_y + callout_h - 12, callout_x + 64, callout_y + callout_h - 50)

# ============= RESTORMER BLOCK DETAIL =============
rest_detail_x = 110
rest_detail_y = 70
rest_detail_w = 100
rest_detail_h = 50

draw_box(rest_detail_x, rest_detail_y, rest_detail_w, rest_detail_h, 'Restormer Block Detail', fontsize=9, bold=True,
         facecolor='#FAFAFA', edgecolor='#BBB')

# MDTA
draw_box(rest_detail_x + 5, rest_detail_y + rest_detail_h - 16, 40, 8, 'MDTA', fontsize=7.5, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER,
         subtext='Multi-Dconv Head Transposed Attn')
# GDFN
draw_box(rest_detail_x + 55, rest_detail_y + rest_detail_h - 16, 40, 8, 'GDFN', fontsize=7.5, bold=True,
         facecolor=COLOR_RESTORMER, edgecolor=COLOR_RESTORMER_BORDER,
         subtext='Gated-Dconv Feed-Forward Net')

# LN labels
draw_box(rest_detail_x + 5, rest_detail_y + rest_detail_h - 28, 18, 6, 'LN', fontsize=6.5,
         facecolor='#F5F5F5', edgecolor='#999')
draw_box(rest_detail_x + 55, rest_detail_y + rest_detail_h - 28, 18, 6, 'LN', fontsize=6.5,
         facecolor='#F5F5F5', edgecolor='#999')

# Residual connections
draw_box(rest_detail_x + 25, rest_detail_y + rest_detail_h - 40, 50, 6,
         'Each module: X\' = Module(LN(X)) + X  (residual connection)', fontsize=6.5,
         facecolor='#FFF', edgecolor='#CCC')

# Flow arrows
draw_arrow(rest_detail_x + 14, rest_detail_y + rest_detail_h - 22, rest_detail_x + 14, rest_detail_y + rest_detail_h - 16)
draw_arrow(rest_detail_x + 25, rest_detail_y + rest_detail_h - 12, rest_detail_x + 55, rest_detail_y + rest_detail_h - 12)
draw_arrow(rest_detail_x + 64, rest_detail_y + rest_detail_h - 22, rest_detail_x + 64, rest_detail_y + rest_detail_h - 16)

# ============= Key Hyperparameters box =============
hp_x = 110
hp_y = 10
hp_w = 100
hp_h = 45

draw_box(hp_x, hp_y, hp_w, hp_h, 'Key Hyperparameters', fontsize=9, bold=True,
         facecolor='#FFFDE7', edgecolor='#F9A825')

params = [
    'hidden_dim = 256',
    'image2text_dim = 32',
    'restormer_dim = 32, heads = 8',
    'ffn_expansion_factor = 4',
    'num_heads (decoder) = 8',
    'cascade_stages = 3',
    'restormer_blocks = 3',
    'Gradient loss weight λ₁ = 20',
    'Intensity loss weight λ₂ = 1',
]

for i, param in enumerate(params):
    ax.text(hp_x + 5, hp_y + hp_h - 4 - i*4.2, param, fontsize=7,
            ha='left', va='top', family='monospace', color='#333')

plt.tight_layout()
plt.savefig('D:/Desktop/IF-FILM-main/img/fig3_1_film_arch.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print('Architecture diagram saved to img/fig3_1_film_arch.png')
