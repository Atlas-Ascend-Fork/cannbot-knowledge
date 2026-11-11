---
type: Optimization
title: "X147: A2/910B3 的 L0C 出口：只有 GM 与量化到不超过 2 字节的 L1"
description: "想在 CV 融合环里把 fp32 中间量从 L0C 直接送 UB/L1 以消掉 GM 往返，在 A2/910B3/DAV2201 上会撞两层硬墙：平台能力表没有 l0c2ub；L0C→L1 的 Fixpipe 只接受 f32→int8/uint8/fp16/bf16 等量化通路，拒绝 f32→f32。调用 UB 版本可能编译失败；直接调 L0C2UBImpl 在 release 下可能是静默 no-op。"
tags:
  - task.optimization
  - topic.memory
  - topic.architecture
status: draft
sources: []
created_at: "2026-10-28T12:12:00Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X147: A2/910B3 的 L0C 出口：只有 GM 与量化到不超过 2 字节的 L1

## 核心思路
"AIC 出中间量 → 直接写 UB/L1 给 AIV/下一个 Mmad 消费"在 A2 上**不成立**：

- **L0C → UB**：无硬件通路（平台能力表里没有该 intrinsic）。
- **L0C → L1**：只有**量化**通路（f32 → {int8, uint8, fp16, bf16}；s32 → {int8, uint8, fp16}），没有 f32 → f32。想用它把 fp32 中间量落回 L1 再喂 Cube，必须先降到不超过 2 字节。

因此在 A2 上，CV 融合环的中间量若必须保持 fp32，就只能走 GM workspace 往返；这直接决定了 X146/X148 中讨论的"FIX 出口"墙。

## 适用场景
- 任何想在 CV 融合环里省掉"中间量经 GM workspace 往返"的设计（FlashAttention 的 P 矩阵、indexer 的 S 矩阵、topk 的 score 矩阵等）。
- 本结论针对 A2/910B3/DAV2201 与对应 CANN 版本；A3 或更新架构必须重新查平台能力表，不能直接套用。

## 实现要点
1. **先查平台能力表**：在 CANN 的 `platform_config/Ascend910B3.ini` 一类文件中搜索 `Intrinsic_fix_pipe_*`。预期能看到 `l0c2l1`、`l0c2out`，没有 `l0c2ub`。
2. **再查头文件 allow-list**：`asc/impl/basic_api/dav_c220/kernel_operator_fixpipe_v2_impl.h` 中
   - `FixpipeL0C2UBImpl` 直接 `ReportNotSupport`；
   - `FixpipeL0C2L1Impl` 的 dtype 断言只允许 `float → int8/uint8/half/bfloat16`、`int32 → int8/uint8/half`。
3. **编译级复现**：写 `Fixpipe(ubTensor, l0cTensor, params)` 时，位置分派若是运行时 `if`，L1 分支也会被实例化，可能报 `the 1st parameter maybe need a type '__cbuf__ half *'`。直接调 `FixpipeL0C2UBImpl` 可能编译通过，但在 release 下是**静默 no-op**（只有 `-DASCENDC_DEBUG` 才有断言）。这是最危险的形态：不报错但什么都不做。
4. **精度门**：若中间量必须降到不超过 2 字节才能走 L1，先验证目标算子的精度。低精度中间量在长归约/大动态范围下可能通不过精度 gate；通不过就说明这条路不可用，不要继续在调度层尝试。

## 验证方法
- 用平台能力表 + 头文件 allow-list + 编译错误三重确认通路不存在。
- 若尝试量化通路，必须做逐 case 精度对比，重点看动态范围大的输入。
- 对"静默 no-op"路径，用哨兵值确认目标 buffer 是否真的被写。

## 关联
- 本卡封死了 [X126](disc_x126.md) 一类"把 O/中间量留在 L0C"之外的"直接写 UB/L1"捷径；X126 是把累加留在 L0C 内，不涉及出口。
- 与 [X148](disc_x148.md) 的 FIX 天花板结论直接相关。

## 补充判据（跨算子复核）

- **workspace 收窄的可行域**：优先收窄“AIV 写、combine 重复读”的中间量（如 partial O），fp32→fp16 可省一半读写且精度门禁通过（实测 +4.75%）；不要先动 cube C2 侧的 score/O 交换缓冲。
- **两个硬边界**：
  1. CANN Fixpipe `F322F16` 在 `mSize=16` 时存在确定性误映射行，cube C2 侧 `ws_o` 收窄会被它挡住；
  2. score/logits 的 `ws_s` 收窄受值域门禁限制，fp16 舍入进入 max/exp 链后精度不足（matched_ratio 会掉到 0.84 量级）。
- 收窄前先证明该量在数学上有界（running-max 下 P≤1 的 O 有界；score/logits 通常无界）；与 X148 的 FIX 天花板一起看。
