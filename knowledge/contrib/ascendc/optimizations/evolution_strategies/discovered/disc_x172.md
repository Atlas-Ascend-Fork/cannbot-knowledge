---
type: Optimization
title: "X172: MLA decode 按形状分档选杠杆（小 shape/中等/大 head_block）"
description: "MLA/paged decode 的三类形状墙不同：小 shape 受跨核握手环与 launch 固定开销支配，应换路由/减 launch；中等 head_block 受 AIC MTE2 分页 gather 支配，应减少 launch/整理访问；head_block 大时 L0C 放不下 fp32 累加器，受 Fixpipe 与 gather 的 CV 依赖链支配，应减 Fixpipe 字节/减轮数。选方向前先按 metrics 分档。"
tags:
  - task.optimization
  - task.debugging
  - topic.attention
  - topic.kv_cache
status: draft
sources: []
created_at: "2026-10-29T06:00:00Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X172: MLA decode 按形状分档选杠杆（小 shape/中等/大 head_block）

## 分档判据与对应杠杆
| 档 | 判据 | 实测墙的形态 | 有效杠杆 | 通常无效的杠杆 |
|---|---|---|---|---|
| 小 shape | KV footprint 小、单 (b,h)、走 tiny/direct_out 路由 | `aic_scalar`/`aiv_scalar` 接近 1，`aic_mte2`/`aic_mac` 接近 0 | **换路由**（例如 bf16 走 AIV-only tiny 单 kernel）、减少 launch 次数 | 拷字节类改动、tiny 单遍化、cps 压平 |
| 中等 head_block | `head_block` 较小、nomax 可用 | `aic_mte2` 忙占比高（分页 gather） | 减少 launch（merge 折进 stage1，按 splits_ub 收窄） | 加深在途、P 双缓冲预取、放宽预取、加大 burst |
| 大 head_block | `head_block` 大、`dc_align` 大 | L0C 放不下 `acc_o`；`aic_fixpipe` + `aic_mte2` 两侧都忙，CV 依赖链 | 减 Fixpipe 字节、减 dc 片轮数（先做 L0B 容量预算） | nomax + L0C 常驻、GM fp32 原子加、AIV 侧重写族 |

## 关键定量结论
- 「quick-batch 逐 case 有效带宽」会把协议成本算进内核：同一二进制在隔离口径与 batch 口径下的时间可能差出固定协议成本 + `min(KV,L2)/带宽` 量级。**不要用 batch 口径的带宽数字判断内核带宽余量**；要看隔离冷态复测与理论纯读上限。
- 小 shape 的固定成本降低在几何均值上的价值远大于大 shape 的同等时延降低（`dG/dT_i = G/(N·t_i)`），而小 shape 的墙是固定开销/路由，不是带宽 ⇒ 小 shape 应优先「换路由 + 减 launch」，不要做数据搬运微调。
- 三档之间不要用一个统一优化套件；先按 metrics 分档，再选杠杆。

## 适用场景
- MLA / MQA / GQA decode、paged KV、V 复用 K 的列（每 token 只读一遍 KV）的结构。
- 分档阈值（KV footprint、head_block、dc_align）要按目标模型与硬件重新标定，不能直接套用。

## 实现要点
1. 先用 `--aic-metrics=PipeUtilization` 采代表 shape，记录 `aic_scalar`/`aiv_scalar`/`aic_mte2`/`aic_fixpipe`/`aic_mac`。
2. 小 shape：优先评估"换路由"（例如单独 AIV-only kernel）与减少 launch；不要先做指令级微调。
3. 中等 shape：先确认 batch 口径的带宽数字是否含协议成本；隔离冷态复测后再判断是否有带宽余量。
4. 大 shape：先算 L0C 预算（`hb*dc*4 + acc_s`），确认 acc_o 是否能常驻；不能常驻时，比较"每 chunk 落 ws_o + AIV 重标定"与"GM 原子加"的 Fixpipe 字节账，后者常因 Fixpipe 字节增加而更差。
5. AIV 侧的重写（整段 DMA、alpha 门控、窄广播）在大 head_block 档收益通常很小，优先做容量/链路侧。

## 验证方法
- 每档选 2–3 个代表 shape，分别做同窗口 A/B。
- 小 shape 重点看 launch 次数与固定开销；中等 shape 看隔离带宽；大 shape 看 Fixpipe/MTE2 字节与 CV 依赖链。
- 所有结论按档位报告，不要用全量 geomean 掩盖某一档的退化。

## 关联
- 与 [X153](disc_x153.md)（head_block 惩罚来源）和 [X128](disc_x128.md)（槽信用时序）配合。
- 与 [X126](disc_x126.md)（L0C 跨 chunk 累加）共享大 head_block 的 L0C 预算分析。
