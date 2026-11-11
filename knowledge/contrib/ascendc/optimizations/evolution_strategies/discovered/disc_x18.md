---
type: Optimization
title: "X18: Fused img2col LoadData3D 随路展开（含 band 窗口化突破 L1 容量）"
description: "卷积的 im2col GM 物化路径流量为 特征图→UB→GM→L1→L0，GM 往返占比高；fused 模式让 A 侧不落地，用 img2col LoadData3D 从 L1 直接随路展开进 L0A，并以 band 窗口化突破 L1 容量。"
tags:
  - task.optimization
  - topic.compute.neighborhood.convolution
  - topic.data_movement.layout_transform
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p129_fused_img2col_loaddata3d
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X18: Fused img2col LoadData3D 随路展开（含 band 窗口化突破 L1 容量）

> **已晋升为 P129**：策略卡见 [../cards/p129_fused_img2col_loaddata3d.md](../cards/p129_fused_img2col_loaddata3d.md)，Playbook 见 [../../../runbooks/performance/p129_fused_img2col_loaddata3d.md](../../../runbooks/performance/p129_fused_img2col_loaddata3d.md)，precondition YAML 见 cannbot-skills 仓 `community/ops/ascendc-evolution-strategies/references/preconditions/`。本文件保留该策略的详细机制说明，卡片内容以 P129 为准。

## 核心思路
卷积的 im2col GM 物化路径流量为 `特征图→UB→GM→L1→L0`，GM 往返占比高。
fused 模式让 **A 侧不落地**：特征图转 NC1HWC0 常驻 L1，用 img2col LoadData3D
（pad/stride/dilation 硬件处理）从 L1 直接随路展开进 L0A，B 侧复用 K-major
权重 ws。CopyOut/epilogue/m/n 分解与 normal 路径完全复用，改动集中在 A 侧加载。

**band 窗口化推广**（特征图 xNz 超 L1 时）：L1 只常驻输入**行带**而非整图。
band 以独立 fmap 身份喂 img2col LoadData3D：重算 `padTop' = pH + minRow − o0·sH
∈ [0,pH]`、`padBottom' ≤ pH`（均在原 pad 范围内，规避 pad 位宽溢出），mStartPt
用 band 相对值——硬件按 `(l1H, padTop', padBottom', sH, dH, kH)` 重建的输出高度
Ho' = o1−o0 代数恒成立，m→(ho,wo) 光栅与全图一致。块 = (img, band)，n 维在块内
循环（band 载一次供全部 nBlock 复用）。

## 适用场景
- **算子类型**: conv2d（kHkW>1）及任何 im2col+GEMM 形态的算子
- **瓶颈类型**: im2col GM 往返带宽/耗时占比大；或大特征图 B 面板随 m-block
  重复加载（L1 入口带宽瓶颈）
- **前提条件**: Ci%16==0（img2col channelSize 约束，非对齐先通道补零）；
  xNz + 常驻 B 面板 ≤ L1 预算（不满足时用 band 窗口化）

## 实现要点
1. **硬件 img2col 展开 k 序 = (ci1, kh, kw, ci0)**——C0 通道块在最外层，与软件
   惯用 (kh,kw,ci) 不同；权重 ws 必须按同序 repack（缓存键带布局标志）。
   两序在 Ci==16 或 kHkW==1 时恰好重合会"蒙对"——**必须用 one-hot 探针**
   （单元素置 1 观察落点）在 Ci>16 且 kHkW>1 的几何上确认，勿凭文档假设
2. NCHW 需 xtrans AIV kernel 先生成 xT [H*W, Ci]（TransDataTo5HD repeat 批量
   转置；bf16 按 uint16 位级转置）；NHWC 直接用原始 x，零中转
3. 门控回退（关键坑）：
   - **窄特征图（l1W 小）img2col LoadData3D 病理性慢**（mExtension 调满无效）
     → 设置宽度下限（经验阈值 W<24）回 im2col 物化路径
   - **kExtension > 64 不可靠**（部分几何出垃圾甚至挂死设备）→ 保持 ≤64
   - 留环境变量开关做 A/B 与回退
4. 每个 k tile 的展开与 Mmad 重叠靠 L0 队列深度（见 X11 要点 3）
5. 尾块纪律不变：m/n 满 tile 计算 + Fixpipe 裁剪；channelSize 非 16 倍数会
   跳分形块，空间尾 round16

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
