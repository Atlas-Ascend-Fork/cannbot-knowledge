---
type: Optimization
title: "X187: host 前处理融合成单个 AIV prep kernel + wrapper 死分配清理"
description: "短/中序列下设备时间常被 host 前处理链（RoPE/scale 折叠/permute/转置/hi-lo 拆分）主导：每个小算子各走 2–4 趟 GM 且各付一次 launch。把前处理链融合成单个 AIV-only prep kernel 一趟产出全部目标面板；同时把 wrapper 里从不被消费的全尺寸零张量退化为占位分配。"
tags:
  - task.optimization
  - topic.implementation.kernel_launch
  - topic.data_movement
status: draft
sources: []
created_at: "2026-11-05T00:00:00Z"
updated_at: "2026-11-05T00:00:00Z"
platforms:
  - a2
  - a3
---
# X187: host 前处理融合成单个 AIV prep kernel + wrapper 死分配清理

## 核心思路

**A. 融合 prep kernel**：host 侧前处理链（RoPE 旋转 + scale 折叠 + permute + K 转置 + hi/lo 拆分）通常由多个小算子组成，每个小算子各走 2–4 趟 GM 且各付一次 launch。合并为一个 AIV-only kernel：一趟从 fp32 源产出全部目标面板，片上完成全部变换。

**B. wrapper 死分配清理**：kernel 已短路、从不解引用的可选输入（pse/sink 等）、未启用的查表、无 padding 路径的 `torch.zeros→empty`，全部退化为 1 元素占位或不分配。不占评分（`asc_us` 只计融合核），但每变体评估提速、长跑复利；注意保留语义上必需的零初始化（多槽 workspace 等）。

## 判据

1. `op_summary`/探针显示 host 侧小算子 launch 数多、设备时间占比高（短序列/小 shape 尤甚）；实测某融合 attention 的短/中序列设备时间 **85.6% 在 host 前处理**。
2. 前处理必须是纯 elementwise/布局变换，可片上完成，且无跨算子归约依赖。
3. 先区分“host 固定开销”与“设备计算”：若 host 前处理各算子总时长已经超过主 kernel，优先做 A；否则先做 B 的零风险清理。

## 实现要点

1. **RoPE 留在 fp32 域**：`hi=(half)x`、`lo=(half)(x-(float)hi)` 的定义域要求 fp32 中间量，才能与 host torch 逐位等价，精度零影响。
2. **stride-2 DataCopyParams 无法表达 4 字节元素步长**：奇偶去交织用一次连续 DataCopy + 两趟 counter-mode GatherMask，仍在向量流水上完成。
3. **B 先做**：可选输入占位化、`zeros→empty`、复用 wrapper 表、scale 预乘。注意保留语义必需的零初始化（例如会被未写行污染读的 workspace 槽）。
4. 融合后按 case 画像分档预期收益：收益严格集中在 host 密集的短/中序列 case，长序列几乎不动。

## 边界

- 前处理若含跨算子归约、动态 shape 依赖或不可片上完成的算子，不能直接融合。
- 长序列 case 的 host 前处理占比低，融合收益有限；不要用短序列收益外推全量。
- B 的 `zeros→empty` 只适用于“kernel 会写满全部区域、无读前未写”的缓冲；会被未写行读取的 workspace 必须保留零初始化。
- 先做 B 再做 A；A 需要逐位数值验证，不能只看吞吐。

## 实测证据

- 在一个 hi/lo 融合 attention 上，A（融合 prep kernel，删 BuildRotPanel 链、`transpose().contiguous()`、3 次拆分）：**1.5210x** 单项 / **1.7671x** 叠加；两个代表 case 3.27x、2.98x，三面板 GM 流量 -43%。
- 同一算子纯 host 瘦身（不新增 kernel，复用 wrapper 表、scale 预乘）：1.0291x——在 prep kernel 落地后存量有限，先后顺序敏感。
- GQA：host 3 pack 收敛为 1 次共享零化分配 + 2 次 `copy_`（K/V 同列块一次填两平面）：**+6.17%**，删 178 device task/50 例。
- GQA：自然 ld 跟随输入张量（删 `x2d/attn2d` 的 zeros 与 narrow+reshape 物化）：**+8.31%**；5 维对齐 view 替代 `permute().reshape()`（消 clone）：+2.78%。
- FFN：mode1 workspace 只零 flag 尾区（≤49KB），数据区 `at::empty`：+2.5%。
- 可选输入占位化 + `zeros→empty`：单次前向省约 2GB 死填充（评分口径 1.0x，吞吐提升）。

## 关联

- Host 数据通路消除：[X52](disc_x52.md)。
- Host launch 合并/per-shape tiling 缓存：[P143](../cards/p143_attention_host_launch_merge.md)。
- Workspace 零初始化：[X39](disc_x39.md)、[P139](../cards/p139_multi_slot_workspace_zero_init.md)。
- dtype 直传：[X3](disc_x3.md)。
