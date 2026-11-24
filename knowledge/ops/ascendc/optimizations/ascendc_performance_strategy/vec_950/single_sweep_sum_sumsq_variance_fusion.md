---
type: Optimization
title: 单趟 sum/sumsq 融合扫描：双矩并发归约求方差
description: 把每行两趟统计扫描（ReduceSum 再 ReduceSumsq）融合为单趟双寄存器累加器，方差改由 E[x²]−mean² 导出。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/single-sweep-sum-sumsq-variance-fusion.md
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
      "方差必须用 E[x²]−mean² 恒等式时，须配 Reg::Max 0 夹取（max(sumsq*invCount − mean^2, 0)）再开方，防止 fp 相消产生微小负值导致 sqrt 出 NaN",
      "两份 partial 区必须各自 32B 对齐：sum 放 [0, maxPartials)，sumsq 放 [sqBase_, sqBase_+maxPartials)，sqBase_ = round8(maxPartials)；workBuf 的固定字节 UB 预算（S3/R1）须同步更新，否则 UB 溢出",
      "累加器必须保持 fp32：低精度累加会放大 E[x²]−mean² 的相消误差",
      "所有统计调用点（L==1 热路径、L==1 回退、L>1 路径）必须同步切换到融合 sweep，避免同一 kernel 内并存两种 partial 布局"
    ],
    "excluded_conditions": [
      "分布可能让 |mean| 相对 range 偏大（重尾/大偏置）时不得直接套用 E[x²]−mean²：灾难性相消会吞掉有效位；该轮测试集（均匀对称范围）未触发，但不能外推",
      "需要 (x−mean)² 参与后续非线性运算（而非只求方差/rstd）时，本融合不完整，须保留重读分支",
      "已知 mte2 真饱和的 fp32 形状不适用本机制：删一趟 UB 重读不减少 GM 流量（该轮 fp32 mte2 58.5-76.6%，vec 85-86% 才是主导）"
    ],
    "required_conditions": [
      "每行统计需要 sum 与 sum-of-squares 两个矩（均值 + 方差/rstd 类归一化）",
      "kernel 由 VF 管道主导（该轮三种 dtype 的 aiv_vec_ratio 均为 85.0-87.9%，为唯一饱和管道）",
      "两趟扫描当前对同一 UB tile 重复载入（ReduceSum 后再 ReduceSumsq），即存在可省的一次 UB 重读与一套循环迭代",
      "行内数据已驻留 UB，融合只需要一次载入；partial 区可容纳两份 32B 对齐布局",
      "归一化后立即消费 rstd，且算子已有极端值回退路径（CPU-native fallback）可承接相消/非有限情形"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "group_norm_batch_norm_slow_thinking",
      "operator_class": "normalization",
      "precision": "20/20 PASS (worst case16 MERE 7.2781e-07, limit 1.2207e-04)",
      "rounds_or_pairs": "5 对 balanced-alternating ABBA（10 次测量，per-pair geomean ratio 0.8872-0.8881）",
      "run_id": "<run-id>",
      "speedup": 1.1264,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-vf-issue",
      "redundant-ub-tile-reread",
      "two-pass-statistics-sweep"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "single-sweep-sum-sumsq-variance-fusion",
    "reduce_mode": "sum-sumsq",
    "structure": [
      "single-sweep-dual-register-accumulator",
      "ex2-minus-mean2-variance",
      "max0-clamp",
      "dual-aligned-partial-buffer"
    ]
  },
  "generality": "op_class",
  "id": "NORM-SINGLE-SWEEP-SUM-SUMSQ-FUSION",
  "implementation_steps": [
    "新增单趟融合 helper（该轮 GNB_TileReduceSumSumsq）：每个 64 宽 chunk 只载入一次，Mul x*x，然后 Reduce SUM x 与 Reduce SUM x²，两个寄存器累加器各加一次，替换原来的 GNB_TileReduceSum + GNB_TileReduceSumsq 两趟",
    "方差改用 E[x²]−mean² 恒等式：rstd = 1/sqrt(max(sumsq*invCount − mean^2, 0) + eps)，Max 0 夹取防 fp 相消负值（该轮 GNB_FinalizeRstd 改收 meanUb）",
    "workBufA/workBufB 扩为两份 32B 对齐 partial 区（sum 在 [0,maxPartials)，sumsq 在 [sqBase_, sqBase_+maxPartials)，sqBase_ = round8(maxPartials)），并同步更新 S3/R1 固定字节 UB 预算",
    "合并树同步改造（该轮 MergeStatsPair）：用一次 ping-pong 树同时合并两份 partial 区；StatsPassFused 每 tile 只拷入一次并产出两份 partial，把 L==1 回退与 L>1 路径的统计相 GM 流量减半",
    "把全部统计调用点切到融合 sweep：L==1 热路径、L==1 回退、L>1 路径（该轮四个调用点）"
  ],
  "intent": "消除行统计相位的重复成本：每行原本对同一 UB tile 做两趟扫描（先 ReduceSum 再 ReduceSumsq，同一数据被载入并归约两次），再加第三趟 NormalizeL1；融合后删掉一整趟 tile 重读、约 40% 的统计 VF 操作、一次 LocalMemBar 与一整套循环迭代。",
  "mechanism": "把每行的两次统计扫描融合为一次双矩并发扫描：每个 64 宽 chunk 只载入一次，Mul x*x 得到平方，然后对 x 与 x² 各做一次 Reduce SUM，两个寄存器累加器各加一次（每 chunk 由 load+mul+reduce+reduce+add+add 组成，替换原来两个独立的 load+reduce+add 与 load+sub+mul+reduce+add 两组）。方差不再靠重读 tile 求 (x−mean)²，而用 E[x²]−mean² = sumsq*invCount − mean^2，出口处 Reg::Max 0 夹取后开方。两份 partial 写进同一 workBuf 的两个 32B 对齐区，合并树一次 ping-pong 同时归约。全流程 fp32 累加；极端值/非有限情形仍由既有 CPU-native 回退路径承接，行为与两趟形式一致。",
  "name": "单趟 sum/sumsq 融合扫描：双矩并发归约求方差",
  "operator_class": "normalization",
  "operator_scope": "需要逐行/逐组双矩统计（mean + 方差 → rstd）的归一化类算子：GroupNorm / BatchNorm / LayerNorm / RMSNorm 等把行统计作为归一化前导相位的实现；输入行驻留 UB，统计相位由 VF 管道主导",
  "principle": "归一化的行统计相位对同一 tile 付两趟代价（sum 一趟、sumsq 一趟），两趟的载入与归约完全重复。把两趟合成一趟的算术依据是：sum 与 sum-of-squares 是同一个载入流的两个可交换归约量，可以在一次遍历里用两个独立寄存器累加器并发累加，每元素只多一条 Mul x*x。方差不再是独立观测量，而是 E[x²]−mean² 的代数导出量，于是省掉「重读 tile 求 (x−mean)²」的第三趟访问。在 VF-issue-bound 的 kernel 上，删除的指令与 UB 访问直接转化为 wall-time。",
  "related_anti_patterns": [],
  "risks": [
    "fp32 相消误差：E[x²]−mean² 在 |mean| 相对 range 偏大时灾难性相消。该轮的 20 个 case（[4096,4096]、num_groups=4、均匀对称测试范围）未触发，MERE 水平与 baseline 持平（~4e-7），最差 case16 MERE 7.2781e-07 对限 1.2207e-04；但分布可能触发相消的算子必须先按此路径评估",
    "极端 case（该轮 case11/12/13 的 inf/nan）在 CPU-native 回退下与两趟形式退化行为完全一致，需在验收中显式复查语义",
    "UB 预算：两份 32B 对齐 partial 区使 workBuf 扩大（sqBase_ = round8(maxPartials)），S3/R1 固定字节预算必须同步更新，否则溢出",
    "该轮的 per-row partials 数为 1，MergeToScalar 本就是 no-op，因此机制只作用于扫描结构本身而非合并树；partials>1 的形状未被该轮测量",
    "一次性诊断 run（fp32 106.5us、mte2 84.4%）与均衡配对测量矛盾（fp32 64.8-68.4us、vec 85-86% 主导），fp32 的 MTE2 受限假设未被证实——非配对证据不足以支撑「mte2 才是主导」的立项判断"
  ],
  "slug": "single-sweep-sum-sumsq-variance-fusion",
  "summary": "把每行的两趟统计扫描（ReduceSum 再 ReduceSumsq，同一 UB tile 被载入并归约两次）融合为单趟双寄存器累加器并发扫描：每个 64 宽 chunk 只载入一次、Mul x*x、两次 Reduce SUM、两个累加器各加一次，方差改用 E[x²]−mean² 恒等式（配 Max-0 夹取）而非重读 tile 求 (x−mean)²。设备 Task Duration geomean 61.370→54.484us（1.1264x，−11.22%；fp32 −14.9% / bf16 −9.9% / fp16 −8.7%），精度 20/20 通过、零修复轮。",
  "verification": {
    "correctness": [
      "20/20 精度通过，repairs_used=0；最差 case16 MERE 7.2781e-07（限 1.2207e-04）",
      "E[x²]−mean² 相消在该轮 case 集上未兑现：MERE 水平与 baseline 持平（~4e-7）",
      "极端 case 11/12/13 与两趟形式退化行为一致（非有限值走既有 CPU-native 回退）"
    ],
    "performance": [
      "5 对 balanced-alternating ABBA（10 次测量，provenance clean、同 shape），每对方向一致，per-pair geomean ratio 0.8872-0.8881",
      "设备 Task Duration geomean 61.370→54.484us（speedup 1.1264，−11.22%）；fp32 −14.9% / bf16 −9.9% / fp16 −8.7%，三种 dtype 在每一对中都改善",
      "champion 配对画像佐证 VF 是唯一主导管道：fp16 vec 85.0-85.7%、fp32 84.8-86.2%、bf16 87.1-87.9%，而 scalar 34.6-73.2%、mte2 13.8-76.6%、mte3 13.8-31.8% 均低于 vec；与「删一趟 tile 重读 + 约 40% 统计 VF 操作」的预期方向一致"
    ],
    "rollback_signals": [
      "大 |mean| 分布上 E[x²]−mean² 相消导致 MERE/MARE 超阈",
      "workBuf 尺寸/对齐改造引入 UB 溢出或两份 partial 区重叠",
      "配对 ABBA geomean 回退，或任一精度 case 在修复预算内无法通过",
      "非有限值 case 语义与两趟形式不再一致"
    ]
  }
}
-->

# 性能优化策略：单趟 sum/sumsq 融合扫描：双矩并发归约求方差

把每行的两趟统计扫描（ReduceSum 再 ReduceSumsq，同一 UB tile 被载入并归约两次）融合为单趟双寄存器累加器并发扫描：每个 64 宽 chunk 只载入一次、Mul x*x、两次 Reduce SUM、两个累加器各加一次，方差改用 E[x²]−mean² 恒等式（配 Max-0 夹取）而非重读 tile 求 (x−mean)²。设备 Task Duration geomean 61.370→54.484us（1.1264x，−11.22%；fp32 −14.9% / bf16 −9.9% / fp16 −8.7%），精度 20/20 通过、零修复轮。

## 1. 原理

归一化的行统计相位对同一 tile 付两趟代价（sum 一趟、sumsq 一趟），两趟的载入与归约完全重复。把两趟合成一趟的算术依据是：sum 与 sum-of-squares 是同一个载入流的两个可交换归约量，可以在一次遍历里用两个独立寄存器累加器并发累加，每元素只多一条 Mul x*x。方差不再是独立观测量，而是 E[x²]−mean² 的代数导出量，于是省掉「重读 tile 求 (x−mean)²」的第三趟访问。在 VF-issue-bound 的 kernel 上，删除的指令与 UB 访问直接转化为 wall-time。

实现机制：把每行的两次统计扫描融合为一次双矩并发扫描：每个 64 宽 chunk 只载入一次，Mul x*x 得到平方，然后对 x 与 x² 各做一次 Reduce SUM，两个寄存器累加器各加一次（每 chunk 由 load+mul+reduce+reduce+add+add 组成，替换原来两个独立的 load+reduce+add 与 load+sub+mul+reduce+add 两组）。方差不再靠重读 tile 求 (x−mean)²，而用 E[x²]−mean² = sumsq*invCount − mean^2，出口处 Reg::Max 0 夹取后开方。两份 partial 写进同一 workBuf 的两个 32B 对齐区，合并树一次 ping-pong 同时归约。全流程 fp32 累加；极端值/非有限情形仍由既有 CPU-native 回退路径承接，行为与两趟形式一致。

与既有卡的分工需要点明：`fused-row-column-statistics-pass` 是把**不同**的下游统计量搭车到已有数据的 pass 上（在算归一化值的同时顺带累加 colSum 等后继统计量，减少的是后续相位的扫描次数）；本卡融合的是**同一行、同一数据的两个同源矩**（sum 与 sumsq），减少的是统计相位自身的 tile 重读。`max-identity-substitution` 走的是另一条路——用代数恒等式把整趟归约**替换成常数条指令**（m2 = fl(1.0/sum1) 替代第二趟 max 归约）；本卡不消除归约，而是把一个归约趟次合并进另一个，方差仍由真实累加量导出。

## 2. 性能问题模式

- 优化目标：消除行统计相位的重复成本：每行原本对同一 UB tile 做两趟扫描（先 ReduceSum 再 ReduceSumsq，同一数据被载入并归约两次），再加第三趟 NormalizeL1；融合后删掉一整趟 tile 重读、约 40% 的统计 VF 操作、一次 LocalMemBar 与一整套循环迭代。
- 适用数据流：需要逐行/逐组双矩统计（mean + 方差 → rstd）的归一化类算子：GroupNorm / BatchNorm / LayerNorm / RMSNorm 等把行统计作为归一化前导相位的实现；输入行驻留 UB，统计相位由 VF 管道主导
- Feature signature：`{"bottleneck": ["vec-vf-issue", "redundant-ub-tile-reread", "two-pass-statistics-sweep"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "single-sweep-sum-sumsq-variance-fusion", "reduce_mode": "sum-sumsq", "structure": ["single-sweep-dual-register-accumulator", "ex2-minus-mean2-variance", "max0-clamp", "dual-aligned-partial-buffer"]}`

## 3. 正确性红线

- fp32 相消误差：E[x²]−mean² 在 |mean| 相对 range 偏大时灾难性相消。该轮的 20 个 case（[4096,4096]、num_groups=4、均匀对称测试范围）未触发，MERE 水平与 baseline 持平（~4e-7），最差 case16 MERE 7.2781e-07 对限 1.2207e-04；但分布可能触发相消的算子必须先按此路径评估
- 极端 case（该轮 case11/12/13 的 inf/nan）在 CPU-native 回退下与两趟形式退化行为完全一致，需在验收中显式复查语义
- UB 预算：两份 32B 对齐 partial 区使 workBuf 扩大（sqBase_ = round8(maxPartials)），S3/R1 固定字节预算必须同步更新，否则溢出
- 该轮的 per-row partials 数为 1，MergeToScalar 本就是 no-op，因此机制只作用于扫描结构本身而非合并树；partials>1 的形状未被该轮测量
- 一次性诊断 run（fp32 106.5us、mte2 84.4%）与均衡配对测量矛盾（fp32 64.8-68.4us、vec 85-86% 主导），fp32 的 MTE2 受限假设未被证实——非配对证据不足以支撑「mte2 才是主导」的立项判断

资源与硬件约束：

- 方差必须用 E[x²]−mean² 恒等式时，须配 Reg::Max 0 夹取（max(sumsq*invCount − mean^2, 0)）再开方，防止 fp 相消产生微小负值导致 sqrt 出 NaN
- 两份 partial 区必须各自 32B 对齐：sum 放 [0, maxPartials)，sumsq 放 [sqBase_, sqBase_+maxPartials)，sqBase_ = round8(maxPartials)；workBuf 的固定字节 UB 预算（S3/R1）须同步更新，否则 UB 溢出
- 累加器必须保持 fp32：低精度累加会放大 E[x²]−mean² 的相消误差
- 所有统计调用点（L==1 热路径、L==1 回退、L>1 路径）必须同步切换到融合 sweep，避免同一 kernel 内并存两种 partial 布局

## 4. 泛化条件

- 策略作用域：op_class：normalization

适用：

- 每行统计需要 sum 与 sum-of-squares 两个矩（均值 + 方差/rstd 类归一化）
- kernel 由 VF 管道主导（该轮三种 dtype 的 aiv_vec_ratio 均为 85.0-87.9%，为唯一饱和管道）
- 两趟扫描当前对同一 UB tile 重复载入（ReduceSum 后再 ReduceSumsq），即存在可省的一次 UB 重读与一套循环迭代
- 行内数据已驻留 UB，融合只需要一次载入；partial 区可容纳两份 32B 对齐布局
- 归一化后立即消费 rstd，且算子已有极端值回退路径（CPU-native fallback）可承接相消/非有限情形

不适用：

- 分布可能让 |mean| 相对 range 偏大（重尾/大偏置）时不得直接套用 E[x²]−mean²：灾难性相消会吞掉有效位；该轮测试集（均匀对称范围）未触发，但不能外推
- 需要 (x−mean)² 参与后续非线性运算（而非只求方差/rstd）时，本融合不完整，须保留重读分支
- 已知 mte2 真饱和的 fp32 形状不适用本机制：删一趟 UB 重读不减少 GM 流量（该轮 fp32 mte2 58.5-76.6%，vec 85-86% 才是主导）

## 5. 实施步骤

1. 新增单趟融合 helper（该轮 GNB_TileReduceSumSumsq）：每个 64 宽 chunk 只载入一次，Mul x*x，然后 Reduce SUM x 与 Reduce SUM x²，两个寄存器累加器各加一次，替换原来的 GNB_TileReduceSum + GNB_TileReduceSumsq 两趟
2. 方差改用 E[x²]−mean² 恒等式：rstd = 1/sqrt(max(sumsq*invCount − mean^2, 0) + eps)，Max 0 夹取防 fp 相消负值（该轮 GNB_FinalizeRstd 改收 meanUb）
3. workBufA/workBufB 扩为两份 32B 对齐 partial 区（sum 在 [0,maxPartials)，sumsq 在 [sqBase_, sqBase_+maxPartials)，sqBase_ = round8(maxPartials)），并同步更新 S3/R1 固定字节 UB 预算
4. 合并树同步改造（该轮 MergeStatsPair）：用一次 ping-pong 树同时合并两份 partial 区；StatsPassFused 每 tile 只拷入一次并产出两份 partial，把 L==1 回退与 L>1 路径的统计相 GM 流量减半
5. 把全部统计调用点切到融合 sweep：L==1 热路径、L==1 回退、L>1 路径（该轮四个调用点）

## 6. LLM 前置问题

- 目标实现是否满足：每行统计需要 sum 与 sum-of-squares 两个矩（均值 + 方差/rstd 类归一化）？
- 目标实现是否满足：kernel 由 VF 管道主导（该轮三种 dtype 的 aiv_vec_ratio 均为 85.0-87.9%，为唯一饱和管道）？
- 目标实现是否满足：两趟扫描当前对同一 UB tile 重复载入（ReduceSum 后再 ReduceSumsq），即存在可省的一次 UB 重读与一套循环迭代？
- 目标实现是否满足：行内数据已驻留 UB，融合只需要一次载入；partial 区可容纳两份 32B 对齐布局？
- 目标实现是否满足：归一化后立即消费 rstd，且算子已有极端值回退路径（CPU-native fallback）可承接相消/非有限情形？
- 是否命中排除条件：分布可能让 |mean| 相对 range 偏大（重尾/大偏置）时不得直接套用 E[x²]−mean²？
- 是否命中排除条件：需要 (x−mean)² 参与后续非线性运算（而非只求方差/rstd）时，本融合不完整，须保留重读分支？
- 是否命中排除条件：已知 mte2 真饱和的 fp32 形状不适用本机制？

## 7. 验收标准

正确性：

- 20/20 精度通过，repairs_used=0；最差 case16 MERE 7.2781e-07（限 1.2207e-04）
- E[x²]−mean² 相消在该轮 case 集上未兑现：MERE 水平与 baseline 持平（~4e-7）
- 极端 case 11/12/13 与两趟形式退化行为一致（非有限值走既有 CPU-native 回退）

性能：

- 5 对 balanced-alternating ABBA（10 次测量，provenance clean、同 shape），每对方向一致，per-pair geomean ratio 0.8872-0.8881
- 设备 Task Duration geomean 61.370→54.484us（speedup 1.1264，−11.22%）；fp32 −14.9% / bf16 −9.9% / fp16 −8.7%，三种 dtype 在每一对中都改善
- champion 配对画像佐证 VF 是唯一主导管道：fp16 vec 85.0-85.7%、fp32 84.8-86.2%、bf16 87.1-87.9%，而 scalar 34.6-73.2%、mte2 13.8-76.6%、mte3 13.8-31.8% 均低于 vec；与「删一趟 tile 重读 + 约 40% 统计 VF 操作」的预期方向一致

回滚信号：

- 大 |mean| 分布上 E[x²]−mean² 相消导致 MERE/MARE 超阈
- workBuf 尺寸/对齐改造引入 UB 溢出或两份 partial 区重叠
- 配对 ABBA geomean 回退，或任一精度 case 在修复预算内无法通过
- 非有限值 case 语义与两趟形式不再一致

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260913_183002（eid=free_explore_001, round=1, status=accepted, speedup=1.1264, precision=20/20 PASS）

## 检索卡（短卡）

动作：把每行两趟统计扫描（ReduceSum 再 ReduceSumsq）融合为单趟双寄存器累加器，方差改由 E[x²]−mean² 导出。
适用：每行需 sum 与 sumsq 双矩；VF 管道主导；两趟对同一 UB tile 重复载入。
限制：重尾/大偏置使 |mean| 相对 range 偏大时不得套用 E[x²]−mean²；须配 Reg::Max 0 夹取与 fp32 累加器。
范围：归一化类算子（GroupNorm/BatchNorm）的行统计相位
检索词：双寄存器累加器、E[x²]−mean²、Reg::Max、ReduceSum、ReduceSumsq、32B 对齐 partial
机会：同一 UB tile 被载入并归约两次，另有 LocalMemBar 冗余
代价：workBuf 扩为两份 32B 对齐 partial 区，UB 预算须同步更新
