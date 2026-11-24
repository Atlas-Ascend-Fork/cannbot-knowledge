---
type: Optimization
title: 跨 pass fp32 exp 的 UB 暂存复用
description: 把 sum-exp 遍算出的 fp32 exp 按原始位暂存 UB，out 遍直接消费该 e。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/cross-pass-ub-staged-exp-reuse.md
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
      "ccec 编译约束：每函数恰好一个循环、寄存器不跨循环边界存活——暂存必须落在既有 sum 循环内，新的 scale 循环必须自成一函数，不得让寄存器跨 pass 存活",
      "暂存缓冲必须是 fp32（e=exp(x-max) 的原始位），且 out 遍消费的必须是与 sum 遍位级相同的 exp 值（同一 UB x、同一 broadcast max），否则位级一致不成立",
      "新增 UB 预算须落在容量内：ReluSoftmax 新增 16KB fp32 staging（fp32 worst case xQue 2x16KB + yQue 2x16KB + staging 16KB + smallBuf ~2KB 约 82KB << 256KB/core）；SoftmaxRelu expBuf_ 为 dimSize*4 + 256 bytes，总 UB 215,360B / 253,952B，rowBatch 保持 6/6/3 不需重规划",
      "multi-tile row 路径（D > ROW_TILE）与 strided 路径（inner>1）必须逐字节不变地保留原 SumExp/OutPass 实现"
    ],
    "excluded_conditions": [
      "不适用于需要整行常驻 UB 改造的场景——本机制不改变既有 single-read row 结构，只增加一次跨 pass 的 UB 暂存（行常驻单读是另有杠杆，见 row-resident-single-gm-read-cross-pass-reuse）",
      "D > ROW_TILE 的多 tile 行与 inner>1 的 strided 路径不适用，保持原码",
      "sum 遍与 out 遍不共享同一份 exp 输入（例如中间有额外逐元素变换）时不适用",
      "以「消除 UB store->reload 往返」为目标的位点不适用——该目标走寄存器直通路线（in-register-s-forwarding），本机制走向相反：保留 pass 边界、显式经 UB 暂存"
    ],
    "required_conditions": [
      "算子已具备 single-read row 结构（isRow && D <= ROW_TILE），每行依次跑 max/sum/out 三遍 UB 扫",
      "sum-exp 遍已按元素算出 e=exp(x-max) 的 fp32 值，out 遍又从同一 x 与同一 broadcast max 重算同一批 e（含 unpack + Cast + Sub + Exp）",
      "aiv_vec 是绑定流水（ReluSoftmax champion bf16 vec 41.79us / aiv 47.984us、fp16 41.78/47.918、fp32 36.69/44.890，vec_ratio 0.82-0.87；SoftmaxRelu champion fp16 vec 41.674/48.814 = 85.4%、bf16 41.702/48.738 = 85.6%、fp32 37.294/45.409 = 82.1%），MTE2/MTE3 远低于 vec",
      "UB 有容纳行规模 fp32 暂存缓冲的余量（ReluSoftmax 新增 16KB 后仍远低于 256KB/core；SoftmaxRelu 215,360B / 253,952B）",
      "输出必须与 champion 位级一致（同一批 exp 位被消费、同一 rcpSum 乘、同一 downcast）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "ReluSoftmax",
      "operator_class": "normalization",
      "pairs": 4,
      "precision": "20/20 PASS（输出位级一致，bit-identical）",
      "run_id": "<run-id>",
      "speedup": 1.0839,
      "status": "accepted"
    },
    {
      "operator": "SoftmaxRelu",
      "operator_class": "normalization",
      "pairs": 5,
      "precision": "20/20 PASS（bit-compatible，同一批 fp32 exp 值被消费）",
      "run_id": "<run-id>",
      "speedup": 1.0732,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "redundant-exp-recompute",
      "duplicate-sub-exp-pass",
      "aiv-vec-emission-bound"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "cross-pass-ub-staged-exp-reuse",
    "reduce_mode": "row-softmax",
    "structure": [
      "fp32-ub-staging-buffer",
      "single-loop-per-function-ccec-constraint",
      "out-sweep-degenerates-to-load-mul-store",
      "bit-identical-output",
      "untouched-multi-tile-and-strided-fallback"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-CROSS-PASS-UB-STAGED-EXP-REUSE",
  "implementation_steps": [
    "在 Init() 内新增一个行规模 fp32 暂存缓冲（ReluSoftmax 为 16KB VECCALC expBuf_ + ExpUb() accessor；SoftmaxRelu 为 TBuf expBuf_ = dimSize*4 + 256 bytes），仅 single-read row 分支使用",
    "把 sum-exp 遍改造成 store 变体：保留原循环体，只在每个 rep 内追加一条掩码 Reg::StoreAlign，把刚算出的 e=exp(x-max) 的 fp32 原始位写入暂存缓冲",
    "新增独立的 scale/out 循环（自成一函数，满足 ccec 单循环约束）：hoist rcpSum（Duplicate 1.0f + Div by sumUb，与 OutPass 完全一致），每 rep 走 LoadAlign(exp) -> Mul -> [fp16/bf16 downcast Cast] -> StoreAlign",
    "把 single-read row 分支改为调用 staged 对（SumExpStore + 新 scale 遍），该分支不再调用原 OutPass",
    "multi-tile row（D > ROW_TILE）与 strided（inner>1）路径保持原 SumExp/OutPass 逐字节不变",
    "跑 20/20 精度与 >=4 对 ABBA 配对（外层 msprof device Task Duration，两级 case-mean 再 geomean）"
  ],
  "intent": "消除 out 遍对 sum-exp 遍已算出的 e=exp(x-max) 的整遍重算（per element: LoadAlign + upcast Cast + Maxs + Sub + Exp 全冗余）：只把 fp32 exp 值经 UB 暂存跨 pass 传递，不动既有的 single-read row 结构。",
  "mechanism": "跨 pass 的 fp32 exp UB 暂存复用。sum-exp 遍在既有单循环内按 rep 追加一条掩码 Reg::StoreAlign，把 e=exp(x-max) 的 fp32 位写进新分配的行规模暂存缓冲；out 遍退化为一个独立单循环：LoadAlign(e) -> Mul by 已 hoist 的 rcpSum -> [fp16/bf16 downcast] -> StoreAlign，删除 GM 重读、B16 unpack+Cast、Sub 与第二次 Exp。因删除的是「同输入同算子的重复计算」，开销仅一次 UB（非 GM）StoreAlign 与一次 fp32 LoadAlign，而输出消费的仍是同一批 exp 位，故位级一致。ccec 只接受「每函数恰好一个循环、寄存器不跨循环边界存活」，因此中间量走 UB 而不是寄存器——这正是与 in-register-s-forwarding 的分界：后者把两遍融合、让中间量驻留寄存器以删掉 UB store->reload 往返；本机制保留 pass 边界，用 UB 暂存换取删掉一次 Exp 重算。回退臂为 multi-tile row 与 strided 路径的原码。",
  "name": "跨 pass fp32 exp 的 UB 暂存复用",
  "operator_class": "normalization",
  "operator_scope": "已具备 single-read row 结构（isRow && D <= ROW_TILE）的 softmax 系融合算子：sum-exp 遍与 out 遍对同一 UB x、同一 broadcast max 重算同一批 exp，且 aiv_vec 为绑定流水",
  "principle": "同一 row 内 max/sum/out 三遍 UB 扫里 (Sub, Exp) 被算两次，两次的输入（同一 UB x、同一 broadcast max）完全相同，属于语义冗余而非精度需要。把这批 exp 按原始位暂存到 fp32 UB 后，out 遍只剩 LoadAlign + Mul + downcast + Store，删掉一次 Exp 及其输入链；代价是多一次 UB StoreAlign 与一次 fp32 LoadAlign，相对一次超越函数与它的 unpack/Cast/Sub 输入链是净赚。之所以走 UB 暂存而不是寄存器直通：ccec 只接受每函数一个循环、寄存器不跨循环边界存活，跨 pass 的中间量无法驻留寄存器；UB 暂存是对该编译约束下的可行解。",
  "related_anti_patterns": [
    "in-register-s-forwarding"
  ],
  "risks": [
    "与 in-register-s-forwarding 的关系必须分清：该卡走向相反——把两遍融合、让中间量全程驻留寄存器，删除的是 UB store->reload 往返与 RAW 屏障；本卡保留 pass 边界、显式经 UB 暂存，删除的是 exp 的重算。二者不可叠加于同一中间量：若同时做，则寄存器直通已经消除了往返，UB 暂存会变成纯增开销",
    "暂存引入的额外 UB StoreAlign/LoadAlign 是收益的对冲项；ReluSoftmax 最差 dtype case（fp32）ratio 仅 1.0300，贴近 1.02x 的回滚线，fp32 侧本就更吃 MTE2（17.84us）",
    "ccec 可能拒绝改造后的单循环体（修复预算只覆盖同一机制内的指令重排），暂存点必须留在既有 sum 循环内、新循环自成一函数",
    "多 tile row（D > ROW_TILE）与 strided（inner>1）路径必须保持原 SumExp/OutPass 逐字节不变；全部 20 个测试用例均为 [4096,4096] dim=-1，非测试形状只能靠原码回退保证正确",
    "暂存与消费的 exp 必须位级相同（同一输入、同一算子、同一舍入），否则输出不再是位级一致，pinned 语义会静默漂移"
  ],
  "slug": "cross-pass-ub-staged-exp-reuse",
  "summary": "在既有 single-read row 结构上，把 sum-exp 遍已算出的 fp32 e=exp(x-max) 按原始位暂存进行规模 fp32 UB 缓冲，out 遍改为直接消费该 e（LoadAlign + Mul by hoist 的 rcpSum + downcast/Store），删除 out 遍的 GM 重读、B16 unpack+Cast、Sub 与第二次 Exp。ReluSoftmax kernel geomean 46.915->43.285us（1.0839x，4 对 ABBA，pair spread 1.0835-1.0846）；SoftmaxRelu kernel geomean 47.9244->44.6547us（1.0732x，5/5 对偏向候选、spread <0.4%，aiv_vec -9.5% fp16/bf16、-6.6% fp32）。两者精度均 20/20 且输出位级一致。",
  "verification": {
    "correctness": [
      "ReluSoftmax 20/20 PASS（all_direct），输出位级一致（bit-identical）",
      "SoftmaxRelu 20/20 PASS，0 修复轮，bit-compatible（消费同一批 fp32 exp 值，Mul/Maxs/downcast/Store 不变）"
    ],
    "performance": [
      "ReluSoftmax：formal paired ABBA 4 对（B A A B B A A B，同 shape，provenance-clean 冻结基线 .so vs 候选 .so）geomean 46.915->43.285us = 1.0839x，pair spread 1.0835-1.0846，worst dtype case ratio 1.0300（bf16 1.1085x、fp16 1.1128x、fp32 1.0300x）；回滚条件（geomean <1.02x 或任一 case <0.97x）未触发",
      "SoftmaxRelu：formal paired ABBA 5 对 / 10 runs（balanced alternating，provenance-clean）kernel geomean 47.9244->44.6547us = 1.0732x，5/5 对偏向候选、spread <0.4%；aiv_vec 时间 -9.5%（fp16/bf16）、-6.6%（fp32）",
      "两例均为每元素删掉一次 Exp 并移除对应输入链：ReluSoftmax fp16/bf16 每元素 18->15 条 v-insn（4+7+4），fp32 14->12（3+6+3）；SoftmaxRelu fp16/bf16 每元素约 16 条降到约 13-14 条"
    ],
    "rollback_signals": [
      "formal paired ABBA 显示 geomean <1.02x 或任一 dtype case mean <0.97x（ReluSoftmax 采用的回滚口径）",
      "ccec 拒绝改造后的单循环体且同一机制内的指令重排无法修复",
      "暂存带来的额外 UB 流量抵消收益（实测增益 <2%）时记 rejected_performance",
      "multi-tile row 或 strided 路径出现回退（说明回退臂被误改）",
      "MERE/MARE 偏离位级一致（说明暂存与重算的 exp 不再同源）"
    ]
  }
}
-->

# 性能优化策略：跨 pass fp32 exp 的 UB 暂存复用

在既有 single-read row 结构上，把 sum-exp 遍已算出的 fp32 e=exp(x-max) 按原始位暂存进行规模 fp32 UB 缓冲，out 遍改为直接消费该 e。ReluSoftmax kernel geomean 46.915->43.285us（1.0839x），SoftmaxRelu kernel geomean 47.9244->44.6547us（1.0732x）。

## 1. 原理

同一 row 内 max/sum/out 三遍 UB 扫里 (Sub, Exp) 被算两次，两次的输入（同一 UB x、同一 broadcast max）完全相同，属于语义冗余而非精度需要。把这批 exp 按原始位暂存到 fp32 UB 后，out 遍只剩 LoadAlign + Mul + downcast + Store，删掉一次 Exp 及其输入链；代价是多一次 UB StoreAlign 与一次 fp32 LoadAlign，相对一次超越函数与它的 unpack/Cast/Sub 输入链是净赚。之所以走 UB 暂存而不是寄存器直通：ccec 只接受每函数一个循环、寄存器不跨循环边界存活，跨 pass 的中间量无法驻留寄存器；UB 暂存是对该编译约束下的可行解。

实现机制：跨 pass 的 fp32 exp UB 暂存复用。sum-exp 遍在既有单循环内按 rep 追加一条掩码 Reg::StoreAlign，把 e=exp(x-max) 的 fp32 位写进新分配的行规模暂存缓冲；out 遍退化为一个独立单循环：LoadAlign(e) -> Mul by 已 hoist 的 rcpSum -> [fp16/bf16 downcast] -> StoreAlign，删除 GM 重读、B16 unpack+Cast、Sub 与第二次 Exp。因删除的是「同输入同算子的重复计算」，开销仅一次 UB（非 GM）StoreAlign 与一次 fp32 LoadAlign，而输出消费的仍是同一批 exp 位，故位级一致。ccec 只接受「每函数恰好一个循环、寄存器不跨循环边界存活」，因此中间量走 UB 而不是寄存器——这正是与 in-register-s-forwarding 的分界：后者把两遍融合、让中间量驻留寄存器以删掉 UB store->reload 往返；本机制保留 pass 边界，用 UB 暂存换取删掉一次 Exp 重算。回退臂为 multi-tile row 与 strided 路径的原码。

## 2. 性能问题模式

- 优化目标：消除 out 遍对 sum-exp 遍已算出的 e=exp(x-max) 的整遍重算（per element: LoadAlign + upcast Cast + Maxs + Sub + Exp 全冗余）：只把 fp32 exp 值经 UB 暂存跨 pass 传递，不动既有的 single-read row 结构
- 适用数据流：已具备 single-read row 结构（isRow && D <= ROW_TILE）的 softmax 系融合算子：sum-exp 遍与 out 遍对同一 UB x、同一 broadcast max 重算同一批 exp，且 aiv_vec 为绑定流水
- Feature signature：`{"bottleneck": ["redundant-exp-recompute", "duplicate-sub-exp-pass", "aiv-vec-emission-bound"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "cross-pass-ub-staged-exp-reuse", "reduce_mode": "row-softmax", "structure": ["fp32-ub-staging-buffer", "single-loop-per-function-ccec-constraint", "out-sweep-degenerates-to-load-mul-store", "bit-identical-output", "untouched-multi-tile-and-strided-fallback"]}`

## 3. 正确性红线

- 与 in-register-s-forwarding 的关系必须分清：该卡走向相反——把两遍融合、让中间量全程驻留寄存器，删除的是 UB store->reload 往返与 RAW 屏障；本卡保留 pass 边界、显式经 UB 暂存，删除的是 exp 的重算。二者不可叠加于同一中间量：若同时做，则寄存器直通已经消除了往返，UB 暂存会变成纯增开销
- 暂存引入的额外 UB StoreAlign/LoadAlign 是收益的对冲项；ReluSoftmax 最差 dtype case（fp32）ratio 仅 1.0300，贴近 1.02x 的回滚线，fp32 侧本就更吃 MTE2（17.84us）
- ccec 可能拒绝改造后的单循环体（修复预算只覆盖同一机制内的指令重排），暂存点必须留在既有 sum 循环内、新循环自成一函数
- 多 tile row（D > ROW_TILE）与 strided（inner>1）路径必须保持原 SumExp/OutPass 逐字节不变；全部 20 个测试用例均为 [4096,4096] dim=-1，非测试形状只能靠原码回退保证正确
- 暂存与消费的 exp 必须位级相同（同一输入、同一算子、同一舍入），否则输出不再是位级一致，pinned 语义会静默漂移

资源与硬件约束：

- ccec 编译约束：每函数恰好一个循环、寄存器不跨循环边界存活——暂存必须落在既有 sum 循环内，新的 scale 循环必须自成一函数，不得让寄存器跨 pass 存活
- 暂存缓冲必须是 fp32（e=exp(x-max) 的原始位），且 out 遍消费的必须是与 sum 遍位级相同的 exp 值（同一 UB x、同一 broadcast max），否则位级一致不成立
- 新增 UB 预算须落在容量内：ReluSoftmax 新增 16KB fp32 staging（fp32 worst case xQue 2x16KB + yQue 2x16KB + staging 16KB + smallBuf ~2KB 约 82KB << 256KB/core）；SoftmaxRelu expBuf_ 为 dimSize*4 + 256 bytes，总 UB 215,360B / 253,952B，rowBatch 保持 6/6/3 不需重规划
- multi-tile row 路径（D > ROW_TILE）与 strided 路径（inner>1）必须逐字节不变地保留原 SumExp/OutPass 实现

## 4. 泛化条件

- 策略作用域：op_class：normalization

适用：

- 算子已具备 single-read row 结构（isRow && D <= ROW_TILE），每行依次跑 max/sum/out 三遍 UB 扫
- sum-exp 遍已按元素算出 e=exp(x-max) 的 fp32 值，out 遍又从同一 x 与同一 broadcast max 重算同一批 e（含 unpack + Cast + Sub + Exp）
- aiv_vec 是绑定流水（ReluSoftmax champion bf16 vec 41.79us / aiv 47.984us、fp16 41.78/47.918、fp32 36.69/44.890，vec_ratio 0.82-0.87；SoftmaxRelu champion fp16 vec 41.674/48.814 = 85.4%、bf16 41.702/48.738 = 85.6%、fp32 37.294/45.409 = 82.1%），MTE2/MTE3 远低于 vec
- UB 有容纳行规模 fp32 暂存缓冲的余量（ReluSoftmax 新增 16KB 后仍远低于 256KB/core；SoftmaxRelu 215,360B / 253,952B）
- 输出必须与 champion 位级一致（同一批 exp 位被消费、同一 rcpSum 乘、同一 downcast）

不适用：

- 不适用于需要整行常驻 UB 改造的场景——本机制不改变既有 single-read row 结构，只增加一次跨 pass 的 UB 暂存（行常驻单读是另有杠杆，见 row-resident-single-gm-read-cross-pass-reuse）
- D > ROW_TILE 的多 tile 行与 inner>1 的 strided 路径不适用，保持原码
- sum 遍与 out 遍不共享同一份 exp 输入（例如中间有额外逐元素变换）时不适用
- 以「消除 UB store->reload 往返」为目标的位点不适用——该目标走寄存器直通路线（in-register-s-forwarding），本机制走向相反：保留 pass 边界、显式经 UB 暂存

## 5. 实施步骤

1. 在 Init() 内新增一个行规模 fp32 暂存缓冲（ReluSoftmax 为 16KB VECCALC expBuf_ + ExpUb() accessor；SoftmaxRelu 为 TBuf expBuf_ = dimSize*4 + 256 bytes），仅 single-read row 分支使用
2. 把 sum-exp 遍改造成 store 变体：保留原循环体，只在每个 rep 内追加一条掩码 Reg::StoreAlign，把刚算出的 e=exp(x-max) 的 fp32 原始位写入暂存缓冲
3. 新增独立的 scale/out 循环（自成一函数，满足 ccec 单循环约束）：hoist rcpSum（Duplicate 1.0f + Div by sumUb，与 OutPass 完全一致），每 rep 走 LoadAlign(exp) -> Mul -> [fp16/bf16 downcast Cast] -> StoreAlign
4. 把 single-read row 分支改为调用 staged 对（SumExpStore + 新 scale 遍），该分支不再调用原 OutPass
5. multi-tile row（D > ROW_TILE）与 strided（inner>1）路径保持原 SumExp/OutPass 逐字节不变
6. 跑 20/20 精度与 >=4 对 ABBA 配对（外层 msprof device Task Duration，两级 case-mean 再 geomean）

## 6. LLM 前置问题

- 目标实现是否满足：算子已具备 single-read row 结构（isRow && D <= ROW_TILE），每行依次跑 max/sum/out 三遍 UB 扫？
- 目标实现是否满足：sum-exp 遍已按元素算出 e=exp(x-max) 的 fp32 值，out 遍又从同一 x 与同一 broadcast max 重算同一批 e（含 unpack + Cast + Sub + Exp）？
- 目标实现是否满足：aiv_vec 是绑定流水（ReluSoftmax champion vec_ratio 0.82-0.87；SoftmaxRelu champion 82.1-85.6%），MTE2/MTE3 远低于 vec？
- 目标实现是否满足：UB 有容纳行规模 fp32 暂存缓冲的余量（ReluSoftmax 新增 16KB；SoftmaxRelu 215,360B / 253,952B）？
- 目标实现是否满足：输出必须与 champion 位级一致（同一批 exp 位被消费、同一 rcpSum 乘、同一 downcast）？
- 是否命中排除条件：不适用于需要整行常驻 UB 改造的场景——本机制不改变既有 single-read row 结构，只增加一次跨 pass 的 UB 暂存？
- 是否命中排除条件：D > ROW_TILE 的多 tile 行与 inner>1 的 strided 路径不适用，保持原码？
- 是否命中排除条件：sum 遍与 out 遍不共享同一份 exp 输入（例如中间有额外逐元素变换）时不适用？
- 是否命中排除条件：以「消除 UB store->reload 往返」为目标的位点不适用——该目标走寄存器直通路线（in-register-s-forwarding），本机制走向相反？

## 7. 验收标准

正确性：

- ReluSoftmax 20/20 PASS（all_direct），输出位级一致（bit-identical）
- SoftmaxRelu 20/20 PASS，0 修复轮，bit-compatible（消费同一批 fp32 exp 值，Mul/Maxs/downcast/Store 不变）

性能：

- ReluSoftmax：formal paired ABBA 4 对（B A A B B A A B，同 shape，provenance-clean 冻结基线 .so vs 候选 .so）geomean 46.915->43.285us = 1.0839x，pair spread 1.0835-1.0846，worst dtype case ratio 1.0300（bf16 1.1085x、fp16 1.1128x、fp32 1.0300x）；回滚条件（geomean <1.02x 或任一 case <0.97x）未触发
- SoftmaxRelu：formal paired ABBA 5 对 / 10 runs（balanced alternating，provenance-clean）kernel geomean 47.9244->44.6547us = 1.0732x，5/5 对偏向候选、spread <0.4%；aiv_vec 时间 -9.5%（fp16/bf16）、-6.6%（fp32）
- 两例均为每元素删掉一次 Exp 并移除对应输入链：ReluSoftmax fp16/bf16 每元素 18->15 条 v-insn（4+7+4），fp32 14->12（3+6+3）；SoftmaxRelu fp16/bf16 每元素约 16 条降到约 13-14 条

回滚信号：

- formal paired ABBA 显示 geomean <1.02x 或任一 dtype case mean <0.97x（ReluSoftmax 采用的回滚口径）
- ccec 拒绝改造后的单循环体且同一机制内的指令重排无法修复
- 暂存带来的额外 UB 流量抵消收益（实测增益 <2%）时记 rejected_performance
- multi-tile row 或 strided 路径出现回退（说明回退臂被误改）
- MERE/MARE 偏离位级一致（说明暂存与重算的 exp 不再同源）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：in-register-s-forwarding

- loop_20260913_070917（operator=ReluSoftmax, status=accepted, speedup=1.0839, precision=20/20 PASS, 4 对 ABBA, kernel geomean 46.915->43.285us）
- loop_20260913_070917（operator=SoftmaxRelu, status=accepted, speedup=1.0732, precision=20/20 PASS, 5 对/10 runs ABBA, kernel geomean 47.9244->44.6547us）

## 检索卡（短卡）

动作：把 sum-exp 遍算出的 fp32 exp 按原始位暂存 UB，out 遍直接消费该 e
适用：已具备 single-read row 结构（isRow && D<=ROW_TILE），sum 与 out 遍重算同一批 e
限制：ccec 每函数一循环、寄存器不跨循环存活；暂存与消费 exp 须位级相同；multi-tile/strided 逐字节不变
范围：normalization 的 single-read row softmax 算子
检索词：UB 暂存、Reg::StoreAlign、LoadAlign、expBuf_、位级一致
机会：out 遍把 sum-exp 遍已算出的 e 整遍重算（含 Cast/Sub/Exp）
代价：多一次 UB StoreAlign/LoadAlign，fp32 贴近 1.02x 回滚线
