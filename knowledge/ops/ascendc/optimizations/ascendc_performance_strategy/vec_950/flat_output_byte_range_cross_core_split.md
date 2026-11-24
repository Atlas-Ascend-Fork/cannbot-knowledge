---
type: Optimization
title: 扁平输出字节区间跨核切分：host 按 32KB/核放宽 blockDim
description: 把 blockDim 从 min(outer,coreNum) 改为按 m*inner*elemSize 每 32KB 一核，按输出字节区间分派。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/flat-output-byte-range-cross-core-split.md
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
      "host 只在 outer==1 分支改 blockDim：min(vectorCoreNum, CeilDiv(m*inner*elemSize, 32KB))（每核至少一个 32KB chunk）；outer>1 保持 min(outer, coreNum) 不变",
      "rangeSplit 的 kernel 侧分流（totalRows==1 && blockDim>1）必须前置于行范围早退判定，否则 core>0 会被行范围早退误杀",
      "核 k 的字节区间 [k*T/P, (k+1)*T/P) 用 u64 运算（T = m*inner*elem），末核吸收取整余数；sum(len) == m 是各核 GM 写天然互斥、无需跨核同步的唯一依据",
      "src 仍由 interval 的 startPos*inner*elem + off 给出，dst 为输出流绝对字节 bsum + off，逐 chunk 与 champion 单行路径字节覆盖等价；slotsPerSet_==0 时回退 CopyBlock 逐 chunk",
      "outer>1 路径（BatchedCopy / IntervalBulkCopy 分流）、prep kernel 与 tiling 结构不得改动，以便把收益隔离到 outer==1 的 copy 路径"
    ],
    "excluded_conditions": [
      "outer>1 的 2D 批量搬运路径不适用（保持原分流），prep kernel 不适用",
      "T = m*inner*elem 太小（不足 32KB * 核数）时每核分不到一个有效 chunk，摊薄收益消失",
      "写序相关或目的字节可能被多个 interval 覆盖（需要 RMW/原子）时不适用：机制的前提是 interval 目的区间两两不相交且 sum(len)==m",
      "与既有卡 scatter-1d-flat-daxis-core-partition 不同：那张卡切的是 D 索引轴、按更新索引归属过滤后执行 y[d]=u；本卡切的是扁平输出字节流，按字节区间把 interval 的搬运重新分派给核，不按索引归属过滤，也不要求 outerLen==innerLen==1 之外的退化形状"
    ],
    "required_conditions": [
      "outer==1 时原 blockDim=min(outer, coreNum)=1，全部 copy 压单核：本 run 冻结基线所有 outer==1 的 copy launch 全部 Block Num=1（bf16[4096,2048]dim0=155.3us、bf16[1000003]1D=156.2us、fp32[2048,2048]dim0-L1=132.7us、fp16 dim0 30.8/41.1/35.4us、bf16[255,8193]dim0=28.9us），而 dim1/中间维 launch 已是 Block Num=64",
      "输出是扁平连续字节流，interval 的目的字节前缀 bsum_i = outPos_i*inner*elem 使输出流按字节范围切分等价于 interval 集合划分，且区间两两互斥、sum(len)==m",
      "存在可复用的 champion 双 slot ring 流式 chunk（每 chunk <= 32KB），1D 字节粒度 DataCopyPad(uint8) 已是既有路径",
      "interval 表可整表载入并由 O(i_k) 标量前缀定位本核首 interval 及其区间内偏移"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "delete",
      "operator_class": "gather-scatter",
      "pairs": 2,
      "precision": "20/20 PASS（bit-exact，0 修复）",
      "run_id": "<run-id>",
      "speedup": 1.679,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "single-core-underfill",
      "outer1-flat-copy",
      "blockdim-1"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "flat-output-byte-range-cross-core-split",
    "structure": [
      "host-blockdim-per-32kb-core",
      "output-byte-range-partition",
      "scalar-prefix-interval-locate",
      "two-slot-ring-streaming",
      "no-cross-core-sync"
    ]
  },
  "generality": "op_class",
  "id": "SCATTER-FLAT-OUTPUT-BYTE-RANGE-CORE-SPLIT",
  "implementation_steps": [
    "host 侧（kernel/pybind11.cpp）仅在 outer==1 分支把 blockDim 由 min(outer, vectorCoreNum) 放宽为 min(vectorCoreNum, CeilDiv(m*inner*elemSize, 32KB))（每核至少一个 32KB chunk）；outer>1 保持 min(outer, coreNum)",
    "kernel 侧在 Process 中以 bool rangeSplit 前置分流（totalRows==1 && blockDim>1），置于行范围早退之前，保证 core>0 不被早退误杀；ivLocal 整表载入后进入 RangeSplitCopy",
    "RangeSplitCopy：核 k 取输出字节流 [k*T/P, (k+1)*T/P)（T=m*inner*elem，u64 运算，末核吸收取整余数），用 O(i_k) 标量前缀定位本核首 interval 与区间内偏移",
    "流式搬运：slotsPerSet_>0 走与 champion 同款的双 slot ring，==0 回退 CopyBlock 逐 chunk；NextRangeChunk 以 (interval, piece, chunk<=32KB) 产出，dst=输出流绝对字节 bsum+off，src=startPos*inner*elem+off",
    "outer>1 路径（BatchedCopy / IntervalBulkCopy 分流）、prep kernel 与 tiling 结构保持零改动，并用对照证明其 Block Num 与时长持平"
  ],
  "intent": "消除 outer==1 时的单核欠载：host 用 min(outer, coreNum) 推导 blockDim 使退化形状（outer=1）把整份 copy 压到 1 个核（Block Num=1），kernel 内再没有任何并行机会；把扁平输出字节流按字节范围切分给多核即可把单核延迟摊薄约 blockDim 倍。",
  "mechanism": "interval-range-cross-core-split（outer==1 copy 路径）：host 按 m*inner*elemSize 每 32KB 一核放宽 blockDim（上限 vectorCoreNum），kernel 在 totalRows==1 && blockDim>1 时把输出字节流 [0, m*inner*elem) 按核均分——核 k 负责 [k*T/P, (k+1)*T/P)（末核吸收取整余数），用 O(i_k) 标量前缀定位首 interval 与区间内偏移，再按 champion BatchedCopy 同款的双 slot ring 逐 chunk（<=32KB）搬运，超长 interval 被字节范围自然切成 piece。正确性论据：interval 的目的字节区间两两不相交且 sum(len)==m，故各核的 GM 写天然互斥、无需任何跨核同步，字节覆盖集合不变（bit-exact）。分流以 bool rangeSplit 前置于行范围早退判定，避免 core>0 被误杀；outer>1 的 2D 批量路径与 prep kernel 完全不变。与 scatter-1d-flat-daxis-core-partition 的区别：那张卡的切分单位是输出索引轴 D，命中后按更新索引的归属过滤决定是否执行 y[d]=u；本卡的切分单位是扁平输出的字节流，按字节区间重新分派 interval 搬运，不做索引归属过滤，也不依赖 outerLen==innerLen==1 的退化形状。",
  "name": "扁平输出字节区间跨核切分：host 按 32KB/核放宽 blockDim",
  "operator_class": "gather-scatter",
  "operator_scope": "索引驱动的 copy/散射类算子中 blockDim 由 outer 维推导、且 outer==1 使整份搬运压到单核（Block Num=1）的退化形状；输出为扁平连续字节流且 interval 目的区间互斥",
  "principle": "并行度由 host 的 blockDim 推导决定：当 blockDim=min(outer, coreNum) 而 outer==1 时，无论输出多大都只激活 1 个核，copy 的 MTE 与标量前缀成本全部串在单核上。若切分单位改取输出字节范围，则并行度由数据量（m*inner*elemSize/32KB）而不是形状外层维决定，单核延迟被约 blockDim 倍摊薄；而目的字节前缀 bsum_i = outPos_i*inner*elem 使「输出流按字节切分」与「interval 集合划分」等价，配合区间两两互斥与 sum(len)==m，切分不需要任何跨核同步或原子，字节覆盖集合保持不变。",
  "related_anti_patterns": [],
  "risks": [
    "互斥性是正确性前提：机制依赖 interval 目的字节区间两两不相交且 sum(len)==m；若数据允许重叠区间或有更新语义（RMW），跨核写会竞态",
    "分流位置必须前置于行范围早退：放在其后会使 core>0 被早退误杀（本 run 的实现契约）",
    "核数提升依赖每个核至少分到 32KB：T 不足 P*32KB 时末核分不到有效区间，需按空区间 O(1) 处理，否则出现空跑或越界",
    "O(i_k) 前缀定位在 interval 数极大且本核首 interval 靠后时会被稀释，收益随 interval 分布右移而衰减",
    "区间切分改变的是核间分工而非写序语义，但前提是下游不依赖写序；若存在写序依赖则不可用",
    "outer>1 与 prep 路径的「零改动」必须由对照证明（本 run 该两路的 Block Num 与时长持平），否则收益归因不成立"
  ],
  "slug": "flat-output-byte-range-cross-core-split",
  "summary": "delete 的 DeleteCopyKernel 用 blockDim=min(outer, vectorCoreNum) 推导并行度，outer==1 时整份 copy 压在 1 个核上（本 run 冻结基线所有 outer==1 launch 全部 Block Num=1：155.3 / 156.2 / 132.7 / 30.8 / 41.1 / 35.4 / 28.9us 级）。改为 host 按 m*inner*elemSize 每 32KB 一核放宽 blockDim（上限 vectorCoreNum），kernel 在 totalRows==1 && blockDim>1 时把扁平输出字节流 [0, m*inner*elem) 按核均分（核 k 取 [k*T/P,(k+1)*T/P)，末核吸收余数），用 O(i_k) 标量前缀定位首 interval，再按 champion 双 slot ring 逐 chunk（<=32KB）搬运；区间两两互斥且 sum(len)==m，故无需跨核同步。两级聚合 geomean 70.223 -> 41.816us（1.679x：bf16 3.56x / fp16 1.77x / fp32 1.26x / prep 持平），候选 Block Num 1 -> 39-64（155.3->15.0、156.2->24.4、132.7->13.5、28.9->11.0us），精度 20/20 bit-exact，outer>1 与 prep 路径零改动。",
  "verification": {
    "correctness": [
      "精度 20/20 bit-exact（字节覆盖集合不变，区间切分只重分配核间分工、写序无关），0 修复轮次",
      "编译 1 次修复后通过；outer>1 的 2D 批量路径与 prep kernel 未改动",
      "各核目的字节区间两两不相交且 sum(len)==m，核间写天然互斥，无需跨核同步或原子"
    ],
    "performance": [
      "ABBA 两对平衡配对（A,B,B,A）全 copy case 改善，对间偏差 <=0.4% 远小于效应量；两级聚合 geomean 70.223 -> 41.816us（1.679x），超出预测区间 48-55us（1.28-1.45x）",
      "候选筛选逐 launch：outer==1 launch 的 Block Num 1 -> 39-64，时长 155.3->15.0、156.2->24.4、132.7->13.5、30.8/41.1/35.4->9.5/8.7/11.0、28.9->11.0us；多行与 prep 路径 Block Num 与时长持平，机制定向命中",
      "冻结基线本轮新采 msprof 两级聚合 geomean 68.648us（bf16=91.512 fp16=49.950 fp32=93.467 prep=51.980）"
    ],
    "rollback_signals": [
      "目的字节区间出现重叠或 sum(len)!=m 导致跨核写竞态/结果错位",
      "rangeSplit 分流未前置于行范围早退，core>0 被误杀",
      "T 不足每核 32KB 时末核空跑或越界",
      "outer>1 或 prep 路径出现超出噪声带的回退（本 run 为持平）"
    ]
  }
}
-->

# 性能优化策略：扁平输出字节区间跨核切分：host 按 32KB/核放宽 blockDim

delete 的 DeleteCopyKernel 用 blockDim=min(outer, vectorCoreNum) 推导并行度，outer==1 时整份 copy 压在 1 个核上（本 run 冻结基线所有 outer==1 launch 全部 Block Num=1：155.3 / 156.2 / 132.7 / 30.8 / 41.1 / 35.4 / 28.9us 级）。改为 host 按 m*inner*elemSize 每 32KB 一核放宽 blockDim（上限 vectorCoreNum），kernel 在 totalRows==1 && blockDim>1 时把扁平输出字节流 [0, m*inner*elem) 按核均分（核 k 取 [k*T/P,(k+1)*T/P)，末核吸收余数），用 O(i_k) 标量前缀定位首 interval，再按 champion 双 slot ring 逐 chunk（<=32KB）搬运；区间两两互斥且 sum(len)==m，故无需跨核同步。两级聚合 geomean 70.223 -> 41.816us（1.679x：bf16 3.56x / fp16 1.77x / fp32 1.26x / prep 持平），候选 Block Num 1 -> 39-64（155.3->15.0、156.2->24.4、132.7->13.5、28.9->11.0us），精度 20/20 bit-exact，outer>1 与 prep 路径零改动。

## 1. 原理

并行度由 host 的 blockDim 推导决定：当 blockDim=min(outer, coreNum) 而 outer==1 时，无论输出多大都只激活 1 个核，copy 的 MTE 与标量前缀成本全部串在单核上。若切分单位改取输出字节范围，则并行度由数据量（m*inner*elemSize/32KB）而不是形状外层维决定，单核延迟被约 blockDim 倍摊薄；而目的字节前缀 bsum_i = outPos_i*inner*elem 使「输出流按字节切分」与「interval 集合划分」等价，配合区间两两互斥与 sum(len)==m，切分不需要任何跨核同步或原子，字节覆盖集合保持不变。

实现机制：interval-range-cross-core-split（outer==1 copy 路径）：host 按 m*inner*elemSize 每 32KB 一核放宽 blockDim（上限 vectorCoreNum），kernel 在 totalRows==1 && blockDim>1 时把输出字节流 [0, m*inner*elem) 按核均分——核 k 负责 [k*T/P, (k+1)*T/P)（末核吸收取整余数），用 O(i_k) 标量前缀定位首 interval 与区间内偏移，再按 champion BatchedCopy 同款的双 slot ring 逐 chunk（<=32KB）搬运，超长 interval 被字节范围自然切成 piece。正确性论据：interval 的目的字节区间两两不相交且 sum(len)==m，故各核的 GM 写天然互斥、无需任何跨核同步，字节覆盖集合不变（bit-exact）。分流以 bool rangeSplit 前置于行范围早退判定，避免 core>0 被误杀；outer>1 的 2D 批量路径与 prep kernel 完全不变。与 scatter-1d-flat-daxis-core-partition 的区别：那张卡的切分单位是输出索引轴 D，命中后按更新索引的归属过滤决定是否执行 y[d]=u；本卡的切分单位是扁平输出的字节流，按字节区间重新分派 interval 搬运，不做索引归属过滤，也不依赖 outerLen==innerLen==1 的退化形状。

## 2. 性能问题模式

- 优化目标：消除 outer==1 时的单核欠载：host 用 min(outer, coreNum) 推导 blockDim 使退化形状（outer=1）把整份 copy 压到 1 个核（Block Num=1），kernel 内再没有任何并行机会；把扁平输出字节流按字节范围切分给多核即可把单核延迟摊薄约 blockDim 倍。
- 适用数据流：索引驱动的 copy/散射类算子中 blockDim 由 outer 维推导、且 outer==1 使整份搬运压到单核（Block Num=1）的退化形状；输出为扁平连续字节流且 interval 目的区间互斥
- Feature signature：`{"bottleneck": ["single-core-underfill", "outer1-flat-copy", "blockdim-1"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "flat-output-byte-range-cross-core-split", "structure": ["host-blockdim-per-32kb-core", "output-byte-range-partition", "scalar-prefix-interval-locate", "two-slot-ring-streaming", "no-cross-core-sync"]}`

## 3. 正确性红线

- 互斥性是正确性前提：机制依赖 interval 目的字节区间两两不相交且 sum(len)==m；若数据允许重叠区间或有更新语义（RMW），跨核写会竞态
- 分流位置必须前置于行范围早退：放在其后会使 core>0 被早退误杀（本 run 的实现契约）
- 核数提升依赖每个核至少分到 32KB：T 不足 P*32KB 时末核分不到有效区间，需按空区间 O(1) 处理，否则出现空跑或越界
- O(i_k) 前缀定位在 interval 数极大且本核首 interval 靠后时会被稀释，收益随 interval 分布右移而衰减
- 区间切分改变的是核间分工而非写序语义，但前提是下游不依赖写序；若存在写序依赖则不可用
- outer>1 与 prep 路径的「零改动」必须由对照证明（本 run 该两路的 Block Num 与时长持平），否则收益归因不成立

资源与硬件约束：

- host 只在 outer==1 分支改 blockDim：min(vectorCoreNum, CeilDiv(m*inner*elemSize, 32KB))（每核至少一个 32KB chunk）；outer>1 保持 min(outer, coreNum) 不变
- rangeSplit 的 kernel 侧分流（totalRows==1 && blockDim>1）必须前置于行范围早退判定，否则 core>0 会被行范围早退误杀
- 核 k 的字节区间 [k*T/P, (k+1)*T/P) 用 u64 运算（T = m*inner*elem），末核吸收取整余数；sum(len) == m 是各核 GM 写天然互斥、无需跨核同步的唯一依据
- src 仍由 interval 的 startPos*inner*elem + off 给出，dst 为输出流绝对字节 bsum + off，逐 chunk 与 champion 单行路径字节覆盖等价；slotsPerSet_==0 时回退 CopyBlock 逐 chunk
- outer>1 路径（BatchedCopy / IntervalBulkCopy 分流）、prep kernel 与 tiling 结构不得改动，以便把收益隔离到 outer==1 的 copy 路径

## 4. 泛化条件

- 策略作用域：op_class：gather-scatter

适用：

- outer==1 时原 blockDim=min(outer, coreNum)=1，全部 copy 压单核：本 run 冻结基线所有 outer==1 的 copy launch 全部 Block Num=1（bf16[4096,2048]dim0=155.3us、bf16[1000003]1D=156.2us、fp32[2048,2048]dim0-L1=132.7us、fp16 dim0 30.8/41.1/35.4us、bf16[255,8193]dim0=28.9us），而 dim1/中间维 launch 已是 Block Num=64
- 输出是扁平连续字节流，interval 的目的字节前缀 bsum_i = outPos_i*inner*elem 使输出流按字节范围切分等价于 interval 集合划分，且区间两两互斥、sum(len)==m
- 存在可复用的 champion 双 slot ring 流式 chunk（每 chunk <= 32KB），1D 字节粒度 DataCopyPad(uint8) 已是既有路径
- interval 表可整表载入并由 O(i_k) 标量前缀定位本核首 interval 及其区间内偏移

不适用：

- outer>1 的 2D 批量搬运路径不适用（保持原分流），prep kernel 不适用
- T = m*inner*elem 太小（不足 32KB * 核数）时每核分不到一个有效 chunk，摊薄收益消失
- 写序相关或目的字节可能被多个 interval 覆盖（需要 RMW/原子）时不适用：机制的前提是 interval 目的区间两两不相交且 sum(len)==m
- 与既有卡 scatter-1d-flat-daxis-core-partition 不同：那张卡切的是 D 索引轴、按更新索引归属过滤后执行 y[d]=u；本卡切的是扁平输出字节流，按字节区间把 interval 的搬运重新分派给核，不按索引归属过滤，也不要求 outerLen==innerLen==1 之外的退化形状

## 5. 实施步骤

1. host 侧（kernel/pybind11.cpp）仅在 outer==1 分支把 blockDim 由 min(outer, vectorCoreNum) 放宽为 min(vectorCoreNum, CeilDiv(m*inner*elemSize, 32KB))（每核至少一个 32KB chunk）；outer>1 保持 min(outer, coreNum)
2. kernel 侧在 Process 中以 bool rangeSplit 前置分流（totalRows==1 && blockDim>1），置于行范围早退之前，保证 core>0 不被早退误杀；ivLocal 整表载入后进入 RangeSplitCopy
3. RangeSplitCopy：核 k 取输出字节流 [k*T/P, (k+1)*T/P)（T=m*inner*elem，u64 运算，末核吸收取整余数），用 O(i_k) 标量前缀定位本核首 interval 与区间内偏移
4. 流式搬运：slotsPerSet_>0 走与 champion 同款的双 slot ring，==0 回退 CopyBlock 逐 chunk；NextRangeChunk 以 (interval, piece, chunk<=32KB) 产出，dst=输出流绝对字节 bsum+off，src=startPos*inner*elem+off
5. outer>1 路径（BatchedCopy / IntervalBulkCopy 分流）、prep kernel 与 tiling 结构保持零改动，并用对照证明其 Block Num 与时长持平

## 6. LLM 前置问题

- 目标实现是否满足：outer==1 时原 blockDim = 1，全部 copy 压单核（本 run 冻结基线所有 outer==1 launch 全部 Block Num=1，155.3 / 156.2 / 132.7us 级），而 dim1/中间维 launch 已是 Block Num=64？
- 目标实现是否满足：输出是扁平连续字节流，interval 目的字节前缀使输出流按字节范围切分等价于 interval 集合划分，且区间两两互斥、sum(len)==m？
- 目标实现是否满足：存在可复用的双 slot ring 流式 chunk（<=32KB）与 1D 字节粒度 DataCopyPad(uint8) 路径？
- 目标实现是否满足：interval 表可整表载入并由 O(i_k) 标量前缀定位本核首 interval 与区间内偏移？
- 是否命中排除条件：outer>1 的 2D 批量搬运路径或 prep kernel？（保持不动）
- 是否命中排除条件：T 太小（不足 32KB * 核数）导致每核分不到有效 chunk？
- 是否命中排除条件：写序相关或目的字节可能被多个 interval 覆盖（需要 RMW/原子）？

## 7. 验收标准

正确性：

- 精度 20/20 bit-exact（字节覆盖集合不变，区间切分只重分配核间分工、写序无关），0 修复轮次
- 编译 1 次修复后通过；outer>1 的 2D 批量路径与 prep kernel 未改动
- 各核目的字节区间两两不相交且 sum(len)==m，核间写天然互斥，无需跨核同步或原子

性能：

- ABBA 两对平衡配对（A,B,B,A）全 copy case 改善，对间偏差 <=0.4% 远小于效应量；两级聚合 geomean 70.223 -> 41.816us（1.679x），超出预测区间 48-55us（1.28-1.45x）
- 候选筛选逐 launch：outer==1 launch 的 Block Num 1 -> 39-64，时长 155.3->15.0、156.2->24.4、132.7->13.5、30.8/41.1/35.4->9.5/8.7/11.0、28.9->11.0us；多行与 prep 路径 Block Num 与时长持平，机制定向命中
- 冻结基线本轮新采 msprof 两级聚合 geomean 68.648us（bf16=91.512 fp16=49.950 fp32=93.467 prep=51.980）

回滚信号：

- 目的字节区间出现重叠或 sum(len)!=m 导致跨核写竞态/结果错位
- rangeSplit 分流未前置于行范围早退，core>0 被误杀
- T 不足每核 32KB 时末核空跑或越界
- outer>1 或 prep 路径出现超出噪声带的回退（本 run 为持平）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260913_154221（pairs=2, status=accepted, speedup=1.679, precision=20/20 PASS bit-exact，0 修复）

## 检索卡（短卡）

动作：把 blockDim 从 min(outer,coreNum) 改为按 m*inner*elemSize 每 32KB 一核，按输出字节区间分派
适用：outer==1 使原 blockDim=1 全 copy 压单核；输出扁平字节流、目的区间互斥
限制：rangeSplit 分流须前置于行范围早退；T 不足 32KB*核数时每核无 chunk；重叠区间不可用
范围：gather-scatter 索引驱动 copy 算子 outer==1
检索词：blockDim、min(outer,coreNum)、字节区间切分、双 slot ring、rangeSplit
机会：outer==1 时 Block Num=1，copy 的 MTE 与标量前缀全串单核
代价：O(i_k) 前缀定位在 interval 数极大、首 interval 靠后时稀释
