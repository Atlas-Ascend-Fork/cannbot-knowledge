---
type: Optimization
title: 按累加深度分桶的多累加器派发：补偿求和去补偿
description: champion 的补偿式运行累加器（KahanStepRot）在每 64-lane 块约 12 条向量指令里有 8 条花在补偿上。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/multi-accumulator-compensated-sum-bucket-dispatch.md
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
      "整掩码提升必须建立在 guaranteed-full 论证之上：fullBlks = subChunks-1，组内 block [0, fullBlks) 恒满足 remaining >= COLS，尾块必须单独 peel 并用自己的 mt + fresh-dst Add/Select 合并；任何 subChunks/COLS 关系变化都会让整掩码越界（见 update-mask-counter-scope）",
      "组体内每个部分累加器必须是 plain mul+add、体内不做任何补偿；补偿只在循环结束后对 P 个部分量做一次",
      "循环结束的合并必须带有限值守卫，且折入 UB 携带的 (s,c) 状态时逐指令与既有非深 BMA 变体一致",
      "P 的上调必须受 VF 栈上限约束（该轮 6144B）：12 宽展开组体 + 逐块 UpdateMask 谓词寄存器会溢出，P 增大必须与掩码提升同时成立",
      "改动只允许落在两条 deep dispatch 分支与 BMA 组体：所有 Path A 段（AccumSegA）与其它桶必须逐字节保持 champion 代码"
    ],
    "excluded_conditions": [
      "Path A（AccumSegA 段）不在作用域内：direction_001 的 P=12 档在 Path A 同样回退（case2 42.7 vs 26.1、case20 79.4 vs 47.4），且没有 P=4 的安全证明",
      "subChunks<16 的桶不适用（该轮退化为 P=0 顺序路径）",
      "非有限 lane 语义、三区间回退（该轮 case11）与 blk=1 单核形状（case12）必须走 champion 行为，不得被本机制改写",
      "N 超出已证明范围（该轮为 N<=8192 fp32 的 P=4 位序证明）时，需要重新做 bit-order 仿真后才能启用对应 P 档",
      "纯 MTE2 受限的形状（该轮 Path A case14 aiv_mte2 0.969、case11 0.924）不适用：本机制只减少向量指令数，不改变 GM 流量"
    ],
    "required_conditions": [
      "累加循环使用逐元素补偿式运行累加器（该轮 KahanStepRot 每 64-lane 块约 12 条向量指令中有 8 条花在补偿上），且该相位由向量管道主导（该轮 aiv_vec 0.85-0.99）",
      "累加在循环体内的串行依赖链是每块周期的组成部分，可用 P 个独立部分累加器打断",
      "累加深度可枚举为互斥桶（该轮由 tiling 布局 [outer][N][inner] 决定的 subChunks 值），每桶可独立选择 P 而不影响其它桶",
      "存在逐块掩码开销可作为同桶的第二个杠杆：组内块恒为整块、只有尾块需要部分掩码",
      "每桶都有未触碰的对照域（其它桶、Path A）用于证明改动范围受限"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "task_0114_cumsum_mean",
      "operator_class": "scan",
      "precision": "20/20 PASS (worst case11 MARE 4.420e-03, three-region fallback unchanged)",
      "rounds_or_pairs": "2 对 ABBA 全 case 一致",
      "run_id": "<run-id>",
      "speedup": 1.2362,
      "status": "accepted"
    },
    {
      "operator": "task_0114_cumsum_mean",
      "operator_class": "scan",
      "precision": "20/20 PASS (worst case5 MARE 2.423e-04, limit 1.2207e-03)",
      "rounds_or_pairs": "2 对 balanced A,B,B,A（1.1040x / 1.1052x → 1.1046x；40 条逐 case 配对测量全部一致）",
      "run_id": "<run-id>",
      "speedup": 1.1046,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "aiv-vec",
      "compensated-serial-accumulator",
      "kahan-compensation-dominance"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "multi-accumulator-compensated-sum-bucket-dispatch",
    "reduce_mode": "sum",
    "structure": [
      "depth-bucketed-dispatch",
      "p-way-plain-partial-accumulators",
      "kahan-tree-combine",
      "hoisted-full-mask-group-body"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-MULTI-ACCUMULATOR-BUCKET-DISPATCH",
  "implementation_steps": [
    "建按累加深度分桶的 dispatch：RowReduceB/AccumChunkB 在 subChunks>=64 走 deep 变体、16<=subChunks<64 走 *BMA<T,4>、subChunks<16 走 *BMA<T,0>；全部 Path A 的 AccumSegA 保持 champion 的 KahanStepRot 逐字节不动",
    "循环体内用 P 个独立 plain mul+add 部分累加器（P=4）打断补偿式串行链，体内不做补偿；循环结束后对 P 个部分量做一次有限值守卫的 Kahan 合并，折入 UB 携带的 (s,c) 状态",
    "deep 变体的组体把逐块 Reg::UpdateMask 提升为单个整掩码（该轮新增 AccumChunkBMAD / RowReduceBMAD），依据 fullBlks = subChunks-1 的 guaranteed-full 论证；尾块 peel 并保留自己的 mt + fresh-dst Add/Select 合并、Kahan 部分和合并与有限保护",
    "尾块计数用标量直算（tailCnt = cnt − fullBlks*COLS，等价 POST_UPDATE 递减终值），避免引入新的掩码状态",
    "保留加载、掩码与非有限 lane 语义与既有非深 BMA 变体逐指令一致；非深桶与 Path A 逐字节不变"
  ],
  "intent": "消除补偿式运行累加器的向量指令浪费：champion 的 KahanStepRot 在每 64-lane 块约 12 条向量指令里花 8 条在补偿（sub,add,sub,sub,cmp,cmp,and,sel）上，而该相位在 deep 桶（该轮 case3/5/12/16，386.9us = 设备总时间的 30.2%，aiv_vec 0.85-0.99）是最后一段仍在跑这段代码的路径。",
  "mechanism": "按累加深度分桶的 dispatch 表：deep 桶（subChunks>=64）走 spill-free 的 AccumChunkBMAD/RowReduceBMAD（P=4 独立 plain mul+add 部分累加器，循环体内不做补偿，循环末一次有限值守卫的 Kahan 合并；组体把逐块 Reg::UpdateMask 提升为单个整掩码，因为 fullBlks = subChunks-1 使组内块 [0,fullBlks) 恒为整块，尾块单独 peel），non-deep 桶（16<=subChunks<64）走 *BMA<T,4>，subChunks<16 退化为 *BMA<T,0> 顺序；所有 Path A 段（AccumSegA）保持 champion 的 KahanStepRot 逐字节不动。机制内修复杠杆：P 在 6144B VF 栈上限内上调（4→8→12）、按桶把 P 降级（4→0）、按 dtype 门控补偿。掩码提升针对的正是此前 P=12 档寄存器溢出的根因。",
  "name": "按累加深度分桶的多累加器派发：补偿求和去补偿",
  "operator_class": "scan",
  "operator_scope": "带补偿式（Kahan/Neumaier 类）运行累加器的归约/扫描类算子：累加深度按 tiling 布局可枚举为互斥桶、逐块补偿开销在向量指令中占多数、且存在恒为整块的组内块可提升掩码；典型为 cumsum + 逐行归约类算子（如 task_0114_cumsum_mean）的多条累积路径",
  "principle": "补偿式累加（KahanStepRot 类）用每块 8 条指令换取精度，代价是把累加串行链拉长、并让补偿指令占据发射流：该轮每 64-lane 块约 12 条向量指令里 8 条是补偿。若循环体内改用 P 个互不依赖的 plain mul+add 部分累加器，块间串行依赖被打断、发射流被纯算术填满；补偿不必全程跟随，只在循环末对这 P 个部分量做一次 Kahan 合并即可保持等价的有限值语义（部分量的中间误差由最后的补偿合并与有限守卫吸收）。分桶是必要的：不同累加深度下寄存器/谓词压力不同，深循环还要额外抑制每块掩码开销，因此 P 与掩码策略必须按 subChunks 桶分别设定。",
  "related_anti_patterns": [
    "update-mask-counter-scope"
  ],
  "risks": [
    "P 不能无限上调：direction_001 的 P=12 deep 档在 12 宽展开组体 + 逐块 UpdateMask 谓词寄存器 + load 临时量下溢出 VF 栈（6144B 上限），deep case3/5/12/16 回退 2.1-3.4x（case5 465.6 vs 169.9us，且 aiv_vec_ratio 不变而 aiv_vec_time ~3x，是典型溢出签名）；必须先把逐块 Reg::UpdateMask 提升为整掩码，P 的上调才有意义",
    "整掩码提升依赖 guaranteed-full：组内块 [0,fullBlks) 恒有 remaining >= COLS，尾块必须 peel 并单独处理；把掩码计数器挪错作用域会造成非对齐尾块越界写 UB（见 update-mask-counter-scope）",
    "数值安全边界：P 路部分量只在该轮的 N<=8192 fp32（case5 恰为 fp32 subChunks=128 / inner N=8192）上经 bit-order CPU 仿真证明到 P=4 安全；bf16 阈值比 fp32 松 64 倍，但更深的循环或更宽的 N 需重新证明",
    "未被本机制覆盖的残余成本仍然显著：该轮 Path A 的 mte2 受限 case14 201.9us（aiv_mte2 0.969）+ case11 79.1us（0.924）合计约 281us 的 bulk-copy 族、case12 blk=1 单核、case9 123.0/case13 132.4us 的 P=0 残留",
    "改动范围的归因必须靠对照：该轮 deep 方向的非深与 Path A case 变化 ±1% 才证明范围严格受限；若对照域出现超噪声带变化，收益归因不成立"
  ],
  "slug": "multi-accumulator-compensated-sum-bucket-dispatch",
  "summary": "champion 的补偿式运行累加器（KahanStepRot）在每 64-lane 块约 12 条向量指令里有 8 条花在补偿上。改为按累加深度分桶的 dispatch 表：循环体内用 P 个独立 plain mul+add 部分累加器打断串行链（体内不做补偿），循环结束后对 P 个部分量做一次有限值守卫的 Kahan 合并。deep 桶（subChunks>=64）P=4，且组体把逐块 Reg::UpdateMask 提升为单个整掩码（guaranteed-full 块），这是此前 P=12 档寄存器溢出的根因修复；non-deep 桶（16<=subChunks<64）P=4，subChunks<16 退化为 P=0 顺序；所有 Path A 段保持 champion 的 KahanStepRot 逐字节不动。deep 桶 geomean 63.921→51.709us（1.2362x），non-deep 桶 70.931→64.215us（1.1046x）。",
  "verification": {
    "correctness": [
      "两个方向各自 20/20 精度通过、零精度修复轮（deep：case11 MARE 4.420e-03 三区间回退与 baseline 一致；non-deep：case5 MARE 2.423e-04，限 1.2207e-03）",
      "P 路部分量的数值安全性由 direction_001 的 bit-order CPU 仿真预测并在 kernel 上确认（如 case2 1.013e-04、case20 1.190e-07、P 档 case8 1.514e-07 与仿真 bit-exact）",
      "加载、掩码与非有限 lane 语义不变；非有限 lane（该轮 case12 inf / case13 NaN）由 judge 排除；case11 保持三区间回退"
    ],
    "performance": [
      "deep 桶：2 对 ABBA 全 case 一致，dtype-group geomean 63.921→51.709us（speedup 1.2362，+23.62%）；bf16 组 61.27→39.88us、fp32 组 60.62→49.37us、fp16 组 70.31→70.23us；deep case3/5/12/16 分别 −63.9% / −53.6% / −59.8% / −33.4%",
      "non-deep 桶：2 对 balanced A,B,B,A（1.1040x / 1.1052x → 1.1046x），geomean 70.931→64.215us；bf16 组 75.898→61.510、fp16 组 72.039→70.534、fp32 组 65.268→61.034；10 个在范围内 case 中 9 个改善 1.10-1.68x，40 条逐 case 配对测量全部一致",
      "改动范围受限的对照证据：deep 方向的非深桶与 Path A case 变化 ±1%；non-deep 方向被排除的桶（deep subChunks>=64、全部 Path A）保持 champion 行为"
    ],
    "rollback_signals": [
      "任一精度 case 在修复预算内 FAIL",
      "配对 ABBA geomean 相对冻结 champion（deep 基准 64.215us / non-deep 基准 70.931us）回退",
      "P=4 组体在 deep 循环 16-31 组下仍出现寄存器/谓词溢出（aiv_vec_ratio 不变而 aiv_vec_time 约 3x 即溢出签名）",
      "整掩码提升的 guaranteed-full 前提被破坏（尾块或非 COLS 整除长度）"
    ]
  }
}
-->

# 性能优化策略：按累加深度分桶的多累加器派发：补偿求和去补偿

champion 的补偿式运行累加器（KahanStepRot）在每 64-lane 块约 12 条向量指令里有 8 条花在补偿上。改为按累加深度分桶的 dispatch 表：循环体内用 P 个独立 plain mul+add 部分累加器打断串行链（体内不做补偿），循环结束后对 P 个部分量做一次有限值守卫的 Kahan 合并。deep 桶（subChunks>=64）P=4，且组体把逐块 Reg::UpdateMask 提升为单个整掩码（guaranteed-full 块），这是此前 P=12 档寄存器溢出的根因修复；non-deep 桶（16<=subChunks<64）P=4，subChunks<16 退化为 P=0 顺序；所有 Path A 段保持 champion 的 KahanStepRot 逐字节不动。deep 桶 geomean 63.921→51.709us（1.2362x），non-deep 桶 70.931→64.215us（1.1046x）。

## 1. 原理

补偿式累加（KahanStepRot 类）用每块 8 条指令换取精度，代价是把累加串行链拉长、并让补偿指令占据发射流：该轮每 64-lane 块约 12 条向量指令里 8 条是补偿。若循环体内改用 P 个互不依赖的 plain mul+add 部分累加器，块间串行依赖被打断、发射流被纯算术填满；补偿不必全程跟随，只在循环末对这 P 个部分量做一次 Kahan 合并即可保持等价的有限值语义（部分量的中间误差由最后的补偿合并与有限守卫吸收）。分桶是必要的：不同累加深度下寄存器/谓词压力不同，深循环还要额外抑制每块掩码开销，因此 P 与掩码策略必须按 subChunks 桶分别设定。

实现机制：按累加深度分桶的 dispatch 表：deep 桶（subChunks>=64）走 spill-free 的 AccumChunkBMAD/RowReduceBMAD（P=4 独立 plain mul+add 部分累加器，循环体内不做补偿，循环末一次有限值守卫的 Kahan 合并；组体把逐块 Reg::UpdateMask 提升为单个整掩码，因为 fullBlks = subChunks-1 使组内块 [0,fullBlks) 恒为整块，尾块单独 peel），non-deep 桶（16<=subChunks<64）走 *BMA<T,4>，subChunks<16 退化为 *BMA<T,0> 顺序；所有 Path A 段（AccumSegA）保持 champion 的 KahanStepRot 逐字节不动。机制内修复杠杆：P 在 6144B VF 栈上限内上调（4→8→12）、按桶把 P 降级（4→0）、按 dtype 门控补偿。掩码提升针对的正是此前 P=12 档寄存器溢出的根因。

该机制是「同一杠杆的两个作用域」而不是两个独立方向：deep 与非深两条证据只差 dispatch 表的桶边界与组体掩码策略，部分累加器结构、Kahan 合并与逐字节不动域完全相同，因此合并为一张卡，卡的核心内容就是这张按累加深度分桶的 dispatch 表。

## 2. 性能问题模式

- 优化目标：消除补偿式运行累加器的向量指令浪费：champion 的 KahanStepRot 在每 64-lane 块约 12 条向量指令里花 8 条在补偿（sub,add,sub,sub,cmp,cmp,and,sel）上，而该相位在 deep 桶（该轮 case3/5/12/16，386.9us = 设备总时间的 30.2%，aiv_vec 0.85-0.99）是最后一段仍在跑这段代码的路径。
- 适用数据流：带补偿式（Kahan/Neumaier 类）运行累加器的归约/扫描类算子：累加深度按 tiling 布局可枚举为互斥桶、逐块补偿开销在向量指令中占多数、且存在恒为整块的组内块可提升掩码；典型为 cumsum + 逐行归约类算子（如 task_0114_cumsum_mean）的多条累积路径
- Feature signature：`{"bottleneck": ["aiv-vec", "compensated-serial-accumulator", "kahan-compensation-dominance"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "multi-accumulator-compensated-sum-bucket-dispatch", "reduce_mode": "sum", "structure": ["depth-bucketed-dispatch", "p-way-plain-partial-accumulators", "kahan-tree-combine", "hoisted-full-mask-group-body"]}`

## 3. 正确性红线

- P 不能无限上调：direction_001 的 P=12 deep 档在 12 宽展开组体 + 逐块 UpdateMask 谓词寄存器 + load 临时量下溢出 VF 栈（6144B 上限），deep case3/5/12/16 回退 2.1-3.4x（case5 465.6 vs 169.9us，且 aiv_vec_ratio 不变而 aiv_vec_time ~3x，是典型溢出签名）；必须先把逐块 Reg::UpdateMask 提升为整掩码，P 的上调才有意义
- 整掩码提升依赖 guaranteed-full：组内块 [0,fullBlks) 恒有 remaining >= COLS，尾块必须 peel 并单独处理；把掩码计数器挪错作用域会造成非对齐尾块越界写 UB（见 update-mask-counter-scope）
- 数值安全边界：P 路部分量只在该轮的 N<=8192 fp32（case5 恰为 fp32 subChunks=128 / inner N=8192）上经 bit-order CPU 仿真证明到 P=4 安全；bf16 阈值比 fp32 松 64 倍，但更深的循环或更宽的 N 需重新证明
- 未被本机制覆盖的残余成本仍然显著：该轮 Path A 的 mte2 受限 case14 201.9us（aiv_mte2 0.969）+ case11 79.1us（0.924）合计约 281us 的 bulk-copy 族、case12 blk=1 单核、case9 123.0/case13 132.4us 的 P=0 残留
- 改动范围的归因必须靠对照：该轮 deep 方向的非深与 Path A case 变化 ±1% 才证明范围严格受限；若对照域出现超噪声带变化，收益归因不成立

资源与硬件约束：

- 整掩码提升必须建立在 guaranteed-full 论证之上：fullBlks = subChunks-1，组内 block [0, fullBlks) 恒满足 remaining >= COLS，尾块必须单独 peel 并用自己的 mt + fresh-dst Add/Select 合并；任何 subChunks/COLS 关系变化都会让整掩码越界（见 update-mask-counter-scope）
- 组体内每个部分累加器必须是 plain mul+add、体内不做任何补偿；补偿只在循环结束后对 P 个部分量做一次
- 循环结束的合并必须带有限值守卫，且折入 UB 携带的 (s,c) 状态时逐指令与既有非深 BMA 变体一致
- P 的上调必须受 VF 栈上限约束（该轮 6144B）：12 宽展开组体 + 逐块 UpdateMask 谓词寄存器会溢出，P 增大必须与掩码提升同时成立
- 改动只允许落在两条 deep dispatch 分支与 BMA 组体：所有 Path A 段（AccumSegA）与其它桶必须逐字节保持 champion 代码

## 4. 泛化条件

- 策略作用域：op_class：scan

适用：

- 累加循环使用逐元素补偿式运行累加器（该轮 KahanStepRot 每 64-lane 块约 12 条向量指令中有 8 条花在补偿上），且该相位由向量管道主导（该轮 aiv_vec 0.85-0.99）
- 累加在循环体内的串行依赖链是每块周期的组成部分，可用 P 个独立部分累加器打断
- 累加深度可枚举为互斥桶（该轮由 tiling 布局 [outer][N][inner] 决定的 subChunks 值），每桶可独立选择 P 而不影响其它桶
- 存在逐块掩码开销可作为同桶的第二个杠杆：组内块恒为整块、只有尾块需要部分掩码
- 每桶都有未触碰的对照域（其它桶、Path A）用于证明改动范围受限

不适用：

- Path A（AccumSegA 段）不在作用域内：direction_001 的 P=12 档在 Path A 同样回退（case2 42.7 vs 26.1、case20 79.4 vs 47.4），且没有 P=4 的安全证明
- subChunks<16 的桶不适用（该轮退化为 P=0 顺序路径）
- 非有限 lane 语义、三区间回退（该轮 case11）与 blk=1 单核形状（case12）必须走 champion 行为，不得被本机制改写
- N 超出已证明范围（该轮为 N<=8192 fp32 的 P=4 位序证明）时，需要重新做 bit-order 仿真后才能启用对应 P 档
- 纯 MTE2 受限的形状（该轮 Path A case14 aiv_mte2 0.969、case11 0.924）不适用：本机制只减少向量指令数，不改变 GM 流量

## 5. 实施步骤

1. 建按累加深度分桶的 dispatch：RowReduceB/AccumChunkB 在 subChunks>=64 走 deep 变体、16<=subChunks<64 走 *BMA<T,4>、subChunks<16 走 *BMA<T,0>；全部 Path A 的 AccumSegA 保持 champion 的 KahanStepRot 逐字节不动
2. 循环体内用 P 个独立 plain mul+add 部分累加器（P=4）打断补偿式串行链，体内不做补偿；循环结束后对 P 个部分量做一次有限值守卫的 Kahan 合并，折入 UB 携带的 (s,c) 状态
3. deep 变体的组体把逐块 Reg::UpdateMask 提升为单个整掩码（该轮新增 AccumChunkBMAD / RowReduceBMAD），依据 fullBlks = subChunks-1 的 guaranteed-full 论证；尾块 peel 并保留自己的 mt + fresh-dst Add/Select 合并、Kahan 部分和合并与有限保护
4. 尾块计数用标量直算（tailCnt = cnt − fullBlks*COLS，等价 POST_UPDATE 递减终值），避免引入新的掩码状态
5. 保留加载、掩码与非有限 lane 语义与既有非深 BMA 变体逐指令一致；非深桶与 Path A 逐字节不变

## 6. LLM 前置问题

- 目标实现是否满足：累加循环使用逐元素补偿式运行累加器（该轮 KahanStepRot 每 64-lane 块约 12 条向量指令中有 8 条花在补偿上），且该相位由向量管道主导（该轮 aiv_vec 0.85-0.99）？
- 目标实现是否满足：累加在循环体内的串行依赖链是每块周期的组成部分，可用 P 个独立部分累加器打断？
- 目标实现是否满足：累加深度可枚举为互斥桶（该轮由 tiling 布局 [outer][N][inner] 决定的 subChunks 值），每桶可独立选择 P 而不影响其它桶？
- 目标实现是否满足：存在逐块掩码开销可作为同桶的第二个杠杆：组内块恒为整块、只有尾块需要部分掩码？
- 目标实现是否满足：每桶都有未触碰的对照域（其它桶、Path A）用于证明改动范围受限？
- 是否命中排除条件：Path A（AccumSegA 段）不在作用域内？
- 是否命中排除条件：subChunks<16 的桶不适用（该轮退化为 P=0 顺序路径）？
- 是否命中排除条件：非有限 lane 语义、三区间回退（该轮 case11）与 blk=1 单核形状（case12）必须走 champion 行为？
- 是否命中排除条件：N 超出已证明范围（该轮为 N<=8192 fp32 的 P=4 位序证明）时，需要重新做 bit-order 仿真？
- 是否命中排除条件：纯 MTE2 受限的形状（该轮 Path A case14 aiv_mte2 0.969、case11 0.924）不适用？

## 7. 验收标准

正确性：

- 两个方向各自 20/20 精度通过、零精度修复轮（deep：case11 MARE 4.420e-03 三区间回退与 baseline 一致；non-deep：case5 MARE 2.423e-04，限 1.2207e-03）
- P 路部分量的数值安全性由 direction_001 的 bit-order CPU 仿真预测并在 kernel 上确认（如 case2 1.013e-04、case20 1.190e-07、P 档 case8 1.514e-07 与仿真 bit-exact）
- 加载、掩码与非有限 lane 语义不变；非有限 lane（该轮 case12 inf / case13 NaN）由 judge 排除；case11 保持三区间回退

性能：

- deep 桶：2 对 ABBA 全 case 一致，dtype-group geomean 63.921→51.709us（speedup 1.2362，+23.62%）；bf16 组 61.27→39.88us、fp32 组 60.62→49.37us、fp16 组 70.31→70.23us；deep case3/5/12/16 分别 −63.9% / −53.6% / −59.8% / −33.4%
- non-deep 桶：2 对 balanced A,B,B,A（1.1040x / 1.1052x → 1.1046x），geomean 70.931→64.215us；bf16 组 75.898→61.510、fp16 组 72.039→70.534、fp32 组 65.268→61.034；10 个在范围内 case 中 9 个改善 1.10-1.68x，40 条逐 case 配对测量全部一致
- 改动范围受限的对照证据：deep 方向的非深桶与 Path A case 变化 ±1%；non-deep 方向被排除的桶（deep subChunks>=64、全部 Path A）保持 champion 行为

回滚信号：

- 任一精度 case 在修复预算内 FAIL
- 配对 ABBA geomean 相对冻结 champion（deep 基准 64.215us / non-deep 基准 70.931us）回退
- P=4 组体在 deep 循环 16-31 组下仍出现寄存器/谓词溢出（aiv_vec_ratio 不变而 aiv_vec_time 约 3x 即溢出签名）
- 整掩码提升的 guaranteed-full 前提被破坏（尾块或非 COLS 整除长度）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：update-mask-counter-scope

- loop_20260912_174322（eid=free_explore_003, round=1, status=accepted, speedup=1.2362, precision=20/20 PASS）— deep 桶（subChunks>=64）P=4 + 整掩码提升
- loop_20260912_174322（eid=free_explore_002, round=1, status=accepted, speedup=1.1046, precision=20/20 PASS）— non-deep 桶（16<=subChunks<64）P=4 / subChunks<16 P=0

## 检索卡（短卡）

动作：按累加深度分桶派发，循环体内改用 P 个独立 plain mul+add 部分累加器，循环末一次守卫式 Kahan 合并，组体逐块掩码提升为整掩码。
适用：使用补偿式运行累加器且相位由向量管道主导（aiv_vec 0.85-0.99）、累加深度可按 tiling 布局枚举为互斥桶。
限制：Path A 与 subChunks<16 桶须逐字节保持；整掩码提升依赖 guaranteed-full，尾块须 peel。
范围：scan 类 cumsum + 逐行归约算子的多条累积路径。
检索词：KahanStepRot、UpdateMask、BMA、AccumChunkB、guaranteed-full、VF 栈
机会：每 64-lane 块约 12 条向量指令里 8 条花在补偿上，deep 桶占总时间 30.2%。
代价：P 上调受 6144B VF 栈上限约束；数值安全仅在 N<=8192 fp32 上证明。
