---
type: Optimization
title: 中轴扫描内轴 lane 跨核分配（blockDim 由 outer x lane 任务空间驱动）
description: 将任务空间从仅外轴扩为outer×laneChunk，并以outerCount×numLaneChunks计算总任务数。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/scan-inner-lane-axis-core-distribution.md
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
      "host blockDim 必须与 kernel 实际 per-core task 分区一致（每核覆盖不相交、完整的任务区间），且所有 lane 切片恰好覆盖一次",
      "scalar taskIdx/numLaneChunks 除法需保证 numLaneChunks==0 不可达（空输入守卫）",
      "uint32 截断 taskBase 只在远超 GM 容量时可达（镜像原有 trajBase 行为）"
    ],
    "excluded_conditions": [
      "T1 快路径（dimNorm == rank-1）不经过 DoTilingT2，机制不适用（1D case 13 无 lane 轴）",
      "outerCount >= coreNumAiv 的已饱和 T2 case 无需启用；其无回归（per-core chunk 更均匀但更少）未被本 round 测量证明"
    ],
    "required_conditions": [
      "T2 模式（dimNorm != rank-1），outerCount < coreNumAiv，axisBlockLen >= 2（lane 轴可切分为独立任务）",
      "每个 (trajectory, laneChunk) 是独立前缀扫描任务，带自己的 running-min/argmin carry，沿扫描轴无跨核依赖",
      "CopyInStrided/CopyOutStrided 已按 chunk 计算 laneBase/wc，per-core chunk 区间只改变各核访问的 lane 范围",
      "fp16/bf16/fp32 dtype 均走同一 laneChunkW=32 VF 路径，机制与 dtype 无关"
    ]
  },
  "classification": "lesson",
  "evidence": [
    {
      "comparison_sha256": "8dbabe062f4ae5195b388eaf03c71172ba650e32d5d7f34a849d0b81824ee705",
      "decision_sha256": "2fc7990c15f6f29355eb0490f9b791417f61541132b249256bf7d53bbf42e80b",
      "operator_class": "reduction",
      "performance_sha256": "93c5bc7b23acf585fa3fe10771441d725086db79023e48109c8e9bb985690c67",
      "round": 1,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "486e3441438609fa50ce57d45ebd90756cd4f7e84665de8d5acb28e00c70ddf2",
      "verify_sha256": "44b1f99a337130dac675ccc49e3d285dc56a32e5d5abf686158a3d89317ce53c"
    },
    {
      "case": "5,8,17,19",
      "env": {
        "device": "5",
        "op_name": "Cummin",
        "post_eval_score": 60.87859925160219,
        "pre_eval_score": 57.42744371577807,
        "score_delta": "+3.45"
      },
      "operator_class": "reduction",
      "precision": "20/20 passed",
      "run_id": "<run-id>",
      "speedup": "19.36-54.92x",
      "status": "accepted",
      "task_dir": "cann-bench_rpy/strategies/cummin_opt_20260821"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "core-underutilization",
      "tiling-axis",
      "parallelism-collapse"
    ],
    "pattern": "scan-inner-lane-axis-core-distribution",
    "structure": [
      "t2-strided-mid-axis-scan",
      "lane-slice",
      "task-space-decomposition",
      "per-core-scan-carry"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-LANE-AXIS-CORE-DIST",
  "implementation_steps": [
    "在 DoTilingT2 中把 numLaneChunks=ceil(axisBlockLen/laneChunkW) 计算提前到 blockDim 之前，计算 totalTasks=outerCount*numLaneChunks",
    "blockDim = min(GetCoreNumAiv(), totalTasks)，沿用余数前置 taskPerCore/tailCoreTask/taskStartBase 分组",
    "kernel Process 改为按 blockIdx 解码 per-core task 区间，每个 task 解码 (outerPos, chunk)",
    "tiling 字段 traj* 改名 task*（同类型同位置，保持序列化 struct layout 不变）",
    "验证边界：totalTasks<coreNum（每核一个 task）、axisBlockLen<=32（numLaneChunks=1 等价于仅 trajectory 分布）、不可整除的尾 chunk（wc<laneChunkW）"
  ],
  "intent": "消除 T2 中轴扫描在 outerCount < coreNumAiv 时仅用 1-2 个 AI 核、内轴 lane 从不贡献核数的问题（case 5/8/17/19 冻结基线 Block Num=1/2）",
  "mechanism": "host DoTilingT2 先算 numLaneChunks=ceil(axisBlockLen/laneChunkW)，totalTasks=outerCount*numLaneChunks（uint64），blockDim=min(GetCoreNumAiv(), totalTasks)（空输入守卫为 1）；沿用余数前置分组 taskBase=totalTasks/blockDim、taskPerCore/tailCoreTask/taskStartBase。kernel CumminT2Kernel::Process 按 blockIdx 解码 per-core task 区间（taskStart=blockIdx*taskStartBase+min(blockIdx,tailCoreTask)，taskCount=taskPerCore 或 taskPerCore-1），每个 task 解码 (outerPos=taskIdx/numLaneChunks, chunk=taskIdx%numLaneChunks) 并做完整扫描轴的 CopyInStrided/Compute/CopyOutStrided；tiling 字段 traj* 改名 task*（同类型同位置，序列化 struct layout 不变）；不增加跨核通信，carry 语义不变。",
  "name": "中轴扫描内轴 lane 跨核分配（blockDim 由 outer x lane 任务空间驱动）",
  "operator_class": "reduction",
  "operator_scope": "跨 stride 中轴扫描（dimNorm != rank-1）的 reduction 类算子（cummin/cumsum 等）T2 路径：每个 (trajectory, laneChunk) 是带独立 running-min/argmin carry 的独立前缀扫描任务，outerCount < coreNumAiv 且 axisBlockLen >= 2 时可把 lane 轴切分到多核",
  "origin": {
    "candidate_id": "CUM-2",
    "evidence_status": "tested-with-boundary",
    "note": "Derived from baseline/reference-extraction/strategy_candidates.json CUM-2 and the reference reserved-rows lane-slice core distribution (reference-source/op_host/arch35/cummin_tiling.cpp:213-249, op_kernel/arch35/cummin.h:158-169, 296-357). Round 1 tested and rolled back (patch.diff, rollback.json); correctness 4/4 with 14-29x measured gains and 0 target regressions, rejected solely on evidence-chain grounds (frozen baseline case 8 instability + round case 8 relative_mad 0.0234>0.02). Not a strategy failure; boundary is the acceptance environment.",
    "reference_label": "mainline-cann",
    "type": "reference_diff"
  },
  "principle": "并行度由 tiling 选择的逻辑任务数决定，不必受限于单一外轴；前缀扫描沿扫描轴的 lane 相互独立（各自携带 running-min/argmin carry、无跨核依赖），把 outer x laneChunk 任务并入任务空间可在不改变每核扫描语义（32-lane VF compute body、GM 地址、carry 语义）的情况下占满核心，延迟按活动核数因子降低。",
  "related_anti_patterns": [
    "tile-ub-budget-mismatch"
  ],
  "risks": [
    "任务重分配改变每个核访问的 lane 切片；已饱和 T2 case 10/14 仍 64 核但 per-core chunk 更均匀，回归未被本 round 证明",
    "case 8 round 测量相对不稳定（relative_mad 0.0234 > 0.02），叠加冻结基线 case 8 不稳定（cv 0.0426）使形式 compare gate 无法通过——正式接受需稳定基线重冻结 + case 8 稳定样本",
    "division by numLaneChunks 必须由空输入守卫保护"
  ],
  "slug": "scan-inner-lane-axis-core-distribution",
  "summary": "把 T2 中轴扫描的 blockDim 从 min(coreNum, outerCount) 改为由 outerCount x numLaneChunks 任务空间驱动，使 outerCount 很小时内轴 lane（axisBlockLen 可达 16384）也贡献核数；每核解码 (outerPos, chunk) 任务、对完整扫描轴扫描自己的 lane 切片。round 1 实测目标 case 14-29x、Block Num 从 1-2 升到多核，4/4 verify 通过、0 目标回归，仅因冻结基线 case 8 不稳定 + round case 8 轻微不稳定被形式 gate 拒绝——边界是验收环境而非机制（详见 verification）。",
  "verification": {
    "correctness": [
      "round 1 verify ok=true，4/4 目标 case（5,8,17,19）通过；kernel_hash db14f7944ca41081 与 build.json kernel_after 一致，git_diff_sha256 4a4eea5927f279d4",
      "每个 lane 切片恰好覆盖一次；values/indices 与冻结 golden 一致（LE 并列、NaN 语义不变）"
    ],
    "performance": [
      "目标 case median（冻结基线 -> round 实测）：case 5 197282.7 -> 6870.1us（28.72x）、case 8 857.5 -> 37.7us（22.74x）、case 17 2558.5 -> 88.9us（28.77x）、case 19 888.8 -> 61.3us（14.49x），comparison 4/4 improved、0 regressed",
      "case 5/17/19 round 样本稳定（relative_mad <= 0.0116）；case 8 relative_mad 0.0234 > 0.02 不稳定",
      "形式 comparison ok=false（input_errors：冻结基线 case 8 + round case 8 不稳定），收益为指示性而非正式接受；机制按 swi_glu 先例记录为 lesson"
    ],
    "rollback_signals": [
      "任一 case 正确性失败（dropped/doubled lane slice 导致的 indices/values 错位）",
      "case 5/8/17/19 Block Num 未上升或 median 未显著低于冻结基线（证伪核数不足假设）",
      "已饱和 T2 case 10/14 回归超噪声"
    ]
  }
}
-->

# 性能优化策略：中轴扫描内轴 lane 跨核分配（blockDim 由 outer x lane 任务空间驱动）

单一优化点：把 T2 中轴扫描的 blockDim 从 min(coreNum, outerCount) 改为由 outerCount x numLaneChunks 任务空间驱动，使 outerCount 很小时内轴 lane（axisBlockLen 可达 16384）也贡献核数；每核解码 (outerPos, chunk) 任务、对完整扫描轴扫描自己的 lane 切片。round 1 实测目标 case 14-29x、Block Num 从 1-2 升到多核，4/4 verify 通过、0 目标回归，仅因冻结基线 case 8 不稳定 + round case 8 轻微不稳定被形式 gate 拒绝——边界是验收环境而非机制（详见 verification）。

## 1. 原理

并行度由 tiling 选择的逻辑任务数决定，不必受限于单一外轴；前缀扫描沿扫描轴的 lane 相互独立（各自携带 running-min/argmin carry、无跨核依赖），把 outer x laneChunk 任务并入任务空间可在不改变每核扫描语义（32-lane VF compute body、GM 地址、carry 语义）的情况下占满核心，延迟按活动核数因子降低。

实现机制：host DoTilingT2 先算 numLaneChunks=ceil(axisBlockLen/laneChunkW)，totalTasks=outerCount*numLaneChunks（uint64），blockDim=min(GetCoreNumAiv(), totalTasks)（空输入守卫为 1）；沿用余数前置分组 taskBase=totalTasks/blockDim、taskPerCore/tailCoreTask/taskStartBase。kernel CumminT2Kernel::Process 按 blockIdx 解码 per-core task 区间（taskStart=blockIdx*taskStartBase+min(blockIdx,tailCoreTask)，taskCount=taskPerCore 或 taskPerCore-1），每个 task 解码 (outerPos=taskIdx/numLaneChunks, chunk=taskIdx%numLaneChunks) 并做完整扫描轴的 CopyInStrided/Compute/CopyOutStrided；tiling 字段 traj* 改名 task*（同类型同位置，序列化 struct layout 不变）；不增加跨核通信，carry 语义不变。

## 2. 性能问题模式

- 优化目标：消除 T2 中轴扫描在 outerCount < coreNumAiv 时仅用 1-2 个 AI 核、内轴 lane 从不贡献核数的问题（case 5/8/17/19 冻结基线 Block Num=1/2）
- 适用数据流：跨 stride 中轴扫描（dimNorm != rank-1）的 reduction 类算子（cummin/cumsum 等）T2 路径：每个 (trajectory, laneChunk) 是带独立 running-min/argmin carry 的独立前缀扫描任务，outerCount < coreNumAiv 且 axisBlockLen >= 2 时可把 lane 轴切分到多核
- Feature signature：`{"bottleneck": ["core-underutilization", "tiling-axis", "parallelism-collapse"], "pattern": "scan-inner-lane-axis-core-distribution", "structure": ["t2-strided-mid-axis-scan", "lane-slice", "task-space-decomposition", "per-core-scan-carry"]}`

## 3. 正确性红线

- 任务重分配改变每个核访问的 lane 切片；已饱和 T2 case 10/14 仍 64 核但 per-core chunk 更均匀，回归未被本 round 证明
- case 8 round 测量相对不稳定（relative_mad 0.0234 > 0.02），叠加冻结基线 case 8 不稳定（cv 0.0426）使形式 compare gate 无法通过——正式接受需稳定基线重冻结 + case 8 稳定样本
- division by numLaneChunks 必须由空输入守卫保护

资源与硬件约束：

- host blockDim 必须与 kernel 实际 per-core task 分区一致（每核覆盖不相交、完整的任务区间），且所有 lane 切片恰好覆盖一次
- scalar taskIdx/numLaneChunks 除法需保证 numLaneChunks==0 不可达（空输入守卫）
- uint32 截断 taskBase 只在远超 GM 容量时可达（镜像原有 trajBase 行为）

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- T2 模式（dimNorm != rank-1），outerCount < coreNumAiv，axisBlockLen >= 2（lane 轴可切分为独立任务）
- 每个 (trajectory, laneChunk) 是独立前缀扫描任务，带自己的 running-min/argmin carry，沿扫描轴无跨核依赖
- CopyInStrided/CopyOutStrided 已按 chunk 计算 laneBase/wc，per-core chunk 区间只改变各核访问的 lane 范围
- fp16/bf16/fp32 dtype 均走同一 laneChunkW=32 VF 路径，机制与 dtype 无关

不适用：

- T1 快路径（dimNorm == rank-1）不经过 DoTilingT2，机制不适用（1D case 13 无 lane 轴）
- outerCount >= coreNumAiv 的已饱和 T2 case 无需启用；其无回归（per-core chunk 更均匀但更少）未被本 round 测量证明

## 5. 实施步骤

1. 在 DoTilingT2 中把 numLaneChunks=ceil(axisBlockLen/laneChunkW) 计算提前到 blockDim 之前，计算 totalTasks=outerCount*numLaneChunks
2. blockDim = min(GetCoreNumAiv(), totalTasks)，沿用余数前置 taskPerCore/tailCoreTask/taskStartBase 分组
3. kernel Process 改为按 blockIdx 解码 per-core task 区间，每个 task 解码 (outerPos, chunk)
4. tiling 字段 traj* 改名 task*（同类型同位置，保持序列化 struct layout 不变）
5. 验证边界：totalTasks<coreNum（每核一个 task）、axisBlockLen<=32（numLaneChunks=1 等价于仅 trajectory 分布）、不可整除的尾 chunk（wc<laneChunkW）

## 6. LLM 前置问题

- 目标实现是否满足：T2 模式（dimNorm != rank-1），outerCount < coreNumAiv，axisBlockLen >= 2（lane 轴可切分为独立任务）？
- 目标实现是否满足：每个 (trajectory, laneChunk) 是独立前缀扫描任务，带自己的 running-min/argmin carry，沿扫描轴无跨核依赖？
- 目标实现是否满足：CopyInStrided/CopyOutStrided 已按 chunk 计算 laneBase/wc，per-core chunk 区间只改变各核访问的 lane 范围？
- 是否命中排除条件：T1 快路径（dimNorm == rank-1）不经过 DoTilingT2，机制不适用（1D case 13 无 lane 轴）？

## 7. 验收标准

正确性：

- round 1 verify ok=true，4/4 目标 case（5,8,17,19）通过；kernel_hash db14f7944ca41081 与 build.json kernel_after 一致，git_diff_sha256 4a4eea5927f279d4
- 每个 lane 切片恰好覆盖一次；values/indices 与冻结 golden 一致（LE 并列、NaN 语义不变）

性能：

- 目标 case median（冻结基线 -> round 实测）：case 5 197282.7 -> 6870.1us（28.72x）、case 8 857.5 -> 37.7us（22.74x）、case 17 2558.5 -> 88.9us（28.77x）、case 19 888.8 -> 61.3us（14.49x），comparison 4/4 improved、0 regressed
- case 5/17/19 round 样本稳定（relative_mad <= 0.0116）；case 8 relative_mad 0.0234 > 0.02 不稳定
- 形式 comparison ok=false（input_errors：冻结基线 case 8 + round case 8 不稳定），收益为指示性而非正式接受；机制按 swi_glu 先例记录为 lesson

回滚信号：

- 任一 case 正确性失败（dropped/doubled lane slice 导致的 indices/values 错位）
- case 5/8/17/19 Block Num 未上升或 median 未显著低于冻结基线（证伪核数不足假设）
- 已饱和 T2 case 10/14 回归超噪声

## 8. 分类与证据

- Classification：`lesson`
- Generality：`op_class`
- Related anti-patterns：tile-ub-budget-mismatch

- cummin-20260823_213117-d2da41（round=1, status=rejected）
- cummin-20260821（status=accepted, case=5,8,17,19, speedup=19.36-54.92x）

## 检索卡（短卡）

动作：将任务空间从仅外轴扩为outer×laneChunk，并以outerCount×numLaneChunks计算总任务数。
适用：T2中轴模式，outerCount小于coreNumAiv，且axisBlockLen至少为2。
限制：host blockDim须匹配kernel分区；lane切片必须完整、不重叠，并保持对齐和尾块处理。
范围：scan-reduce的T2中轴扫描任务分配。
检索词：T2、中轴扫描、laneChunk、totalTasks、running-min/argmin carry。
机会：outerCount不足核心数，且独立内轴lane尚未参与切核。
代价：任务重分配还需核对已充分并行路径的行为。
