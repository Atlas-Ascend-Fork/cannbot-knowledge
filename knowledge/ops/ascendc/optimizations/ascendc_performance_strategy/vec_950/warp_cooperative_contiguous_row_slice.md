---
type: Optimization
title: warp 协作连续行切片：SIMT lane 重映射消除散射访存
description: 把 lane→data 映射由「一 lane 独占一行」改为「一 warp 认领连续行段」，lane l 取元素对 l,l+32,…，以免除法增量状态保 warp-uniform。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/warp-cooperative-contiguous-row-slice.md
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
      "per-row 索引算术必须保持 warp-uniform 且免除法：若朴素地每行做 2 次 div/mod，标量发射将由 ~5us 膨胀 32 倍并成为新的瓶颈——必须用 leader 计算 + broadcast，或（本轮采用）免除法增量状态",
      "行区间划分 chunk = ceil(coreRows/32) 必须覆盖且不重叠，残余行并入尾部处理；不得改动奇 E 回退臂与 host/tiling 代码，位级数据流保持不变",
      "行边界推进（row/b/M 回卷）必须由全体 lane 一致执行（warp-uniform 分支），不得引入 lane 分歧",
      "设备编译约束：__simt_vf__ 上下文不能调用普通 __aicore__ helper（该轮 EmbCatCeilDiv 报 no matching function），ceil-div 算术需内联"
    ],
    "excluded_conditions": [
      "行映射可由 host 解析（stride 字段可表达、每行源范围在结构校验内）时不适用本机制：直接走既有 per-row copy + 对齐 slot 的 host 可解析 gather 免路径",
      "E=32 时每行只有 16 个元素对，lane 利用率仅一半，收益上限受限；奇 E 走 legacy 臂，不被本机制覆盖",
      "若硬件 LSU 已对 lane 访存做内部合并（MSB merging），本机制增益将塌缩为噪声；该轮未出现，但作为排除条件保留",
      "非 SIMT/VF 载体（以 MTE 批量搬运为主、lane 不直接发起访存）的算子不适用"
    ],
    "required_conditions": [
      "kernel 为 VF SIMT 载体（每核 1024 VF 线程、asc_vf_call 载体），访存由 lane 直接发起",
      "champion 的 lane→data 映射使同一 warp 的各 lane 落在互不相邻的 128B line 上（该轮：lane l 处理 rowGlobal = startRow + l + k*1024）",
      "每条 y 输出 line 需要同一 warp 的多次 k 迭代逐步填满，形成部分行存储放大",
      "per-row 索引量可表达为增量状态，无需每行 div/mod",
      "op_summary 证实 aiv_vec_time ≈ Task Duration、MTE pipe 近 0、实测带宽远低于 HBM 峰值（transaction-efficiency 受限而非带宽饱和）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "embcat",
      "operator_class": "embedding-gather",
      "precision": "20/20 PASS (MERE=MARE=0.000e+00, bit-exact)",
      "rounds_or_pairs": "5 对 balanced-alternating ABBA（10 次 run 级测量，零对间分歧）",
      "run_id": "<run-id>",
      "speedup": 4.982,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-lsu",
      "scattered-line-transactions",
      "partial-line-write-amplification"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "warp-cooperative-contiguous-row-slice",
    "structure": [
      "simt-lane-remap",
      "warp-cooperative-row-chunk",
      "div-free-incremental-index-state",
      "warp-uniform-branch"
    ]
  },
  "generality": "op_class",
  "id": "EMBCAT-WARP-COOPERATIVE-ROW-SLICE",
  "implementation_steps": [
    "重写 even-E 臂的 VF SIMT 映射：warp w 认领该 core 行区间内的连续行段 [w*chunk, (w+1)*chunk)，chunk = ceil(coreRows/32)；每行 lane l 处理元素对 k = l, l+32, …，使每条 warp LD/ST 都成为行内连续的满线 128B 事务",
    "把 per-row 索引算术改为免除法增量状态并由全体 lane 一致执行：yOff += E; row++; 行回卷时 row=0 且 b++ 并 p += PT-rowsCount+1；b 回卷时 b=0、M++、p = M*rowsCount",
    "x[p] 保持全 lane 同址广播 load；w 行基址 = src*E 每行只算一次",
    "保留奇 E 回退臂与全部 host/tiling 代码逐字节不变（位级数据流保持不变）",
    "处理设备编译：__simt_vf__ 内联 ceil-div 算术，避免调用普通 __aicore__ helper"
  ],
  "intent": "消除 VF SIMT lane→data 映射造成的低效访存事务：champion 一个 lane 独占一整条输出行，使每个 warp 的 LD/ST 跨 32 条 128B line 散射、每条 y line 由 32 次连续 k 迭代逐步填出，实测写带宽仅 82-163 GB/s（fp16/bf16 u32 打包路径）与 92-139 GB/s（fp32 u64 打包路径），读+写合计约 330 GB/s，远低于 ascend950 HBM 峰值。",
  "mechanism": "在 EmbCatGatherRows 的 even-E 臂内做纯 lane→data 重映射：warp w 认领 core 行区间内的连续行段 [w*chunk, (w+1)*chunk)，chunk = ceil(coreRows/32)，每行 lane l 取元素对 l, l+32, …，于是每条 warp 访存指令都是行内连续的满线事务。配套改造是让 per-row 索引算术保持 warp-uniform 且免除法：用增量式 yOff/row/b/p/M 状态替代每行 2 次 div/mod（yOff += E; row++; 行回卷时 b++ 且 p += PT-rowsCount+1；b 回卷时 M++ 且 p = M*rowsCount），全体 lane 一致执行、无分歧。x[p] 为全 lane 同址广播 load，w 行基址 = src*E 每行算一次；奇 E 回退臂与全部 host/tiling 代码逐字节不动。",
  "name": "warp 协作连续行切片：SIMT lane 重映射消除散射访存",
  "operator_class": "embedding-gather",
  "operator_scope": "带 device 侧行映射（gather）的 SIMT VF 类算子：输出每行由一条（或少量）输入行构成、行内元素可连续向量化，且行映射依赖输入数据值因而无法由 host 解析（典型为 embedding bag / 特征拼接类算子，如 embcat）；输入/输出 dtype 为 fp16/bf16/fp32",
  "principle": "VF SIMT kernel 的访存效率由「单条 warp LD/ST 覆盖多少条 128B line」决定，而非总字节数。lane l 处理 rowGlobal = startRow + l + k*1024 时，同一 warp 的 32 个 lane 落在 32 条不同行，每次 LD 只用掉每条 line 的一个 4B sector；y store 虽然 32 个 lane 落在连续的 32 条 line 上，但每条 line 每次只被写 4B，需要同一 warp 连续 32 次 k 迭代才填满——即部分行写放大、L2 写放大与 LSU 串行化。改成「一个 warp 认领一段连续行、lane l 取元素对 l, l+32, …」后，每条 warp 访存指令都落在行内连续的 128B 线上，成为满线事务，同一字节量所需的事务数下降一到两个数量级。",
  "related_anti_patterns": [],
  "risks": [
    "per-row 索引算术若朴素写成每行 2 次 div/mod，标量发射将膨胀 32 倍（champion 标量仅 ~5us），可能吞掉全部收益——必须用 leader+broadcast 或免除法增量状态",
    "E=32 时每行只有 16 个元素对，lane 利用率仅一半，收益上限受限；奇 E 走 legacy 臂不享受本机制",
    "同一 binary 的 u32 打包路径（fp16/bf16）在 pair_5 中出现过整体约 5x 劣化（降至 13-39 GB/s），而同 binary 的 u64 路径（fp32）保持正常 83-139 GB/s；散射事务病态与 DVFS/干扰均未排除，本机制是否稳定该方差未被单独证明",
    "增益归因依赖未触碰域（奇 E 回退臂、host/tiling 代码）保持位级等价",
    "编译期约束：__simt_vf__ 无法调用普通 __aicore__ 设备函数（该轮 3 次编译修复额度中用了 1 次）"
  ],
  "slug": "warp-cooperative-contiguous-row-slice",
  "summary": "把 EmbCatGatherRows 的 VF SIMT lane→data 映射从「一个 lane 独占一整条输出行」改为「一个 warp 认领一段连续行」：lane l 取元素对 l, l+32, …，使每条 warp LD/ST 都是行内连续的满线 128B 事务，消除 y 的部分行写放大与 w 的散射 sector 读；配套用免除法增量索引状态（yOff/row/b/p/M）保住 per-row 索引算术的 warp-uniform。dtype-group geomean 119.459→23.980us（4.982x；bf16 4.255x / fp16 5.042x / fp32 5.759x），全部 20 shape 改善，最大 case5 9.88x，精度 20/20 位级精确。",
  "verification": {
    "correctness": [
      "20/20 精度通过，全部 case MERE=MARE=0.000e+00（位级精确）",
      "免除法增量索引状态在 (B=2, PT=6, rowsCount=3) 上穷举验证",
      "奇 E 回退臂与 host/tiling 代码未改动，数据流位级保留"
    ],
    "performance": [
      "5 对 balanced-alternating ABBA 配对（10 次 run 级测量，零对间分歧，全部 20 shape 改善）",
      "dtype-group geomean 119.459→23.980us（speedup 4.982；bf16 4.255x / fp16 5.042x / fp32 5.759x，最大 case5 9.88x）",
      "champion 画像证实瓶颈在事务形态而非 MTE/标量：aiv_vec_time ≈ Task Duration（119.563 vs 119.469us geomean，vec_ratio ~1.0），aiv_scalar ~5us，各 MTE pipe 近 0"
    ],
    "rollback_signals": [
      "配对 ABBA（≥2 对，外层 msprof device Task Duration、两级 case-mean/geomean 聚合）显示 geomean 增益 < 1.0x 或任一 dtype case mean < 0.95x → 回退 champion 并记 rejected_performance",
      "per-row 索引算术膨胀标量 pipe 抵消收益（预测风险，该轮未兑现）",
      "若 VF SIMT 已被 LSU 内部合并 lane 访存，增益塌缩为噪声",
      "u32 打包路径的病态劣化在合并化后仍复现"
    ]
  }
}
-->

# 性能优化策略：warp 协作连续行切片：SIMT lane 重映射消除散射访存

把 EmbCatGatherRows 的 VF SIMT lane→data 映射从「一个 lane 独占一整条输出行」改为「一个 warp 认领一段连续行」：lane l 取元素对 l, l+32, …，使每条 warp LD/ST 都是行内连续的满线 128B 事务，消除 y 的部分行写放大与 w 的散射 sector 读；配套用免除法增量索引状态（yOff/row/b/p/M）保住 per-row 索引算术的 warp-uniform。dtype-group geomean 119.459→23.980us（4.982x；bf16 4.255x / fp16 5.042x / fp32 5.759x），全部 20 shape 改善，最大 case5 9.88x，精度 20/20 位级精确。

## 1. 原理

VF SIMT kernel 的访存效率由「单条 warp LD/ST 覆盖多少条 128B line」决定，而非总字节数。lane l 处理 rowGlobal = startRow + l + k*1024 时，同一 warp 的 32 个 lane 落在 32 条不同行，每次 LD 只用掉每条 line 的一个 4B sector；y store 虽然 32 个 lane 落在连续的 32 条 line 上，但每条 line 每次只被写 4B，需要同一 warp 连续 32 次 k 迭代才填满——即部分行写放大、L2 写放大与 LSU 串行化。改成「一个 warp 认领一段连续行、lane l 取元素对 l, l+32, …」后，每条 warp 访存指令都落在行内连续的 128B 线上，成为满线事务，同一字节量所需的事务数下降一到两个数量级。

实现机制：在 EmbCatGatherRows 的 even-E 臂内做纯 lane→data 重映射：warp w 认领 core 行区间内的连续行段 [w*chunk, (w+1)*chunk)，chunk = ceil(coreRows/32)，每行 lane l 取元素对 l, l+32, …，于是每条 warp 访存指令都是行内连续的满线事务。配套改造是让 per-row 索引算术保持 warp-uniform 且免除法：用增量式 yOff/row/b/p/M 状态替代每行 2 次 div/mod（yOff += E; row++; 行回卷时 b++ 且 p += PT-rowsCount+1；b 回卷时 M++ 且 p = M*rowsCount），全体 lane 一致执行、无分歧。x[p] 为全 lane 同址广播 load，w 行基址 = src*E 每行算一次；奇 E 回退臂与全部 host/tiling 代码逐字节不动。

## 2. 性能问题模式

- 优化目标：消除 VF SIMT lane→data 映射造成的低效访存事务：champion 一个 lane 独占一整条输出行，使每个 warp 的 LD/ST 跨 32 条 128B line 散射、每条 y line 由 32 次连续 k 迭代逐步填出，实测写带宽仅 82-163 GB/s（fp16/bf16 u32 打包路径）与 92-139 GB/s（fp32 u64 打包路径），读+写合计约 330 GB/s，远低于 ascend950 HBM 峰值。
- 适用数据流：带 device 侧行映射（gather）的 SIMT VF 类算子：输出每行由一条（或少量）输入行构成、行内元素可连续向量化，且行映射依赖输入数据值因而无法由 host 解析（典型为 embedding bag / 特征拼接类算子，如 embcat）；输入/输出 dtype 为 fp16/bf16/fp32
- Feature signature：`{"bottleneck": ["vec-lsu", "scattered-line-transactions", "partial-line-write-amplification"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "warp-cooperative-contiguous-row-slice", "structure": ["simt-lane-remap", "warp-cooperative-row-chunk", "div-free-incremental-index-state", "warp-uniform-branch"]}`

## 3. 正确性红线

- per-row 索引算术若朴素写成每行 2 次 div/mod，标量发射将膨胀 32 倍（champion 标量仅 ~5us），可能吞掉全部收益——必须用 leader+broadcast 或免除法增量状态
- E=32 时每行只有 16 个元素对，lane 利用率仅一半，收益上限受限；奇 E 走 legacy 臂不享受本机制
- 同一 binary 的 u32 打包路径（fp16/bf16）在 pair_5 中出现过整体约 5x 劣化（降至 13-39 GB/s），而同 binary 的 u64 路径（fp32）保持正常 83-139 GB/s；散射事务病态与 DVFS/干扰均未排除，本机制是否稳定该方差未被单独证明
- 增益归因依赖未触碰域（奇 E 回退臂、host/tiling 代码）保持位级等价
- 编译期约束：__simt_vf__ 无法调用普通 __aicore__ 设备函数（该轮 3 次编译修复额度中用了 1 次）

资源与硬件约束：

- per-row 索引算术必须保持 warp-uniform 且免除法：若朴素地每行做 2 次 div/mod，标量发射将由 ~5us 膨胀 32 倍并成为新的瓶颈——必须用 leader 计算 + broadcast，或（本轮采用）免除法增量状态
- 行区间划分 chunk = ceil(coreRows/32) 必须覆盖且不重叠，残余行并入尾部处理；不得改动奇 E 回退臂与 host/tiling 代码，位级数据流保持不变
- 行边界推进（row/b/M 回卷）必须由全体 lane 一致执行（warp-uniform 分支），不得引入 lane 分歧
- 设备编译约束：__simt_vf__ 上下文不能调用普通 __aicore__ helper（该轮 EmbCatCeilDiv 报 no matching function），ceil-div 算术需内联

## 4. 泛化条件

- 策略作用域：op_class：embedding-gather

适用：

- kernel 为 VF SIMT 载体（每核 1024 VF 线程、asc_vf_call 载体），访存由 lane 直接发起
- champion 的 lane→data 映射使同一 warp 的各 lane 落在互不相邻的 128B line 上（该轮：lane l 处理 rowGlobal = startRow + l + k*1024）
- 每条 y 输出 line 需要同一 warp 的多次 k 迭代逐步填满，形成部分行存储放大
- per-row 索引量可表达为增量状态，无需每行 div/mod
- op_summary 证实 aiv_vec_time ≈ Task Duration、MTE pipe 近 0、实测带宽远低于 HBM 峰值（transaction-efficiency 受限而非带宽饱和）

不适用：

- 行映射可由 host 解析（stride 字段可表达、每行源范围在结构校验内）时不适用本机制：直接走既有 per-row copy + 对齐 slot 的 host 可解析 gather 免路径
- E=32 时每行只有 16 个元素对，lane 利用率仅一半，收益上限受限；奇 E 走 legacy 臂，不被本机制覆盖
- 若硬件 LSU 已对 lane 访存做内部合并（MSB merging），本机制增益将塌缩为噪声；该轮未出现，但作为排除条件保留
- 非 SIMT/VF 载体（以 MTE 批量搬运为主、lane 不直接发起访存）的算子不适用

## 5. 实施步骤

1. 重写 even-E 臂的 VF SIMT 映射：warp w 认领该 core 行区间内的连续行段 [w*chunk, (w+1)*chunk)，chunk = ceil(coreRows/32)；每行 lane l 处理元素对 k = l, l+32, …，使每条 warp LD/ST 都成为行内连续的满线 128B 事务
2. 把 per-row 索引算术改为免除法增量状态并由全体 lane 一致执行：yOff += E; row++; 行回卷时 row=0 且 b++ 并 p += PT-rowsCount+1；b 回卷时 b=0、M++、p = M*rowsCount
3. x[p] 保持全 lane 同址广播 load；w 行基址 = src*E 每行只算一次
4. 保留奇 E 回退臂与全部 host/tiling 代码逐字节不变（位级数据流保持不变）
5. 处理设备编译：__simt_vf__ 内联 ceil-div 算术，避免调用普通 __aicore__ helper

## 6. LLM 前置问题

- 目标实现是否满足：kernel 为 VF SIMT 载体（每核 1024 VF 线程、asc_vf_call 载体），访存由 lane 直接发起？
- 目标实现是否满足：champion 的 lane→data 映射使同一 warp 的各 lane 落在互不相邻的 128B line 上（该轮：lane l 处理 rowGlobal = startRow + l + k*1024）？
- 目标实现是否满足：每条 y 输出 line 需要同一 warp 的多次 k 迭代逐步填满，形成部分行存储放大？
- 目标实现是否满足：per-row 索引量可表达为增量状态，无需每行 div/mod？
- 目标实现是否满足：op_summary 证实 aiv_vec_time ≈ Task Duration、MTE pipe 近 0、实测带宽远低于 HBM 峰值（transaction-efficiency 受限而非带宽饱和）？
- 是否命中排除条件：行映射可由 host 解析（stride 字段可表达、每行源范围在结构校验内）时不适用本机制？
- 是否命中排除条件：E=32 时每行只有 16 个元素对，lane 利用率仅一半，收益上限受限；奇 E 走 legacy 臂？
- 是否命中排除条件：若硬件 LSU 已对 lane 访存做内部合并（MSB merging），本机制增益将塌缩为噪声？
- 是否命中排除条件：非 SIMT/VF 载体（以 MTE 批量搬运为主、lane 不直接发起访存）的算子不适用？

## 7. 验收标准

正确性：

- 20/20 精度通过，全部 case MERE=MARE=0.000e+00（位级精确）
- 免除法增量索引状态在 (B=2, PT=6, rowsCount=3) 上穷举验证
- 奇 E 回退臂与 host/tiling 代码未改动，数据流位级保留

性能：

- 5 对 balanced-alternating ABBA 配对（10 次 run 级测量，零对间分歧，全部 20 shape 改善）
- dtype-group geomean 119.459→23.980us（speedup 4.982；bf16 4.255x / fp16 5.042x / fp32 5.759x，最大 case5 9.88x）
- champion 画像证实瓶颈在事务形态而非 MTE/标量：aiv_vec_time ≈ Task Duration（119.563 vs 119.469us geomean，vec_ratio ~1.0），aiv_scalar ~5us，各 MTE pipe 近 0

回滚信号：

- 配对 ABBA（≥2 对，外层 msprof device Task Duration、两级 case-mean/geomean 聚合）显示 geomean 增益 < 1.0x 或任一 dtype case mean < 0.95x → 回退 champion 并记 rejected_performance
- per-row 索引算术膨胀标量 pipe 抵消收益（预测风险，该轮未兑现）
- 若 VF SIMT 已被 LSU 内部合并 lane 访存，增益塌缩为噪声
- u32 打包路径的病态劣化在合并化后仍复现

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260913_154221（eid=free_explore_001, round=1, status=accepted, speedup=4.982, precision=20/20 PASS bit-exact）

## 检索卡（短卡）

动作：把 lane→data 映射由「一 lane 独占一行」改为「一 warp 认领连续行段」，lane l 取元素对 l,l+32,…，以免除法增量状态保 warp-uniform。
适用：kernel 为 VF SIMT 载体（每核 1024 线程）；同 warp lane 落在互不相邻的 128B line。
限制：per-row 索引每行 2 次 div/mod 使标量膨胀 32 倍；chunk 须覆盖不重叠；__simt_vf__ 内须内联 ceil-div。
范围：device 侧行映射的 SIMT VF gather
检索词：lane 重映射、warp 协作行段、128B line 满线事务、免除法增量状态、warp-uniform、asc_vf_call
机会：每 lane 独占一行使 LD/ST 跨 32 条 line 散射，带宽远低于峰值
代价：u32 打包路径（fp16/bf16）曾现约 5x 劣化
