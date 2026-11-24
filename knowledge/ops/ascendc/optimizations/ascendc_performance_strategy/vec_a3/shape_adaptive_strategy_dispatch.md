---
type: Optimization
title: 形状自适应双路径分派（形状可算判据 + host/kernel 一致路由）
description: 将硬编码单一路径改为形状自适应双路径分派，host与kernel用同一形状公式计算判据。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/shape-adaptive-strategy-dispatch.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：形状自适应双路径分派（形状可算判据 + host/kernel 一致路由）

> 单一优化点：当一个 kernel 的输入形状跨度极大、单一策略无法在所有形状下都最优时，不要硬编码单一路径，也不要按 dtype/场景写死分支——而是**抽象出两条各有专长的计算路径 + 一个只依赖形状、host 与 kernel 都能静态算出的判据**，据此在 kernel 内分派。判据两侧的路径各取所长，host tiling 与 kernel 用**同一公式**选路径并绑定各自的 buffer 预算。

本策略适用于任何"形状跨度大、单一策略有明确适用边界、且边界可由形状静态判定"的 kernel，与具体算子无关。

**融合来源**：本卡由原 `13-shape-adaptive-strategy-dispatch`（按 repeat-stride 上限分派跨行批 vs 逐行/分块）与原 `29-shape-adaptive-two-path-dispatch`（按 distinct 源行数分派缓存 vs 直接路径，上/下采样各取所长）融合而成；两者是同一泛化模式的两个判据实例。

---

## 1. 原理

**泛化模式**：设两条路径 A、B 各自有明确的适用域与失效边界（硬件参数上限、复杂度比值翻转点等）。若存在一个**只依赖形状、host tiling 与 kernel Init 都能用同一公式计算**的判据 `P(shape)`，使得 P 成立时 A 优于 B、P 不成立时 B 优于（或不劣于）A，则在 kernel 内按 P 分派，可覆盖全部形状且无单一路径的退化区间。

判据必须满足三个性质：

1. **形状可算**：只依赖静态形状（维度、行数、对齐性），不依赖运行时数据值；
2. **host/kernel 一致**：两侧用同一公式，保证 host 的 buffer/tile 预算与 kernel 实际路径匹配；
3. **边界双正确**：恰好处于阈值上的形状，两条路径都应正确（选任一不崩），仅性能有差异。

**判据实例 A（硬件参数上限型）**：跨行批归约/批施加依赖 `BinaryRepeatParams` 与整段规约的 repeat-stride 字段（uint8 ≤ 255，单位 DataBlock 32B），行步长（元素）必须 ≤ 255·8 = 2040（fp32 口径）。判据 `align(D, 最紧dtype对齐)/8 ≤ 255`：成立走跨行批路径（大 N 小 D 强），否则走逐行/分块路径（大 D 强）。

**判据实例 B（复杂度比值型）**：可分离插值的缓存路径指令数 ∝ distinct 源行数，直接路径 ∝ 输出行数。上采样（Hout > H）时 distinct ≈ 输出行数/scale ≪ 输出行数，缓存路径省 scale 倍；下采样（Hout ≤ H）时 distinct ≈ 2×输出行数 > 输出行数，缓存路径多算 ~1.75× 向量 op。判据 `(nA+nB) < n`（distinct 源行数 < 输出行数，kernel pre-scan 后即知）：成立走缓存路径，否则走直接路径。

配套地，tile 大小应按 UB 预算随形状自适应缩放（大末维/大 dtype 自动缩小 tile），避免固定 tile 在极端形状下越界或浪费（见策略 06 精神）。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. kernel 形状跨度大（如归约维 D 从个位到上千、行数 N 从百到百万；或上采样与下采样并存），且已有（或可实现）两条各有专长的路径。
2. 当前硬编码单一路径：部分形状区间实测明显退化（大 N 小 D 被每行固定开销拖垮；或上采样 case 慢数倍），或越出某路径的硬上限（repeat-stride 溢出、缓冲越界）。
3. profiling 显示两类 shape 的瓶颈类型不同（如上采样 VEC-bound vs 下采样带宽-bound），单一优化无法同时命中。
4. host tiling 与 kernel 若用不同判据选路径，会导致 buffer 预算与实际分配不符（片上缓存溢出）。

不适用：形状跨度小、单一策略已覆盖所有 case；或两条路径无明确边界（边界模糊时分派无意义）；或边界判据依赖运行时数据值、无法静态确定。

## 3. 正确性红线

- **host/kernel 同一判据**：分派阈值必须 host tiling 与 kernel Init/Compute 用同一个公式（同一对齐口径、同一上限、同一比较方向）。host 据此算 tile 行数与 buffer 预算，kernel 据此选路径并分配 buffer；两者不一致 → buffer 溢出或路径错配。判据尽量用 dtype 无关口径（如统一按最紧 dtype 的对齐行步长），host 无需知道 dtype。
- **buffer 预算与路径绑定**：两条路径的 buffer 需求不同（如跨行批路径需广播输出/暂存，缓存路径需中间结果缓冲，直接路径只需单行临时区）。host 的 rowBytes/UB 预算公式必须按"该形状实际会走的路径"计入对应 buffer；若判据运行时才最终确定，则保守按最紧路径分配，两路径都安全。
- **判据边界条件**：判据用 ≤ 还是 < 需与硬件上限的语义严格一致（如 repeat-stride ≤ 255 vs < 256）；恰好处于阈值上的形状，两条路径都应正确。缓存路径若按"槽位上限动态分配"（释放 UB 换大 tile），启用前必须检查槽数不超过上限，否则越界。
- **路径间结果一致**：两条路径的浮点结果应在相对误差门槛内一致（运算顺序相同则逐位一致）；fp16/bf16 注意舍入/饱和；大 D（或下采样）case 不得被误纳入另一路径的失效区间。
- **分派判据可由形状算出**：判据只依赖形状，不依赖运行时数据；依赖 pre-scan 的判据（如 distinct 计数）须保证 pre-scan 本身廉价且在分派前完成。

## 4. 泛化条件

适用（任一）：
- 形状跨度大的 reduce/elementwise/插值类 kernel，已有两条专长路径，需按形状自动选择。
- 某路径存在 repeat-stride/寄存器位宽/复杂度比值类硬边界（可由形状算出），边界外会出错或劣化。
- 有 UB 预算随形状缩放的需求（大末维/大 dtype 自动缩小 tile）。

不适用（任一）：
- 形状跨度小，单一策略覆盖全部。
- 只有一条路径（无需分派）。
- 边界判据无法由形状静态确定（依赖运行时数据值）。

## 5. 实施步骤

1. 确认两条路径各自的适用边界与失效条件（硬件参数上限型：如跨行批路径的 repeat-stride 上限 D≤2040；复杂度比值型：如 distinct 源行数与输出行数之比）。
2. 把边界抽象为一个只依赖形状、host 与 kernel 都能算的判据 `P(shape)`（如 `align(D,16)/8 ≤ 255` 或 `(nA+nB) < n`）。
3. host tiling：按判据两侧的最大需求分配 buffer（保守按最紧路径，或按形状只分配一侧）；据此算 tile 行数，并使 tile 大小随末维/dtype 自适应缩放。
4. kernel Init：用同一判据选路径并分配对应 buffer（仅该路径需要的 buffer 才分配）。
5. kernel Compute：用同一判据分派到两条 Compute 之一。
6. 全量编译，覆盖两类形状的精度全过，多次取样性能；确认判据成立侧走专长路径（大 N 小 D 走批路径 / 上采样走缓存）、另一侧不劣化，且无 buffer 溢出、边界附近无性能断崖。
7. 若性能/精度退化或判据不一致则修正判据/公式，或回退为单一策略。

## 6. LLM 前置问题

- 两条路径各自的适用边界是什么？边界属于硬件参数上限型还是复杂度比值型？能否抽象为只依赖形状的判据 `P(shape)`？
- host tiling 与 kernel 是否用完全相同的判据公式（同一对齐口径、同一比较方向）？判据是否 dtype 无关？
- 判据两侧的 buffer/rowBytes 公式是否分别匹配各自路径的分配？边界形状两条路径是否都正确？
- 两条路径的浮点结果是否在相对误差门槛内一致？失效区间（大 D / 下采样）是否被正确排除？

## 7. 验收标准

- 编译通过，无新增越界/片上缓存溢出。
- 精度：全部形状（两类路径）相对误差不退化（运算顺序相同则逐位一致）。
- 性能：判据成立侧走专长路径、显著优于另一路径；另一侧不劣化；判据边界附近无性能断崖。实例参考：跨行批分派下大 N 小 D 显著优于逐行、大 D 走逐行/分块不劣化；ResizeBilinear 双路径分派下上采样 case5 2.97× / case13 3.06×，下采样全部 ≥0.97×（无退化）。
- host 与 kernel 判据/rowBytes 一致。
- 若任一不满足则修正判据/公式或回退为单一策略。

## 检索卡（短卡）

动作：将硬编码单一路径改为形状自适应双路径分派，host与kernel用同一形状公式计算判据。
适用：形状跨度大的reduce、elementwise或插值kernel，且已有两条专长路径。
限制：host tiling与kernel Init/Compute必须使用同一公式及同一分派阈值。
范围：形状跨度大的reduce、elementwise与插值kernel。
检索词：P(shape)、双路径分派、host tiling、kernel Init、repeat-stride、复杂度比值。
机会：输入形状跨度极大，单一路径无法覆盖全域，且存在两条各有专长的路径。
