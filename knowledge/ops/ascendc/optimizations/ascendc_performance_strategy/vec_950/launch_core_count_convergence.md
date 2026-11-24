---
type: Optimization
title: 启动核数收敛：按工作量反解 launch 几何填平每核固定开销地板
description: 把 launch 核数从满核改为按工作量反解：实测拟合截距+斜率成本律，按每核预算 clamp 出 blockDim，数据面不动。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/launch-core-count-convergence.md
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
      "核数只能沿既有 grid 语义收缩，数据面必须不变：本 run 三个成员均为 host-only 改动——conj 只改 kernel/pybind11.cpp 的 ChooseBlockDim、cudnnrnnflattenweight kernel 源码零改动（只改 host 展开量与 launch 参数）、conj__v2 只改 host sizing 与每核 wave 常量，DataCopyPad 载荷、tile 大小、同步点与逐字节语义全部保持不变",
      "必须保留『大/带宽 case 满核』分支：conj case_02（fp32 262144）保留 blk64 后 9.585→9.658us 属容许持平；若为省固定成本把大 case 也收核，带宽回退会吃掉聚合收益",
      "每核预算常量是 per-op 的，不可跨 op 照搬：conj 是 16KB/核 锚点 clamp(ceil(totalBytes/16384),1,min(coreNum,totalLength))，cudnnrnnflattenweight 是 64KB/核 clamp(ceil(totalBytes/64KB),4,32)，conj__v2 是 pair 预算 cap 32",
      "conj__v2 的每线程 pair 预算必须 dtype-aware：2B dtype=16 pair、4B dtype=8 pair；round_01 统一 16ppt 使 case2（fp32/u64）回归 +7.3%，round_02 按访存宽度细分后消除",
      "blockDim 的上界必须显式 clamp（min(coreNum,totalLength) / MIN_CORES=4 / cap 32），下界不小于 1，且缩核后 host 侧展开的计划量随之下降而不是固定展开满核（cudnnrnnflattenweight 只展开 blockDim 个计划段）"
    ],
    "excluded_conditions": [
      "瓶颈是带宽而非固定成本时不适用：本 run cudnnrnnflattenweight case20（24MB）刻意保持 32 核、收益 1.006x，保留满核是机制的一部分而不是例外",
      "kernel 的分段/数据映射依赖 blockDim 本身（非自定位段）时不适用：此时缩核会改变搬运语义而非只改变调度核数",
      "workload 与核数之间没有可测关系（已有独立 work queue 或动态负载均衡）时没有可收敛的自由变量"
    ],
    "required_conditions": [
      "wall 近似服从『截距 + 斜率×激活核数』的成本律，且对数据量弱敏感：本 run conj champion 在 64 BlockNum 下 21 elems 与 262144 elems 同为 ~9.4us（≈0.11-0.19us/核 + ~2.4us 截距）；conj__v2 拟合 t ≈ 1.15us + 0.177us×blocks；cudnnrnnflattenweight case18（3KB）6.228us vs case11（1.5MB）6.348us 贴同一地板",
      "kernel 对任意 blockDim 天然兼容：conj 由 tiling 的 blockLength/startElem 守卫支持缩核；cudnnrnnflattenweight 的固定步长自定位段地址 = coreIdx*FLATTEN_SEG_BYTES(3080) 与 blockDim 解耦，kernel 源码零改动；conj__v2 的 grid-stride pair 拷贝体与核数无关",
      "存在可实测的拟合点：conj__v2 逐 case 实测 1 核=1.53-1.66us、4-5 核=2.26-2.32us、16 核=3.76us、32 核=5.77-6.87us，先拟合出截距与斜率，才能反解每核预算",
      "小/中 case 在性能 case 构成中占多数，且收核后每核工作量仍落在单 tile 预算内：conj 7/10 个 case 被判定为可收核、cudnnrnnflattenweight 19/20（totalBytes<=1.6MB）收到 4-32 核、conj__v2 中大 case 32→8-16 核"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "conj",
      "operator_class": "elementwise",
      "precision": "10/10 PASS（MERE/MARE 全 0）",
      "run_id": "<run-id>",
      "speedup": 3.095,
      "status": "accepted"
    },
    {
      "operator": "cudnnrnnflattenweight",
      "operator_class": "elementwise",
      "precision": "20/20 PASS bit-exact（threshold=0，逐字节比对含 NaN/Inf/±0）",
      "run_id": "<run-id>",
      "speedup": 1.4373,
      "status": "accepted"
    },
    {
      "operator": "conj__v2",
      "operator_class": "elementwise",
      "precision": "10/10 PASS",
      "run_id": "<run-id>",
      "speedup": 1.1706,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "launch-fixed-cost",
      "core-count-linear-duration-slope",
      "per-core-fixed-scalar-prologue",
      "idle-core-redundant-work"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "launch-core-count-convergence",
    "reduce_mode": "",
    "structure": [
      "intercept-plus-slope-cost-law",
      "workload-aware-grid-sizing",
      "clamped-core-count",
      "kernel-data-path-unchanged",
      "full-core-retention-for-bandwidth-cases"
    ]
  },
  "generality": "op_class",
  "id": "LAUNCH-CORE-COUNT-CONVERGENCE",
  "implementation_steps": [
    "先用逐 case msprof device Task Duration 拟合成本律：以激活核数为自变量、duration 为因变量回归出截距与斜率（conj__v2 得 t ≈ 1.15us + 0.177us×blocks；conj d001 得 ≈0.11-0.19us/核 + ~2.4us 截距），并确认 duration 对数据量弱敏感（21 elems 与 262144 elems 在 64 核下同为 ~9.4us）",
    "在 host 侧（pybind/tiling 计算）用该成本律反解每核预算常量，把 blockDim 从『满核』改成按工作量收敛：conj 用 ChooseBlockDim = clamp(ceil(totalBytes/16384),1,min(coreNum,totalLength))（16KB/核 锚点）；cudnnrnnflattenweight 用 clamp(ceil(totalBytes/64KB),4,32)；conj__v2 用 ceil(nPairs/(wave×ppt)) cap 32 且 ppt 按访存宽度 dtype-aware（2B=16、4B=8）",
    "kernel 侧保持语义不变：只允许改动 host sizing 与随 blockDim 变化的展开量（cudnnrnnflattenweight 只展开/上传 blockDim 个固定步长计划段，segBytes=ceil(totalBytes/blockDim)，seg-split/overlap 语义与设备端逐字节相同，host 断言每核 coreCnt<=128），kernel 源码零改动或只读新常量",
    "为小 N 补上 wave 维度自缩：conj__v2 在 nPairs<=1024 时退化为 1 核并把每核 wave 取 next-pow2(nPairs) 再 clamp 到 [32,1024]（dim3(simtWave_) 替代固定 dim3(1024)），避免小 N 仍发射 1024 线程",
    "以 ABBA 平衡交替配对实测裁决：要求逐 case 无回退、geomean 显著超过 5% 采纳门槛才保留；任一 dtype/shape 组回退即回滚到满核公式（conj d001 预注册的回滚条件即『大 case 带宽回退导致 geomean 上升』）"
  ],
  "intent": "把 launch 的 grid 几何从『有多少核就发多少核』改成按工作量反解核数：在 duration ≈ 截距 + 斜率×激活核数的场景里，闲置核仍在执行每核固定标量 prologue（InitBuffer、事件对、计划预取、解码），核数本身就是可压缩变量。",
  "mechanism": "launch-core-count-convergence：host 用『截距 + 斜率×激活核数』的成本律反解 launch 几何，而不是按 coreNum 满发。conj（target_scope=host-tiling）：ChooseBlockDim(totalLength, elementSize, coreNum) = clamp(ceil(totalBytes/16384), 1, min(coreNum, totalLength))，16KB/核 锚点，kernel 侧零改动（tiling 的 blockLength/startElem 守卫天然支持任意 blockDim）。cudnnrnnflattenweight（target_scope=grid-dispatch）：blockDim = clamp(ceil(totalBytes/64KB), 4, 32)，host 只展开/上传 blockDim 个固定步长计划段（segBytes=ceil(totalBytes/blockDim)，把原先硬编码的 FLATTEN_BLOCK_DIM=32 变成按 workload 反解），kernel 源码零改动——固定步长自定位段地址 = coreIdx*FLATTEN_SEG_BYTES(3080) 与 blockDim 解耦，GetBlockIdx 天然支持任意核数。conj__v2（target_scope=whole-kernel-carrier）：把 SIMT 载体的 sizing 反过来做——nPairs=ceil(N/2)，nPairs<=1024 时 1 核且每核 wave=next-pow2(nPairs) clamp[32,1024]；否则 wave=1024、核数=ceil(nPairs/(1024×ppt)) cap 32，ppt 按访存宽度 dtype-aware（2B=16、4B=8）；kernel 的 grid-stride pair 拷贝体不变。三者的数据面（tile 大小、同步点、载荷字节、逐字节语义）与 kernel 计算路径全部不变，收益全部来自不再发射那些只能执行空段的核。",
  "name": "启动核数收敛：按工作量反解 launch 几何填平每核固定开销地板",
  "operator_class": "elementwise",
  "operator_scope": "一次性（非流式）整块/分段搬运或逐元素映射，host 侧已知总工作量、kernel 对任意 blockDim 有守卫或段地址与 blockDim 解耦的场景；典型如 conj/identity 类逐元素算子、权重与索引展平拷贝类算子、SIMT 逐元素载体（本 run 覆盖 conj host-tiling、cudnnrnnflattenweight grid-dispatch、conj__v2 whole-kernel-carrier 三种作用域）",
  "principle": "当 device Task Duration 由『每次 launch 的固定成本 + 每个被调度核的固定成本』决定而非由数据量决定时，launch 的 grid 几何就是一等优化对象。本族三个成员的共同观测是 duration 与字节数几乎无关、与激活核数近似线性——conj champion 在 64 核下 21 elems 与 262144 elems 同为 ~9.4us（0.11-0.19us/核 + ~2.4us 截距），conj__v2 拟合出 t ≈ 1.15us + 0.177us×blocks（每线程工作量 ×4 仅 +15%），cudnnrnnflattenweight 的 case18（3KB）6.228us 与 case11（1.5MB）6.348us 贴同一地板。斜率项的经济含义是：每个被调度核无论如何都会付一份 InitBuffer、事件对、计划预取与解码；当该核分到的段是空的（cudnnrnnflattenweight 19/20 个 case 的多数核 coreCnt=0，却仍执行 2×InitBuffer 共 67KB UB + 无条件 3080B MTE2 预取 + 等待 + 2 次 GetValue + 分支），这份成本是纯冗余。因此正确的 sizing 不是 max 核数，而是把核数当成由工作量反解的自由变量：用实测的截距+斜率成本律定出每核预算（conj 16KB/核、cudnnrnnflattenweight 64KB/核、conj__v2 每线程 pair 数），blockDim = clamp(ceil(work/perCoreBudget), lower, upper)。这条杠杆与『削减每核固定链本身』（init-buffer-pool-consolidation 一类）正交：后者削的是斜率前的系数，本机制削的是斜率乘的那个核数，两者可叠加。",
  "related_anti_patterns": [
    "simt-direct-gm-size-gate-regression"
  ],
  "risks": [
    "成本律外推可能不成立：拟合点之外（<21 核或 >64 核区间）截距/斜率可能变号，性能门会如实地停在约 1.0x；conj d001 预注册的回滚条件即『核数地板斜率在外推区间不成立，或大 case 带宽回退导致 geomean 上升』",
    "缩核会压低并行度，若每核工作量超出 tile 预算使 loopTimes 上升，每核循环开销会把省下的固定成本重新加回来；cudnnrnnflattenweight 的记录显示 64KB/核 目标偏保守（case7 13 核 1.93x 为最大收益，提示最优 SEG_TARGET 可能更小）",
    "dtype 相关的每线程预算若给成统一常量，会让某种访存宽度的大 case 回归：conj__v2 round_01 统一 16ppt 使 case2（fp32/u64）回归 +7.3%，round_02 按 2B=16/4B=8 细分后消除",
    "『核数敏感分量』是机制的核心假设，若某 SoC 上 launch/调度固定成本与 blockDim 无关，收益趋于 0——cudnnrnnflattenweight 把这个方向同时设计成一次廉价的决定性假设检验（收益 ~0 即 rejected_performance 回滚）",
    "存在未归因的逐 case 偏差：cudnnrnnflattenweight case11 的 blockDim 未变（仍 32 核、plan/segBytes 逐字节不变）却 ABBA 稳定改善 1.26x，机制本身无法解释，只能按未归因项记录（case20 同配置 1.006x 佐证机制对 32 核 case 无直接影响）"
  ],
  "slug": "launch-core-count-convergence",
  "summary": "把 launch 的核数从『满核』改为按 workload 反解：先用 msprof 实测拟合『截距 + 斜率×激活核数』的成本律（conj ~2.4us + 0.11-0.19us/核；conj__v2 1.15us + 0.177us/核；cudnnrnnflattenweight 的 3KB 与 1.5MB case 贴同一 6.2us 地板），再按每核预算定 blockDim（conj 16KB/核 clamp 到 min(coreNum,totalLength)；cudnnrnnflattenweight 64KB/核 clamp 到 [4,32]；conj__v2 pair 预算 dtype-aware cap 32），kernel 数据面与计算路径零改动、大/带宽 case 保留满核。实测 conj host-tiling 9.0139→2.9128us（3.095x，保留 blk64 的 fp32 262144 持平 9.658us）、cudnnrnnflattenweight 6.8451→4.7625us（1.4373x，20/20 case 改善 0 回退）、conj__v2 3.2791→2.8011us（1.1706x）。",
  "verification": {
    "correctness": [
      "conj：10/10 PASS（MERE/MARE 全 0）——只改 host 侧 blockDim 计算，kernel 零改动，数据位级不变",
      "cudnnrnnflattenweight：20/20 bit-exact（mismatch=0，threshold=0，逐字节比对含 NaN/Inf/±0）——host 每核段展开与设备端 u32 seg-split/overlap 语义逐字节等价，host 断言每核 coreCnt<=128；pair_dirs base/cand 重建后各自复验 20/20 bit-exact",
      "conj__v2：10/10 PASS——纯 launch 几何调整（host sizing 公式 + 每核 wave 常量），grid-stride pair 拷贝体与恒等语义不动，round_01 的 dtype 回归在 round_02 按访存宽度细分后消除"
    ],
    "performance": [
      "conj（host-tiling）：dtype 组 geomean 9.0139→2.9128us = 3.095x，ABBA 两块 4 对配对 ratio 0.3223-0.3245（区间无歧义）；逐 case 核数与均值 case_01_fp32_512→blk1 1.558us、case_03_fp32_21→blk1 1.634、case_04_fp16_65536→blk8 3.021、case_05_fp16_33000→blk5 2.695、case_06_bf16_131072→blk16 4.097、case_07_bf16_217→blk1 1.661、case_08_fp32_4096→blk1 1.880、case_09_fp16_16384→blk2 2.363、case_10_bf16_4160→blk1 1.718；case_02_fp32_262144 保留 blk64 9.585→9.658us（持平，带宽不回退）",
      "cudnnrnnflattenweight（grid-dispatch）：两级聚合 6.8451→4.7625us = 1.4373x；ABBA 两块（pb1 6.8432 / pa1 4.7698 / pa2 4.7551 / pb2 6.8470，n=230/run）pair ratio 1.4347/1.4399，同侧偏差 base 0.056% / cand 0.309%；20/20 case 改善 0 回退，case7（13 核，61KB/core）1.93x 最大、case20（24MB，保持 32 核）1.006x；aiv_scalar_ratio 0.6287→0.3308、aiv_mte2_ratio 0.3181→0.5545",
      "conj__v2（whole-kernel-carrier）：两级聚合 3.2791→2.8011us = 1.1706x（ABBA 2 对 40 项配对，逐 case 两对均改善）；大 case case_2_fp32_262144 6.879→5.920us、case_4_fp16_65536 6.017→4.859、case_5_fp16_33000 5.671→3.412、case_6_bf16_131072 6.117→5.059；小 case 持平（case_7_bf16_217 1.662→1.635）"
    ],
    "rollback_signals": [
      "任一 dtype/shape 组回退，尤其大 case 的带宽底线被击穿（cudnnrnnflattenweight case20 保持 32 核 1.006x、conj case_02 保留 blk64 的 9.585→9.658us 属容许的持平）",
      "ABBA 配对比值区间不显著：conj d001 的回滚条件即『核数地板斜率在外推区间不成立，或大 case 带宽回退导致 geomean 上升』",
      "dtype 相关预算被写成统一常量导致某种访存宽度 case 回归（conj__v2 round_01 统一 16ppt 使 case2 回归 +7.3% 的形态）",
      "缩核后每核 loopTimes 上升，把固定成本重新加回去（每核工作量超出 tile 预算的情形）"
    ]
  }
}
-->

# 性能优化策略：启动核数收敛：按工作量反解 launch 几何填平每核固定开销地板

把 launch 的核数从『满核』改为按 workload 反解：先用 msprof 实测拟合『截距 + 斜率×激活核数』的成本律（conj ~2.4us + 0.11-0.19us/核；conj__v2 1.15us + 0.177us/核；cudnnrnnflattenweight 的 3KB 与 1.5MB case 贴同一 6.2us 地板），再按每核预算定 blockDim（conj 16KB/核 clamp 到 min(coreNum,totalLength)；cudnnrnnflattenweight 64KB/核 clamp 到 [4,32]；conj__v2 pair 预算 dtype-aware cap 32），kernel 数据面与计算路径零改动、大/带宽 case 保留满核。实测 conj host-tiling 9.0139→2.9128us（3.095x，保留 blk64 的 fp32 262144 持平 9.658us）、cudnnrnnflattenweight 6.8451→4.7625us（1.4373x，20/20 case 改善 0 回退）、conj__v2 3.2791→2.8011us（1.1706x）。

## 1. 原理

当 device Task Duration 由『每次 launch 的固定成本 + 每个被调度核的固定成本』决定而非由数据量决定时，launch 的 grid 几何就是一等优化对象。本族三个成员的共同观测是 duration 与字节数几乎无关、与激活核数近似线性——conj champion 在 64 核下 21 elems 与 262144 elems 同为 ~9.4us（0.11-0.19us/核 + ~2.4us 截距），conj__v2 拟合出 t ≈ 1.15us + 0.177us×blocks（每线程工作量 ×4 仅 +15%），cudnnrnnflattenweight 的 case18（3KB）6.228us 与 case11（1.5MB）6.348us 贴同一地板。斜率项的经济含义是：每个被调度核无论如何都会付一份 InitBuffer、事件对、计划预取与解码；当该核分到的段是空的（cudnnrnnflattenweight 19/20 个 case 的多数核 coreCnt=0，却仍执行 2×InitBuffer 共 67KB UB + 无条件 3080B MTE2 预取 + 等待 + 2 次 GetValue + 分支），这份成本是纯冗余。因此正确的 sizing 不是 max 核数，而是把核数当成由工作量反解的自由变量：用实测的截距+斜率成本律定出每核预算（conj 16KB/核、cudnnrnnflattenweight 64KB/核、conj__v2 每线程 pair 数），blockDim = clamp(ceil(work/perCoreBudget), lower, upper)。这条杠杆与『削减每核固定链本身』（init-buffer-pool-consolidation 一类）正交：后者削的是斜率前的系数，本机制削的是斜率乘的那个核数，两者可叠加。

实现机制：launch-core-count-convergence：host 用『截距 + 斜率×激活核数』的成本律反解 launch 几何，而不是按 coreNum 满发。conj（target_scope=host-tiling）：ChooseBlockDim(totalLength, elementSize, coreNum) = clamp(ceil(totalBytes/16384), 1, min(coreNum, totalLength))，16KB/核 锚点，kernel 侧零改动（tiling 的 blockLength/startElem 守卫天然支持任意 blockDim）。cudnnrnnflattenweight（target_scope=grid-dispatch）：blockDim = clamp(ceil(totalBytes/64KB), 4, 32)，host 只展开/上传 blockDim 个固定步长计划段（segBytes=ceil(totalBytes/blockDim)，把原先硬编码的 FLATTEN_BLOCK_DIM=32 变成按 workload 反解），kernel 源码零改动——固定步长自定位段地址 = coreIdx*FLATTEN_SEG_BYTES(3080) 与 blockDim 解耦，GetBlockIdx 天然支持任意核数。conj__v2（target_scope=whole-kernel-carrier）：把 SIMT 载体的 sizing 反过来做——nPairs=ceil(N/2)，nPairs<=1024 时 1 核且每核 wave=next-pow2(nPairs) clamp[32,1024]；否则 wave=1024、核数=ceil(nPairs/(1024×ppt)) cap 32，ppt 按访存宽度 dtype-aware（2B=16、4B=8）；kernel 的 grid-stride pair 拷贝体不变。三者的数据面（tile 大小、同步点、载荷字节、逐字节语义）与 kernel 计算路径全部不变，收益全部来自不再发射那些只能执行空段的核。

## 2. 性能问题模式

- 优化目标：把 launch 的 grid 几何从『有多少核就发多少核』改成按工作量反解核数：在 duration ≈ 截距 + 斜率×激活核数的场景里，闲置核仍在执行每核固定标量 prologue（InitBuffer、事件对、计划预取、解码），核数本身就是可压缩变量。
- 适用数据流：一次性（非流式）整块/分段搬运或逐元素映射，host 侧已知总工作量、kernel 对任意 blockDim 有守卫或段地址与 blockDim 解耦的场景；典型如 conj/identity 类逐元素算子、权重与索引展平拷贝类算子、SIMT 逐元素载体（本 run 覆盖 conj host-tiling、cudnnrnnflattenweight grid-dispatch、conj__v2 whole-kernel-carrier 三种作用域）
- Feature signature：`{"bottleneck": ["launch-fixed-cost", "core-count-linear-duration-slope", "per-core-fixed-scalar-prologue", "idle-core-redundant-work"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "launch-core-count-convergence", "reduce_mode": "", "structure": ["intercept-plus-slope-cost-law", "workload-aware-grid-sizing", "clamped-core-count", "kernel-data-path-unchanged", "full-core-retention-for-bandwidth-cases"]}`

## 3. 正确性红线

- 成本律外推可能不成立：拟合点之外（<21 核或 >64 核区间）截距/斜率可能变号，性能门会如实地停在约 1.0x；conj d001 预注册的回滚条件即『核数地板斜率在外推区间不成立，或大 case 带宽回退导致 geomean 上升』
- 缩核会压低并行度，若每核工作量超出 tile 预算使 loopTimes 上升，每核循环开销会把省下的固定成本重新加回来；cudnnrnnflattenweight 的记录显示 64KB/核 目标偏保守（case7 13 核 1.93x 为最大收益，提示最优 SEG_TARGET 可能更小）
- dtype 相关的每线程预算若给成统一常量，会让某种访存宽度的大 case 回归：conj__v2 round_01 统一 16ppt 使 case2（fp32/u64）回归 +7.3%，round_02 按 2B=16/4B=8 细分后消除
- 『核数敏感分量』是机制的核心假设，若某 SoC 上 launch/调度固定成本与 blockDim 无关，收益趋于 0——cudnnrnnflattenweight 把这个方向同时设计成一次廉价的决定性假设检验（收益 ~0 即 rejected_performance 回滚）
- 存在未归因的逐 case 偏差：cudnnrnnflattenweight case11 的 blockDim 未变（仍 32 核、plan/segBytes 逐字节不变）却 ABBA 稳定改善 1.26x，机制本身无法解释，只能按未归因项记录（case20 同配置 1.006x 佐证机制对 32 核 case 无直接影响）

资源与硬件约束：

- 核数只能沿既有 grid 语义收缩，数据面必须不变：本 run 三个成员均为 host-only 改动——conj 只改 kernel/pybind11.cpp 的 ChooseBlockDim、cudnnrnnflattenweight kernel 源码零改动（只改 host 展开量与 launch 参数）、conj__v2 只改 host sizing 与每核 wave 常量，DataCopyPad 载荷、tile 大小、同步点与逐字节语义全部保持不变
- 必须保留『大/带宽 case 满核』分支：conj case_02（fp32 262144）保留 blk64 后 9.585→9.658us 属容许持平；若为省固定成本把大 case 也收核，带宽回退会吃掉聚合收益
- 每核预算常量是 per-op 的，不可跨 op 照搬：conj 是 16KB/核 锚点 clamp(ceil(totalBytes/16384),1,min(coreNum,totalLength))，cudnnrnnflattenweight 是 64KB/核 clamp(ceil(totalBytes/64KB),4,32)，conj__v2 是 pair 预算 cap 32
- conj__v2 的每线程 pair 预算必须 dtype-aware：2B dtype=16 pair、4B dtype=8 pair；round_01 统一 16ppt 使 case2（fp32/u64）回归 +7.3%，round_02 按访存宽度细分后消除
- blockDim 的上界必须显式 clamp（min(coreNum,totalLength) / MIN_CORES=4 / cap 32），下界不小于 1，且缩核后 host 侧展开的计划量随之下降而不是固定展开满核（cudnnrnnflattenweight 只展开 blockDim 个计划段）

## 4. 泛化条件

- 策略作用域：op_class：elementwise

适用：

- wall 近似服从『截距 + 斜率×激活核数』的成本律，且对数据量弱敏感：本 run conj champion 在 64 BlockNum 下 21 elems 与 262144 elems 同为 ~9.4us（≈0.11-0.19us/核 + ~2.4us 截距）；conj__v2 拟合 t ≈ 1.15us + 0.177us×blocks；cudnnrnnflattenweight case18（3KB）6.228us vs case11（1.5MB）6.348us 贴同一地板
- kernel 对任意 blockDim 天然兼容：conj 由 tiling 的 blockLength/startElem 守卫支持缩核；cudnnrnnflattenweight 的固定步长自定位段地址 = coreIdx*FLATTEN_SEG_BYTES(3080) 与 blockDim 解耦，kernel 源码零改动；conj__v2 的 grid-stride pair 拷贝体与核数无关
- 存在可实测的拟合点：conj__v2 逐 case 实测 1 核=1.53-1.66us、4-5 核=2.26-2.32us、16 核=3.76us、32 核=5.77-6.87us，先拟合出截距与斜率，才能反解每核预算
- 小/中 case 在性能 case 构成中占多数，且收核后每核工作量仍落在单 tile 预算内：conj 7/10 个 case 被判定为可收核、cudnnrnnflattenweight 19/20（totalBytes<=1.6MB）收到 4-32 核、conj__v2 中大 case 32→8-16 核

不适用：

- 瓶颈是带宽而非固定成本时不适用：本 run cudnnrnnflattenweight case20（24MB）刻意保持 32 核、收益 1.006x，保留满核是机制的一部分而不是例外
- kernel 的分段/数据映射依赖 blockDim 本身（非自定位段）时不适用：此时缩核会改变搬运语义而非只改变调度核数
- workload 与核数之间没有可测关系（已有独立 work queue 或动态负载均衡）时没有可收敛的自由变量

## 5. 实施步骤

1. 先用逐 case msprof device Task Duration 拟合成本律：以激活核数为自变量、duration 为因变量回归出截距与斜率（conj__v2 得 t ≈ 1.15us + 0.177us×blocks；conj d001 得 ≈0.11-0.19us/核 + ~2.4us 截距），并确认 duration 对数据量弱敏感（21 elems 与 262144 elems 在 64 核下同为 ~9.4us）
2. 在 host 侧（pybind/tiling 计算）用该成本律反解每核预算常量，把 blockDim 从『满核』改成按工作量收敛：conj 用 ChooseBlockDim = clamp(ceil(totalBytes/16384),1,min(coreNum,totalLength))（16KB/核 锚点）；cudnnrnnflattenweight 用 clamp(ceil(totalBytes/64KB),4,32)；conj__v2 用 ceil(nPairs/(wave×ppt)) cap 32 且 ppt 按访存宽度 dtype-aware（2B=16、4B=8）
3. kernel 侧保持语义不变：只允许改动 host sizing 与随 blockDim 变化的展开量（cudnnrnnflattenweight 只展开/上传 blockDim 个固定步长计划段，segBytes=ceil(totalBytes/blockDim)，seg-split/overlap 语义与设备端逐字节相同，host 断言每核 coreCnt<=128），kernel 源码零改动或只读新常量
4. 为小 N 补上 wave 维度自缩：conj__v2 在 nPairs<=1024 时退化为 1 核并把每核 wave 取 next-pow2(nPairs) 再 clamp 到 [32,1024]（dim3(simtWave_) 替代固定 dim3(1024)），避免小 N 仍发射 1024 线程
5. 以 ABBA 平衡交替配对实测裁决：要求逐 case 无回退、geomean 显著超过 5% 采纳门槛才保留；任一 dtype/shape 组回退即回滚到满核公式（conj d001 预注册的回滚条件即『大 case 带宽回退导致 geomean 上升』）

## 6. LLM 前置问题

- 目标实现是否满足：wall 近似服从『截距 + 斜率×激活核数』的成本律，且对数据量弱敏感：本 run conj champion 在 64 BlockNum 下 21 elems 与 262144 elems 同为 ~9.4us（≈0.11-0.19us/核 + ~2.4us 截距）；conj__v2 拟合 t ≈ 1.15us + 0.177us×blocks；cudnnrnnflattenweight case18（3KB）6.228us vs case11（1.5MB）6.348us 贴同一地板？
- 目标实现是否满足：kernel 对任意 blockDim 天然兼容：conj 由 tiling 的 blockLength/startElem 守卫支持缩核；cudnnrnnflattenweight 的固定步长自定位段地址 = coreIdx*FLATTEN_SEG_BYTES(3080) 与 blockDim 解耦，kernel 源码零改动；conj__v2 的 grid-stride pair 拷贝体与核数无关？
- 目标实现是否满足：存在可实测的拟合点：conj__v2 逐 case 实测 1 核=1.53-1.66us、4-5 核=2.26-2.32us、16 核=3.76us、32 核=5.77-6.87us，先拟合出截距与斜率，才能反解每核预算？
- 目标实现是否满足：小/中 case 在性能 case 构成中占多数，且收核后每核工作量仍落在单 tile 预算内：conj 7/10 个 case 被判定为可收核、cudnnrnnflattenweight 19/20（totalBytes<=1.6MB）收到 4-32 核、conj__v2 中大 case 32→8-16 核？
- 是否命中排除条件：瓶颈是带宽而非固定成本时不适用：本 run cudnnrnnflattenweight case20（24MB）刻意保持 32 核、收益 1.006x，保留满核是机制的一部分而不是例外？
- 是否命中排除条件：kernel 的分段/数据映射依赖 blockDim 本身（非自定位段）时不适用：此时缩核会改变搬运语义而非只改变调度核数？
- 是否命中排除条件：workload 与核数之间没有可测关系（已有独立 work queue 或动态负载均衡）时没有可收敛的自由变量？

## 7. 验收标准

正确性：

- conj：10/10 PASS（MERE/MARE 全 0）——只改 host 侧 blockDim 计算，kernel 零改动，数据位级不变
- cudnnrnnflattenweight：20/20 bit-exact（mismatch=0，threshold=0，逐字节比对含 NaN/Inf/±0）——host 每核段展开与设备端 u32 seg-split/overlap 语义逐字节等价，host 断言每核 coreCnt<=128；pair_dirs base/cand 重建后各自复验 20/20 bit-exact
- conj__v2：10/10 PASS——纯 launch 几何调整（host sizing 公式 + 每核 wave 常量），grid-stride pair 拷贝体与恒等语义不动，round_01 的 dtype 回归在 round_02 按访存宽度细分后消除

性能：

- conj（host-tiling）：dtype 组 geomean 9.0139→2.9128us = 3.095x，ABBA 两块 4 对配对 ratio 0.3223-0.3245（区间无歧义）；逐 case 核数与均值 case_01_fp32_512→blk1 1.558us、case_03_fp32_21→blk1 1.634、case_04_fp16_65536→blk8 3.021、case_05_fp16_33000→blk5 2.695、case_06_bf16_131072→blk16 4.097、case_07_bf16_217→blk1 1.661、case_08_fp32_4096→blk1 1.880、case_09_fp16_16384→blk2 2.363、case_10_bf16_4160→blk1 1.718；case_02_fp32_262144 保留 blk64 9.585→9.658us（持平，带宽不回退）
- cudnnrnnflattenweight（grid-dispatch）：两级聚合 6.8451→4.7625us = 1.4373x；ABBA 两块（pb1 6.8432 / pa1 4.7698 / pa2 4.7551 / pb2 6.8470，n=230/run）pair ratio 1.4347/1.4399，同侧偏差 base 0.056% / cand 0.309%；20/20 case 改善 0 回退，case7（13 核，61KB/core）1.93x 最大、case20（24MB，保持 32 核）1.006x；aiv_scalar_ratio 0.6287→0.3308、aiv_mte2_ratio 0.3181→0.5545
- conj__v2（whole-kernel-carrier）：两级聚合 3.2791→2.8011us = 1.1706x（ABBA 2 对 40 项配对，逐 case 两对均改善）；大 case case_2_fp32_262144 6.879→5.920us、case_4_fp16_65536 6.017→4.859、case_5_fp16_33000 5.671→3.412、case_6_bf16_131072 6.117→5.059；小 case 持平（case_7_bf16_217 1.662→1.635）

回滚信号：

- 任一 dtype/shape 组回退，尤其大 case 的带宽底线被击穿（cudnnrnnflattenweight case20 保持 32 核 1.006x、conj case_02 保留 blk64 的 9.585→9.658us 属容许的持平）
- ABBA 配对比值区间不显著：conj d001 的回滚条件即『核数地板斜率在外推区间不成立，或大 case 带宽回退导致 geomean 上升』
- dtype 相关预算被写成统一常量导致某种访存宽度 case 回归（conj__v2 round_01 统一 16ppt 使 case2 回归 +7.3% 的形态）
- 缩核后每核 loopTimes 上升，把固定成本重新加回去（每核工作量超出 tile 预算的情形）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：simt-direct-gm-size-gate-regression

- loop_20260916_165309 status=accepted, speedup=3.095, precision=10/10 PASS（MERE/MARE 全 0））
- loop_20260916_165309 status=accepted, speedup=1.4373, precision=20/20 PASS bit-exact（threshold=0，逐字节比对含 NaN/Inf/±0））
- loop_20260916_165309 status=accepted, speedup=1.1706, precision=10/10 PASS）

## 检索卡（短卡）

动作：把 launch 核数从满核改为按工作量反解：实测拟合截距+斜率成本律，按每核预算 clamp 出 blockDim，数据面不动。
适用：wall 服从截距+斜率×激活核数且对数据量弱敏感；kernel 对任意 blockDim 天然兼容。
限制：带宽瓶颈须保留大 case 满核；缩核后 host 展开量须随之下降；每核预算 per-op 不可照搬；dtype 预算不可统一常量。
范围：elementwise 整块/分段搬运或逐元素映射 launch 几何。
检索词：blockDim、ChooseBlockDim、GetBlockIdx、FLATTEN_SEG_BYTES、grid-stride、wave 自缩
机会：duration 与数据量几乎无关却与激活核数近似线性，闲置核仍付每核固定标量开销。
代价：缩核压低并行度，每核工作量超出 tile 预算使 loopTimes 上升会把省下的固定成本加回。
