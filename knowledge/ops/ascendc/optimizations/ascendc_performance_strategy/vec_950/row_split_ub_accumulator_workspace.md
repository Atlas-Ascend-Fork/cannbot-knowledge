---
type: Optimization
title: 输入行切分与片上分段累加
description: 按输入行分核，每核在 UB 中分段累加，再通过私有工作区完成跨核归约。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/row-split-ub-accumulator-workspace.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "tile 行数、输出段宽和累加 dtype 必须共同满足 UB 预算，所有乘加地址计算使用宽整数",
      "私有工作区容量至少覆盖有效核数乘以局部输出大小，且同步前后不得复用未消费的数据"
    ],
    "excluded_conditions": [
      "覆盖写、顺序敏感归约或具有跨输入行依赖的语义不能直接使用两阶段局部归约",
      "输出段极大且索引过于稀疏时，反复清零和写回 UB 段可能高于直接更新成本"
    ],
    "required_conditions": [
      "归约运算允许把输入划分为多个局部结果后再合并，且输入行之间可独立分配给不同核",
      "输出可以按连续段装入 UB，或能够进一步分段处理而不改变索引映射",
      "运行环境能够为每核私有局部结果提供工作区，并支持阶段间的核间同步"
    ]
  },
  "applicability_boundary": "",
  "classification": "validated_strategy",
  "created": "2026-08-21",
  "evidence": [
    {
      "after_us": 607.0,
      "before_us": 61830.0,
      "case": "12",
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/strategies/unsorted_segment_sum_opt_20260820.md",
      "speedup": 101.9,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "gm-rmw",
      "rescan"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "row-split-accumulator-workspace",
    "reduce_mode": "add",
    "structure": [
      "row-split",
      "workspace-reduce",
      "ub-accumulator"
    ]
  },
  "gain": "UnsortedSegmentSum case_12 61830→607us（101.9x）、case_16 119466→1194us（100.0x）。",
  "generality": "op_class",
  "id": "S1",
  "implementation_steps": [
    "将输入行数均匀切分到有效核，保证每个输入元素只被一个核扫描",
    "依据 UB 容量、索引与数据 tile 占用以及累加器宽度求解 tile 行数和输出段宽",
    "批量搬入索引与更新值，在 UB 常驻累加器中完成当前输出段的局部散射归约",
    "把每核局部结果连续写入私有工作区，完成必要的写后可见性处理和核间同步",
    "按输出段切分第二阶段任务，向量化合并各核局部结果并写回最终输出",
    "对资源不足、非结合归约和不支持 dtype 保留原路径"
  ],
  "instance_ids": [
    "S1-GmAddWs"
  ],
  "intent": "消除 scatter-add 的逐行 GM RMW / 每核重扫",
  "mechanism": "行切分 + UB 常驻段累加器：N 行切分到各核 → ids+data 整块连续搬运（每 tile 2 条 MTE2）→ 标量散射累加进 UB segAcc（零 GM RMW、每 tile 仅 2 次 barrier）→ 整块 MTE3 写私有 workspace → SyncAll（KERNEL_TYPE_MIX_AIV_1_0）→ 段片切分向量归约写 y。host 按 UB 预算解 tileN，放不下回退旧路径。",
  "name": "输入行切分与片上分段累加",
  "op": "seed",
  "operator_class": "scatter-update",
  "operator_scope": "存在重复索引或分段归约、输入可按行独立切分的 scatter-update 类数据流",
  "principle": "逐更新访问 GM 会把随机读改写延迟和核间竞争放进最内层循环；让每个核只扫描自己的输入，并将可复用的输出段常驻 UB，可把随机 GM RMW 变为片上累加与少量连续写回。",
  "provenance": {
    "skill": "SKILL.md §7 S1"
  },
  "related_anti_patterns": [
    "per-row-gm-rmw",
    "wrong-axis-per-core-rescan"
  ],
  "related_seed_ids": [],
  "risks": [
    "工作区按核复制可能显著增加 GM 占用，输出很大时必须分段或限制有效核数",
    "浮点局部归约会改变加法顺序，需要依据算子精度契约选择累加 dtype 和容差",
    "遗漏阶段间同步会让第二阶段读取未完成或陈旧的局部结果"
  ],
  "schema_version": 2,
  "slug": "row-split-ub-accumulator-workspace",
  "source": "skill",
  "status": "applied",
  "summary": "按输入行分核，每核在 UB 中分段累加，再通过私有工作区完成跨核归约。",
  "verification": {
    "correctness": [
      "覆盖无重复、高重复、空输入、尾 tile、不同索引 dtype 及不同输出段边界",
      "核对每个输入只参与一次局部归约，工作区布局与第二阶段读取完全一致"
    ],
    "performance": [
      "对比 GM 读写量、输入重扫次数、同步次数和有效核利用率，并在稀疏/密集索引下分别测量",
      "确认工作区清零与第二阶段归约没有成为新的主瓶颈"
    ],
    "rollback_signals": [
      "工作区超预算、同步语义无法保证、精度超限或小规模输入稳定回归时回退"
    ]
  }
}
-->

# 性能优化策略：输入行切分与片上分段累加

单一优化点：按输入行分核，每核在 UB 中分段累加，再通过私有工作区完成跨核归约。

## 1. 原理

逐更新访问 GM 会把随机读改写延迟和核间竞争放进最内层循环；让每个核只扫描自己的输入，并将可复用的输出段常驻 UB，可把随机 GM RMW 变为片上累加与少量连续写回。

实现机制：行切分 + UB 常驻段累加器：N 行切分到各核 → ids+data 整块连续搬运（每 tile 2 条 MTE2）→ 标量散射累加进 UB segAcc（零 GM RMW、每 tile 仅 2 次 barrier）→ 整块 MTE3 写私有 workspace → SyncAll（KERNEL_TYPE_MIX_AIV_1_0）→ 段片切分向量归约写 y。host 按 UB 预算解 tileN，放不下回退旧路径。

## 2. 性能问题模式

- 优化目标：消除 scatter-add 的逐行 GM RMW / 每核重扫
- 适用数据流：存在重复索引或分段归约、输入可按行独立切分的 scatter-update 类数据流
- Feature signature：`{"bottleneck": ["gm-rmw", "rescan"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "row-split-accumulator-workspace", "reduce_mode": "add", "structure": ["row-split", "workspace-reduce", "ub-accumulator"]}`

## 3. 正确性红线

- 工作区按核复制可能显著增加 GM 占用，输出很大时必须分段或限制有效核数
- 浮点局部归约会改变加法顺序，需要依据算子精度契约选择累加 dtype 和容差
- 遗漏阶段间同步会让第二阶段读取未完成或陈旧的局部结果

资源与硬件约束：

- tile 行数、输出段宽和累加 dtype 必须共同满足 UB 预算，所有乘加地址计算使用宽整数
- 私有工作区容量至少覆盖有效核数乘以局部输出大小，且同步前后不得复用未消费的数据

## 4. 泛化条件

- 策略作用域：op_class：scatter-update

适用：

- 归约运算允许把输入划分为多个局部结果后再合并，且输入行之间可独立分配给不同核
- 输出可以按连续段装入 UB，或能够进一步分段处理而不改变索引映射
- 运行环境能够为每核私有局部结果提供工作区，并支持阶段间的核间同步

不适用：

- 覆盖写、顺序敏感归约或具有跨输入行依赖的语义不能直接使用两阶段局部归约
- 输出段极大且索引过于稀疏时，反复清零和写回 UB 段可能高于直接更新成本

## 5. 实施步骤

1. 将输入行数均匀切分到有效核，保证每个输入元素只被一个核扫描
2. 依据 UB 容量、索引与数据 tile 占用以及累加器宽度求解 tile 行数和输出段宽
3. 批量搬入索引与更新值，在 UB 常驻累加器中完成当前输出段的局部散射归约
4. 把每核局部结果连续写入私有工作区，完成必要的写后可见性处理和核间同步
5. 按输出段切分第二阶段任务，向量化合并各核局部结果并写回最终输出
6. 对资源不足、非结合归约和不支持 dtype 保留原路径

## 6. LLM 前置问题

- 目标实现是否满足：归约运算允许把输入划分为多个局部结果后再合并，且输入行之间可独立分配给不同核？
- 目标实现是否满足：输出可以按连续段装入 UB，或能够进一步分段处理而不改变索引映射？
- 目标实现是否满足：运行环境能够为每核私有局部结果提供工作区，并支持阶段间的核间同步？
- 是否命中排除条件：覆盖写、顺序敏感归约或具有跨输入行依赖的语义不能直接使用两阶段局部归约？

## 7. 验收标准

正确性：

- 覆盖无重复、高重复、空输入、尾 tile、不同索引 dtype 及不同输出段边界
- 核对每个输入只参与一次局部归约，工作区布局与第二阶段读取完全一致

性能：

- 对比 GM 读写量、输入重扫次数、同步次数和有效核利用率，并在稀疏/密集索引下分别测量
- 确认工作区清零与第二阶段归约没有成为新的主瓶颈

回滚信号：

- 工作区超预算、同步语义无法保证、精度超限或小规模输入稳定回归时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-row-gm-rmw, wrong-axis-per-core-rescan

- strategy-unsorted-segment-sum-20260820-uss-001（status=accepted, case=12, speedup=101.9）

## 检索卡（短卡）

动作：将输入按行分核扫描，输出连续段驻留UB累加，再以少量连续写回形成可合并的局部结果。
适用：归约可由多个局部结果合并，且输入行可独立分配给不同核。
限制：tile行数、输出段宽和累加dtype须满足UB预算；地址乘加用宽整数；每个输入只由一核扫描。
范围：重复索引或分段归约的scatter-reduce数据流。
检索词：scatter-add、行切分、UB常驻段累加器、局部结果、输出段宽。
机会：最内层仍逐更新执行随机GM读改写，并承受核间竞争或每核重扫。
代价：按核复制增加GM占用；大输出须分段或限核；浮点局部归约改变加法顺序
