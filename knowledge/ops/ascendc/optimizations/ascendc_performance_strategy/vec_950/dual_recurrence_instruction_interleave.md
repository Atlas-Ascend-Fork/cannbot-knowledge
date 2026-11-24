---
type: Optimization
title: 跨 chunk 双递推链指令级交错：扫描链延迟隐藏
description: 饱和多 chunk 场景（totalChunks >= 64 向量核）被单条 64-lane 递推的 per-position 串行率钉住（该轮实测每核 7.67-8.81 ns/position，与单链单核参考 8.06 ns/pos 一致），每核是 latency-bound 而非 issue-bound。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/dual-recurrence-instruction-interleave.md
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
      "UB 占用必须与 champion 持平：dual 时 tilePos 减半（fp32 128->64，fp16/bf16 256->128），四条队列（inA/inB/outA/outB）各深 2 x 16KB = 128KB，与 champion 的 2 队列 x 深 2 x 32KB 相等；任何加队列深度或回调 tilePos 的变体都可能 UB 溢出",
      "门控必须是 dualMode = (segSplitMode==0 && chunkPerCore>=2)：segSplitMode 路径与 chunkPerCore<2 的 few-chunk 形状必须留在 champion 路径，不可强行交错",
      "奇数尾 chunk 必须回落到 A 队列的单链 champion 路径，保证 chunk 覆盖完整",
      "两条链的逐行递推、元素顺序与舍入必须 bit 级不变：交错只允许是指令顺序的重排，不允许任何代数重写"
    ],
    "excluded_conditions": [
      "segSplitMode 路径（沿扫描轴切分、每核只持一个 chunk 的两趟扫描）结构上无法配对，不适用本机制",
      "每核 chunk 数 < 2（chunkPerCore<2 / totalChunks <= coreNum）的形状没有可配对的第二条独立链，不适用",
      "若向量管道实为发射带宽饱和（issue-bound）而非停顿归因（latency-bound），交错无收益：该轮 aiv_vec_ratio 0.991 的停顿归因是结论成立的前提，未独立证实前不得立项",
      "非饱和情形下已有更便宜的加核/切分手段（如 vf-thread-chunked-two-pass-scan 对少数长扫描形状）时不适用"
    ],
    "required_conditions": [
      "每核持有 >=2 个完全独立的 chunk，且每个 chunk 的递推只沿自身扫描轴（跨 chunk 无依赖）",
      "每核吞吐被单链 per-position 串行率封顶：该轮饱和 case 实测 7.67-8.81 ns/position/core，与孤立单链单核参考值 8.06 ns/pos 一致",
      "核心数已用尽（blockDim = 64 = 物理向量核数），加核不再是可选杠杆",
      "kernel 为纯向量核（全部 aic pipe 0.0）、无 MTE/scalar 重叠余量可挖",
      "存在可融合统一 tile 循环的两条同构递推（该轮两条 64-lane (rmax,rsum) 链，指令序列完全相同）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "logcumsumexp__v2",
      "operator_class": "scan",
      "precision": "20/20 PASS (worst case3 bf16 MARE 7.752e-3 < 1e-2)",
      "rounds_or_pairs": "4 对 balanced-alternating ABBA（同 shape、provenance clean，每对方向一致）",
      "run_id": "<run-id>",
      "speedup": 1.1527,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scan-chain-latency",
      "dependency-stall-bubbles",
      "latency-bound-not-issue-bound"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "dual-recurrence-instruction-interleave",
    "reduce_mode": "scan",
    "structure": [
      "two-chunk-pairing",
      "instruction-granular-interleave",
      "four-queue-ub-neutral",
      "bit-identical-recurrence"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-DUAL-RECURRENCE-INTERLEAVE",
  "implementation_steps": [
    "新增双链实现（该轮 LogcumsumexpDualScanImpl/DualScan）：把两条独立的 64-lane (rmax,rsum) 递推按指令粒度交错（loadA,loadB,cmpA,cmpB,subA,subB,expA,expB,…），每条链内部的指令序列与 champion 的单链实现完全一致",
    "复制队列资源：新增 inputQueueB_/outputQueueB_/stateBufB_，并把 CopyIn/CopyOut 泛化为队列参数，使两路数据各自独立流动",
    "Process() 增加路由：dualMode 时走 ProcessDual，chunk 两两配对成融合 tile 循环（CopyInA,CopyInB,ComputeDual,CopyOutA,CopyOutB）；奇数尾 chunk 用 A 队列单链回退",
    "tiling 增加 uint32_t dualMode 字段，host 侧判定 dualMode = (segSplitMode==0 && chunkPerCore>=2)",
    "dual 时 tilePos 减半（fp32 128->64，fp16/bf16 256->128）以保持 UB 足迹与 champion 持平（4 队列 x 深 2 x 16KB = 128KB）"
  ],
  "intent": "消除饱和多 chunk 形状上单条 64-lane 扫描链的 per-position 串行延迟封顶：该轮饱和 case（totalChunks >= 64 向量核，如 case4/case5 各 8192 chunks = 128/core）每核实测 7.67-8.81 ns/position，与孤立单链单核参考值 8.06 ns/pos 相同，说明每核是 latency-bound（被 cast->compare->sub->select->exp->mul->adds->select 依赖链钉住）而非 issue-bound，核数、MTE 与发射带宽都无杠杆。",
  "mechanism": "把每核的 chunk 列表两两成组，在同一个融合 tile 循环里把两条独立递推逐指令交错（A.step; B.step; A.step; B.step; …），使 chunk-B 的指令落进 chunk-A 的依赖停顿气泡（反之亦然）。每链内部的指令序列、逐行递推、元素顺序与舍入与 champion 单链实现 bit 级一致，因此精度中性、纯 ILP。配套资源：复制一套 in/out/state 队列（inA/inB/outA/outB），并把 tilePos 减半以维持 UB 占用不变。奇数尾 chunk 回落到 A 队列单链路径；segSplitMode 与 chunkPerCore<2 的路径完全不进入 dualMode。",
  "name": "跨 chunk 双递推链指令级交错：扫描链延迟隐藏",
  "operator_class": "scan",
  "operator_scope": "扫描（scan / prefix-recurrence）类算子：每核持有多个完全独立的一维递推 chunk、每核吞吐被单链 per-position 串行延迟封顶、核心数已用尽且 kernel 纯向量（无 MTE/scalar 重叠余量）的饱和形状；dtype 覆盖 fp16/bf16/fp32（fp32 用双 exp 链、fp16/bf16 用共享 exp 链，两条链各自同构即可交错）",
  "principle": "串行递推的吞吐上限不是发射带宽而是依赖链延迟：每 position 的关键路径由 cast->compare->sub->select->exp->mul->adds->select 约 8 条操作组成，实测 ~8 ns/position，而此时每 position 只有约 19 条向量指令——远低于发射带宽所能覆盖的数量，说明周期大量消耗在等待依赖。若每核还握有另一条与其完全独立的同构递推，把两条链的指令流交错发射即可用 B 的指令填 A 的停顿气泡，硬件不需要任何新资源（寄存器与队列各复制一份），吞吐趋近两条链交替后的有效延迟。这是纯 loop-jamming / ILP 杠杆，语料库中没有先例。与既有 negative 卡 `scalar-reduce-window-ilp` 的关系是同一杠杆的反面对照：那张卡在 scatter reduce 上进一步缩小 fp32 累加器窗口求 ILP，结论是「串行依赖已由 PIPE_S 承担，窗口再小也不产生额外 ILP」；本卡之所以获益，是先把第二条独立递推链引入同一发射流，而不是在已有链内部做更细的切分——即 ILP 的来源必须是新增的独立工作，而非现有依赖链的重排。",
  "related_anti_patterns": [],
  "risks": [
    "交错只部分隐藏停顿：该轮每 position 有效时延下降 15-24%、kernel geomean −13.24%，未达立项时乐观段（x0.60-0.80 即 −20% 到 −40%），提示新上限是发射带宽/寄存器依赖受限；后续加深交错的预期收益必须按这个天花板设定",
    "UB 压力强制 tilePos 减半才腾出第二套队列空间，任何提高队列深度或 tilePos 的变体会破坏 UB 中性条件",
    "奇数尾 chunk 必须正确回落到 A 队列单链路径，否则尾 chunk 被漏算",
    "门控必须排除 segSplitMode：该轮 case12（seg 模式）等价 1.000、case1/3/6/8/10（chunkPerCore<2）等价 0.999-1.010，证实未触碰域保持等价",
    "核心归因依赖管道计数语义：aiv_vec_ratio 0.991 既可能计停顿周期（latency-bound）也可能是真实发射饱和（issue-bound）；若为后者交错增益将塌缩（<3%）。该轮结果支持停顿归因，但该语义未在仓库内被独立文档化，A5 向量发射宽度与 exp/ln 延迟只能从实测 ns/pos 反推"
  ],
  "slug": "dual-recurrence-instruction-interleave",
  "summary": "饱和多 chunk 场景（totalChunks >= 64 向量核）被单条 64-lane 递推的 per-position 串行率钉住（该轮实测每核 7.67-8.81 ns/position，与单链单核参考 8.06 ns/pos 一致），每核是 latency-bound 而非 issue-bound。机制：把每核的 chunk 列表两两成组，在同一个融合循环里把两条独立递推逐指令交错（loadA,loadB,cmpA,cmpB,subA,subB,expA,expB,…），让 B 的指令落进 A 的依赖气泡；逐行递推、元素顺序与舍入 bit 级不变。kernel geomean 132.112→114.614us（1.1527x，−13.24%），全部饱和 case 改善 15-24%。",
  "verification": {
    "correctness": [
      "20/20 精度首过，编译一次通过（纯指令重排，bit 级不变设计成立）",
      "最差 case3 bf16 MARE 7.752e-3 < 1e-2 阈",
      "未触碰域对照等价：segSplitMode 路径 case12 1.000，chunkPerCore<2 路径 case1/3/6/8/10 为 0.999-1.010（噪声级）"
    ],
    "performance": [
      "4 对同 shape / provenance clean / balanced alternating ABBA，每对方向一致",
      "kernel geomean 132.112→114.614us（−13.24%，speedup 1.1527），全部饱和 case 改善 15-24%，无任何 case 稳定回退 >2%",
      "champion 画像佐证 latency-bound：aiv_vec_ratio 0.991、全部 aic pipe 0.0（纯向量核、无 MTE/scalar 重叠余量）；每 position 约 19 条向量指令与约 8 条操作的超越函数关键路径；饱和 case 每核吞吐 7.67-8.81 ns/pos 与孤立单链 8.06 ns/pos 相同，证明加核已用尽",
      "UB 中性：四队列（inA/inB/outA/outB）各深 2 x 16KB = 128KB，与 champion 2 队列 x 深 2 x 32KB 持平"
    ],
    "rollback_signals": [
      "配对 ABBA（>=2 对，全 20 case）geomean 改善 < 3% 或任一饱和 case 回退 >2% → 记 rejected_performance 并回退 champion",
      "若向量管道实为发射带宽饱和，交错保持平坦、aiv_vec_time 不变",
      "因 UB 压力而降 tilePos / 降队列深度的变体若打不过 champion，记为该机制的 falsified 变体而非修复",
      "交错导致递推顺序或舍入改变（精度门失败）"
    ]
  }
}
-->

# 性能优化策略：跨 chunk 双递推链指令级交错：扫描链延迟隐藏

饱和多 chunk 场景（totalChunks >= 64 向量核）被单条 64-lane 递推的 per-position 串行率钉住（该轮实测每核 7.67-8.81 ns/position，与单链单核参考 8.06 ns/pos 一致），每核是 latency-bound 而非 issue-bound。机制：把每核的 chunk 列表两两成组，在同一个融合循环里把两条独立递推逐指令交错（loadA,loadB,cmpA,cmpB,subA,subB,expA,expB,…），让 B 的指令落进 A 的依赖气泡；逐行递推、元素顺序与舍入 bit 级不变。kernel geomean 132.112→114.614us（1.1527x，−13.24%），全部饱和 case 改善 15-24%。

## 1. 原理

串行递推的吞吐上限不是发射带宽而是依赖链延迟：每 position 的关键路径由 cast->compare->sub->select->exp->mul->adds->select 约 8 条操作组成，实测 ~8 ns/position，而此时每 position 只有约 19 条向量指令——远低于发射带宽所能覆盖的数量，说明周期大量消耗在等待依赖。若每核还握有另一条与其完全独立的同构递推，把两条链的指令流交错发射即可用 B 的指令填 A 的停顿气泡，硬件不需要任何新资源（寄存器与队列各复制一份），吞吐趋近两条链交替后的有效延迟。这是纯 loop-jamming / ILP 杠杆，语料库中没有先例。与既有 negative 卡 `scalar-reduce-window-ilp` 的关系是同一杠杆的反面对照：那张卡在 scatter reduce 上进一步缩小 fp32 累加器窗口求 ILP，结论是「串行依赖已由 PIPE_S 承担，窗口再小也不产生额外 ILP」；本卡之所以获益，是先把第二条独立递推链引入同一发射流，而不是在已有链内部做更细的切分——即 ILP 的来源必须是新增的独立工作，而非现有依赖链的重排。

实现机制：把每核的 chunk 列表两两成组，在同一个融合 tile 循环里把两条独立递推逐指令交错（A.step; B.step; A.step; B.step; …），使 chunk-B 的指令落进 chunk-A 的依赖停顿气泡（反之亦然）。每链内部的指令序列、逐行递推、元素顺序与舍入与 champion 单链实现 bit 级一致，因此精度中性、纯 ILP。配套资源：复制一套 in/out/state 队列（inA/inB/outA/outB），并把 tilePos 减半以维持 UB 占用不变。奇数尾 chunk 回落到 A 队列单链路径；segSplitMode 与 chunkPerCore<2 的路径完全不进入 dualMode。

## 2. 性能问题模式

- 优化目标：消除饱和多 chunk 形状上单条 64-lane 扫描链的 per-position 串行延迟封顶：该轮饱和 case（totalChunks >= 64 向量核，如 case4/case5 各 8192 chunks = 128/core）每核实测 7.67-8.81 ns/position，与孤立单链单核参考值 8.06 ns/pos 相同，说明每核是 latency-bound（被 cast->compare->sub->select->exp->mul->adds->select 依赖链钉住）而非 issue-bound，核数、MTE 与发射带宽都无杠杆。
- 适用数据流：扫描（scan / prefix-recurrence）类算子：每核持有多个完全独立的一维递推 chunk、每核吞吐被单链 per-position 串行延迟封顶、核心数已用尽且 kernel 纯向量（无 MTE/scalar 重叠余量）的饱和形状；dtype 覆盖 fp16/bf16/fp32（fp32 用双 exp 链、fp16/bf16 用共享 exp 链，两条链各自同构即可交错）
- Feature signature：`{"bottleneck": ["scan-chain-latency", "dependency-stall-bubbles", "latency-bound-not-issue-bound"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "dual-recurrence-instruction-interleave", "reduce_mode": "scan", "structure": ["two-chunk-pairing", "instruction-granular-interleave", "four-queue-ub-neutral", "bit-identical-recurrence"]}`

## 3. 正确性红线

- 交错只部分隐藏停顿：该轮每 position 有效时延下降 15-24%、kernel geomean −13.24%，未达立项时乐观段（x0.60-0.80 即 −20% 到 −40%），提示新上限是发射带宽/寄存器依赖受限；后续加深交错的预期收益必须按这个天花板设定
- UB 压力强制 tilePos 减半才腾出第二套队列空间，任何提高队列深度或 tilePos 的变体会破坏 UB 中性条件
- 奇数尾 chunk 必须正确回落到 A 队列单链路径，否则尾 chunk 被漏算
- 门控必须排除 segSplitMode：该轮 case12（seg 模式）等价 1.000、case1/3/6/8/10（chunkPerCore<2）等价 0.999-1.010，证实未触碰域保持等价
- 核心归因依赖管道计数语义：aiv_vec_ratio 0.991 既可能计停顿周期（latency-bound）也可能是真实发射饱和（issue-bound）；若为后者交错增益将塌缩（<3%）。该轮结果支持停顿归因，但该语义未在仓库内被独立文档化，A5 向量发射宽度与 exp/ln 延迟只能从实测 ns/pos 反推

资源与硬件约束：

- UB 占用必须与 champion 持平：dual 时 tilePos 减半（fp32 128->64，fp16/bf16 256->128），四条队列（inA/inB/outA/outB）各深 2 x 16KB = 128KB，与 champion 的 2 队列 x 深 2 x 32KB 相等；任何加队列深度或回调 tilePos 的变体都可能 UB 溢出
- 门控必须是 dualMode = (segSplitMode==0 && chunkPerCore>=2)：segSplitMode 路径与 chunkPerCore<2 的 few-chunk 形状必须留在 champion 路径，不可强行交错
- 奇数尾 chunk 必须回落到 A 队列的单链 champion 路径，保证 chunk 覆盖完整
- 两条链的逐行递推、元素顺序与舍入必须 bit 级不变：交错只允许是指令顺序的重排，不允许任何代数重写

## 4. 泛化条件

- 策略作用域：op_class：scan

适用：

- 每核持有 >=2 个完全独立的 chunk，且每个 chunk 的递推只沿自身扫描轴（跨 chunk 无依赖）
- 每核吞吐被单链 per-position 串行率封顶：该轮饱和 case 实测 7.67-8.81 ns/position/core，与孤立单链单核参考值 8.06 ns/pos 一致
- 核心数已用尽（blockDim = 64 = 物理向量核数），加核不再是可选杠杆
- kernel 为纯向量核（全部 aic pipe 0.0）、无 MTE/scalar 重叠余量可挖
- 存在可融合统一 tile 循环的两条同构递推（该轮两条 64-lane (rmax,rsum) 链，指令序列完全相同）

不适用：

- segSplitMode 路径（沿扫描轴切分、每核只持一个 chunk 的两趟扫描）结构上无法配对，不适用本机制
- 每核 chunk 数 < 2（chunkPerCore<2 / totalChunks <= coreNum）的形状没有可配对的第二条独立链，不适用
- 若向量管道实为发射带宽饱和（issue-bound）而非停顿归因（latency-bound），交错无收益：该轮 aiv_vec_ratio 0.991 的停顿归因是结论成立的前提，未独立证实前不得立项
- 非饱和情形下已有更便宜的加核/切分手段（如 vf-thread-chunked-two-pass-scan 对少数长扫描形状）时不适用

## 5. 实施步骤

1. 新增双链实现（该轮 LogcumsumexpDualScanImpl/DualScan）：把两条独立的 64-lane (rmax,rsum) 递推按指令粒度交错（loadA,loadB,cmpA,cmpB,subA,subB,expA,expB,…），每条链内部的指令序列与 champion 的单链实现完全一致
2. 复制队列资源：新增 inputQueueB_/outputQueueB_/stateBufB_，并把 CopyIn/CopyOut 泛化为队列参数，使两路数据各自独立流动
3. Process() 增加路由：dualMode 时走 ProcessDual，chunk 两两配对成融合 tile 循环（CopyInA,CopyInB,ComputeDual,CopyOutA,CopyOutB）；奇数尾 chunk 用 A 队列单链回退
4. tiling 增加 uint32_t dualMode 字段，host 侧判定 dualMode = (segSplitMode==0 && chunkPerCore>=2)
5. dual 时 tilePos 减半（fp32 128->64，fp16/bf16 256->128）以保持 UB 足迹与 champion 持平（4 队列 x 深 2 x 16KB = 128KB）

## 6. LLM 前置问题

- 目标实现是否满足：每核持有 >=2 个完全独立的 chunk，且每个 chunk 的递推只沿自身扫描轴（跨 chunk 无依赖）？
- 目标实现是否满足：每核吞吐被单链 per-position 串行率封顶：该轮饱和 case 实测 7.67-8.81 ns/position/core，与孤立单链单核参考值 8.06 ns/pos 一致？
- 目标实现是否满足：核心数已用尽（blockDim = 64 = 物理向量核数），加核不再是可选杠杆？
- 目标实现是否满足：kernel 为纯向量核（全部 aic pipe 0.0）、无 MTE/scalar 重叠余量可挖？
- 目标实现是否满足：存在可融合统一 tile 循环的两条同构递推（该轮两条 64-lane (rmax,rsum) 链，指令序列完全相同）？
- 是否命中排除条件：segSplitMode 路径（沿扫描轴切分、每核只持一个 chunk 的两趟扫描）结构上无法配对，不适用本机制？
- 是否命中排除条件：每核 chunk 数 < 2（chunkPerCore<2 / totalChunks <= coreNum）的形状没有可配对的第二条独立链，不适用？
- 是否命中排除条件：若向量管道实为发射带宽饱和（issue-bound）而非停顿归因（latency-bound），交错无收益？
- 是否命中排除条件：非饱和情形下已有更便宜的加核/切分手段（如 vf-thread-chunked-two-pass-scan 对少数长扫描形状）时不适用？

## 7. 验收标准

正确性：

- 20/20 精度首过，编译一次通过（纯指令重排，bit 级不变设计成立）
- 最差 case3 bf16 MARE 7.752e-3 < 1e-2 阈
- 未触碰域对照等价：segSplitMode 路径 case12 1.000，chunkPerCore<2 路径 case1/3/6/8/10 为 0.999-1.010（噪声级）

性能：

- 4 对同 shape / provenance clean / balanced alternating ABBA，每对方向一致
- kernel geomean 132.112→114.614us（−13.24%，speedup 1.1527），全部饱和 case 改善 15-24%，无任何 case 稳定回退 >2%
- champion 画像佐证 latency-bound：aiv_vec_ratio 0.991、全部 aic pipe 0.0（纯向量核、无 MTE/scalar 重叠余量）；每 position 约 19 条向量指令与约 8 条操作的超越函数关键路径；饱和 case 每核吞吐 7.67-8.81 ns/pos 与孤立单链 8.06 ns/pos 相同，证明加核已用尽
- UB 中性：四队列（inA/inB/outA/outB）各深 2 x 16KB = 128KB，与 champion 2 队列 x 深 2 x 32KB 持平

回滚信号：

- 配对 ABBA（>=2 对，全 20 case）geomean 改善 < 3% 或任一饱和 case 回退 >2% → 记 rejected_performance 并回退 champion
- 若向量管道实为发射带宽饱和，交错保持平坦、aiv_vec_time 不变
- 因 UB 压力而降 tilePos / 降队列深度的变体若打不过 champion，记为该机制的 falsified 变体而非修复
- 交错导致递推顺序或舍入改变（精度门失败）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260913_220548（eid=free_explore_001, round=1, status=accepted, speedup=1.1527, precision=20/20 PASS）

## 检索卡（短卡）

动作：把每核 chunk 两两成组，在同一融合 tile 循环里把两条独立递推逐指令交错填依赖气泡
适用：每核持有 >=2 个完全独立 chunk、核心数已用尽、纯向量核且每核被单链 per-position 串行率封顶
限制：UB 须与 champion 持平（tilePos 减半）；门控须排除 segSplitMode 与 chunkPerCore<2
范围：scan/prefix-recurrence 类算子的饱和多 chunk 形状
检索词：指令级交错、loop-jamming、dualMode、tilePos、latency-bound
机会：单条 64-lane 扫描链的 per-position 串行延迟封顶（7.67-8.81 ns/position）
代价：交错只部分隐藏停顿（有效时延降 15-24%），新上限是发射带宽/寄存器依赖
