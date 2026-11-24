---
type: Optimization
title: 逐行归约的树形折叠向量化
description: 将逐行的通用归约接口加标量回读链改为树形折叠向量化
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/vector-tree-reduce.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：逐行归约的树形折叠向量化

单一优化点

## 1. 原理

per-token 归一化/量化算子中，每行需要对尾维做一次归约（求和或求最大）得到一个标量，再用该标量归一化整行。慢实现常调用「通用归约接口 + 取标量」链：通用接口内部开销大、且每行一次标量回读，使归约段在行循环中成为瓶颈。

改用**树形折叠 + 单次整段归约**：先把行内数据按二分折叠（用向量加/取大把 N 个元素压到单个 vector lane 宽度），再一次整段归约指令产出标量。折叠用纯向量指令、整段归约只发一次，归约段指令数与往返大幅下降。

## 2. 性能问题模式

- 每行调用通用归约接口（带临时 buffer、内部多 rep），随后立即取标量。
- 行循环中归约调用频次高（行数 × 每行归约次数）。
- 归约段占用显著时间但计算强度低（瓶颈在指令开销与同步，而非算力）。

## 3. 正确性红线

- **归约长度**：折叠与整段归约均按该行有效长度；非对齐尾段用余数分支处理。
- **原地折叠副作用**：树形折叠会破坏源数据（后续若仍需该行原始值，须先复制或确保该 buffer 归约后不再用）。
- **掩码与对齐**：整段归约前按有效长度设置掩码；折叠步长按 vector lane 宽度对齐。
- **标量同步**：整段归约后取标量前，须保证向量→标量的事件同步。
- **数值一致性**：树形折叠的求和顺序与朴素顺序求和不同，浮点结果可能有尾位差异——归一化/量化场景通常在容差内，但对「逐位精确求和」敏感的算子需评估。

## 4. 泛化条件

- 算子含 per-row 归约（沿尾维求和/求最大），且归约结果以标量形式回用（如归一化系数、量化缩放）。
- 归约长度大于一个 vector lane 宽度（否则折叠无意义，直接整段归约）。
- 非适用：沿非尾维归约、或归约结果需保留为向量（非标量）的场景。

## 5. 实施步骤

1. 对每行待归约数据，取有效长度 n；若 n 大于单 vector lane 宽度 W：
   - 找不超过 n 的最大 2 的幂 b；把尾部 (n−b) 个元素折叠到前 b 个（向量加/取大）。
   - 对 b 反复折半折叠，直到剩余 ≤ W。
2. 按剩余长度设置归约掩码，发一次整段归约指令，产出标量到片上标量位。
3. 向量→标量事件同步后取标量，用于本行归一化/量化。
4. 确认折叠 buffer 归约后不再被使用（否则先备份）。

伪代码（语义化）：

```text
for each row:
    n = effective_len(row)
    if n > lane_width:
        fold_tail_into_body(row, n)        # 向量加/取大
        halve_fold_until_le_lane_width(row)
    set_mask(remaining_len)
    scalar = whole_reduce(row)             # 单次整段归约
    sync_vector_to_scalar()
    use(scalar)
```

## 6. LLM 前置问题

- 归约沿哪个维度？结果以标量还是向量回用？
- 归约长度相对 vector lane 宽度的大小（决定折叠层数）？
- 待归约 buffer 在归约后是否仍被使用（决定是否需备份）？
- 算子对求和顺序的数值敏感性（决定树形折叠是否可接受）？

## 7. 验收标准

- 编译通过；全量精度用例通过（归约长度对齐与非对齐均覆盖）。
- 性能多次取样相对通用归约基线正向；归约调用频次越高、单次归约长度越大，收益越明显。
- 掩码按有效长度设置，非对齐尾段有专门分支。

## 检索卡（短卡）

动作：将逐行的通用归约接口加标量回读链改为树形折叠向量化
适用：沿尾维逐行求和或求最大，标量结果被回用，且长度大于一个 vector lane
限制：折叠与整段归约须遵循行有效长度；非对齐尾段走余数分支
范围：per-token 归一化或量化算子的逐行尾维归约
检索词：per-row 归约、尾维、树形折叠、vector lane、标量回读
机会：每行频繁调用带临时 buffer 和多 rep 的通用归约，随后立即取标量
