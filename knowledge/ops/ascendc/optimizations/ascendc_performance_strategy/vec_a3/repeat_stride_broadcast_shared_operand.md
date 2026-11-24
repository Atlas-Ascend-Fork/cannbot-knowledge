---
type: Optimization
title: 行共享/列广播操作数用 repeat-stride 二元 op（repStride=0）
description: 将逐行调用或预广播矩阵改为高维切分二元op，并令共享操作数repStride=0。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/repeat-stride-broadcast-shared-operand.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：行共享/列广播操作数用 repeat-stride 二元 op（repStride=0）

> 单一优化点：当逐行 element-wise 二元运算中一个操作数对"所有行相同"（如每行共用同一份按列向量），不要为每行复制一份广播矩阵、也不要逐行单独调用；用高维切分二元 op 的 `BinaryRepeatParams`，把那个共享操作数的 `repStride=0`（相邻 repeat 不推进），一条指令的多个 repeat 各处理一行，共享操作数自动跨行复用。

本策略适用于任何"逐行 element-wise op 带一个行不变操作数"的 kernel（scale by per-column vector、add per-column bias、mul shared mask 等），与具体算子无关。

---

## 1. 原理

AscendC 高维切分二元 op（Add/Mul/... 的 `mask, repeatTime, BinaryRepeatParams` 重载）通过 `BinaryRepeatParams{dstBlkStride, src0BlkStride, src1BlkStride, dstRepStride, src0RepStride, src1RepStride}` 控制每个 repeat 的地址推进。其中 `srcN_RepStride` 是该操作数相邻 repeat（跨迭代）跳过的 DataBlock 数。

若某操作数对所有 repeat（即所有行）应保持同一份，把它的 `repStride` 设为 0：每个 repeat 都从该操作数同一处读，等价于跨行广播。配合 `dstRepStride = src0RepStride = 行步长/8`（按行推进另一操作数与目的），一条 repeat=行数（分批 ≤255）的 op 即可处理整 tile 所有行，共享操作数只读一份。

对比两种次优写法：(a) 预先把共享操作数广播成 (行数, 列) 矩阵再整块 op——多一次广播写 + op 多读一份，片上缓存流量翻倍；(b) 逐行调 op——每行一次发射 + 屏障，行数大时固定开销主导。`repStride=0` 两者皆避。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. kernel 有逐行 element-wise 二元 op，其中一个操作数对所有行相同（行不变）。
2. 当前实现是：逐行循环调用 op，或预先广播共享操作数为整 tile 矩阵再整块 op。
3. 该 op 出现在热路径（如归一化的按列 scale、按列加 bias），profiling/代码审查显示其片上流量或调用次数占比可观。
4. 行步长 ≤ 255·8 元素（repStride 装 uint8）。

不适用：两个操作数都逐行不同（无行不变量可复用）；或行步长 > 255·8（repStride 溢出，需分块或逐行）。

## 3. 正确性红线

- **字段顺序**：`BinaryRepeatParams` 构造为 `{dstBlkStride, src0BlkStride, src1BlkStride, dstRepStride, src0RepStride, src1RepStride}`，全是 uint8、单位为 DataBlock（32B）。把共享操作数放对应 src 槽、其 repStride 置 0；切勿搞反字段。
- **共享操作数无行偏移**：按列分块循环（每块 vectorWidth 元素）时，共享操作数在该块内从 `[块偏移]` 读，跨行 repeat 不再叠加行偏移（repStride=0）；逐 255 行外层批循环时，每批共享操作数仍从同一块偏移读（不随行批推进）。
- **行步长一致**：dst 与逐行操作数的 repStride = 行步长/8 必须与 tile 的实际行布局一致（32B 对齐）。
- **repeat ≤ 255**：repeatTime 是 uint8；行数 >255 必须按 255 切批，每批 dst/逐行操作数按 `批×行步长` 推进，共享操作数不推进。
- **mask 与列尾**：按列分块时，主体用 mask=vectorWidth，列尾用 mask=D%vectorWidth；mask 是该 repeat 内参与计算的元素数（连续模式）。
- **in-place**：dst 与逐行操作数可为同一 tensor（in-place op），element-wise 无重叠问题；op 间需 `PipeBarrier<PIPE_V>`。

## 4. 泛化条件

适用（任一）：
- 逐行 element-wise op 带行不变操作数（per-column vector / shared mask / broadcast scalar-as-vector），当前逐行调用或预广播矩阵。
- 该 op 在热路径，片上流量或调用次数可观。

不适用（任一）：
- 两操作数皆逐行不同。
- 行步长 > 255·8（repStride uint8 溢出）。
- op 不在热路径，优化无意义。

## 4.1 收益上限预检（2026-09-22 新增，选路阶段执行）

本策略只作用于 epilogue / 行共享操作数路径，**收益上限 ≈ 该 op 在墙钟中的占比**（Amdahl）。选路前必须估算该 op 占比：

- 占比 **<5%** → 即使完全消除也过不了门槛，**不选**（本组 6 个失败轮该 op 占比均 <1%，加速比 ≤1.008，如 `_scaled_mm`/`mkldnn_linear`/`weight_int8pack_mm`）。
- 占比可观且**标量发射主导**时收益显著（成功轮 fbgemm_linear_fp16 达 1.5932×；cdist 1.0622×）。

## 5. 实施步骤

1. 定位逐行/预广播的 element-wise 二元 op，确认哪个操作数行不变。
2. 确认行步长 32B 对齐、≤255·8 元素。
3. 改写为高维切分重载：按列分块（vectorWidth 一块 + 列尾 mask），每块一条 repeat=行数（分批 ≤255）的 op，`BinaryRepeatParams` 中行不变操作数的 repStride=0、dst 与逐行操作数 repStride=行步长/8。
4. 全量编译，精度全过（与逐行/预广播实现逐比特或相对误差一致），多次取样性能。
5. 若改善超噪声且精度过则采纳；否则回退。

## 6. LLM 前置问题

- 该逐行 element-wise op 是否有一个操作数对所有行相同？当前是逐行调用还是预广播矩阵？
- 共享操作数放在 BinaryRepeatParams 的哪个 src 槽？其 repStride 是否置 0、其它两个是否按行步长/8？
- 行步长是否 32B 对齐且 ≤255·8？行数 >255 是否按 255 切批（每批共享操作数不推进）？
- 列尾（D 非 vectorWidth 整除）是否用 mask=D%vectorWidth 单独处理？

## 7. 验收标准

- 编译通过。
- 精度：全部用例与改前一致（逐比特或相对误差不变；浮点顺序变化允许末位差异）。
- 性能：含该 op 的 case 墙钟多次取样稳定改善、超噪声；改善来自调用次数与片上流量的减少。
- repStride 不溢出（行步长 ≤255·8），否则该 case 走其它路径。
- 若任一不满足则回退。

## 检索卡（短卡）

动作：将逐行调用或预广播矩阵改为高维切分二元op，并令共享操作数repStride=0。
适用：逐行element-wise二元运算中，一个操作数对所有行不变。
限制：行步长须32B对齐且不超过255·8元素；收益上限=该 op 墙钟占比，<5% 不选（Amdahl 预检）
范围：逐行二元op的列向量、共享mask或标量向量操作数。
检索词：repeat-stride、repStride=0、BinaryRepeatParams、高维切分二元op。
机会：当前逐行调用二元op，或先把行不变操作数广播成整tile矩阵。
