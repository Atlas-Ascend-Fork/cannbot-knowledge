---
type: Optimization
title: 逐 batch 串行 VEC 归一化算子的 elementwise batch-per-lane 打包 + batch-column MTE3
description: 把 G 个 batch 的 (i,j) 元素打包进一条 64-lane 指令，MTE 改为每 group 一组 batch-column 描述符。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/elementwise-batch-per-lane-multibatch-norm.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "DataCopyPad blockLen=4B/blockCount=G 的 element 描述符数量与 n×n 成正比，n 大时描述符开销增长（R2 曾见 MTE3 描述符成为新瓶颈，R3 用 batch-column 描述符缓解）",
      "组合 UB 槽位需按 n×n×G×32B+guard 预留",
      "必须保留逐 batch 回退路径（resident4/generic VF）并逐字保留",
      "正确性按 bitwise CopyIn/CopyOut round-trip + 严格 eps gates 验收，覆盖 0/-0/±inf/nan/subnormal"
    ],
    "excluded_conditions": [
      "MTE/launch/scalar 主导而非 VEC 主导时不预期收益",
      "n 大（矩阵驻留不了寄存器，n>8）或迭代间需全局可见时不适用",
      "存在跨 batch 数据依赖或动态形状无法路由时不适用"
    ],
    "required_conditions": [
      "AIV-VEC bound 且逐 batch 串行（lane 利用率低）",
      "batch 数 ≥8 且 n=hcMult 固定（4 或扩展到 2/3/6/8），n×n 矩阵可整体驻留寄存器",
      "行/列归一化可拆成逐位置 elementwise 序列（softmax 行归一化 + 列归一化），无跨 batch 数据依赖",
      "目标工具链无可用 block-reduce/broadcast 原语时仍可用 elementwise 路径（规避工具链边界）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "29c76b7d95cdda81a87543ed80dfaf9881f22b4c3f5250bfd825404b0022a3a3",
      "decision_sha256": "d5955a0c136cb65b3f4f48a8524ceb8ed4f3d9b40ad65be0b15548b4256722ba",
      "operator_class": "vv-fusion",
      "performance_sha256": "ec6210fe2dbe61e3bb9aa6f61d64224c802f7441d5a647a9ba1a9bec14122845",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "33f0504508be8913232dcbfb28e9ca124e6a2aca57f45364b07de6fa0b62936d",
      "verify_sha256": "7b7dba4092e0d973e25bff26b4bceef6ed2144af536d157f5515b3b3f97029e2"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "low-lane-utilization",
      "per-batch-serial",
      "mte3-element-scatter"
    ],
    "dtypes": [
      "fp32"
    ],
    "hardware": [
      "ascend950",
      "dav_3510"
    ],
    "pattern": "elementwise-batch-per-lane-multibatch-norm",
    "structure": [
      "multi-batch-normalization",
      "iterative-row-col-norm",
      "element-major-transpose"
    ]
  },
  "generality": "op_class",
  "id": "VEC-MULTIBATCH-ELEMENTWISE-LANE-PACKING",
  "implementation_steps": [
    "先 probe 验证 DataCopyPad element-major 转置 + elementwise 归约的正确性（bitwise A/B）",
    "实现 batch-per-lane VF（具名位置寄存器、elementwise reductions）",
    "CopyIn/CopyOut 用 batch-column 描述符；Init 预留 group 槽位",
    "保留回退路径，全量 correctness + 官方路径 spot check 验收"
  ],
  "intent": "消除逐 batch 串行 VF 的低 lane 利用率（n=4 只占 4/64 lanes 或逐 batch 发射）与每 batch 一条 MTE3 element-gather/scatter 描述符的搬运瓶颈。",
  "mechanism": "host tiling 保持原逻辑（本工作流 host 改动不生效，策略必须 kernel-only）；Init() 按 n×n×G×32B+guard 预留 group 槽位；CopyIn() 对每 group 发 n×n 个 2D DataCopyPad 描述符（blockLen=4B、blockCount=G、dstStride=0）把 G 个 batch 的元素按 element-major 布局搬进 UB；Compute() 对 hcMult==4 且 batchCount_>=8 走 batch-per-lane VF（16 个具名位置寄存器、elementwise reductions、byte-identical per-batch 值序列）；CopyOut() 发反向 element-scatter 描述符；保留 resident4/generic 逐 batch VF 作为回退。",
  "name": "逐 batch 串行 VEC 归一化算子的 elementwise batch-per-lane 打包 + batch-column MTE3",
  "operator_class": "vv-fusion",
  "operator_scope": "AIV-VEC bound 的逐 batch 串行迭代归一化算子（multi-batch normalization，如 mhc_sinkhorn：每个 batch 一个 n×n 矩阵，迭代做行/列 softmax 归一化），batch 数大、n=hcMult∈{2,3,4,6,8} 且矩阵可整体驻留向量寄存器",
  "principle": "VEC-bound 下指令发射次数由 batch 数 × 每 batch 位置数决定；把 G 个 batch 的同一位置元素放进一条 64-lane 指令，并把 MTE 从每 batch 一条 element 描述符合并为每 group 一组 batch-column 描述符（blockLen=4B、blockCount=G），同时压缩 VEC 指令数与 MTE 描述符数。元素按 element-major 排列，归约是逐位置 elementwise 操作，因此不依赖目标工具链上不可用的 block-reduce/broadcast/gather 原语。",
  "related_anti_patterns": [],
  "risks": [
    "element-major 转置描述符参数错导致元素错位（bitwise 差分验收拦截）",
    "MTE3 描述符数量增长转移瓶颈（batch-column 描述符缓解）",
    "工具链 block-reduce/broadcast 不可用时不得走 MicroAPI gather 路径（NEG-MHC-BATCH-LANE-PACKING 边界）"
  ],
  "slug": "elementwise-batch-per-lane-multibatch-norm",
  "summary": "把 G 个独立 batch 的 n×n 元素打包进同一条 64-lane 向量指令：DataCopyPad blockLen=4B 的 element-major 转置描述符把 G 个 batch 的同一 (i,j) 位置元素 gather 进一条指令，所有行/列归约都用 elementwise RegBase 操作（Max/Add/Div/Exp/Adds），无 block-reduce/broadcast/gather。R3 首次接受：11 个 target case 提升 1.57-6.14x，incremental total_speedup 2.2333，case6 官方路径可复现（claimed 41.9 vs official 41.94us）；MTE3 element-scatter 瓶颈被 batch-column 描述符消除（aiv_mte3 126.9->7.6us，aiv_mte2 53.9->7.3us），kernel 转为 VEC-bound（aiv_vec ~39us）。后续 R4/R5 将其泛化到 n=2/3 与 n=6/8 路由（见 variant 卡）。",
  "verification": {
    "correctness": [
      "R3 verify 20/20 correctness_pass（严格 eps gates 16/17/19/20 + bitwise CopyIn/CopyOut round-trip case 4/6/16）",
      "R4/R5 对 n=2/3/6 的 bitwise round-trip（0/-0/±inf/nan/subnormal/min-normal/max-finite）"
    ],
    "performance": [
      "R3 incremental total_speedup 2.2333（11 target case 1.57-6.14x）",
      "case6 official 复现 41.9us vs claimed 41.94us（ratio 0.9989, reproducible）",
      "case6 aiv_mte3 126.9->7.6us、aiv_mte2 53.9->7.3us、aiv_vec ~39us（VEC-bound 达成）",
      "R5 cumulative total_speedup 2.6459"
    ],
    "rollback_signals": [
      "bitwise A/B 差分失败",
      "描述符参数导致元素错位或 MTE3 成为新瓶颈",
      "回退路径 correctness 失败"
    ]
  }
}
-->

# 性能优化策略：逐 batch 串行 VEC 归一化算子的 elementwise batch-per-lane 打包 + batch-column MTE3

单一优化点：把 G 个独立 batch 的 n×n 元素打包进同一条 64-lane 向量指令：DataCopyPad blockLen=4B 的 element-major 转置描述符把 G 个 batch 的同一 (i,j) 位置元素 gather 进一条指令，所有行/列归约都用 elementwise RegBase 操作（Max/Add/Div/Exp/Adds），无 block-reduce/broadcast/gather。R3 首次接受：11 个 target case 提升 1.57-6.14x，incremental total_speedup 2.2333，case6 官方路径可复现（claimed 41.9 vs official 41.94us）；MTE3 element-scatter 瓶颈被 batch-column 描述符消除（aiv_mte3 126.9->7.6us，aiv_mte2 53.9->7.3us），kernel 转为 VEC-bound（aiv_vec ~39us）。后续 R4/R5 将其泛化到 n=2/3 与 n=6/8 路由（见 variant 卡）。

## 1. 原理

VEC-bound 下指令发射次数由 batch 数 × 每 batch 位置数决定；把 G 个 batch 的同一位置元素放进一条 64-lane 指令，并把 MTE 从每 batch 一条 element 描述符合并为每 group 一组 batch-column 描述符（blockLen=4B、blockCount=G），同时压缩 VEC 指令数与 MTE 描述符数。元素按 element-major 排列，归约是逐位置 elementwise 操作，因此不依赖目标工具链上不可用的 block-reduce/broadcast/gather 原语。

实现机制：host tiling 保持原逻辑（本工作流 host 改动不生效，策略必须 kernel-only）；Init() 按 n×n×G×32B+guard 预留 group 槽位；CopyIn() 对每 group 发 n×n 个 2D DataCopyPad 描述符（blockLen=4B、blockCount=G、dstStride=0）把 G 个 batch 的元素按 element-major 布局搬进 UB；Compute() 对 hcMult==4 且 batchCount_>=8 走 batch-per-lane VF（16 个具名位置寄存器、elementwise reductions、byte-identical per-batch 值序列）；CopyOut() 发反向 element-scatter 描述符；保留 resident4/generic 逐 batch VF 作为回退。

## 2. 性能问题模式

- 优化目标：消除逐 batch 串行 VF 的低 lane 利用率（n=4 只占 4/64 lanes 或逐 batch 发射）与每 batch 一条 MTE3 element-gather/scatter 描述符的搬运瓶颈。
- 适用数据流：AIV-VEC bound 的逐 batch 串行迭代归一化算子（multi-batch normalization，如 mhc_sinkhorn：每个 batch 一个 n×n 矩阵，迭代做行/列 softmax 归一化），batch 数大、n=hcMult∈{2,3,4,6,8} 且矩阵可整体驻留向量寄存器
- Feature signature：`{"bottleneck": ["vec-bound", "low-lane-utilization", "per-batch-serial", "mte3-element-scatter"], "dtypes": ["fp32"], "hardware": ["ascend950", "dav_3510"], "pattern": "elementwise-batch-per-lane-multibatch-norm", "structure": ["multi-batch-normalization", "iterative-row-col-norm", "element-major-transpose"]}`

## 3. 正确性红线

- element-major 转置描述符参数错导致元素错位（bitwise 差分验收拦截）
- MTE3 描述符数量增长转移瓶颈（batch-column 描述符缓解）
- 工具链 block-reduce/broadcast 不可用时不得走 MicroAPI gather 路径（NEG-MHC-BATCH-LANE-PACKING 边界）

资源与硬件约束：

- DataCopyPad blockLen=4B/blockCount=G 的 element 描述符数量与 n×n 成正比，n 大时描述符开销增长（R2 曾见 MTE3 描述符成为新瓶颈，R3 用 batch-column 描述符缓解）
- 组合 UB 槽位需按 n×n×G×32B+guard 预留
- 必须保留逐 batch 回退路径（resident4/generic VF）并逐字保留
- 正确性按 bitwise CopyIn/CopyOut round-trip + 严格 eps gates 验收，覆盖 0/-0/±inf/nan/subnormal

## 4. 泛化条件

- 策略作用域：op_class：vv-fusion

适用：

- AIV-VEC bound 且逐 batch 串行（lane 利用率低）
- batch 数 ≥8 且 n=hcMult 固定（4 或扩展到 2/3/6/8），n×n 矩阵可整体驻留寄存器
- 行/列归一化可拆成逐位置 elementwise 序列（softmax 行归一化 + 列归一化），无跨 batch 数据依赖
- 目标工具链无可用 block-reduce/broadcast 原语时仍可用 elementwise 路径（规避工具链边界）

不适用：

- MTE/launch/scalar 主导而非 VEC 主导时不预期收益
- n 大（矩阵驻留不了寄存器，n>8）或迭代间需全局可见时不适用
- 存在跨 batch 数据依赖或动态形状无法路由时不适用

## 5. 实施步骤

1. 先 probe 验证 DataCopyPad element-major 转置 + elementwise 归约的正确性（bitwise A/B）
2. 实现 batch-per-lane VF（具名位置寄存器、elementwise reductions）
3. CopyIn/CopyOut 用 batch-column 描述符；Init 预留 group 槽位
4. 保留回退路径，全量 correctness + 官方路径 spot check 验收

## 6. LLM 前置问题

- 目标实现是否满足：AIV-VEC bound 且逐 batch 串行（lane 利用率低）？
- 目标实现是否满足：batch 数 ≥8 且 n=hcMult 固定（4 或扩展到 2/3/6/8），n×n 矩阵可整体驻留寄存器？
- 目标实现是否满足：行/列归一化可拆成逐位置 elementwise 序列（softmax 行归一化 + 列归一化），无跨 batch 数据依赖？
- 是否命中排除条件：MTE/launch/scalar 主导而非 VEC 主导时不预期收益？

## 7. 验收标准

正确性：

- R3 verify 20/20 correctness_pass（严格 eps gates 16/17/19/20 + bitwise CopyIn/CopyOut round-trip case 4/6/16）
- R4/R5 对 n=2/3/6 的 bitwise round-trip（0/-0/±inf/nan/subnormal/min-normal/max-finite）

性能：

- R3 incremental total_speedup 2.2333（11 target case 1.57-6.14x）
- case6 official 复现 41.9us vs claimed 41.94us（ratio 0.9989, reproducible）
- case6 aiv_mte3 126.9->7.6us、aiv_mte2 53.9->7.3us、aiv_vec ~39us（VEC-bound 达成）
- R5 cumulative total_speedup 2.6459

回滚信号：

- bitwise A/B 差分失败
- 描述符参数导致元素错位或 MTE3 成为新瓶颈
- 回退路径 correctness 失败

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- mhc_sinkhorn-20260831_151225-9b5adb（round=3, status=accepted）

## 检索卡（短卡）

动作：把 G 个 batch 的 (i,j) 元素打包进一条 64-lane 指令，MTE 改为每 group 一组 batch-column 描述符
适用：AIV-VEC bound 且逐 batch 串行，batch 数 >=8、n×n 矩阵可驻留寄存器
限制：须逐字保留 resident4/generic VF 回退路径；描述符参数错致元素错位
范围：vv-fusion 的 multi-batch 行/列归一化
检索词：batch-per-lane、DataCopyPad、blockCount=G、element-major 转置、mte3-scatter
机会：逐 batch 串行 VF 低 lane 利用率，每 batch 一条 MTE3 描述符
代价：element 描述符数量与 n×n 成正比，n 大时开销增长
