import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patches as patches

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(1, 1, figsize=(18, 12))
ax.set_xlim(0, 180)
ax.set_ylim(0, 120)
ax.set_aspect('equal')
ax.axis('off')

# Colors
C_BROWSER = '#E8F5E9'
C_BROWSER_BORDER = '#4CAF50'
C_VUE = '#42B883'
C_API = '#FFF3E0'
C_API_BORDER = '#FF9800'
C_ENGINE = '#F3E5F5'
C_ENGINE_BORDER = '#9C27B0'
C_HTTP = '#E3F2FD'
C_HTTP_BORDER = '#2196F3'
C_DB = '#FCE4EC'
C_DB_BORDER = '#E91E63'
C_STATIC = '#F5F5F5'
C_STATIC_BORDER = '#9E9E9E'

def draw_box(x, y, w, h, text, fontsize=9, facecolor=C_BROWSER, edgecolor=C_BROWSER_BORDER,
             bold=False, subtext=None, alpha=1.0):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", linewidth=1.8,
                         edgecolor=edgecolor, facecolor=facecolor, alpha=alpha)
    ax.add_patch(box)
    tx, ty = x + w/2, y + h/2
    if subtext:
        ty += 0.3
    if bold:
        ax.text(tx, ty, text, fontsize=fontsize, fontweight='bold',
                ha='center', va='center', family='sans-serif')
    else:
        ax.text(tx, ty, text, fontsize=fontsize,
                ha='center', va='center', family='sans-serif')
    if subtext:
        ax.text(tx, y + h/2 - 0.3, subtext, fontsize=fontsize-1.5,
                ha='center', va='center', style='italic', color='#666', family='sans-serif')
    return box

def draw_arrow(x1, y1, x2, y2, color='#555', lw=1.5, style='->'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw))

def draw_dashed_arrow(x1, y1, x2, y2, color='#888', lw=1.2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw, linestyle='--'))

def draw_brace(x, y_top, y_bottom, text, side='left', fontsize=9):
    mid_y = (y_top + y_bottom) / 2
    brace_w = 3
    if side == 'left':
        ax.plot([x+brace_w, x, x, x+brace_w], [y_top, y_top, y_bottom, y_bottom], color='#666', lw=1.8)
        ax.text(x-2, mid_y, text, fontsize=fontsize, ha='right', va='center', fontweight='bold', color='#333')
    else:
        ax.plot([x-brace_w, x, x, x-brace_w], [y_top, y_top, y_bottom, y_bottom], color='#666', lw=1.8)
        ax.text(x+2, mid_y, text, fontsize=fontsize, ha='left', va='center', fontweight='bold', color='#333')

def draw_container(x, y, w, h, label, fontsize=10, color='#FAFAFA', edgecolor='#CCC', label_offset=0):
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01", linewidth=1.5,
                          edgecolor=edgecolor, facecolor=color, linestyle='--', alpha=0.5)
    ax.add_patch(rect)
    ax.text(x + 3, y + h - 2, label, fontsize=fontsize, ha='left', va='top',
            fontweight='bold', color='#444', family='sans-serif')

# Title
ax.text(90, 116, 'System Architecture', fontsize=14, fontweight='bold', ha='center', color='#333')

# ===== FRONTEND container =====
draw_container(5, 55, 55, 52, 'Frontend (Browser)', fontsize=11)

# Browser
draw_box(12, 95, 40, 8, 'Web Browser', fontsize=10, bold=True,
         facecolor=C_BROWSER, edgecolor=C_BROWSER_BORDER, subtext='Chrome / Firefox / Edge / Safari')

# Vue SPA
draw_box(15, 78, 34, 8, 'Vue 3 SPA', fontsize=10, bold=True,
         facecolor=C_VUE, edgecolor=C_VUE, subtext='Single Page Application')

# Vue sub-components
comp_y = 62
draw_box(8, comp_y, 15, 6, 'DraggableUpload', fontsize=7, facecolor='#E8F5E9', edgecolor='#66BB6A')
draw_box(25, comp_y, 15, 6, 'AlgorithmSelector', fontsize=7, facecolor='#E8F5E9', edgecolor='#66BB6A')
comp_y2 = 55
draw_box(8, comp_y2, 15, 6, 'FusionViewer', fontsize=7, facecolor='#E8F5E9', edgecolor='#66BB6A')
draw_box(25, comp_y2, 15, 6, 'MetricsDashboard', fontsize=7, facecolor='#E8F5E9', edgecolor='#66BB6A')

draw_arrow(32, 95, 32, 86)
draw_arrow(32, 78, 32, 72)
draw_arrow(32, 72, 15, 68)
draw_arrow(32, 72, 32, 68)
draw_arrow(32, 72, 47, 68)

# ===== HTTP layer =====
http_y = 45
draw_box(10, http_y, 160, 8, 'HTTP / RESTful API (JSON + Multipart)', fontsize=9, bold=True,
         facecolor=C_HTTP, edgecolor=C_HTTP_BORDER)

# Arrows from frontend to HTTP
draw_arrow(32, 62, 32, 53)
draw_dashed_arrow(32, 53, 32, 45)

# ===== BACKEND container =====
draw_container(75, 5, 100, 42, 'Backend (Server)', fontsize=11)

# FastAPI
draw_box(80, 33, 35, 8, 'FastAPI Server', fontsize=10, bold=True,
         facecolor=C_API, edgecolor=C_API_BORDER, subtext='Uvicorn 0.0.0.0:8000')

# Endpoints
ep_y = 18
draw_box(77, ep_y, 14, 5, '/api/fuse', fontsize=6.5, facecolor='#FFF3E0', edgecolor='#FFB74D')
draw_box(93, ep_y, 22, 5, '/api/fuse/traditional', fontsize=6.5, facecolor='#FFF3E0', edgecolor='#FFB74D')
draw_box(117, ep_y, 14, 5, '/api/evaluate', fontsize=6.5, facecolor='#FFF3E0', edgecolor='#FFB74D')
draw_box(133, ep_y, 14, 5, '/api/history', fontsize=6.5, facecolor='#FFF3E0', edgecolor='#FFB74D')

draw_arrow(97.5, 33, 97.5, 23)
draw_arrow(97.5, 23, 84, 23)
draw_arrow(97.5, 23, 104, 23)
draw_arrow(97.5, 23, 124, 23)
draw_arrow(97.5, 23, 140, 23)

# Arrows from HTTP to backend
draw_arrow(32, 45, 32, 37)
draw_arrow(32, 37, 97.5, 41)

# ===== Engine layer =====
engine_y = 5
draw_box(142, 5, 30, 8, 'MEFFusionEngine', fontsize=9, bold=True,
         facecolor=C_ENGINE, edgecolor=C_ENGINE_BORDER, subtext='PyTorch FILM Model')

# Static files
draw_box(142, 15, 30, 6, 'Static File Server', fontsize=8, bold=False,
         facecolor=C_STATIC, edgecolor=C_STATIC_BORDER, subtext='storage/results/')

# SQLite DB
draw_box(142, 23, 30, 6, 'SQLite Database', fontsize=8, bold=False,
         facecolor=C_DB, edgecolor=C_DB_BORDER, subtext='mef_history.db')

# Arrows from engine to static/db
draw_arrow(157, 13, 157, 21)
draw_arrow(157, 21, 157, 23)
draw_arrow(157, 29, 157, 31)

# Arrow from FastAPI to Engine
draw_arrow(115, 37, 142, 37)

# Arrows from endpoints to engine
draw_arrow(84, 23, 84, 18)
draw_arrow(104, 23, 104, 18)
draw_arrow(124, 23, 124, 18)
draw_arrow(140, 23, 140, 18)

# ===== Legend =====
legend_x = 8
legend_y = 8
legend_w = 60
legend_h = 14
draw_box(legend_x, legend_y, legend_w, legend_h, '', fontsize=8,
         facecolor='#FFF', edgecolor='#DDD')

legend_items = [
    ('Frontend', C_BROWSER, C_BROWSER_BORDER),
    ('Vue Component', C_VUE, C_VUE),
    ('HTTP API', C_HTTP, C_HTTP_BORDER),
    ('Backend API', C_API, C_API_BORDER),
    ('Engine/Model', C_ENGINE, C_ENGINE_BORDER),
    ('Database', C_DB, C_DB_BORDER),
    ('Static Files', C_STATIC, C_STATIC_BORDER),
]

for i, (label, fc, ec) in enumerate(legend_items):
    ly = legend_y + legend_h - 2.5 - i * 1.8
    lx = legend_x + 2
    box = FancyBboxPatch((lx, ly), 4, 1.4, boxstyle="round,pad=0.005", linewidth=1,
                         edgecolor=ec, facecolor=fc)
    ax.add_patch(box)
    ax.text(lx + 6, ly + 0.7, label, fontsize=7, ha='left', va='center', family='sans-serif')

# ===== Data flow annotations =====
ax.text(58, 49, 'POST /api/fuse\nFormData\nover_image + under_image', fontsize=7,
        ha='center', va='center', color='#1976D2', style='italic')
ax.text(58, 36, '← JPEG Response\n(JSON metadata)', fontsize=7,
        ha='center', va='center', color='#388E3C', style='italic')

ax.text(120, 42, '← 200 OK', fontsize=7, ha='center', va='center', color='#388E3C')

plt.tight_layout()
plt.savefig('D:/Desktop/IF-FILM-main/img/fig4_1_system_arch.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print('System architecture diagram saved to img/fig4_1_system_arch.png')
