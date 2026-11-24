---
type: Optimization
title: T1 末轴串行扫描的行并行 lane 打包（一行一 lane + per-lane carry，无跨 lane 通信）
description: 把 T1 串行 per-element VF 扫描改为行并行 lane 打包：K 行重排进向量寄存器，per-lane Compare/Select 更新 carry。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/row-per-lane-packed-scan.md
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
      "Reg::Gather/Scatter 为按 lane 串行微码：per-step 成本约 21-24 cyc/活跃 lane（4B dtype）、约 42-46 cyc（2B dtype），与 K 无关——收益上限由该微码地板决定，『每元素指令数 ÷ K』的指令计数模型不成立，预期收益须按 per-step 微码成本折算",
      "idx64 写回 tile 的行距须 32B 对齐（MTE3 UB 源对齐契约，否则设备异常）",
      "dtype 门控必须在编译期完成；未门控 dtype 的旧核逐字保留，共享模板文件时控制 case 应字节级不动"
    ],
    "excluded_conditions": [
      "2B dtype（fp16/bf16）直接套单位置形态：B16 粒度 Gather/Scatter 地板导致回归，须改用 u32 双位置打包形态（见 subword-u32-pair-packed-scan）",
      "int32 在未建立机理判据（该 shape 串行基线是否已低于 4B 行并 Gather/Scatter 吞吐地板）前保守不启用，不得为单 case 收益猜测门控",
      "独立行数不足以填满 lane 的退化 shape（outerRowCount 小、超长 scanLen）应走行拆分/跨核机制（见 scan-row-split-two-level-cross-core）而非本机制"
    ],
    "required_conditions": [
      "T1 模式（dimNorm == rank-1）串行分支，独立行数足以填满向量 lane（行组重排后 K*dt >= 32B）",
      "比较/选择语义可逐元素在 lane 内封闭表达（LE tie-break 与 fp32 NaN sticky 与串行核同构，无跨 lane 归约）",
      "host tiling 可表达行组重排与 K×T tile 推导（scan-split 判定不变）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "case": "fp32 T1 last-axis 行并子集（level2/cummin_2/6/9/12/16）",
      "note": "control case 0.986-1.001；correctness 20/20。硬件行为证据：Gather/Scatter 按 lane 串行微码 per-step 约 21-24 cyc/活跃 lane（dt=4）、约 42-46 cyc（dt=2）且与 K 无关，证伪『每元素指令数 ~11/K』假设（route 实测 1.20x << 预期 2.5x）。int32 无机理判据不加子门控（4B 行并路径存在 Gather/Scatter 吞吐地板），放弃短 5D int32 case 的单点收益；always-on 版本留存 rounds/001/kernel-always-on.backup.h。",
      "operator_class": "reduction",
      "round": 1,
      "run_id": "<run-id>",
      "speedup": "incremental 1.1276x、route subset 1.2021x、fp32 目标 case 1.433-2.045x；always-on 未门控形态 1.0849x 且 5 case 0.874-0.937x 回归 -> float32-only 门控后 1.1276x 零回归",
      "status": "accepted"
    },
    {
      "comparison_sha256": "2286970d4252313bece1bb159a40fb51171610badc2e64ef7b7ae0dfb8a8ba30",
      "decision_sha256": "ce28d9da0594dcee6c6bddf014b2851683a97c5815954626e3546b4f62d3919f",
      "operator_class": "reduction",
      "performance_sha256": "2f803d18c33ff1d0f1d1e5082aaa9cc4daeb5f806a0ae354f31fb79e07f7c92d",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "0938c49f508cd1d645eb95d89d83d52885bc9aa9ccdf256eb01609bf3d05c0a8",
      "verify_sha256": "b525cedde7c2e5f37f92c7e13e67e741cb56d3360c1011996c333f90e0764fd9"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-serial-scan",
      "per-element-vector-issue",
      "vector-width-unused"
    ],
    "pattern": "row-per-lane-packed-scan",
    "structure": [
      "t1-contiguous-axis-scan",
      "row-group-repack",
      "per-lane-carry",
      "gather-per-step",
      "transposed-full-width-store",
      "int32-argmin-tile-resident",
      "dtype-gated"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-ROW-PER-LANE-PACKED",
  "implementation_steps": [
    "从 tiling 读取行打包参数 K，行组重排使每行组 K*dt >= 32B，推导 K×T tile 布局（scan-split 判定条件不改）",
    "实现 __simd_vf__ 行并核心：per-row 偏移 Gather 索引寄存器，每 step 取 K 行同位置元素",
    "per-lane Compare（fp32 加 NaN 掩码）+ Select 更新 running min/argmin carry，LE tie-break/NaN sticky 逐元素同构保留",
    "值经转置 tile 整宽 store 写出；argmin 驻留 int32 tile，tile 尾单次 Cast 加宽 int64 后写回（行距 32B 对齐）",
    "编译期 dtype 门控（float32 only 起步），旧串行核作为未门控 dtype 的逐字回退；验证控制 case 字节级不动",
    "probe 先做双 case 前缀语义差分（前缀 vs elementwise 是首要风险），再全量 all_cases verify"
  ],
  "intent": "消除 T1 串行快路径的单核吞吐墙：per-element VF 扫描沿单行串行推进，每元素一条 1-lane 向量指令，吞吐恒定、不随独立行数扩展（向量宽度闲置）。",
  "mechanism": "kernel 新增 __simd_vf__ 行并核心，仅接入 Process() 的 scanBlocks==1 串行分支（scan-split/I64 路径原样保留作回退）：构建 per-row 偏移的 Gather 索引寄存器，每 step 取 K 行同位置元素 -> per-lane Compare（fp32 加 NaN 掩码）+ Select 更新 running min/argmin -> 值经转置 tile 整宽 store 写出；argmin 驻留 int32 工作 tile，tile 尾单次 Cast 加宽 int64 写回。host tiling 增加 K 行打包与 K×T tile 推导（行组重排使 K*dt >= 32B），scan-split 判定条件不改；编译期 dtype 门控（float32 only 起步）控制实例化范围。",
  "name": "T1 末轴串行扫描的行并行 lane 打包（一行一 lane + per-lane carry，无跨 lane 通信）",
  "operator_class": "reduction",
  "operator_scope": "末轴连续前缀扫描（dimNorm == rank-1，T1 快路径）且独立行数足以填满向量 lane 的 reduction 算子：单行内沿扫描轴的串行依赖不可消除，但行与行完全独立；基线串行 per-element VF 核（每元素一条 1-lane 向量指令）是主路径",
  "principle": "前缀扫描的串行依赖只在行内（扫描轴方向），行与行完全独立。把 K 个独立行打包进一个向量寄存器的 lane（一行一 lane），每步 Gather 取 K 行同位置元素、per-lane 独立 Compare/Select 更新 carry，一条全宽向量指令同时推进 K 行且无任何跨 lane 通信——串行链长度不变（仍为 scanLen 步），吞吐按 K 扩展。与 Hillis-Steele 扫描树（见 register-carried-scan-tree-vectorization：跨 lane 归并、短/非对齐 int32 回归的负边界）不同，lane=行 的映射不需要跨 lane combine 规则，LE 并列（后出现索引胜）与 fp32 NaN sticky 在 lane 内逐元素与串行核同构，新增正确性面更小。",
  "related_anti_patterns": [],
  "risks": [
    "lane 载体数学错误是首要风险：lane=段内位置 + 广播 carry 计算的是 elementwise min 而非前缀（probe 精度门可捕获，形态为前缀最小值/argmin 停滞在陈旧值）；机制本体必须是 lane=行 + per-lane carry",
    "未门控 dtype 的静默回归：always-on 形态在 2B 与部分 4B 整型 shape 上回归，门控范围应按机理判据逐步放开而非一次全开",
    "按指令计数模型设定 expected_route_speedup 会显著高估收益（Gather/Scatter 微码地板）；验收门应按 per-step 微码成本折算，实测显著低于模型时先怀疑模型而非测量"
  ],
  "slug": "row-per-lane-packed-scan",
  "summary": "把 T1 串行 per-element VF 扫描改为行并行 lane 打包：K 个独立行重排进一个 256B 向量寄存器（一行一 lane），每 step 用 Reg::Gather 按各行偏移取同一步元素，running-min/argmin 成为 per-lane 寄存器 carry，per-lane Compare/Select 逐元素同构保留 LE tie-break 与 fp32 NaN sticky；值走转置 tile 整宽 store，argmin 以 int32 驻留工作 tile、tile 尾单次 Cast 加宽 int64；编译期 dtype 门控（float32 起步）使未验证 dtype 逐字回退旧核，实现零回归接受。",
  "verification": {
    "correctness": [
      "probe 双 case 前缀语义差分（值与 argmin 索引，覆盖 NaN/inf/并列 tie-break）先于全量；全量 all_cases verify 通过",
      "未门控 dtype 的路由字节级不动（共享模板文件时全量验证）",
      "idx64 写回行距 32B 对齐复核（MTE3 对齐契约）"
    ],
    "performance": [
      "incremental total_speedup 达任务阈值且无 case 低于 max_case_regression；目标 route 子集聚合提升",
      "控制 case（其他 route 代表）在噪声带内；门控回退 case 恢复约 1.0x"
    ],
    "rollback_signals": [
      "任一精度失败（前缀语义/tie-break 顺序/NaN 粘性/索引错位）",
      "门控 dtype 外 case 回归超阈值（门控泄漏或共享文件污染）",
      "route 实测收益持续低于按 Gather/Scatter 微码地板折算的预期时，重新评估机制模型而非放宽验收"
    ]
  }
}
-->

# 性能优化策略：T1 末轴串行扫描的行并行 lane 打包（一行一 lane + per-lane carry，无跨 lane 通信）

单一优化点：把 T1 串行 per-element VF 扫描改为行并行 lane 打包：K 个独立行重排进一个 256B 向量寄存器（一行一 lane），每 step 用 Reg::Gather 按各行偏移取同一步元素，running-min/argmin 成为 per-lane 寄存器 carry，per-lane Compare/Select 逐元素同构保留 LE tie-break 与 fp32 NaN sticky；值走转置 tile 整宽 store，argmin 以 int32 驻留工作 tile、tile 尾单次 Cast 加宽 int64；编译期 dtype 门控（float32 起步）使未验证 dtype 逐字回退旧核，实现零回归接受。

## 1. 原理

前缀扫描的串行依赖只在行内（扫描轴方向），行与行完全独立。把 K 个独立行打包进一个向量寄存器的 lane（一行一 lane），每步 Gather 取 K 行同位置元素、per-lane 独立 Compare/Select 更新 carry，一条全宽向量指令同时推进 K 行且无任何跨 lane 通信——串行链长度不变（仍为 scanLen 步），吞吐按 K 扩展。与 Hillis-Steele 扫描树（见 register-carried-scan-tree-vectorization：跨 lane 归并、短/非对齐 int32 回归的负边界）不同，lane=行 的映射不需要跨 lane combine 规则，LE 并列（后出现索引胜）与 fp32 NaN sticky 在 lane 内逐元素与串行核同构，新增正确性面更小。

实现机制：kernel 新增 __simd_vf__ 行并核心，仅接入 Process() 的 scanBlocks==1 串行分支（scan-split/I64 路径原样保留作回退）：构建 per-row 偏移的 Gather 索引寄存器，每 step 取 K 行同位置元素 -> per-lane Compare（fp32 加 NaN 掩码）+ Select 更新 running min/argmin -> 值经转置 tile 整宽 store 写出；argmin 驻留 int32 工作 tile，tile 尾单次 Cast 加宽 int64 写回。host tiling 增加 K 行打包与 K×T tile 推导（行组重排使 K*dt >= 32B），scan-split 判定条件不改；编译期 dtype 门控（float32 only 起步）控制实例化范围。

## 2. 性能问题模式

- 优化目标：消除 T1 串行快路径的单核吞吐墙：per-element VF 扫描沿单行串行推进，每元素一条 1-lane 向量指令，吞吐恒定、不随独立行数扩展（向量宽度闲置）。
- 适用数据流：末轴连续前缀扫描（dimNorm == rank-1，T1 快路径）且独立行数足以填满向量 lane 的 reduction 算子：单行内沿扫描轴的串行依赖不可消除，但行与行完全独立；基线串行 per-element VF 核（每元素一条 1-lane 向量指令）是主路径
- Feature signature：`{"bottleneck": ["scalar-serial-scan", "per-element-vector-issue", "vector-width-unused"], "pattern": "row-per-lane-packed-scan", "structure": ["t1-contiguous-axis-scan", "row-group-repack", "per-lane-carry", "gather-per-step", "transposed-full-width-store", "int32-argmin-tile-resident", "dtype-gated"]}`

## 3. 正确性红线

- lane 载体数学错误是首要风险：lane=段内位置 + 广播 carry 计算的是 elementwise min 而非前缀（probe 精度门可捕获，形态为前缀最小值/argmin 停滞在陈旧值）；机制本体必须是 lane=行 + per-lane carry
- 未门控 dtype 的静默回归：always-on 形态在 2B 与部分 4B 整型 shape 上回归，门控范围应按机理判据逐步放开而非一次全开
- 按指令计数模型设定 expected_route_speedup 会显著高估收益（Gather/Scatter 微码地板）；验收门应按 per-step 微码成本折算，实测显著低于模型时先怀疑模型而非测量

资源与硬件约束：

- Reg::Gather/Scatter 为按 lane 串行微码：per-step 成本约 21-24 cyc/活跃 lane（4B dtype）、约 42-46 cyc（2B dtype），与 K 无关——收益上限由该微码地板决定，『每元素指令数 ÷ K』的指令计数模型不成立，预期收益须按 per-step 微码成本折算
- idx64 写回 tile 的行距须 32B 对齐（MTE3 UB 源对齐契约，否则设备异常）
- dtype 门控必须在编译期完成；未门控 dtype 的旧核逐字保留，共享模板文件时控制 case 应字节级不动

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- T1 模式（dimNorm == rank-1）串行分支，独立行数足以填满向量 lane（行组重排后 K*dt >= 32B）
- 比较/选择语义可逐元素在 lane 内封闭表达（LE tie-break 与 fp32 NaN sticky 与串行核同构，无跨 lane 归约）
- host tiling 可表达行组重排与 K×T tile 推导（scan-split 判定不变）

不适用：

- 2B dtype（fp16/bf16）直接套单位置形态：B16 粒度 Gather/Scatter 地板导致回归，须改用 u32 双位置打包形态（见 subword-u32-pair-packed-scan）
- int32 在未建立机理判据（该 shape 串行基线是否已低于 4B 行并 Gather/Scatter 吞吐地板）前保守不启用，不得为单 case 收益猜测门控
- 独立行数不足以填满 lane 的退化 shape（outerRowCount 小、超长 scanLen）应走行拆分/跨核机制（见 scan-row-split-two-level-cross-core）而非本机制

## 5. 实施步骤

1. 从 tiling 读取行打包参数 K，行组重排使每行组 K*dt >= 32B，推导 K×T tile 布局（scan-split 判定条件不改）
2. 实现 __simd_vf__ 行并核心：per-row 偏移 Gather 索引寄存器，每 step 取 K 行同位置元素
3. per-lane Compare（fp32 加 NaN 掩码）+ Select 更新 running min/argmin carry，LE tie-break/NaN sticky 逐元素同构保留
4. 值经转置 tile 整宽 store 写出；argmin 驻留 int32 tile，tile 尾单次 Cast 加宽 int64 后写回（行距 32B 对齐）
5. 编译期 dtype 门控（float32 only 起步），旧串行核作为未门控 dtype 的逐字回退；验证控制 case 字节级不动
6. probe 先做双 case 前缀语义差分（前缀 vs elementwise 是首要风险），再全量 all_cases verify

## 6. LLM 前置问题

- 目标实现是否满足：T1 模式（dimNorm == rank-1）串行分支，独立行数足以填满向量 lane（行组重排后 K*dt >= 32B）？
- 目标实现是否满足：比较/选择语义可逐元素在 lane 内封闭表达（LE tie-break 与 fp32 NaN sticky 与串行核同构，无跨 lane 归约）？
- 目标实现是否满足：host tiling 可表达行组重排与 K×T tile 推导（scan-split 判定不变）？
- 是否命中排除条件：2B dtype（fp16/bf16）直接套单位置形态：B16 粒度 Gather/Scatter 地板导致回归，须改用 u32 双位置打包形态（见 subword-u32-pair-packed-scan）？

## 7. 验收标准

正确性：

- probe 双 case 前缀语义差分（值与 argmin 索引，覆盖 NaN/inf/并列 tie-break）先于全量；全量 all_cases verify 通过
- 未门控 dtype 的路由字节级不动（共享模板文件时全量验证）
- idx64 写回行距 32B 对齐复核（MTE3 对齐契约）

性能：

- incremental total_speedup 达任务阈值且无 case 低于 max_case_regression；目标 route 子集聚合提升
- 控制 case（其他 route 代表）在噪声带内；门控回退 case 恢复约 1.0x

回滚信号：

- 任一精度失败（前缀语义/tie-break 顺序/NaN 粘性/索引错位）
- 门控 dtype 外 case 回归超阈值（门控泄漏或共享文件污染）
- route 实测收益持续低于按 Gather/Scatter 微码地板折算的预期时，重新评估机制模型而非放宽验收

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- cummin-20260831_113913-196633（round=1, status=accepted, case=fp32 T1 last-axis 行并子集（level2/cummin_2/6/9/12/16）, speedup=incremental 1.1276x、route subset 1.2021x、fp32 目标 case 1.433-2.045x；always-on 未门控形态 1.0849x 且 5 case 0.874-0.937x 回归 -> float32-only 门控后 1.1276x 零回归）
- cummin-20260831_113913-196633（round=1, status=accepted）

## 检索卡（短卡）

动作：把 T1 串行 per-element VF 扫描改为行并行 lane 打包：K 行重排进向量寄存器，per-lane Compare/Select 更新 carry。
适用：T1（dimNorm==rank-1）串行分支且独立行数足以填满 lane（K*dt>=32B）。
限制：lane 载体必须是 lane=行 + per-lane carry；idx64 写回行距须 32B 对齐；dtype 门控须编译期完成。
范围：reduction 末轴串行前缀扫描的 T1 快路径。
检索词：__simd_vf__、Reg::Gather、per-lane carry、K×T tile、LE tie-break
机会：per-element VF 扫描沿单行串行推进，每元素一条 1-lane 向量指令。
代价：Gather/Scatter 是按 lane 串行微码（约 21-24 cyc/lane），收益受该地板封顶。
