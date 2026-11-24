---
type: Optimization
title: 多块描述符写回合并
description: 用 Normal 模式的 32B 块补齐（UB 侧 AlignUp(blockLen,32)==padded 行距）加 GM 侧 dstStride=0，把每列一条写回压成整 tile 一条多块描述符
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/wide-descriptor-store-collapse.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：多块描述符写回合并

把奇数 C 的「每列一条 `DataCopyPad`」改成「整 tile 一条 `blockCount=tx` 的描述符」：`PaddingMode::Normal` 在 UB 侧按 32B 补齐，`AlignUp(C*2,32)==Cp*2` 正好是 padded 行距，GM 侧 `dstStride=0` 又正好是 NHWC 紧凑行距。

## 1. 原理

奇数 C 时实现者通常认为「UB 行隙 `(Cp-C)*2B` 无法用 32B 粒度的 `srcStride` 表达」，于是退回逐列搬运——这也是常见原实现的形态：每个输出列一条描述符。

但 `DataCopyPad` 的 `Normal` 模式本来就把每个 block 补齐到 32B，源地址按 `AlignUp(blockLen, 32)` 步进。奇数 C 时：

- UB 侧：`AlignUp(C*2, 32)` 恰好等于 `Cp*2`（padded 行距）——这就是我们想要的步长；
- GM 侧：`dstStride=0` 让块按 `C*2` 紧凑排列，恰好等于 NHWC 行距。

两侧同时成立，一条 `blockCount=tx` 的描述符就能跨过行隙。成本因此从「每条描述符搬多少字节」变成「描述符条数」：整个 tile 由每列一条压成一条。

## 2. 性能问题模式

- 优化目标：消除奇数 C 写回的描述符发射开销（每 tile 最多 tx 条小 DMA）
- 判定入口：`aiv_mte3_time / Duration` 明显偏高，且 `Cp != C`

## 3. 正确性红线

- 必须使用带 `PaddingMode` 模板参数的原型：`AscendC::DataCopyPad<T, PaddingMode::Normal>`
- 块长 `C*2B` 可以不是 32B 整数倍；`srcStride=0` 只在 `Cp*2B == AlignUp(C*2B,32)` 时正确
- 块数上限 65535（`uint16 blockCount`）；一次搬整行的大 outW 需分段
- 前提不成立时后果是**整行错位**（不是局部误差）——错位即回退逐列

## 4. 泛化条件

适用：

- 输出按行组织且行内有 32B 对齐填充（`Cp = CeilAlign(C,16)`，fp16）
- GM 侧是紧凑 NHWC（行距 = `C*2B`）
- MTE3 是绑定/次绑定管（`aiv_mte3_time / Duration ≥ 0.3`）

不适用：

- 行距不等于 `AlignUp(C*2B,32)`（例如人为 padding 到 C+8 这类非 16 元素倍数）
- 目标张量 GM 侧非紧凑（有 stride / 非连续 view）
- fp32/bf16 需按 32B = 8 元素重算对齐粒度
- 与 `2d-bulk-data-copy` 的分工：那张卡是**读侧**把逐行描述符合并成一条多块描述符；本卡是**写侧**利用 Normal 模式的 32B 块补齐恰好等于 padded 行距，把“每列一条”压成“整 tile 一条”。两者共用 `DataCopyExtParams` 的 stride 口径，但一个靠“行距可表达”、一个靠“补齐步长 == 真实行距”。
- 与 `mte-row-pad-strided-staging` 的关系：那张卡要求 UB 行槽被 MTE 自动垫整到 32B（读侧对齐域转换），本卡是同一对齐契约在写侧的镜像用法。

## 5. 实施步骤

1. 确认 UB 行距 == `AlignUp(C*dtypeSize, 32)`
2. 逐列 `blockCount=1` 改成整 tile 一次：`blockCount=tx`、`blockLen=C*dtypeSize`、`srcStride=0`、`dstStride=0`
3. GM 目的地址用 `yBase*C`，不再是逐列 `(yBase+i)*C`
4. 先在小形状上验证逐元素一致，再跑全量

## 6. LLM 前置问题

- 目标实现是否满足：UB 行距 == `AlignUp(C*dtypeSize,32)`？
- 目标实现是否满足：GM 侧紧凑 NHWC？
- 目标实现是否满足：MTE3 是绑定/次绑定管？
- 是否命中排除条件：行距不是 32B 补齐值？
- 是否命中排除条件：GM 侧非紧凑？

## 7. 分类与关联

- Classification：`validated_strategy`
- Generality：`op_class`
- 相关策略：`2d-bulk-data-copy`（读侧同族）、`mte-row-pad-strided-staging`（同一 32B 对齐契约）

## 检索卡（短卡）

动作：用 Normal 模式的 32B 块补齐（UB 侧 AlignUp(blockLen,32)==padded 行距）加 GM 侧 dstStride=0，把每列一条写回压成整 tile 一条多块描述符
适用：输出按行组织且 UB 行距恰为 AlignUp(C*2B,32)；GM 侧紧凑 NHWC；MTE3 绑定或次绑定
限制：须用带 PaddingMode::Normal 的 DataCopyPad；两侧 stride 都为 0 才成立；fp32 对齐粒度是 8 元素
范围：逐元素/窗口/归约后按行写回的向量算子
检索词：DataCopyPad、PaddingMode::Normal、dstStride=0、多块描述符、32B 补齐、MTE3 发射开销
机会：奇数 C 时每列一条小 DMA，MTE3 忙时里大部分是描述符发射
代价：对齐口径须与读侧行距一致，任一侧非紧凑即不成立
