---
type: Optimization
title: datablock 分段归约：短行用 vcgmax/vcgadd 一次产出逐行统计，取代跨 lane Reduce 链
description: 把短行每行的跨 lane Reduce 链改为按 32B datablock 分段的硬件归约原语，8 行一寄存器出统计量。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/short-row-datablock-segmented-reduce.md
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
      "vcgmax/vcgadd 结果压缩于 lanes 0-7（每 32B 块一个标量），必须经 32B scratch 往返广播回行块：masked 8-lane store + LocalMemBar + DIST_E2B_B32 load，每 8 行 2 次往返；按『块内复制』消费会得到垃圾级结果（round_01 18/20）",
      "-inf pad 必须使 datablock 边界与行边界精确重合；分段归约的 pad 语义（exp 后贡献 0、不夺 max）必须与 champion 的 Select(-inf) 掩码语义数值等价",
      "路由条件必须是 if constexpr(float) && rowLen<=8；余数行（rowCnt%8）、2-datablock 行、长行与 fp16/bf16 行逐字节保留原路径",
      "一个 256B 寄存器装 8 行 fp32（或 4 行上采后的 16-bit）；替换后的区域内不得再出现跨 lane Reduce 链",
      "消费模式须与 CANN reg-base softmax（l300/softmax_impl.h:575-613）同构：8-lane store + DIST_E2B_B32 load 广播回填"
    ],
    "excluded_conditions": [
      "行跨多个 datablock 或行很长（rowLen>64）时不适用：分段归约按 32B 段产出标量，2-datablock 行的部分和跨块合并无原语支持（本 run c13 fp32 pad16=64B 保留原路径）",
      "fp16/bf16 单 datablock 行（rowLen<=16）不在本 run 已验证的实现范围内：sum 需 16-lane 行跨 2 个 fp32 datablock，该分支逐字节保留 champion",
      "行不是行主序连续、或每 tile 不能保持单条连续 DataCopyPad 时不适用：本机制要求内存路径逐字节保留",
      "区域内并发存在多条独立跨 lane Reduce 链时本机制失效（缺陷域被重新触发）：替换后的路径必须 0 条跨 lane Reduce + Duplicate 链",
      "精度护栏要求与 champion 的 Reduce 树逐位一致时不适用：分段求和是另一种结合顺序，本 run 只在容差门（20/20）下成立"
    ],
    "required_conditions": [
      "短行 pad 后恰为一个 32B datablock（fp32 rowLen<=8；本 run 受益 case c20 rowLen3(pad8)、c11 rowLen7(pad8)），行边界与 datablock 边界重合",
      "行内归约的关键路径是跨 lane Reduce 链 + Duplicate 广播（每行 ~15 条向量指令、12 级串行依赖，实测 c20 约 59-72ns/行/核 = latency-bound）",
      "已有的 -inf pad（exp 后贡献 0、不夺 max）与 champion 的 Select(-inf) 掩码语义数值等价，使分段归约无需预处理",
      "目标 arch 的 CANN 9.1.0 Reg API 提供 Reg::ReduceMaxWithDataBlock/ReduceSumWithDataBlock（vcgmax/vcgadd，datablock=32B），与 champion 已在用的 Reg::Reduce 同一编译分派路径",
      "受益面集中在少数极多行的 case：c20+c13+c11 占 fp32 dtype 均值的 96%（其中 c20 74.8%、c13 13.9%、c11 3.4%），c14 占 fp16 均值的 77%"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "softmaxmul__v2",
      "operator_class": "fused-composite",
      "precision": "20/20 PASS（round_01 18/20 -> round_02 E2B 广播回填后一次通过）",
      "run_id": "<run-id>",
      "speedup": 1.4435,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "short-row-reduce-chain-latency",
      "per-row-cross-lane-reduce-duplicate-chain",
      "single-simd-region-multi-reduce-chain-hazard"
    ],
    "dtypes": [
      "fp32"
    ],
    "pattern": "datablock-segmented-row-reduce",
    "reduce_mode": "row-softmax",
    "structure": [
      "one-datablock-row-main-loop",
      "hardware-datablock-segmented-reduce",
      "vcgmax-vcgadd",
      "lanes-0-7-compressed-result",
      "32b-scratch-e2b-broadcast-roundtrip",
      "inf-pad-datablock-alignment",
      "remainder-row-fallback"
    ]
  },
  "generality": "op_class",
  "id": "VEC-DATABLOCK-SEGMENTED-ROW-REDUCE",
  "implementation_steps": [
    "先探针确认 vcgmax/vcgadd 的块内 lane 布局（lanes 0-7 压缩 vs 块内复制），并核对 CANN 9.1.0 kernel_reg_compute_vec_reduce_intf.h 与目标 arch impl 的可用性",
    "在 kernel 新增 SoftmaxMulDatablockRowGroupCompute：每 8 行（fp32）装入一个 256B 寄存器，链 LoadAlign->Muls->vcgmax->Sub->Exp->vcgadd->Div->Mul->Mul->StoreAlign",
    "在分段归约输出后接 32B scratch 往返把逐行统计量广播回行块：masked 8-lane store + LocalMemBar + DIST_E2B_B32 load，每 8 行 2 次往返",
    "路由条件收敛为 if constexpr(float) && rowLen<=8；余数行（rowCnt%8）走 champion W=1 路径，2-datablock 行、长行与 fp16/bf16 短行逐字节保留",
    "以 20/20 精度门 + 形式化配对 ABBA 验收，并核对 fp32 dtype 均值下降而 bf16/fp16 零扰动（本 run fp32 663.1→220.8us，bf16 51.0032→50.928、fp16 111.7131→111.7103）"
  ],
  "intent": "消除短行主循环里每行一条跨 lane Reduce 链 + Duplicate 广播的串行延迟：本 run 短行 W=1 路径每行 ~15 条向量指令、关键路径 12 级串行依赖（实测 ~59-72ns/行/核），且该形状恰好落在『单 __simd_vf__ 区域内多条独立跨 lane Reduce 链共存』的 ccec/硬件缺陷域里（多行交错 W>=2 的 2.4x 空间被锁死），本机制用硬件分段归约原语把每行的 max/sum 压成一条指令以绕开该域。",
  "mechanism": "datablock-segmented-row-reduce：路由条件 if constexpr(float) && rowLen<=8（pad 后恰一个 32B datablock），新增 SoftmaxMulDatablockRowGroupCompute：每 8 行一组装入一个 256B 寄存器，链为 LoadAlign->Muls->vcgmax->Sub->Exp->vcgadd->Div->Mul->Mul->StoreAlign。关键语义（本 run 的核心可证伪点）：ascend950 的 vcgmax/vcgadd（Reg::ReduceMaxWithDataBlock / Reg::ReduceSumWithDataBlock）结果压缩于 lanes 0-7（每 32B 块一个标量），不做块内复制，因此必须用 32B scratch 往返把它们广播回行块——masked 8-lane store + LocalMemBar + DIST_E2B_B32 load，每 8 行 2 次往返（2 次 membar），消费模式与 CANN reg-base softmax（l300/softmax_impl.h:575-613）同构。CANN 9.1.0 的 kernel_reg_compute_vec_reduce_intf.h 提供 Reg::ReduceDataBlock/ReduceSumWithDataBlock/ReduceMaxWithDataBlock（dav impl 的 vcgadd/vcgmax，datablock=32B），另有 PairReduceElem（vcpadd），三套 arch impl（3510/3003/3113）均定义，与 champion 已在用的 Reg::ReduceMax/Reg::ReduceSum 同一编译分派路径。余数行（rowCnt%8）、2-datablock 行（c13 fp32 pad16=64B）、fp16/bf16 短行与长行（rowLen>64）逐字节保留 champion 的 W=1 路径。",
  "name": "datablock 分段归约：短行用 vcgmax/vcgadd 一次产出逐行统计，取代跨 lane Reduce 链",
  "operator_class": "fused-composite",
  "operator_scope": "行主序、逐行独立、行 pad 后恰为一个 32B datablock（fp32 rowLen<=8）的 per-row softmax 类算子主循环；行内归约是每行一次跨 lane max/sum，行数极多（本 run c20 3,499,776 行 = 64 AIV 核 × 54,684 行/核）使链长乘行数成为 wall 主体。",
  "principle": "短行的逐行归约不是算力问题而是串行链问题：行足够短（pad 后只有一个 32B datablock）时，每行的跨 lane Reduce 链 + Duplicate 广播构成一条 12 级、约 15 条向量指令的串行依赖链，实测 ~59-72ns/行/核，远高于访存下界，wall 由链长乘行数决定。硬件提供的分段归约原语把『每行一次跨 lane 树』从软件链变成指令：一个 256B 寄存器装 8 行 fp32（或 4 行上采后的 16-bit），按 32B datablock 分段做 max/sum，一次产出全部 8 行的统计量——既去掉了跨行跨 lane Reduce 链与 Duplicate 广播，也把指令数压缩一个量级。它与『多行交错 / 私有化』类做法是正交的不同杠杆：后者试图在缺陷域内绕过（区域内两条独立 Reduce 链共存即失效），本机制直接把 Reduce 链的结构消掉，缺陷触发条件结构性消失。前提是 -inf pad 让 datablock 边界与行边界重合：pad 值 exp 后贡献 0、不夺 max，与 champion 的 Select(-inf) 掩码语义数值等价，因此无需预处理，行主序内存布局与每 tile 单条连续 DataCopyPad 也逐字节保留。",
  "related_anti_patterns": [],
  "risks": [
    "vcg 结果的块内 lane 布局是核心可证伪点：本 run round_01 假设『块内复制』，c11/c20 精度失败（18/20，垃圾级）；round_02 依 CANN reg-base softmax 同构消费改为 lanes 0-7 压缩 + E2B 广播回填后精度一次通过 20/20——必须先用单次探针确认布局再放大",
    "替换后区域内若残留任何跨 lane Reduce 链 / Duplicate 广播，就回到 direction_001/002 已证实的 ccec 缺陷域（单 __simd_vf__ 区域两条独立跨 lane Reduce 链共存 -> 第二条链确定性垃圾；2x2 矩阵 batched/spaced × shared/privatized 已闭合）",
    "路由面必须精确：余数行（rowCnt%8）与 2-datablock 行若被误纳入分段路径，会因段边界与行边界错位而出错",
    "每 8 行 2 次 UB 往返 + 2 次 membar 是固定税；行数不足或访存主导时机制的指令削减不转化为 wall（收益面集中在 c20/c11）",
    "fp16/bf16 短行未在本 run 落地，其精度论证不可从 fp32 旁推（c14 单 datablock 行需 16-lane 跨 2 个 fp32 datablock，半精度 vcgadd 或 UB 两半拆分往返均为未验证候选）"
  ],
  "slug": "short-row-datablock-segmented-reduce",
  "summary": "对 pad 后恰为一个 32B datablock 的 fp32 短行（rowLen<=8），把每行一条 12 级串行依赖链（Muls->Select->Max->ReduceMax->Duplicate->Sub->Exp->ReduceSum->Duplicate->Div->Mul->Mul，每行约 15 条向量指令、实测 ~59-72ns/行/核）换成按 datablock 分段的硬件归约原语 Reg::ReduceMaxWithDataBlock / Reg::ReduceSumWithDataBlock（vcgmax/vcgadd）：一个 256B 寄存器装 8 行，每行 max/sum 一次产出，全程零跨行跨 lane Reduce 链与零 Duplicate 广播，结构性绕开『单 __simd_vf__ 区域内多条独立跨 lane Reduce 链共存』的 ccec/硬件缺陷域。关键配方：vcg 结果压缩在 lanes 0-7（每 32B 块一个标量、不做块内复制），必须经 32B scratch 往返（masked 8-lane store + LocalMemBar + DIST_E2B_B32 load）把逐行统计量广播回行块，每 8 行 2 次往返。ModelNew 现有的 -inf pad 使 datablock 边界与行边界天然重合，无需 Select/-inf 预处理。geomean 155.7506→107.8956us（1.4435x；fp32 dtype 均值 663.1→220.8us = 3.0x，bf16/fp16 零扰动），c20 3940.5→552.2us（7.1x）、c11 184.6→34.1us（5.4x），精度 20/20。",
  "verification": {
    "correctness": [
      "20/20 PASS（round_01 18/20（c11/c20 失败）-> 预注册回退路径 round_02 E2B 广播回填后一次通过；编译修复 1 次，精度修复 1 次）",
      "替换路径零跨行跨 lane Reduce 链、零 Duplicate 广播；pad 语义（-inf 贡献 0 / 不夺 max）与 champion Select(-inf) 掩码数值等价",
      "未触碰路径逐字节保留 champion：余数行、2-datablock 行（c13 fp32 pad16=64B）、长行、fp16/bf16 全部 case"
    ],
    "performance": [
      "形式化配对 3 对 ABBA（12 次独立 msprof 测量，pair geomean ratio 0.69253/0.69306/0.69265，一致性 <0.1%）：geomean 155.7506→107.8956us（1.4435x）",
      "fp32 dtype 均值 663.1→220.8us（3.0x）；bf16 51.0032→50.928、fp16 111.7131→111.7103（零扰动）",
      "c20 3940.5→552.2us（7.1x）、c11 184.6→34.1us（5.4x）",
      "round_01 损坏态的性能探测 geomean 104.806us（1.49x 有可见收益），据此进入精度修复"
    ],
    "rollback_signals": [
      "vcg 结果布局假设错误（按块内复制消费 -> c11/c20 级垃圾输出）且 E2B 广播回填仍不通过",
      "分段路径与余数行/2-datablock 行的路由边界混淆，出现段-行错位",
      "fp16/bf16 或长行 case 相对 champion 出现超出噪声的扰动（本 run 期望 0.98-1.02x 无扰动）",
      "区域内被重新引入跨 lane Reduce 链 / Duplicate 广播，触发 ccec 多 Reduce 链缺陷",
      "每 8 行 2 次 UB 往返 + membar 的固定税在低行数 case 上超过指令削减收益"
    ]
  }
}
-->

# 性能优化策略：datablock 分段归约：短行用 vcgmax/vcgadd 一次产出逐行统计，取代跨 lane Reduce 链

对 pad 后恰为一个 32B datablock 的 fp32 短行（rowLen<=8），把每行一条 12 级串行依赖链（Muls->Select->Max->ReduceMax->Duplicate->Sub->Exp->ReduceSum->Duplicate->Div->Mul->Mul，每行约 15 条向量指令、实测 ~59-72ns/行/核）换成按 datablock 分段的硬件归约原语 Reg::ReduceMaxWithDataBlock / Reg::ReduceSumWithDataBlock（vcgmax/vcgadd）：一个 256B 寄存器装 8 行，每行 max/sum 一次产出，全程零跨行跨 lane Reduce 链与零 Duplicate 广播，结构性绕开『单 __simd_vf__ 区域内多条独立跨 lane Reduce 链共存』的 ccec/硬件缺陷域。关键配方：vcg 结果压缩在 lanes 0-7（每 32B 块一个标量、不做块内复制），必须经 32B scratch 往返（masked 8-lane store + LocalMemBar + DIST_E2B_B32 load）把逐行统计量广播回行块，每 8 行 2 次往返。ModelNew 现有的 -inf pad 使 datablock 边界与行边界天然重合，无需 Select/-inf 预处理。geomean 155.7506→107.8956us（1.4435x；fp32 dtype 均值 663.1→220.8us = 3.0x，bf16/fp16 零扰动），c20 3940.5→552.2us（7.1x）、c11 184.6→34.1us（5.4x），精度 20/20。

## 1. 原理

短行的逐行归约不是算力问题而是串行链问题：行足够短（pad 后只有一个 32B datablock）时，每行的跨 lane Reduce 链 + Duplicate 广播构成一条 12 级、约 15 条向量指令的串行依赖链，实测 ~59-72ns/行/核，远高于访存下界，wall 由链长乘行数决定。硬件提供的分段归约原语把『每行一次跨 lane 树』从软件链变成指令：一个 256B 寄存器装 8 行 fp32（或 4 行上采后的 16-bit），按 32B datablock 分段做 max/sum，一次产出全部 8 行的统计量——既去掉了跨行跨 lane Reduce 链与 Duplicate 广播，也把指令数压缩一个量级。它与『多行交错 / 私有化』类做法是正交的不同杠杆：后者试图在缺陷域内绕过（区域内两条独立 Reduce 链共存即失效），本机制直接把 Reduce 链的结构消掉，缺陷触发条件结构性消失。前提是 -inf pad 让 datablock 边界与行边界重合：pad 值 exp 后贡献 0、不夺 max，与 champion 的 Select(-inf) 掩码语义数值等价，因此无需预处理，行主序内存布局与每 tile 单条连续 DataCopyPad 也逐字节保留。

实现机制：datablock-segmented-row-reduce：路由条件 if constexpr(float) && rowLen<=8（pad 后恰一个 32B datablock），新增 SoftmaxMulDatablockRowGroupCompute：每 8 行一组装入一个 256B 寄存器，链为 LoadAlign->Muls->vcgmax->Sub->Exp->vcgadd->Div->Mul->Mul->StoreAlign。关键语义（本 run 的核心可证伪点）：ascend950 的 vcgmax/vcgadd（Reg::ReduceMaxWithDataBlock / Reg::ReduceSumWithDataBlock）结果压缩于 lanes 0-7（每 32B 块一个标量），不做块内复制，因此必须用 32B scratch 往返把它们广播回行块——masked 8-lane store + LocalMemBar + DIST_E2B_B32 load，每 8 行 2 次往返（2 次 membar），消费模式与 CANN reg-base softmax（l300/softmax_impl.h:575-613）同构。CANN 9.1.0 的 kernel_reg_compute_vec_reduce_intf.h 提供 Reg::ReduceDataBlock/ReduceSumWithDataBlock/ReduceMaxWithDataBlock（dav impl 的 vcgadd/vcgmax，datablock=32B），另有 PairReduceElem（vcpadd），三套 arch impl（3510/3003/3113）均定义，与 champion 已在用的 Reg::ReduceMax/Reg::ReduceSum 同一编译分派路径。余数行（rowCnt%8）、2-datablock 行（c13 fp32 pad16=64B）、fp16/bf16 短行与长行（rowLen>64）逐字节保留 champion 的 W=1 路径。

## 2. 性能问题模式

- 优化目标：消除短行主循环里每行一条跨 lane Reduce 链 + Duplicate 广播的串行延迟：本 run 短行 W=1 路径每行 ~15 条向量指令、关键路径 12 级串行依赖（实测 ~59-72ns/行/核），且该形状恰好落在『单 __simd_vf__ 区域内多条独立跨 lane Reduce 链共存』的 ccec/硬件缺陷域里（多行交错 W>=2 的 2.4x 空间被锁死），本机制用硬件分段归约原语把每行的 max/sum 压成一条指令以绕开该域。
- 适用数据流：行主序、逐行独立、行 pad 后恰为一个 32B datablock（fp32 rowLen<=8）的 per-row softmax 类算子主循环；行内归约是每行一次跨 lane max/sum，行数极多（本 run c20 3,499,776 行 = 64 AIV 核 × 54,684 行/核）使链长乘行数成为 wall 主体。
- Feature signature：`{"bottleneck": ["short-row-reduce-chain-latency", "per-row-cross-lane-reduce-duplicate-chain", "single-simd-region-multi-reduce-chain-hazard"], "dtypes": ["fp32"], "pattern": "datablock-segmented-row-reduce", "reduce_mode": "row-softmax", "structure": ["one-datablock-row-main-loop", "hardware-datablock-segmented-reduce", "vcgmax-vcgadd", "lanes-0-7-compressed-result", "32b-scratch-e2b-broadcast-roundtrip", "inf-pad-datablock-alignment", "remainder-row-fallback"]}`

## 3. 正确性红线

- vcg 结果的块内 lane 布局是核心可证伪点：本 run round_01 假设『块内复制』，c11/c20 精度失败（18/20，垃圾级）；round_02 依 CANN reg-base softmax 同构消费改为 lanes 0-7 压缩 + E2B 广播回填后精度一次通过 20/20——必须先用单次探针确认布局再放大
- 替换后区域内若残留任何跨 lane Reduce 链 / Duplicate 广播，就回到 direction_001/002 已证实的 ccec 缺陷域（单 __simd_vf__ 区域两条独立跨 lane Reduce 链共存 -> 第二条链确定性垃圾；2x2 矩阵 batched/spaced × shared/privatized 已闭合）
- 路由面必须精确：余数行（rowCnt%8）与 2-datablock 行若被误纳入分段路径，会因段边界与行边界错位而出错
- 每 8 行 2 次 UB 往返 + 2 次 membar 是固定税；行数不足或访存主导时机制的指令削减不转化为 wall（收益面集中在 c20/c11）
- fp16/bf16 短行未在本 run 落地，其精度论证不可从 fp32 旁推（c14 单 datablock 行需 16-lane 跨 2 个 fp32 datablock，半精度 vcgadd 或 UB 两半拆分往返均为未验证候选）

资源与硬件约束：

- vcgmax/vcgadd 结果压缩于 lanes 0-7（每 32B 块一个标量），必须经 32B scratch 往返广播回行块：masked 8-lane store + LocalMemBar + DIST_E2B_B32 load，每 8 行 2 次往返；按『块内复制』消费会得到垃圾级结果（round_01 18/20）
- -inf pad 必须使 datablock 边界与行边界精确重合；分段归约的 pad 语义（exp 后贡献 0、不夺 max）必须与 champion 的 Select(-inf) 掩码语义数值等价
- 路由条件必须是 if constexpr(float) && rowLen<=8；余数行（rowCnt%8）、2-datablock 行、长行与 fp16/bf16 行逐字节保留原路径
- 一个 256B 寄存器装 8 行 fp32（或 4 行上采后的 16-bit）；替换后的区域内不得再出现跨 lane Reduce 链
- 消费模式须与 CANN reg-base softmax（l300/softmax_impl.h:575-613）同构：8-lane store + DIST_E2B_B32 load 广播回填

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 短行 pad 后恰为一个 32B datablock（fp32 rowLen<=8；本 run 受益 case c20 rowLen3(pad8)、c11 rowLen7(pad8)），行边界与 datablock 边界重合
- 行内归约的关键路径是跨 lane Reduce 链 + Duplicate 广播（每行 ~15 条向量指令、12 级串行依赖，实测 c20 约 59-72ns/行/核 = latency-bound）
- 已有的 -inf pad（exp 后贡献 0、不夺 max）与 champion 的 Select(-inf) 掩码语义数值等价，使分段归约无需预处理
- 目标 arch 的 CANN 9.1.0 Reg API 提供 Reg::ReduceMaxWithDataBlock/ReduceSumWithDataBlock（vcgmax/vcgadd，datablock=32B），与 champion 已在用的 Reg::Reduce 同一编译分派路径
- 受益面集中在少数极多行的 case：c20+c13+c11 占 fp32 dtype 均值的 96%（其中 c20 74.8%、c13 13.9%、c11 3.4%），c14 占 fp16 均值的 77%

不适用：

- 行跨多个 datablock 或行很长（rowLen>64）时不适用：分段归约按 32B 段产出标量，2-datablock 行的部分和跨块合并无原语支持（本 run c13 fp32 pad16=64B 保留原路径）
- fp16/bf16 单 datablock 行（rowLen<=16）不在本 run 已验证的实现范围内：sum 需 16-lane 行跨 2 个 fp32 datablock，该分支逐字节保留 champion
- 行不是行主序连续、或每 tile 不能保持单条连续 DataCopyPad 时不适用：本机制要求内存路径逐字节保留
- 区域内并发存在多条独立跨 lane Reduce 链时本机制失效（缺陷域被重新触发）：替换后的路径必须 0 条跨 lane Reduce + Duplicate 链
- 精度护栏要求与 champion 的 Reduce 树逐位一致时不适用：分段求和是另一种结合顺序，本 run 只在容差门（20/20）下成立

## 5. 实施步骤

1. 先探针确认 vcgmax/vcgadd 的块内 lane 布局（lanes 0-7 压缩 vs 块内复制），并核对 CANN 9.1.0 kernel_reg_compute_vec_reduce_intf.h 与目标 arch impl 的可用性
2. 在 kernel 新增 SoftmaxMulDatablockRowGroupCompute：每 8 行（fp32）装入一个 256B 寄存器，链 LoadAlign->Muls->vcgmax->Sub->Exp->vcgadd->Div->Mul->Mul->StoreAlign
3. 在分段归约输出后接 32B scratch 往返把逐行统计量广播回行块：masked 8-lane store + LocalMemBar + DIST_E2B_B32 load，每 8 行 2 次往返
4. 路由条件收敛为 if constexpr(float) && rowLen<=8；余数行（rowCnt%8）走 champion W=1 路径，2-datablock 行、长行与 fp16/bf16 短行逐字节保留
5. 以 20/20 精度门 + 形式化配对 ABBA 验收，并核对 fp32 dtype 均值下降而 bf16/fp16 零扰动（本 run fp32 663.1→220.8us，bf16 51.0032→50.928、fp16 111.7131→111.7103）

## 6. LLM 前置问题

- 目标实现是否满足：短行 pad 后恰为一个 32B datablock（fp32 rowLen<=8；本 run 受益 case c20 rowLen3(pad8)、c11 rowLen7(pad8)），行边界与 datablock 边界重合？
- 目标实现是否满足：行内归约的关键路径是跨 lane Reduce 链 + Duplicate 广播（每行 ~15 条向量指令、12 级串行依赖，实测 c20 约 59-72ns/行/核 = latency-bound）？
- 目标实现是否满足：已有的 -inf pad（exp 后贡献 0、不夺 max）与 champion 的 Select(-inf) 掩码语义数值等价，使分段归约无需预处理？
- 目标实现是否满足：目标 arch 的 CANN 9.1.0 Reg API 提供 Reg::ReduceMaxWithDataBlock/ReduceSumWithDataBlock（vcgmax/vcgadd，datablock=32B），与 champion 已在用的 Reg::Reduce 同一编译分派路径？
- 目标实现是否满足：受益面集中在少数极多行的 case：c20+c13+c11 占 fp32 dtype 均值的 96%（其中 c20 74.8%、c13 13.9%、c11 3.4%），c14 占 fp16 均值的 77%？
- 是否命中排除条件：行跨多个 datablock 或行很长（rowLen>64）时不适用：分段归约按 32B 段产出标量，2-datablock 行的部分和跨块合并无原语支持（本 run c13 fp32 pad16=64B 保留原路径）？
- 是否命中排除条件：fp16/bf16 单 datablock 行（rowLen<=16）不在本 run 已验证的实现范围内：sum 需 16-lane 行跨 2 个 fp32 datablock，该分支逐字节保留 champion？
- 是否命中排除条件：行不是行主序连续、或每 tile 不能保持单条连续 DataCopyPad 时不适用：本机制要求内存路径逐字节保留？
- 是否命中排除条件：区域内并发存在多条独立跨 lane Reduce 链时本机制失效（缺陷域被重新触发）：替换后的路径必须 0 条跨 lane Reduce + Duplicate 链？
- 是否命中排除条件：精度护栏要求与 champion 的 Reduce 树逐位一致时不适用：分段求和是另一种结合顺序，本 run 只在容差门（20/20）下成立？

## 7. 验收标准

正确性：

- 20/20 PASS（round_01 18/20（c11/c20 失败）-> 预注册回退路径 round_02 E2B 广播回填后一次通过；编译修复 1 次，精度修复 1 次）
- 替换路径零跨行跨 lane Reduce 链、零 Duplicate 广播；pad 语义（-inf 贡献 0 / 不夺 max）与 champion Select(-inf) 掩码数值等价
- 未触碰路径逐字节保留 champion：余数行、2-datablock 行（c13 fp32 pad16=64B）、长行、fp16/bf16 全部 case

性能：

- 形式化配对 3 对 ABBA（12 次独立 msprof 测量，pair geomean ratio 0.69253/0.69306/0.69265，一致性 <0.1%）：geomean 155.7506→107.8956us（1.4435x）
- fp32 dtype 均值 663.1→220.8us（3.0x）；bf16 51.0032→50.928、fp16 111.7131→111.7103（零扰动）
- c20 3940.5→552.2us（7.1x）、c11 184.6→34.1us（5.4x）
- round_01 损坏态的性能探测 geomean 104.806us（1.49x 有可见收益），据此进入精度修复

回滚信号：

- vcg 结果布局假设错误（按块内复制消费 -> c11/c20 级垃圾输出）且 E2B 广播回填仍不通过
- 分段路径与余数行/2-datablock 行的路由边界混淆，出现段-行错位
- fp16/bf16 或长行 case 相对 champion 出现超出噪声的扰动（本 run 期望 0.98-1.02x 无扰动）
- 区域内被重新引入跨 lane Reduce 链 / Duplicate 广播，触发 ccec 多 Reduce 链缺陷
- 每 8 行 2 次 UB 往返 + membar 的固定税在低行数 case 上超过指令削减收益

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`

- loop_20260915_101435 status=accepted, speedup=1.4435, precision=20/20 PASS（round_01 18/20 -> round_02 E2B 广播回填后一次通过））

## 检索卡（短卡）

动作：把短行每行的跨 lane Reduce 链改为按 32B datablock 分段的硬件归约原语，8 行一寄存器出统计量。
适用：fp32 行 pad 后恰为一个 32B datablock（rowLen<=8）且与行边界重合。
限制：区域内不得残留跨 lane Reduce 链；余数行与 2-datablock 行须走原路径；fp16/bf16 不可由 fp32 旁推。
范围：pad 后单 datablock 的逐行 softmax 主循环。
检索词：vcgmax、vcgadd、ReduceDataBlock、DIST_E2B_B32、LocalMemBar
机会：短行主循环每行一条跨 lane Reduce 链 + Duplicate 广播，12 级串行依赖。
代价：每 8 行 2 次 UB 往返 + membar 为固定税。
