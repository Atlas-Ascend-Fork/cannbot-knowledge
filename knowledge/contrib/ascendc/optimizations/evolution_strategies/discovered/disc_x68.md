---
type: Optimization
title: "X68: decode MLA 精度机器放松（去 Dot2/Kahan）+ 两遍精确 p-rounding + KV-chunk 核切分"
description: "decode MLA/GQA 注意力的基线内核常为对齐 golden（fp64 CPU）而背负精度机器：Dot2 双 fp32 QK（TwoProd + TwoSum 树 + 跨 chunk DS）+ Kahan 补偿 + fp16/bf16 round-trip mimic。在 MERE/allclose 容差下这些机器多为过度设计，可改为普通 fp32 QK、两遍精确 p-rounding 与 KV-chunk 核切分；其中两遍结构是保证近零对消元素精度的硬约束。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X68: decode MLA 精度机器放松（去 Dot2/Kahan）+ 两遍精确 p-rounding + KV-chunk 核切分

## 核心思路
decode MLA/GQA 注意力的基线内核常为过 golden（fp64 CPU）而背负**精度机器**：
Dot2 双 fp32 QK（TwoProd + TwoSum 树 + 跨 chunk DS，显著增加 QK 向量指令）+ Kahan 补偿
+ fp16/bf16 round-trip mimic。在 eval 容差（rtol/atol≈1e-3，MERE<rel_thr）下，
这些机器**大部分是过度设计**。三招组合拳：

1. **精度放松**：QK 降为普通 fp32 点积（nope/rope 分段保留 golden 两次独立原 dtype
   matmul 的舍入 mimic，但去掉 DS 误差补偿），去掉 Kahan。fp16/bf16 输入低精度
   （~2^-11），标准 fp32 累加误差（~1e-5）远低于容差。
2. **两遍结构 + 精确 p-rounding（精度通过的关键）**：pass A 在线 softmax 求 chunk
   m/denom；pass B 用全局 m/denom 重算 e，做 `p = round_T(exp2(s2-mGlobal)/denomGlobal)`
   再 PV —— 精确复现 golden 的 `(e/denom).to(q_dtype)` 舍入点。**单遍 online softmax
   在 PV 前拿不到最终 denom，逐 tile fl_T(e) 舍入与 golden 的 fl_T(e/denom) 舍入点
   不同，近零对消元素（|o| 远小于 1）相对误差被 MERE 放大 → 超阈**。两遍是精度硬约束。
3. **KV-chunk 核切分**（FlashDecode 式）：任务空间 = B·qLen·headBlocks·maxChunks，
   每核只处理一段 KV 行区间，缓解长 KV、小 H 的 shape 的单核瓶颈；配轻量归并 kernel
   合并分段结果。maxChunks==1 时走单核两遍快速路径（同 kernel 内
   m/denom → e/PV + 写 o/lse），省去 passB/combine 两次 launch。

## 适用场景
- decode MLA/GQA 注意力，baseline 为过精度而背 Dot2/Kahan 机器的纯 AIV 实现
- 长 KV、小 H 的 shape 存在单核瓶颈（KV-split 缓解）
- eval 容差为相对宽松的 MERE/allclose（rtol/atol≈1e-3），非逐 bit 精确

## 实现要点
- QK 放松后仍保留 nope/rope 分段 round-trip（golden 为两次独立原 dtype matmul）
- 两遍结构不可省：p-rounding 需要最终全局 denom；单遍必超 MERE（近零元素）
- KV-chunk 切分用 maxChunks 均匀切 + 轻量 combine kernel；maxChunks==1 快速路径
  消除 2 次 launch
- 910B2C 大列（>256）向量归约 API 不可靠：例如 4×576 的归约只覆盖前 64 列、
  chunk 归约异常 → 归约必须走 Add/Sub 对数树或 Cube，或用 KV-chunk 减小归约宽度

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），对比父变体与变体；全量精度
  门禁采用目标 eval 的 MERE/allclose 容差，并构造近零对消元素验证两遍 p-rounding
  的舍入点。
- 容量类改动先做 UB/L1/L0C 预算审计；KV-chunk 切分需覆盖 maxChunks==1 与多 chunk、
  长 KV 小 H 的边界 shape。
