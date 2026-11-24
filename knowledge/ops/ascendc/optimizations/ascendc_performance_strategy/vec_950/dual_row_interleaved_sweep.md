---
type: Optimization
title: 双行交错扫描：双 loop-carried 累加器填 vec 发射空闲
description: 对逐行独立的 softmax 类扫描，把行两两成对交错进同一循环体：三条扫描各带双份 loop-carried 累加器（两个 maxAcc / 两个 sumAcc），双份分段 exp 缓冲，pair loop 按 depth-4 队列环流水化，尾行保留单行路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/dual-row-interleaved-sweep.md
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
      "交错的前提是 ccec 的『每函数一个循环、循环体内寄存器不得跨循环边界存活』约束继续成立：每个交错扫描仍必须是单个循环，只允许新增一个与既有累加器等价的 loop-carried 累加器",
      "expBuf_ 必须容纳两行分段落盘（2*RS_ROW_TILE floats，行宽 4096 下 32KB），且 InitBuffer 是类级共享——multi-tile/strided 路径虽不使用 expBuf_，也不得被容量变化破坏",
      "流水化 pair loop 的 TQue 模板深度必须与 Alloc 缓冲数一致（round_02 把 xQue 提到 4 个缓冲却把模板深度留在 2，队列环与 Alloc 环不匹配，精度由 20/20 直接掉到 0/20）",
      "尾行单行路径必须保留，成对主循环不得假设行数为偶"
    ],
    "excluded_conditions": [
      "行之间不独立（存在跨行归约或行间依赖）时不适用：机制的全部收益来自两条链的独立性",
      "瓶颈不是 vec 发射槽空闲时不适用（例如 mte2/mte3 或标量为主）：本机制不减少任何一条指令，只改变发射密度",
      "UB 余量不足以容纳双行寄存器工作集与双份分段 exp 缓冲时不适用"
    ],
    "required_conditions": [
      "逐行串行的扫描/归约链，每 rep 的指令链短且被 loop-carried 累加器或长延迟链串行化（本 run：16-bit max 扫 3 v-insn/128 元素带串行 Max 累加器；sum 扫 14 v-insn/128 带串行 Add 与 Sub->Exp->Add 链；fp32 max 扫 3 v-insn/64）",
      "实测 vec 管已绑定且仍有可观发射空闲（本 run vec_ratio 0.820-0.836，每 launch 空闲 6.7us（bf16/fp16）/8.0us（fp32），约 17-18%）",
      "行完全独立（softmax per row），队列深度已为每行搬运双缓冲（depth 2），交错不需要新的 GM 流量模式"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "ReluSoftmax",
      "operator_class": "fused-composite",
      "precision": "20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8，三 dtype 输出位相同）",
      "run_id": "<run-id>",
      "speedup": 1.0901,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-issue-slot-idle",
      "dependency-serialized-sweep-chain",
      "short-per-rep-instruction-chain"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "dual-row-interleaved-sweep",
    "reduce_mode": "row-softmax",
    "structure": [
      "two-row-interleaved-sweeps",
      "dual-loop-carried-accumulator",
      "one-loop-per-function",
      "depth-4-pipelined-pair-loop",
      "odd-tail-single-row-fallback"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-DUAL-ROW-INTERLEAVED-SWEEP",
  "implementation_steps": [
    "把逐行主循环改为成对处理：一次 CopyInX 搬入第 2r 与 2r+1 两行，奇数尾行保留原单行路径作为回退",
    "每个扫描改为对两行寄存器的一个循环，为每行各带一个 loop-carried 累加器（maxAcc / sumAcc），每轮先发射 A 行链再发射 B 行链，循环结构保持『每函数一个循环』",
    "sum 扫为两行分别分段落盘 exp（expBuf_ 扩到 2*RS_ROW_TILE floats），scale 扫交错两行的 Mul/downcast/Store，两行共享每轮一次 UpdateMask",
    "把 pair loop 流水化：xQue 提到 4 个缓冲并同步把 TQue<QuePosition::VECIN,4> 的模板深度改到 4，插入 prologue 与下一对预取，Free(xA/xB) 移到 sum 扫之后",
    "以 20/20 位相同精度门 + 配对 ABBA 性能门验收，任一 dtype case 低于 0.97x 即回退"
  ],
  "intent": "消除逐行串行扫描在 vec 管上留下的约 17-18% 发射槽空闲（vec_ratio 0.820-0.836；每 launch 空闲 6.7us（bf16/fp16）/8.0us（fp32）），在不减少任何一条指令的前提下把行独立性转成指令级并行。",
  "mechanism": "two-row-interleaved-sweeps：把逐行主循环改为成对（行 2r / 2r+1）。三条扫描（max / sum-of-exp / scale）各变成一个覆盖两行寄存器的单循环——max 扫带两个 loop-carried maxAcc，每轮先发射 A 行链再发射 B 行链；sum 扫带两个 sumAcc，交错两行分段落盘的 exp（expBuf_ 2*RS_ROW_TILE floats）；scale 扫交错两行的 Mul/downcast/Store。每轮共享一次 UpdateMask。pair loop 进一步流水化（depth-4 队列环 + prologue + 下一对预取，Free(xA/xB) 后移到 sum 扫之后），使每个扫描边界同时有两个独立链在飞。每行每元素的算子序与取值完全不变（只是与同构的邻行序列交错），因此三 dtype 输出位相同。奇数行数/尾行保留原单行路径。",
  "name": "双行交错扫描：双 loop-carried 累加器填 vec 发射空闲",
  "operator_class": "fused-composite",
  "operator_scope": "逐行独立、行内多趟扫描/归约、每趟循环指令链短且被 loop-carried 累加器串行化的算子；典型如 per-row softmax 家族（本 run 覆盖 20 个 perf case：[4096,4096] dim=-1，D=4096=RS_ROW_TILE，64 行/核）",
  "principle": "vec 管的利用率上限由发射槽能否被填满决定，而不是由指令数决定。逐行串行扫描里，max 扫每 rep 只有 Load/Maxs/Max 三条且带串行 Max 累加器，sum 扫的 Add 累加与 Sub->Exp->Add 延迟链同样串行——链太短、依赖太密，每 rep 之后 issue 槽空转。实测每核 ~51.2k 条 v-insn 落在 32.8us 的 vec busy 上，约 1 v-insn/cycle 的发射率下，任何依赖停顿都直接变成可见的空闲窗口。行与行之间完全独立，把两条同构链交错进同一循环体，等于每轮提供两倍独立工作，让同一份发射带宽被填满；同时扫描循环迭代次数减半，标量循环控制开销下降。这是一个发射密度杠杆：指令数、每条指令的取值、每行的算子序都不变，因此与『减指令数』类策略（vec-frontend-instruction-diet 一类的每元素微替换/去冗余指令）是正交的不同杠杆——后者改变发射流的内容，本机制只改变发射流的时间分布。",
  "related_anti_patterns": [],
  "risks": [
    "round_02 的流水化 pair loop 只把 xQue 的 Alloc 提到 4 个缓冲，却把 TQue<QuePosition::VECIN,2> 模板深度留在 2，队列环与 Alloc 环不匹配导致精度 20/20 -> 0/20（在设备上定位），round_03 一行修复 TQue<QuePosition::VECIN,4> 后直接通过；流水化改动必须同步模板深度",
    "ccec 可能拒绝双 loop-carried 累加器或加倍的循环内寄存器工作集（register spill）；机制内的收窄路径是只交错 max+sum 两个带依赖的扫描（scale 扫无携带依赖），或先在 16-bit 上开",
    "vec 空闲可能部分是结构性的（队列同步边界 / Reduce 微序列），单纯 ILP 无法回收，此时性能门会如实地停在约 1.0x，不构成机制反例",
    "expBuf_ 由 16KB 增至 32KB 后 UB 最坏情形（fp32）仍约 98KB << 256KB/core，但 multi-tile/strided 路径的 InitBuffer 是类级共享，需确认不被破坏"
  ],
  "slug": "dual-row-interleaved-sweep",
  "summary": "对逐行独立的 softmax 类扫描，把行两两成对交错进同一循环体：三条扫描各带双份 loop-carried 累加器（两个 maxAcc / 两个 sumAcc），双份分段 exp 缓冲，pair loop 按 depth-4 队列环流水化，尾行保留单行路径。指令数与每行算子序不变（三 dtype 输出位相同，20/20 PASS），把实测 17-18% 的 vec 发射空闲转成任务时间：formal ABBA geomean 41.097 -> 37.701us = 1.0901x（bf16 1.0886、fp16 1.0859、fp32 1.0957）。",
  "verification": {
    "correctness": [
      "20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8），三 dtype 输出位相同：每行逐元素算子序与取值未变，只是与同构的邻行序列交错",
      "配对 loop 与未改动的奇数尾行单行路径共存，尾行语义与位结果不变",
      "round_02 的队列模板深度缺陷已由 round_03 的一行修复覆盖，修复后 20/20 直接通过"
    ],
    "performance": [
      "formal 配对 ABBA：geomean 41.097 -> 37.701us = 1.0901x（bf16 1.0886、fp16 1.0859、fp32 1.0957；最差 case 1.0859，最小对 1.0888）",
      "基线 40.911us（BEST_MS）与 run_state.json 及 A 侧重聚合 geomean 一致",
      "无任何 dtype case 低于回滚阈值（配对 geomean <1.02x 或任一 dtype case mean <0.97x）",
      "vec 空闲归因自 4 条 provenance-clean 的交替 champion .so 运行重聚合（bf16 vec 32.805us ratio 0.833 / fp16 32.806us 0.836 / fp32 35.170us 0.820）"
    ],
    "rollback_signals": [
      "任一 dtype case mean <0.97x，或配对 geomean <1.02x",
      "TQue 模板深度与 Alloc 缓冲数不一致（round_02 的 0/20 事故形态）",
      "ccec 因双累加器/寄存器工作集翻倍报错，或编译产物出现明显 spill",
      "奇数行/尾行路径不再与单行实现位一致"
    ]
  }
}
-->

# 性能优化策略：双行交错扫描：双 loop-carried 累加器填 vec 发射空闲

对逐行独立的 softmax 类扫描，把行两两成对交错进同一循环体：三条扫描各带双份 loop-carried 累加器，pair loop 按 depth-4 队列环流水化，尾行保留单行路径。指令数与每行算子序不变（三 dtype 输出位相同，20/20 PASS），把实测 17-18% 的 vec 发射空闲转成任务时间：formal ABBA geomean 41.097 -> 37.701us = 1.0901x。

## 1. 原理

vec 管的利用率上限由发射槽能否被填满决定，而不是由指令数决定。逐行串行扫描里，max 扫每 rep 只有 Load/Maxs/Max 三条且带串行 Max 累加器，sum 扫的 Add 累加与 Sub->Exp->Add 延迟链同样串行——链太短、依赖太密，每 rep 之后 issue 槽空转。实测每核 ~51.2k 条 v-insn 落在 32.8us 的 vec busy 上，约 1 v-insn/cycle 的发射率下，任何依赖停顿都直接变成可见的空闲窗口。行与行之间完全独立，把两条同构链交错进同一循环体，等于每轮提供两倍独立工作，让同一份发射带宽被填满；同时扫描循环迭代次数减半，标量循环控制开销下降。这是一个发射密度杠杆：指令数、每条指令的取值、每行的算子序都不变，因此与『减指令数』类策略（vec-frontend-instruction-diet 一类的每元素微替换/去冗余指令）是正交的不同杠杆——后者改变发射流的内容，本机制只改变发射流的时间分布。

实现机制：two-row-interleaved-sweeps——把逐行主循环改为成对（行 2r / 2r+1）。三条扫描（max / sum-of-exp / scale）各变成一个覆盖两行寄存器的单循环：max 扫带两个 loop-carried maxAcc，每轮先发射 A 行链再发射 B 行链；sum 扫带两个 sumAcc，交错两行分段落盘的 exp（expBuf_ 2*RS_ROW_TILE floats）；scale 扫交错两行的 Mul/downcast/Store。每轮共享一次 UpdateMask。pair loop 进一步流水化（depth-4 队列环 + prologue + 下一对预取，Free(xA/xB) 后移到 sum 扫之后），使每个扫描边界同时有两个独立链在飞。每行每元素的算子序与取值完全不变（只是与同构的邻行序列交错），因此三 dtype 输出位相同。奇数行数/尾行保留原单行路径。

## 2. 性能问题模式

- 优化目标：消除逐行串行扫描在 vec 管上留下的约 17-18% 发射槽空闲（vec_ratio 0.820-0.836；每 launch 空闲 6.7us（bf16/fp16）/8.0us（fp32）），在不减少任何一条指令的前提下把行独立性转成指令级并行
- 适用数据流：逐行独立、行内多趟扫描/归约、每趟循环指令链短且被 loop-carried 累加器串行化的算子；典型如 per-row softmax 家族（本 run 覆盖 20 个 perf case：[4096,4096] dim=-1，D=4096=RS_ROW_TILE，64 行/核）
- Feature signature：`{"bottleneck": ["vec-issue-slot-idle", "dependency-serialized-sweep-chain", "short-per-rep-instruction-chain"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "dual-row-interleaved-sweep", "reduce_mode": "row-softmax", "structure": ["two-row-interleaved-sweeps", "dual-loop-carried-accumulator", "one-loop-per-function", "depth-4-pipelined-pair-loop", "odd-tail-single-row-fallback"]}`

## 3. 正确性红线

- round_02 的流水化 pair loop 只把 xQue 的 Alloc 提到 4 个缓冲，却把 TQue<QuePosition::VECIN,2> 模板深度留在 2，队列环与 Alloc 环不匹配导致精度 20/20 -> 0/20（在设备上定位），round_03 一行修复 TQue<QuePosition::VECIN,4> 后直接通过；流水化改动必须同步模板深度
- ccec 可能拒绝双 loop-carried 累加器或加倍的循环内寄存器工作集（register spill）；机制内的收窄路径是只交错 max+sum 两个带依赖的扫描（scale 扫无携带依赖），或先在 16-bit 上开
- vec 空闲可能部分是结构性的（队列同步边界 / Reduce 微序列），单纯 ILP 无法回收，此时性能门会如实地停在约 1.0x，不构成机制反例
- expBuf_ 由 16KB 增至 32KB 后 UB 最坏情形（fp32）仍约 98KB << 256KB/core，但 multi-tile/strided 路径的 InitBuffer 是类级共享，需确认不被破坏

资源与硬件约束：

- 交错的前提是 ccec 的『每函数一个循环、循环体内寄存器不得跨循环边界存活』约束继续成立：每个交错扫描仍必须是单个循环，只允许新增一个与既有累加器等价的 loop-carried 累加器
- expBuf_ 必须容纳两行分段落盘（2*RS_ROW_TILE floats，行宽 4096 下 32KB），且 InitBuffer 是类级共享——multi-tile/strided 路径虽不使用 expBuf_，也不得被容量变化破坏
- 流水化 pair loop 的 TQue 模板深度必须与 Alloc 缓冲数一致（round_02 把 xQue 提到 4 个缓冲却把模板深度留在 2，队列环与 Alloc 环不匹配，精度由 20/20 直接掉到 0/20）
- 尾行单行路径必须保留，成对主循环不得假设行数为偶

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 逐行串行的扫描/归约链，每 rep 的指令链短且被 loop-carried 累加器或长延迟链串行化（本 run：16-bit max 扫 3 v-insn/128 元素带串行 Max 累加器；sum 扫 14 v-insn/128 带串行 Add 与 Sub->Exp->Add 链；fp32 max 扫 3 v-insn/64）
- 实测 vec 管已绑定且仍有可观发射空闲（本 run vec_ratio 0.820-0.836，每 launch 空闲 6.7us（bf16/fp16）/8.0us（fp32），约 17-18%）
- 行完全独立（softmax per row），队列深度已为每行搬运双缓冲（depth 2），交错不需要新的 GM 流量模式

不适用：

- 行之间不独立（存在跨行归约或行间依赖）时不适用：机制的全部收益来自两条链的独立性
- 瓶颈不是 vec 发射槽空闲时不适用（例如 mte2/mte3 或标量为主）：本机制不减少任何一条指令，只改变发射密度
- UB 余量不足以容纳双行寄存器工作集与双份分段 exp 缓冲时不适用

## 5. 实施步骤

1. 把逐行主循环改为成对处理：一次 CopyInX 搬入第 2r 与 2r+1 两行，奇数尾行保留原单行路径作为回退
2. 每个扫描改为对两行寄存器的一个循环，为每行各带一个 loop-carried 累加器（maxAcc / sumAcc），每轮先发射 A 行链再发射 B 行链，循环结构保持『每函数一个循环』
3. sum 扫为两行分别分段落盘 exp（expBuf_ 扩到 2*RS_ROW_TILE floats），scale 扫交错两行的 Mul/downcast/Store，两行共享每轮一次 UpdateMask
4. 把 pair loop 流水化：xQue 提到 4 个缓冲并同步把 TQue<QuePosition::VECIN,4> 的模板深度改到 4，插入 prologue 与下一对预取，Free(xA/xB) 移到 sum 扫之后
5. 以 20/20 位相同精度门 + 配对 ABBA 性能门验收，任一 dtype case 低于 0.97x 即回退

## 6. LLM 前置问题

- 目标实现是否满足：逐行串行的扫描/归约链，每 rep 的指令链短且被 loop-carried 累加器或长延迟链串行化（本 run：16-bit max 扫 3 v-insn/128 元素带串行 Max 累加器；sum 扫 14 v-insn/128 带串行 Add 与 Sub->Exp->Add 链；fp32 max 扫 3 v-insn/64）？
- 目标实现是否满足：实测 vec 管已绑定且仍有可观发射空闲（本 run vec_ratio 0.820-0.836，每 launch 空闲 6.7us（bf16/fp16）/8.0us（fp32），约 17-18%）？
- 目标实现是否满足：行完全独立（softmax per row），队列深度已为每行搬运双缓冲（depth 2），交错不需要新的 GM 流量模式？
- 是否命中排除条件：行之间不独立（存在跨行归约或行间依赖）时不适用？
- 是否命中排除条件：瓶颈不是 vec 发射槽空闲时不适用（例如 mte2/mte3 或标量为主）？
- 是否命中排除条件：UB 余量不足以容纳双行寄存器工作集与双份分段 exp 缓冲时不适用？

## 7. 验收标准

正确性：

- 20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8），三 dtype 输出位相同：每行逐元素算子序与取值未变，只是与同构的邻行序列交错
- 配对 loop 与未改动的奇数尾行单行路径共存，尾行语义与位结果不变
- round_02 的队列模板深度缺陷已由 round_03 的一行修复覆盖，修复后 20/20 直接通过

性能：

- formal 配对 ABBA：geomean 41.097 -> 37.701us = 1.0901x（bf16 1.0886、fp16 1.0859、fp32 1.0957；最差 case 1.0859，最小对 1.0888）
- 基线 40.911us（BEST_MS）与 run_state.json 及 A 侧重聚合 geomean 一致
- 无任何 dtype case 低于回滚阈值（配对 geomean <1.02x 或任一 dtype case mean <0.97x）
- vec 空闲归因自 4 条 provenance-clean 的交替 champion .so 运行重聚合（bf16 vec 32.805us ratio 0.833 / fp16 32.806us 0.836 / fp32 35.170us 0.820）

回滚信号：

- 任一 dtype case mean <0.97x，或配对 geomean <1.02x
- TQue 模板深度与 Alloc 缓冲数不一致（round_02 的 0/20 事故形态）
- ccec 因双累加器/寄存器工作集翻倍报错，或编译产物出现明显 spill
- 奇数行/尾行路径不再与单行实现位一致

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260913_070917（round=03, status=accepted, speedup=1.0901, precision=20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8，三 dtype 输出位相同））

## 检索卡（短卡）

动作：把逐行主循环改为成对，三条扫描各带双份 loop-carried 累加器交错两行，pair loop 按 depth-4 队列环流水
适用：逐行独立、行内多趟扫描、每 rep 指令链短且被 loop-carried 累加器串行化
限制：TQue 模板深度须与 Alloc 缓冲数一致；expBuf_ 须容纳 2*RS_ROW_TILE floats；尾行路径须保留
范围：fused-composite 的 per-row softmax 扫描
检索词：双 loop-carried 累加器、maxAcc/sumAcc、depth-4 队列环、UpdateMask、expBuf_
机会：逐行串行扫描链太短、依赖太密，vec 管留下 17-18% 发射槽空闲
代价：expBuf_ 16KB→32KB，UB 最坏约 98KB；寄存器压力翻倍或 spill
