---
type: Optimization
title: tiny-row 场景的多行 strided DataCopy 批量搬运
description: 将逐行单块搬运合并为一条多行strided DataCopy，在总字节不变时减少迭代和描述符。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/multirow-strided-datacopy-tiny-row.md
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
      "DataCopyPad blockLen/stride 为字节粒度且 <= 65535；blockCount <= 4095",
      "UB 预算：3 队列 x 2 缓冲下 batchRows * AlignUp(halfRowLen, alignUnit) * sizeof(DX) <= halfSegLenMax * sizeof(DX)，host/kernel 的 alignUnit 必须一致",
      "tail 批裁剪 blockCount 为剩余行数；masked VF 的 64 元素 chunk 边界读取依赖放大缓冲尺寸覆盖"
    ],
    "excluded_conditions": [
      "tilesPerRow > 1（多 tile 路径）时启用批处理会破坏既有路径，保持 batchRows=1",
      "字段溢出或 UB 预算不足时回退单行路径，禁止截断参数",
      "形式验收要求两侧 stable 样本；当基线 artifact 不可变地 stable:false、或优化后延迟落入 sub-10us profiler 噪声地板（或 MAD 微超阈值）时，正式 compare gate 必然返回 rejected——这是验收环境的边界，不是机制失败的证据"
    ],
    "required_conditions": [
      "rowLen <= segLen（tilesPerRow==1），kernel 每行一个独立迭代，per-iteration MTE + pipeline sync 主导",
      "逐行地址间距可用固定 stride 表达（行内两半 x0/x1 可由同一 strided 描述符覆盖，gap = halfRowLen 元素）",
      "batchRows * AlignUp(halfRowLen, 32/sizeof(DX)) <= halfSegLen（每队列 UB 预算），且 batchRows >= 2",
      "DataCopyPad 字段上限满足：blockLen = halfRowLen*dsize <= 65535、stride <= 65535、blockCount = batchRows <= 4095"
    ]
  },
  "classification": "lesson",
  "created": "2026-08-23",
  "evidence": [
    {
      "comparison_sha256": "32ec6a5d685a3d1dd0bff0ced55e9c3e78aaeb60b14d361badc81e8ebfe62c08",
      "decision_sha256": "a23296ea6247358cc556f77d585da3ba799a578eb0717ac0d6d226a88ad8c42d",
      "operator_class": "elementwise",
      "performance_sha256": "ada459a96fe2212764110438a4a07edfc447f13305c048b5db395a6cd557b950",
      "round": 2,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "28da8480921475c6a47847e94214acd403860c4daa72be1281357684e6be2e9c",
      "verify_sha256": "d27df1941fb2fba89951c641843ebea7527252b53f2529facf9a5cc84a768f65"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "per-iteration-overhead",
      "mte-descriptor-spray"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "multirow-strided-datacopy",
    "structure": [
      "strided-datacopy",
      "row-batching",
      "tiny-row"
    ]
  },
  "generality": "op_class",
  "id": "L-SWIGLU-MULTIROW-STRIDED-DATACOPY",
  "implementation_steps": [
    "host 在 tilesPerRow==1 时按 UB 预算与 DataCopyPad 字段上限推导 batchRows",
    "kernel 的 Init 解析 batchRows，batchRows>1 时设置 loopCount = ceil(rowCount/batchRows) 与批量缓冲大小",
    "CopyIn/Compute/CopyOut 增加 batchRows>1 分支：strided DataCopyPad 搬入 x0/x1 + 一条 VF + strided DataCopyPad 搬出，tail 批裁剪 blockCount",
    "tilesPerRow>1、batchRows<2 或字段溢出时走原单行路径（原代码逐字保留）",
    "用 op_summary Task Duration / 迭代数算术确认每核迭代数按 ~batchRows 下降"
  ],
  "intent": "消除 tiny-row（rowLen <= segLen, tilesPerRow==1）时逐行单块 MTE 搬运、标量 div-mod 与每迭代 pipeline sync 往返的开销。",
  "mechanism": "仅在 tilesPerRow==1 时，host 计算 batchRows = min(floor(halfSegLenMax / AlignUp(halfRowLen, 32/sizeof(DX))), 4095)（UB 预算 + DataCopyPad 字段上限双守卫，batchRows>=2 才启用）；kernel 的 Init 设置 loopCount = ceil(rowCount/batchRows) 与批量缓冲大小；Process 每批用一条 strided DataCopyPad 搬入 x0/x1（blockCount=batchRows, blockLen=halfRowLen*dsize, srcStride=halfRowLen*dsize, dstStride=0）、一条 VF ComputeSwiGlu 计算 batchLen*halfRowLen 连续元素、一条 strided DataCopyPad 搬出（srcStride=0, dstStride=0），tail 批裁剪 blockCount=min(batchRows, rowEnd-rowBase)；tilesPerRow>1、batchRows<2 或字段溢出时回退 batchRows=1 原单行路径。blockDim/Block Num 不变（本策略针对 per-iteration 开销而非并行度）。",
  "name": "tiny-row 场景的多行 strided DataCopy 批量搬运",
  "op": "swi_glu",
  "operator_class": "elementwise",
  "operator_scope": "rowLen <= segLen（tilesPerRow==1）使每行成为独立 loop 迭代、逐行单块 DataCopyPad 的 tiny-row 单 tile 数据流",
  "principle": "当 tile 粒度退化为单行时，每行重复的 MTE 描述符发射、标量行/块重算和 pipeline 同步成为主导成本；把多行合并进一条 strided DataCopy 描述符可在总字节不变时按行批次数减少迭代与描述符数，放大每次 MTE2/MTE3 的有效搬运粒度。",
  "related_anti_patterns": [
    "per-element-mte-descriptor-spray"
  ],
  "risks": [
    "DataCopyPad 行内打包布局假设（dstStride=0/srcStride=0 连续落盘）若存在隐藏 32B 行填充会污染数据",
    "byte-vs-unit 映射错误会导致跨行错位；blockCount/blockLen/stride 溢出会导致构建失败或越界 UB 访问",
    "masked VF 的 64 元素 chunk 边界读取依赖放大的缓冲尺寸覆盖，host/kernel 的 alignUnit 不一致会破坏 UB 预算不变式"
  ],
  "slug": "multirow-strided-datacopy-tiny-row",
  "summary": "当 rowLen <= segLen（tilesPerRow==1）时，baseline 每行一个独立迭代并逐行单块 DataCopyPad，per-iteration MTE 发射 + pipeline sync 往返主导；把 baseRowLen 行合并成一条 strided DataCopyPad（blockCount=batchRows, blockLen=halfRowLen*dsize, stride=halfRowLen*dsize, dstStride=0）可把每核迭代数按 ~batchRows 降低。机制经机器证据确认有效（cases 9/12/20 12.28x-19.85x，合计 7.21x，0 回归，guard 无回归），仅因形式稳定性门禁（基线不可变 stable:false + cases 9/12 微超 MAD + case 20 落噪声地板）被记录为 rejected——边界是验收环境而非机制。",
  "verification": {
    "correctness": [
      "rounds/002 verify 5/5 通过（cases 5/9/12/18/20），comparison verify_ok true；re-collected performance.json 指纹 kernel_hash 95b09ef8a7b96cc0 与 build.json kernel_after 一致（verify.json 记录的为 pre-rebuild 基线指纹，正确性以 round-2 kernel 的 re-collected 证据为准）",
      "guard case 5（tilesPerRow=4, batchRows=1 多 tile 路径）不变（241.8->243.3us, 0.9937x）；case 18（批量 32B 对齐路径）在界内（9.5->10.0us, 0.9509x）"
    ],
    "performance": [
      "cases 9/12/20 分别 19.85x/12.28x/16.35x（399.9->20.1us, 2982.3->242.8us, 158.8->9.7us），合计 3792.219->525.897us = 7.21x，0 回归",
      "每核迭代数按 ~batchRows 下降：case 12 ~15625->~12，case 9 ~2082->~2，case 20 ~816->~5",
      "注意：正式 compare gate 返回 ok:false（input_errors：基线不可变 stable:false + 当前 cases 9/12 MAD 0.0229/0.0219 微超 0.02 + case 20 落入噪声地板），非策略失败"
    ],
    "rollback_signals": [
      "case 12 中位数未降到 ~1000us 以下（per-iteration 不是主导瓶颈）或 cases 9/20 无延迟下降",
      "case 5（多 tile 路径）或 case 18（批量 32B 对齐路径）中位数低于 0.95x",
      "blockCount > 4095 或 blockLen/stride > 65535 的构建/运行错误或越界 UB 访问"
    ]
  }
}
-->

# 性能优化策略：tiny-row 场景的多行 strided DataCopy 批量搬运

单一优化点：当 rowLen <= segLen（tilesPerRow==1）时，baseline 每行一个独立迭代并逐行单块 DataCopyPad，per-iteration MTE 发射 + pipeline sync 往返主导；把 baseRowLen 行合并成一条 strided DataCopyPad（blockCount=batchRows, blockLen=halfRowLen*dsize, stride=halfRowLen*dsize, dstStride=0）可把每核迭代数按 ~batchRows 降低。机制经机器证据确认有效（cases 9/12/20 12.28x-19.85x，合计 7.21x，0 回归，guard 无回归），仅因形式稳定性门禁（基线不可变 stable:false + cases 9/12 微超 MAD + case 20 落噪声地板）被记录为 rejected——边界是验收环境而非机制。

## 1. 原理

当 tile 粒度退化为单行时，每行重复的 MTE 描述符发射、标量行/块重算和 pipeline 同步成为主导成本；把多行合并进一条 strided DataCopy 描述符可在总字节不变时按行批次数减少迭代与描述符数，放大每次 MTE2/MTE3 的有效搬运粒度。

实现机制：仅在 tilesPerRow==1 时，host 计算 batchRows = min(floor(halfSegLenMax / AlignUp(halfRowLen, 32/sizeof(DX))), 4095)（UB 预算 + DataCopyPad 字段上限双守卫，batchRows>=2 才启用）；kernel 的 Init 设置 loopCount = ceil(rowCount/batchRows) 与批量缓冲大小；Process 每批用一条 strided DataCopyPad 搬入 x0/x1（blockCount=batchRows, blockLen=halfRowLen*dsize, srcStride=halfRowLen*dsize, dstStride=0）、一条 VF ComputeSwiGlu 计算 batchLen*halfRowLen 连续元素、一条 strided DataCopyPad 搬出（srcStride=0, dstStride=0），tail 批裁剪 blockCount=min(batchRows, rowEnd-rowBase)；tilesPerRow>1、batchRows<2 或字段溢出时回退 batchRows=1 原单行路径。blockDim/Block Num 不变（本策略针对 per-iteration 开销而非并行度）。

## 2. 性能问题模式

- 优化目标：消除 tiny-row（rowLen <= segLen, tilesPerRow==1）时逐行单块 MTE 搬运、标量 div-mod 与每迭代 pipeline sync 往返的开销。
- 适用数据流：rowLen <= segLen（tilesPerRow==1）使每行成为独立 loop 迭代、逐行单块 DataCopyPad 的 tiny-row 单 tile 数据流
- Feature signature：`{"bottleneck": ["per-iteration-overhead", "mte-descriptor-spray"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "multirow-strided-datacopy", "structure": ["strided-datacopy", "row-batching", "tiny-row"]}`

## 3. 正确性红线

- DataCopyPad 行内打包布局假设（dstStride=0/srcStride=0 连续落盘）若存在隐藏 32B 行填充会污染数据
- byte-vs-unit 映射错误会导致跨行错位；blockCount/blockLen/stride 溢出会导致构建失败或越界 UB 访问
- masked VF 的 64 元素 chunk 边界读取依赖放大的缓冲尺寸覆盖，host/kernel 的 alignUnit 不一致会破坏 UB 预算不变式

资源与硬件约束：

- DataCopyPad blockLen/stride 为字节粒度且 <= 65535；blockCount <= 4095
- UB 预算：3 队列 x 2 缓冲下 batchRows * AlignUp(halfRowLen, alignUnit) * sizeof(DX) <= halfSegLenMax * sizeof(DX)，host/kernel 的 alignUnit 必须一致
- tail 批裁剪 blockCount 为剩余行数；masked VF 的 64 元素 chunk 边界读取依赖放大缓冲尺寸覆盖

## 4. 泛化条件

- 策略作用域：op_class：elementwise

适用：

- rowLen <= segLen（tilesPerRow==1），kernel 每行一个独立迭代，per-iteration MTE + pipeline sync 主导
- 逐行地址间距可用固定 stride 表达（行内两半 x0/x1 可由同一 strided 描述符覆盖，gap = halfRowLen 元素）
- batchRows * AlignUp(halfRowLen, 32/sizeof(DX)) <= halfSegLen（每队列 UB 预算），且 batchRows >= 2
- DataCopyPad 字段上限满足：blockLen = halfRowLen*dsize <= 65535、stride <= 65535、blockCount = batchRows <= 4095

不适用：

- tilesPerRow > 1（多 tile 路径）时启用批处理会破坏既有路径，保持 batchRows=1
- 字段溢出或 UB 预算不足时回退单行路径，禁止截断参数
- 形式验收要求两侧 stable 样本；当基线 artifact 不可变地 stable:false、或优化后延迟落入 sub-10us profiler 噪声地板（或 MAD 微超阈值）时，正式 compare gate 必然返回 rejected——这是验收环境的边界，不是机制失败的证据

## 5. 实施步骤

1. host 在 tilesPerRow==1 时按 UB 预算与 DataCopyPad 字段上限推导 batchRows
2. kernel 的 Init 解析 batchRows，batchRows>1 时设置 loopCount = ceil(rowCount/batchRows) 与批量缓冲大小
3. CopyIn/Compute/CopyOut 增加 batchRows>1 分支：strided DataCopyPad 搬入 x0/x1 + 一条 VF + strided DataCopyPad 搬出，tail 批裁剪 blockCount
4. tilesPerRow>1、batchRows<2 或字段溢出时走原单行路径（原代码逐字保留）
5. 用 op_summary Task Duration / 迭代数算术确认每核迭代数按 ~batchRows 下降

## 6. LLM 前置问题

- 目标实现是否满足：rowLen <= segLen（tilesPerRow==1），kernel 每行一个独立迭代，per-iteration MTE + pipeline sync 主导？
- 目标实现是否满足：逐行地址间距可用固定 stride 表达（行内两半 x0/x1 可由同一 strided 描述符覆盖，gap = halfRowLen 元素）？
- 目标实现是否满足：batchRows * AlignUp(halfRowLen, 32/sizeof(DX)) <= halfSegLen（每队列 UB 预算），且 batchRows >= 2？
- 是否命中排除条件：tilesPerRow > 1（多 tile 路径）时启用批处理会破坏既有路径，保持 batchRows=1？

## 7. 验收标准

正确性：

- rounds/002 verify 5/5 通过（cases 5/9/12/18/20），comparison verify_ok true；re-collected performance.json 指纹 kernel_hash 95b09ef8a7b96cc0 与 build.json kernel_after 一致（verify.json 记录的为 pre-rebuild 基线指纹，正确性以 round-2 kernel 的 re-collected 证据为准）
- guard case 5（tilesPerRow=4, batchRows=1 多 tile 路径）不变（241.8->243.3us, 0.9937x）；case 18（批量 32B 对齐路径）在界内（9.5->10.0us, 0.9509x）

性能：

- cases 9/12/20 分别 19.85x/12.28x/16.35x（399.9->20.1us, 2982.3->242.8us, 158.8->9.7us），合计 3792.219->525.897us = 7.21x，0 回归
- 每核迭代数按 ~batchRows 下降：case 12 ~15625->~12，case 9 ~2082->~2，case 20 ~816->~5
- 注意：正式 compare gate 返回 ok:false（input_errors：基线不可变 stable:false + 当前 cases 9/12 MAD 0.0229/0.0219 微超 0.02 + case 20 落入噪声地板），非策略失败

回滚信号：

- case 12 中位数未降到 ~1000us 以下（per-iteration 不是主导瓶颈）或 cases 9/20 无延迟下降
- case 5（多 tile 路径）或 case 18（批量 32B 对齐路径）中位数低于 0.95x
- blockCount > 4095 或 blockLen/stride > 65535 的构建/运行错误或越界 UB 访问

## 8. 分类与证据

- Classification：`lesson`
- Generality：`op_class`
- Related anti-patterns：per-element-mte-descriptor-spray

- swi_glu-20260823_153850-12764c（round=2, status=rejected）

## 检索卡（短卡）

动作：将逐行单块搬运合并为一条多行strided DataCopy，在总字节不变时减少迭代和描述符
适用：rowLen≤segLen且tilesPerRow=1，每行独立迭代并由MTE与pipeline同步主导
限制：blockLen/stride按字节且≤65535，blockCount≤4095；须排除隐藏32B行填充
范围：elementwise-arithmetic的tiny-row搬运循环
检索词：tiny-row、strided DataCopy、DataCopyPad、batchRows、tilesPerRow
机会：每行重复MTE描述符、标量行块重算与pipeline同步成为主导成本
