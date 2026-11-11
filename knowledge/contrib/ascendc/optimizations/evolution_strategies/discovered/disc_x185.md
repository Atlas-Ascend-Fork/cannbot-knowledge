---
type: Optimization
title: "X185: DMA 切片轴翻转：列分块微 DMA → 行分块连续取数 + UB 常驻"
description: "当 DMA 沿列分块切小 tile（blockLen 128–256B、srcStride 跨步、取数密度 12.5–50%）时，成本正比于指令条数而非字节数；把切片轴翻成行分块（整行宽、源连续）并把整块常驻 UB，指令数与描述符量可降 1–2 个数量级。只修读侧或只修写侧通常不兑现，读写两侧要成对修。"
tags:
  - task.optimization
  - topic.data_movement
  - topic.memory
status: draft
sources: []
created_at: "2026-11-05T00:00:00Z"
updated_at: "2026-11-05T00:00:00Z"
platforms:
  - a2
  - a3
---
# X185: DMA 切片轴翻转：列分块微 DMA → 行分块连续取数 + UB 常驻

## 核心思路

数据搬运的固定成本在每条 DMA 指令上：16B/128B 的 strided 微 DMA（blockLen 1–4 个 32B 块、srcStride 大、取数密度低）每条约 600ns 量级，`指令条数 × 600ns` 往往比实际字节数的带宽时间大 10–40 倍。解法是把切片轴从“沿列切小 tile”翻成“沿行切宽 tile”：

1. **行分块 row-chunk**：`bwC = floor(UB预算/行宽)` 行 × 整 Dc 宽，源地址完全连续，段长从 128B 升到 8KB；
2. **整块 UB 常驻**：row-block 入口 1 条连续 DataCopy 把整个 `[bw, Dc]` 块搬进 UB，QK/PV 两段消费都从常驻块取连续子块，消费侧不再回 GM 重读；
3. **读写两侧成对修**：只修读侧或只修写侧实测无收益；读+写双修才兑现。

## 判据

1. msprof 显示 `undersize_transfer` 密集、MTE2 指令数远超数据量应有的条数；先算“指令条数 × 单条固定成本”与“字节数 / 实测带宽”两个下界，若前者大一个量级以上，属指令条数 bound。
2. 典型场景：上百万条 DataCopyPad 搬几百 MB，带宽利用率仅 2–3%、单条约 600ns——成本正比于指令条数而非字节。
3. 对照组：只减权重/操作数字节、不减条数时墙钟 flat（约 0.97x），可证伪“字节数主导”模型。

## 实现要点

1. row-block 尺寸按 UB 预算取整行宽；若整块放不下，先做“只翻轴不常驻”的对照组拿到 +15% 量级，再评估常驻的额外 +5%。
2. 常驻块在 row-block 入口一次连续 DataCopy；QK/PV 两段都从常驻块切片，避免消费侧回 GM。
3. 写侧同样改连续/合并描述符；只改读侧时收益常被写侧的微 DMA 吃掉。
4. 若源布局是 paged/展平，先确认 GM 上存在连续段；不存在时先做页内连续化，再翻轴。

## 边界

- 源布局必须允许整行宽连续；paged/展平布局要先确认连续段。
- UB 容量不足以放整块时，退化为“只翻轴不常驻”对照，不要硬上常驻。
- 只修单侧（读或写）通常不兑现；不要把单侧收益当成完整收益。
- 若单条 DMA 已经是大段连续、指令条数不占主导，本卡不适用。

## 实测证据

- 在一个 paged MLA decode 算子上：列分块 128B@stride → 行分块连续 + `[bw,Dc]` 整块常驻，**1.20x**；只翻轴 1.15x，常驻再 +5%。
- 同一算子：DB 32→64 + 列切片合并连续 DataCopyPad，单项 **1.64x**；微 DMA 合并（逐 head 128B → 单条 strided）1.34x（per-case 1.17–1.48x）。
- 在一个 CV 融合卷积上：ci-block 批量装载使 DMA 16,644→852 条（**19.5x**），bytes 仅 -43%，总体 **+19.6%**；对照“只减权重字节不减条数”为 0.968x（flat）。
- BSH band-mean 读写双修 1.512x；读侧单独 1.44x 不兑现。

## 关联

- 描述符数 KPI：[X95](disc_x95.md)。
- im2col 读放大：[X182](disc_x182.md)。
- Gather/重采样：[X93](disc_x93.md)、[X94](disc_x94.md)。
- stride 搬运：[P26](../cards/p26_stride_fused_transpose.md)、[P24](../cards/p24_nd2nz_format_copy.md)。
