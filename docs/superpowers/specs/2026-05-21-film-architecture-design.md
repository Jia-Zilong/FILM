# FILM 底层架构改进设计：Cross-Image Attention

**Date**: 2026-05-21
**Status**: Draft

## 问题陈述

当前 FILM 架构存在以下根本性问题：

1. **文本引导是虚假优势**：推理时只加载 `MEFB_test.h5` 第一条样本的文本，所有图像共用同一段 BLIP2 embedding。6 个 CrossAttention 模块（~1.6M 参数，占总参数 80%）实际是在用固定向量做查询，不是真正的语义引导。

2. **SSIM 损失被禁用**：`loss_ssim=0`（默认），模型只学强度和梯度匹配，不学结构一致性。

3. **双图在最终层才接触**：图A和图B各自独立通过3层 `restormer_cablock`，互不通信。中间层无法交叉学习"过曝区域在另一张图里有更好的细节"。

4. **推理时 min-max 归一化放大噪声**：对 sigmoid 输出再做 min-max 拉伸，会把平坦区域的噪声放大。

## 改进方案

### 核心创新：Cross-Image Attention

用**图像间的互相查询**替代文本查询。让过曝图的特征作为 Query 去查询欠曝图的特征（反之亦然），实现真正的双图信息交换。

**参数对比**：
- 旧架构：~2.0M 参数（CrossAttention ~1.6M）
- 新架构：~0.4M 参数（减少 80%）

### 具体改动

#### 改动1：`net/Film.py` — 架构重写

**移除的模块**：
- `CrossAttention` — 不再需要文本查询
- `imagefeature2textfeature` — 不再需要投影到文本空间
- `text_preprocess` — 不再处理文本输入
- `ChannelAttention` — 已存在的死代码

**新增模块**：`CrossImageAttention`
- Query: 图像A的特征 `[B, C, H, W]`
- Key/Value: 图像B的特征 `[B, C, H, W]`
- 使用与 Restormer 一致的 `TransformerBlock` 内部结构，但在两个图像间交换信息
- 具体实现：`q = conv_q(imageA)`, `k = conv_k(imageB)`, `v = conv_v(imageB)`, 然后 MDTA 注意力

**重写 `restormer_cablock`**：
- 移除所有 `imagef2textf`、`cross_attentionA1/A2`、`convA2/B2`
- 新增 `cross_image_attention`：imageA 查 imageB，imageB 查 imageA
- 前向签名从 `(imageA, imageB, text)` 改为 `(imageA, imageB)`

**重写 `Net`**：
- 移除 `text_process`
- 前向签名从 `(imageA, imageB, text)` 改为 `(imageA, imageB)`
- 3 层 `restormer_cablock` 不再传 text 参数

**改动2：`train.py` — 训练调优**
- `loss_ssim` 默认值从 0 改为 0.1
- 添加数据增强：随机水平翻转 + 随机旋转（0/90/180/270）
- 学习率从 1e-5 改为 5e-5
- `batch_size` 从 2 改为 4（3090 单卡 24GB 显存足够）
- `numepochs` 从 150 改为 200（参数减少后需要更多 epoch 收敛）

**改动3：`test.py` — 测试适配**
- `model(data_IR, data_VIS, text)` 改为 `model(data_IR, data_VIS)`
- 移除 text 相关的 DataLoader 读取

**改动4：`mef_engine.py` — 推理适配**
- 移除 `self.text_tensor` 加载逻辑（不再从 `MEFB_test.h5` 读文本）
- `self.model(tensor_over, tensor_under, self.text_tensor)` 改为 `self.model(tensor_over, tensor_under)`
- `mef_engine.__init__` 移除 text 相关的 DataLoader 代码

**改动5：`mef_engine.py` — 后处理改进**
- 用 sigmoid 归一化替代 min-max 拉伸：
  ```python
  # 旧：min-max 归一化
  min_val = torch.min(fused_y_tensor)
  max_val = torch.max(fused_y_tensor)
  fused_y_tensor = (fused_y_tensor - min_val) / clamp(max_val - min_val, min=1e-8)

  # 新：sigmoid + 线性映射到 [0, 1]
  fused_y_tensor = torch.sigmoid(fused_y_tensor * 10 - 5)  # 中心在 0.5，斜率10
  ```
  实际上网络输出已经是 sigmoid 值（0-1），所以直接 clamp 即可：
  ```python
  fused_y_tensor = torch.clamp(fused_y_tensor, 0, 1)
  ```

**改动6：`utils/lossfun.py` — 确认 Fusionloss 兼容单通道输入**
- 当前 `Fusionloss` 已经是基于梯度和强度的 L1 损失，无需修改

#### 改动7：`api_server.py` — 兼容性调整（如有需要）
- 检查 `/api/fuse` 等端点是否直接调用 `film_engine.fuse()`（是的，通过 `mef_engine.py` 封装）
- `api_server.py` 本身不直接调用 model，所以无需修改

### 训练流程

```
1. 备份当前权重: cp models/MEF.pth models/MEF.pth.backup
2. 运行新训练: python train.py --loss_ssim 0.1 --lr 5e-5 --batch_size 4 --numepochs 200
3. 测试新权重: python test.py （记录 6 项指标）
4. 对比旧权重指标:
   - 如果 ≥5/6 指标持平或提升 → 替换 MEF.pth
   - 如果 <5/6 指标提升 → 回退到 backup
5. 确认提升后再推送代码到仓库
```

### 风险评估

| 风险 | 缓解措施 |
|------|----------|
| 新架构训练后指标下降 | 保留旧权重备份，`git checkout` 恢复代码，用旧权重继续服务 |
| 训练时间较长 | 3090 单卡 ~200 epoch 约 6-8 小时（batch_size=4，24GB 显存） |
| 跨注意力在空间维度可能显存爆炸 | 使用全局池化后做 attention（HW 维度先 pool 到 8x8 再查） |

### 验证标准

在 MEFB 测试集上，新权重对比旧权重的 6 项指标：

| 指标 | 旧权重基线 | 新权重目标 |
|------|-----------|-----------|
| EN | TBD（待 `python test.py` 获取） | ≥ 基线 |
| SD | TBD | ≥ 基线 |
| SF | TBD | ≥ 基线 |
| AG | TBD | ≥ 基线 |
| VIF | TBD | ≥ 基线 |
| Qabf | TBD | ≥ 基线 |

整体提升 ≥ 5/6 项指标视为成功。

### 不回退策略

- 所有修改**暂不推送**到仓库
- 训练结果确认后再决定是否推送
- 如果性能下降，直接 `git checkout -- net/Film.py train.py test.py mef_engine.py` 恢复
