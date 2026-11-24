---
type: Optimization
title: 宿主机拟合代价模型分段路由：用实测 per-step 代价律 argmin 掉启发式下限
description: 把 kernel 的 segs>=4 与 router 每段>=16 tiles 两处下界改为 host 拟合闭式代价模型 argmin 分段深度。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/host-fitted-cost-model-seg-routing.md
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
      "argmin 必须 padding 感知：L_pad = segs*ceil(dTiles/segs)*32 参与代价，否则深分段把扫描尾撑大（case18 2080→3072 列的形态）",
      "必须带 chunk 感知的 rcCap 与 chunks 项：rcCap=(512/segs/8)*8、chunks=ceil(rowsPerCore/rcMax)，否则多 chunk case 会被误路由",
      "必须带 pass-2 combine 项（~250ns/segment/chunk），否则深分段被高估",
      "改路由与改 kernel 门必须同步：router 选出低于 4 的 segs 时 kernel 必须接受（SEG_MIN_COUNT 4→2），否则路由被 kernel 拒绝",
      ">=3% 预测收益门是零回退的保证：不满足就留在 legacy，本 run worst per-case ratio = 1.0000",
      "内层循环、pass-2 combine、buffer 布局与 split 路径一律不动，收益归因只能落在工作整形上"
    ],
    "excluded_conditions": [
      "内层循环不是本机制的作用面：direction_001（+25% 向量算子 -> +23.6%）与 direction_002（算子数持平、屏障 -38% -> +15.2%）两次证伪都指向工作整形而非指令流，本机制不改内层",
      "当引擎是 thread-per-line 且两遍扫描导致 GM 双读时不适用该代价律的结论：vf-thread-chunked-two-pass-scan 的『segs<4 净负』测的是线程每线模型 + GM 双读，本 champion 的 pass-2 combine 是 UB 驻留、每元素单读",
      "split 路径（rowNum==1，case12）不在本机制路由范围：其路由保持不动",
      "已饱和 512 lanes 的 case 没有可兑换的 lane 预算：case3/4/5/9/13 不改善（同一路由决策或噪声内）",
      "代价律换引擎/换形状族后必须重拟合：模型常数是拟合量，不是通用常量"
    ],
    "required_conditions": [
      "champion 的实测代价律可被闭式拟合并复现多数 case：step_ns ≈ 67 + 0.63*lanes 在冻结 champion（loop pair4_B msprof op_summary，64 blocks，20 case）上 18/20 落在 ±6% 内（case9 +18% multi-chunk、case19 -16% 小 case 开销），跨 legacy / segmented / split 三条路径成立",
      "固定项占比可量化且确实主导：67/(67+0.63*lanes) 在现行路由下 case1/6/7（16 lanes）87%、case8（25）81%、case10/15（33）76%、case14（47）69%、case11（56）66%、case17/18（65/64）62%、case2/16（128）45%；只有 512-lane 的 case3/4/5/9/13 饱和（17%）",
      "限制来自路由下界而非物理预算：13/20 case 停在 512 lanes 以下，成因是 kernel 的 seg gate segs>=4（cumsummin_kernel.h:77）与 router 的 segsByLen=dTiles/16（pybind11.cpp:113-117），不是 512-lane 预算",
      "分段引擎与 pass-2 combine 已被验证且是 UB 驻留单读：combine 形状无关、每元素只读一次 GM（case12 早已成功跑 segs=61，本 run 最深路由到 case16 的 segs=43）",
      "kernel 侧只需一个常量改动即可接受新路由：SEG_MIN_COUNT 4→2"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "cumsummin",
      "operator_class": "scan",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "speedup": 1.5001,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "fixed-per-step-interlock",
      "serial-column-step",
      "lane-count-underutilized",
      "heuristic-routing-floor"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "host-fitted-cost-model-seg-routing",
    "reduce_mode": "scan",
    "structure": [
      "closed-form-cost-model",
      "argmin-over-segs",
      "padding-aware-pad-length",
      "chunk-aware-rc-cap",
      "pass2-combine-cost-term",
      "3pct-predicted-win-gate",
      "kernel-seg-gate-lowered-to-2",
      "host-router-only-change"
    ]
  },
  "generality": "op_class",
  "id": "HOST-FITTED-COST-MODEL-SEG-ROUTING",
  "implementation_steps": [
    "在冻结 champion 上实测拟合代价律：按 64 blocks 逐 case 取 op_summary，得 step_ns ≈ 67 + 0.63*lanes，并核对复现率（本 run 18/20 在 ±6% 内）与固定项占比 67/(67+0.63*lanes)",
    "定位并替换两个启发式下界：kernel 的 segs>=SEG_MIN_COUNT(4)（cumsummin_kernel.h:77）与 router 的每段 >=16 tiles（pybind11.cpp:113-117）",
    "在 host router 实现闭式 argmin：segs∈[2..64] 且 segs*ceil8(rcMax)<=512，代价含 step = 67ns + 0.63ns*lanes、L_pad = segs*ceil(dTiles/segs)*32、rcCap=(512/segs/8)*8、chunks=ceil(rowsPerCore/rcMax)、pass-2 combine ~250ns/segment/chunk",
    "只保留 >=3% 预测收益才改路由的闸门，split 路径（rowNum==1）路由不动；kernel 侧 SEG_MIN_COUNT 4→2 与之同步",
    "以 20/20 精度 + 形式化配对 ABBA（provenance-clean 双 .so、A 侧复现 sealed baseline）验收，并核对无 case 回退（本 run worst per-case ratio = 1.0000）"
  ],
  "intent": "把 13/20 个被启发式下界钉在 16-72 lanes、固定项占 62-87% 的小/中 case 提升到 lane 饱和（用更深的列分段摊薄每步 ~67ns 的宽度无关 interlock 代价），且不触碰已被两次证伪的内层循环。",
  "mechanism": "host-fitted-cost-model-seg-routing：kernel/pybind11.cpp 用 padding 与 chunk 感知的闭式代价模型替换原来的两个启发式下界（segs>=4 与每段 >=16 tiles=512 列），在 segs∈[2..64]（且 segs*ceil8(rcMax)<=512）上取 argmin：步代价 step = 67ns + 0.63ns*lanes（在冻结 champion 的 loop pair4_B msprof op_summary、64 blocks、20 case 上拟合，18/20 落在 ±6% 内），L_pad = segs*ceil(dTiles/segs)*32（padding 感知的扫描长度），rcCap = (512/segs/8)*8，chunks = ceil(rowsPerCore/rcMax)，pass-2 combine ~250ns/segment/chunk；只有当预测收益相对 per-chunk legacy 代价 >=3% 时才路由到分段路径，split 路径（rowNum==1）路由不动。kernel/cumsummin_kernel.h 把 SEG_MIN_COUNT 4→2，使 kernel 接受新路由出的低 segs 配置；内层循环、pass-2 combine、buffer 布局、split 路径均未改动（纯路由/工作整形，数值只差已验证的 ulp 级 pass-2 重结合）。路由结果：case1/6/7 segs=16、case2 16、case8 13、case10 9、case11 32、case14 8、case15 8、case16 43、case17 4、case18 22、case19 2、case20 3；已饱和的 case3/4/5 保持 segs 8/4/4，case9/13 保持 legacy，case12 走 split 不变。",
  "name": "宿主机拟合代价模型分段路由：用实测 per-step 代价律 argmin 掉启发式下限",
  "operator_class": "scan",
  "operator_scope": "存在可深化的列分段引擎、且每核 wall 由串行列步的固定项主导的扫描/前缀类算子（本 run cumsummin 20 case，512-lane 预算、segs 引擎已验证 4..61）；瓶颈是 fixed-per-step-interlock，而不是每元素算力或访存。",
  "principle": "当一段串行列步的代价由固定项主导时，wall 由步数而不是由每步宽度决定：本 run 的代价律 step_ns ≈ 67 + 0.63*lanes 里，67ns（≈107 cycles）是与宽度无关的 interlock 代价，(Add; Min; 2×PipeBarrier) 每组列步付一次，于是每核总固定代价 = 67ns × steps × chunks，固定项在低 lanes 时占绝对多数（16 lanes 87%、25 lanes 81%、33 lanes 76%、128 lanes 45%）。此时唯一的摊销手段是把串行步数按段数除下去——即更深的列分段，而分段引擎早就存在，只是被两个启发式下界挡住。把『什么时候启用、启用多深』从启发式（segs>=4、每段>=512 列）换成对冻结 champion 拟合出的闭式代价模型 + argmin，收益直接来自把闲置的 lane 预算换成分段深度，而不是来自任何内层循环改动——这是本机制与两次被证伪的内层重构（direction_001 向量算子 +25% 只换来 +23.6%；direction_002 屏障 -38% 换来 +15.2%）的本质区别。模型必须同时含三项才安全：padding 感知的扫描长度（否则深分段把扫描尾撑大）、chunk 感知的 rcCap 与 chunks、以及 pass-2 combine 的每段每 chunk 代价（否则深分段被高估）。",
  "related_anti_patterns": [],
  "risks": [
    "代价模型是拟合量：换引擎或换形状族后常数不再成立，argmin 会误路由；必须先在冻结 champion 上重新拟合并验证复现率（本 run 18/20 在 ±6% 内，case9 +18% multi-chunk、case19 -16% 小 case 开销）",
    "只按步数削减而忽略 padding 会把扫描尾撑大（本 run 朴素按最大 segs 路由会把 case18 从 2080 撑到 3072 列），必须让 L_pad = segs*ceil(dTiles/segs)*32 参与 argmin（本 run 所有被路由扫描的 padding 控制在 +1.6% 内）",
    "深分段 case 的绝对预测会高估：模型外还有 ~20-27us/例的 per-case floor（装载/epilogue），argmin 仍安全但预测值偏乐观（实测 1.15-3.05x vs 预测 1.04-4.4x）",
    "外部库证据的『segs<4 净负』不能跨代价结构搬运：那是 thread-per-line 引擎 + GM 双读的结论，本 champion 的 pass-2 combine 是 UB 驻留、每元素单读，重复到 segs=2 仍净正（case19 在 segs=2 下 ratio 0.868）",
    "route 与 kernel 门不同步会让选出的 segs 被 kernel 拒绝，或（更坏）回退到未验证的配置"
  ],
  "slug": "host-fitted-cost-model-seg-routing",
  "summary": "cumsummin champion 的实测代价律是 T_case ≈ chunks × steps × (67ns + 0.63ns × lanes)（steps = paddedScan/segs、lanes = segs*rcW <= 512）：每个串行 (Add; Min; 2×PipeBarrier) 列步都带一个与宽度无关的 ~67ns interlock 代价，故每核固定代价 = 67ns × scanLen/segs × chunks。路由里两个人造下界（kernel 的 segs>=SEG_MIN_COUNT(4)、router 的 dTiles/16 即每段 >=512 列）把 13/20 个 case 钉在 16-72 lanes，固定项占到 case 时长的 62-87%（16 lanes 时 87%、33 lanes 76%、128 lanes 45%），只有 512-lane 的 case 3/4/5/9/13 饱和。改为在宿主机用实测拟合的闭式代价模型做 argmin（step = 67ns + 0.63ns*lanes、padding 感知 L_pad = segs*ceil(dTiles/segs)*32、chunk 感知 rcCap=(512/segs/8)*8 与 chunks=ceil(rowsPerCore/rcMax)、pass-2 combine ~250ns/segment/chunk），在 segs∈[2..64]（且 segs*ceil8(rcMax)<=512）上取 argmin，仅当预测收益 >=3% 才改路由，并把 kernel 的 seg 门从 4 降到 2；内层循环、pass-2 combine、split 路径与 buffer 布局一律不动。geomean 118.853→79.228us（1.5001x，6 对 balanced ABBA / 12 runs，worst per-case ratio 1.0000 无回退），精度 20/20 首次通过。",
  "verification": {
    "correctness": [
      "20/20 PASS，首次通过（纯路由变更，数值与已校验的 ulp 级 pass-2 重结合一致；编译与精度均零修复轮次）",
      "被路由 case 使用的 pass-2 combine 语义与形状无关，且在 segs 4..61 上已验证（case12 早已成功跑 segs=61）",
      "split 路径（rowNum==1）路由未改动：case12 124.20→124.01us 无变化"
    ],
    "performance": [
      "形式化配对 ABBA 6 对 / 12 runs（balanced alternating，provenance clean，A 侧在 0.03% 内复现 sealed baseline）：geomean 118.853→79.228us（1.5001x），worst per-case ratio 1.0000（无回退）",
      "screening 118.884→79.252us（1.50x）",
      "13 个原先被下界钉住的 case 改到 lane 饱和的列分段，实测逐 case 收益 1.15-3.05x（预测 1.04-4.4x）：case01 80.85→26.98、case06 80.01→26.16、case07 80.02→26.16、case08 68.06→31.68、case10 52.53→29.64、case11 62.46→40.00、case14 99.21→50.08、case15 49.87→27.51、case16 87.29→67.96、case17 61.24→41.75、case18 62.62→39.11、case19 46.37→40.26、case20 171.16→141.86us",
      "饱和 case 3/4/5/9/13 与 split case12 不变（208.32/798.90/789.46/632.96/250.66/124.20 -> 208.29/798.85/789.48/632.84/250.52/124.01us）"
    ],
    "rollback_signals": [
      "代价模型复现率跌破验收线（本 run 18/20 在 ±6% 内）：换引擎/形状族后必须重拟合，不能沿用常数",
      "任一 case 在配对 ABBA 中出现超出噪声的回退（本 run worst per-case ratio = 1.0000）",
      "padding 未参与 argmin 导致扫描尾被撑大（case18 2080→3072 列形态）",
      "router 与 kernel 门不同步（选出的 segs 被 kernel 拒绝）",
      "精度中出现超出 ulp 级 pass-2 重结合的变化"
    ]
  }
}
-->

# 性能优化策略：宿主机拟合代价模型分段路由：用实测 per-step 代价律 argmin 掉启发式下限

cumsummin champion 的实测代价律是 T_case ≈ chunks × steps × (67ns + 0.63ns × lanes)（steps = paddedScan/segs、lanes = segs*rcW <= 512）：每个串行 (Add; Min; 2×PipeBarrier) 列步都带一个与宽度无关的 ~67ns interlock 代价，故每核固定代价 = 67ns × scanLen/segs × chunks。路由里两个人造下界（kernel 的 segs>=SEG_MIN_COUNT(4)、router 的 dTiles/16 即每段 >=512 列）把 13/20 个 case 钉在 16-72 lanes，固定项占到 case 时长的 62-87%（16 lanes 时 87%、33 lanes 76%、128 lanes 45%），只有 512-lane 的 case 3/4/5/9/13 饱和。改为在宿主机用实测拟合的闭式代价模型做 argmin（step = 67ns + 0.63ns*lanes、padding 感知 L_pad = segs*ceil(dTiles/segs)*32、chunk 感知 rcCap=(512/segs/8)*8 与 chunks=ceil(rowsPerCore/rcMax)、pass-2 combine ~250ns/segment/chunk），在 segs∈[2..64]（且 segs*ceil8(rcMax)<=512）上取 argmin，仅当预测收益 >=3% 才改路由，并把 kernel 的 seg 门从 4 降到 2；内层循环、pass-2 combine、split 路径与 buffer 布局一律不动。geomean 118.853→79.228us（1.5001x，6 对 balanced ABBA / 12 runs，worst per-case ratio 1.0000 无回退），精度 20/20 首次通过。

## 1. 原理

当一段串行列步的代价由固定项主导时，wall 由步数而不是由每步宽度决定：本 run 的代价律 step_ns ≈ 67 + 0.63*lanes 里，67ns（≈107 cycles）是与宽度无关的 interlock 代价，(Add; Min; 2×PipeBarrier) 每组列步付一次，于是每核总固定代价 = 67ns × steps × chunks，固定项在低 lanes 时占绝对多数（16 lanes 87%、25 lanes 81%、33 lanes 76%、128 lanes 45%）。此时唯一的摊销手段是把串行步数按段数除下去——即更深的列分段，而分段引擎早就存在，只是被两个启发式下界挡住。把『什么时候启用、启用多深』从启发式（segs>=4、每段>=512 列）换成对冻结 champion 拟合出的闭式代价模型 + argmin，收益直接来自把闲置的 lane 预算换成分段深度，而不是来自任何内层循环改动——这是本机制与两次被证伪的内层重构（direction_001 向量算子 +25% 只换来 +23.6%；direction_002 屏障 -38% 换来 +15.2%）的本质区别。模型必须同时含三项才安全：padding 感知的扫描长度（否则深分段把扫描尾撑大）、chunk 感知的 rcCap 与 chunks、以及 pass-2 combine 的每段每 chunk 代价（否则深分段被高估）。

实现机制：host-fitted-cost-model-seg-routing：kernel/pybind11.cpp 用 padding 与 chunk 感知的闭式代价模型替换原来的两个启发式下界（segs>=4 与每段 >=16 tiles=512 列），在 segs∈[2..64]（且 segs*ceil8(rcMax)<=512）上取 argmin：步代价 step = 67ns + 0.63ns*lanes（在冻结 champion 的 loop pair4_B msprof op_summary、64 blocks、20 case 上拟合，18/20 落在 ±6% 内），L_pad = segs*ceil(dTiles/segs)*32（padding 感知的扫描长度），rcCap = (512/segs/8)*8，chunks = ceil(rowsPerCore/rcMax)，pass-2 combine ~250ns/segment/chunk；只有当预测收益相对 per-chunk legacy 代价 >=3% 时才路由到分段路径，split 路径（rowNum==1）路由不动。kernel/cumsummin_kernel.h 把 SEG_MIN_COUNT 4→2，使 kernel 接受新路由出的低 segs 配置；内层循环、pass-2 combine、buffer 布局、split 路径均未改动（纯路由/工作整形，数值只差已验证的 ulp 级 pass-2 重结合）。路由结果：case1/6/7 segs=16、case2 16、case8 13、case10 9、case11 32、case14 8、case15 8、case16 43、case17 4、case18 22、case19 2、case20 3；已饱和的 case3/4/5 保持 segs 8/4/4，case9/13 保持 legacy，case12 走 split 不变。

## 2. 性能问题模式

- 优化目标：把 13/20 个被启发式下界钉在 16-72 lanes、固定项占 62-87% 的小/中 case 提升到 lane 饱和（用更深的列分段摊薄每步 ~67ns 的宽度无关 interlock 代价），且不触碰已被两次证伪的内层循环。
- 适用数据流：存在可深化的列分段引擎、且每核 wall 由串行列步的固定项主导的扫描/前缀类算子（本 run cumsummin 20 case，512-lane 预算、segs 引擎已验证 4..61）；瓶颈是 fixed-per-step-interlock，而不是每元素算力或访存。
- Feature signature：`{"bottleneck": ["fixed-per-step-interlock", "serial-column-step", "lane-count-underutilized", "heuristic-routing-floor"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "host-fitted-cost-model-seg-routing", "reduce_mode": "scan", "structure": ["closed-form-cost-model", "argmin-over-segs", "padding-aware-pad-length", "chunk-aware-rc-cap", "pass2-combine-cost-term", "3pct-predicted-win-gate", "kernel-seg-gate-lowered-to-2", "host-router-only-change"]}`

## 3. 正确性红线

- 代价模型是拟合量：换引擎或换形状族后常数不再成立，argmin 会误路由；必须先在冻结 champion 上重新拟合并验证复现率（本 run 18/20 在 ±6% 内，case9 +18% multi-chunk、case19 -16% 小 case 开销）
- 只按步数削减而忽略 padding 会把扫描尾撑大（本 run 朴素按最大 segs 路由会把 case18 从 2080 撑到 3072 列），必须让 L_pad = segs*ceil(dTiles/segs)*32 参与 argmin（本 run 所有被路由扫描的 padding 控制在 +1.6% 内）
- 深分段 case 的绝对预测会高估：模型外还有 ~20-27us/例的 per-case floor（装载/epilogue），argmin 仍安全但预测值偏乐观（实测 1.15-3.05x vs 预测 1.04-4.4x）
- 外部库证据的『segs<4 净负』不能跨代价结构搬运：那是 thread-per-line 引擎 + GM 双读的结论，本 champion 的 pass-2 combine 是 UB 驻留、每元素单读，重复到 segs=2 仍净正（case19 在 segs=2 下 ratio 0.868）
- route 与 kernel 门不同步会让选出的 segs 被 kernel 拒绝，或（更坏）回退到未验证的配置

资源与硬件约束：

- argmin 必须 padding 感知：L_pad = segs*ceil(dTiles/segs)*32 参与代价，否则深分段把扫描尾撑大（case18 2080→3072 列的形态）
- 必须带 chunk 感知的 rcCap 与 chunks 项：rcCap=(512/segs/8)*8、chunks=ceil(rowsPerCore/rcMax)，否则多 chunk case 会被误路由
- 必须带 pass-2 combine 项（~250ns/segment/chunk），否则深分段被高估
- 改路由与改 kernel 门必须同步：router 选出低于 4 的 segs 时 kernel 必须接受（SEG_MIN_COUNT 4→2），否则路由被 kernel 拒绝
- >=3% 预测收益门是零回退的保证：不满足就留在 legacy，本 run worst per-case ratio = 1.0000
- 内层循环、pass-2 combine、buffer 布局与 split 路径一律不动，收益归因只能落在工作整形上

## 4. 泛化条件

- 策略作用域：op_class：scan

适用：

- champion 的实测代价律可被闭式拟合并复现多数 case：step_ns ≈ 67 + 0.63*lanes 在冻结 champion（loop pair4_B msprof op_summary，64 blocks，20 case）上 18/20 落在 ±6% 内（case9 +18% multi-chunk、case19 -16% 小 case 开销），跨 legacy / segmented / split 三条路径成立
- 固定项占比可量化且确实主导：67/(67+0.63*lanes) 在现行路由下 case1/6/7（16 lanes）87%、case8（25）81%、case10/15（33）76%、case14（47）69%、case11（56）66%、case17/18（65/64）62%、case2/16（128）45%；只有 512-lane 的 case3/4/5/9/13 饱和（17%）
- 限制来自路由下界而非物理预算：13/20 case 停在 512 lanes 以下，成因是 kernel 的 seg gate segs>=4（cumsummin_kernel.h:77）与 router 的 segsByLen=dTiles/16（pybind11.cpp:113-117），不是 512-lane 预算
- 分段引擎与 pass-2 combine 已被验证且是 UB 驻留单读：combine 形状无关、每元素只读一次 GM（case12 早已成功跑 segs=61，本 run 最深路由到 case16 的 segs=43）
- kernel 侧只需一个常量改动即可接受新路由：SEG_MIN_COUNT 4→2

不适用：

- 内层循环不是本机制的作用面：direction_001（+25% 向量算子 -> +23.6%）与 direction_002（算子数持平、屏障 -38% -> +15.2%）两次证伪都指向工作整形而非指令流，本机制不改内层
- 当引擎是 thread-per-line 且两遍扫描导致 GM 双读时不适用该代价律的结论：vf-thread-chunked-two-pass-scan 的『segs<4 净负』测的是线程每线模型 + GM 双读，本 champion 的 pass-2 combine 是 UB 驻留、每元素单读
- split 路径（rowNum==1，case12）不在本机制路由范围：其路由保持不动
- 已饱和 512 lanes 的 case 没有可兑换的 lane 预算：case3/4/5/9/13 不改善（同一路由决策或噪声内）
- 代价律换引擎/换形状族后必须重拟合：模型常数是拟合量，不是通用常量

## 5. 实施步骤

1. 在冻结 champion 上实测拟合代价律：按 64 blocks 逐 case 取 op_summary，得 step_ns ≈ 67 + 0.63*lanes，并核对复现率（本 run 18/20 在 ±6% 内）与固定项占比 67/(67+0.63*lanes)
2. 定位并替换两个启发式下界：kernel 的 segs>=SEG_MIN_COUNT(4)（cumsummin_kernel.h:77）与 router 的每段 >=16 tiles（pybind11.cpp:113-117）
3. 在 host router 实现闭式 argmin：segs∈[2..64] 且 segs*ceil8(rcMax)<=512，代价含 step = 67ns + 0.63ns*lanes、L_pad = segs*ceil(dTiles/segs)*32、rcCap=(512/segs/8)*8、chunks=ceil(rowsPerCore/rcMax)、pass-2 combine ~250ns/segment/chunk
4. 只保留 >=3% 预测收益才改路由的闸门，split 路径（rowNum==1）路由不动；kernel 侧 SEG_MIN_COUNT 4→2 与之同步
5. 以 20/20 精度 + 形式化配对 ABBA（provenance-clean 双 .so、A 侧复现 sealed baseline）验收，并核对无 case 回退（本 run worst per-case ratio = 1.0000）

## 6. LLM 前置问题

- 目标实现是否满足：champion 的实测代价律可被闭式拟合并复现多数 case：step_ns ≈ 67 + 0.63*lanes 在冻结 champion（loop pair4_B msprof op_summary，64 blocks，20 case）上 18/20 落在 ±6% 内（case9 +18% multi-chunk、case19 -16% 小 case 开销），跨 legacy / segmented / split 三条路径成立？
- 目标实现是否满足：固定项占比可量化且确实主导：67/(67+0.63*lanes) 在现行路由下 case1/6/7（16 lanes）87%、case8（25）81%、case10/15（33）76%、case14（47）69%、case11（56）66%、case17/18（65/64）62%、case2/16（128）45%；只有 512-lane 的 case3/4/5/9/13 饱和（17%）？
- 目标实现是否满足：限制来自路由下界而非物理预算：13/20 case 停在 512 lanes 以下，成因是 kernel 的 seg gate segs>=4（cumsummin_kernel.h:77）与 router 的 segsByLen=dTiles/16（pybind11.cpp:113-117），不是 512-lane 预算？
- 目标实现是否满足：分段引擎与 pass-2 combine 已被验证且是 UB 驻留单读：combine 形状无关、每元素只读一次 GM（case12 早已成功跑 segs=61，本 run 最深路由到 case16 的 segs=43）？
- 目标实现是否满足：kernel 侧只需一个常量改动即可接受新路由：SEG_MIN_COUNT 4→2？
- 是否命中排除条件：内层循环不是本机制的作用面：direction_001（+25% 向量算子 -> +23.6%）与 direction_002（算子数持平、屏障 -38% -> +15.2%）两次证伪都指向工作整形而非指令流，本机制不改内层？
- 是否命中排除条件：当引擎是 thread-per-line 且两遍扫描导致 GM 双读时不适用该代价律的结论：vf-thread-chunked-two-pass-scan 的『segs<4 净负』测的是线程每线模型 + GM 双读，本 champion 的 pass-2 combine 是 UB 驻留、每元素单读？
- 是否命中排除条件：split 路径（rowNum==1，case12）不在本机制路由范围：其路由保持不动？
- 是否命中排除条件：已饱和 512 lanes 的 case 没有可兑换的 lane 预算：case3/4/5/9/13 不改善（同一路由决策或噪声内）？
- 是否命中排除条件：代价律换引擎/换形状族后必须重拟合：模型常数是拟合量，不是通用常量？

## 7. 验收标准

正确性：

- 20/20 PASS，首次通过（纯路由变更，数值与已校验的 ulp 级 pass-2 重结合一致；编译与精度均零修复轮次）
- 被路由 case 使用的 pass-2 combine 语义与形状无关，且在 segs 4..61 上已验证（case12 早已成功跑 segs=61）
- split 路径（rowNum==1）路由未改动：case12 124.20→124.01us 无变化

性能：

- 形式化配对 ABBA 6 对 / 12 runs（balanced alternating，provenance clean，A 侧在 0.03% 内复现 sealed baseline）：geomean 118.853→79.228us（1.5001x），worst per-case ratio 1.0000（无回退）
- screening 118.884→79.252us（1.50x）
- 13 个原先被下界钉住的 case 改到 lane 饱和的列分段，实测逐 case 收益 1.15-3.05x（预测 1.04-4.4x）：case01 80.85→26.98、case06 80.01→26.16、case07 80.02→26.16、case08 68.06→31.68、case10 52.53→29.64、case11 62.46→40.00、case14 99.21→50.08、case15 49.87→27.51、case16 87.29→67.96、case17 61.24→41.75、case18 62.62→39.11、case19 46.37→40.26、case20 171.16→141.86us
- 饱和 case 3/4/5/9/13 与 split case12 不变（208.32/798.90/789.46/632.96/250.66/124.20 -> 208.29/798.85/789.48/632.84/250.52/124.01us）

回滚信号：

- 代价模型复现率跌破验收线（本 run 18/20 在 ±6% 内）：换引擎/形状族后必须重拟合，不能沿用常数
- 任一 case 在配对 ABBA 中出现超出噪声的回退（本 run worst per-case ratio = 1.0000）
- padding 未参与 argmin 导致扫描尾被撑大（case18 2080→3072 列形态）
- router 与 kernel 门不同步（选出的 segs 被 kernel 拒绝）
- 精度中出现超出 ulp 级 pass-2 重结合的变化

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`

- loop_20260917_024611 status=accepted, speedup=1.5001, precision=20/20 PASS）

## 检索卡（短卡）

动作：把 kernel 的 segs>=4 与 router 每段>=16 tiles 两处下界改为 host 拟合闭式代价模型 argmin 分段深度。
适用：已有可深化的列分段引擎、每核 wall 由串行列步固定项主导的扫描类算子。
限制：模型常数是拟合量，换形状族须重拟合；argmin 漏 padding/chunk 项会误路由；须与 kernel 门同步。
范围：扫描/前缀类算子的列分段路由，split 与内层循环不动。
检索词：step_ns、interlock、argmin、L_pad、SEG_MIN_COUNT、pass-2 combine
机会：每步约 67ns interlock 代价主导，13/20 case 被下界钉在 16-72 lanes。
代价：模型外还有约 20-27us/例 per-case floor，深分段预测偏乐观。
