---
type: Optimization
title: 跳过被 cross-core split 覆盖时冗余执行的 whole-tensor 归约路径
description: 当 cross-core split 完整覆盖且最终写回同一输出时，跳过先执行后被覆盖的 whole-tensor 路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/skip-redundant-whole-tensor-split-path.md
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
      "守卫与 splitTensorId_==listLen_ sentinel 语义耦合：任何改变 sentinel 值或非参与者含义的后续编辑必须同步守卫",
      "依赖 host 保证的 split 完整性：建议在 host 加防御性断言（最后参与者切片非空、切片铺满张量）作为加固",
      "splitStartElem_ = blockIdx * sliceLen 需保持 32B 对齐（sliceLen 为 32B 对齐倍数）"
    ],
    "excluded_conditions": [
      "无 split launch（totalElems<=tileLen）：splitTensorId_==listLen_ sentinel，守卫不得命中，whole-tensor 路径是唯一路径",
      "未来 fused L>1 launch 的非 split 张量仍需 whole-tensor 路径（守卫只跳过 split 张量）",
      "split 切片覆盖不完整（如某参与者切片为空）时不得跳过 whole-tensor 路径"
    ],
    "required_conditions": [
      "host 保证 split 路径产生 split 张量的完整范数：splitEnabled=(listLen<coreNum && totalElems>listLen*tileLen) 为真、numPartials==blockDim、切片铺满整个张量且最后参与者切片非空",
      "split owner（sliceStart==0）是 post-SyncAll 对 y[splitTensorId] 的唯一写者，且其 CopyOutSplit 在改动前就已覆盖 whole-tensor 结果",
      "split 路径自持 accumulator（InitAcc）与独立 workspace slots/partialsBuf，对 whole-tensor 路径无数据依赖",
      "每块仍到达同一个无条件 AscendC::SyncAll()（守卫只跳过循环体，不跳过同步）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "e22a8fd8243ef0ff27db04b251dd0462688259c3a1d04891c78853ac78ba70f4",
      "decision_sha256": "6121a3b59db09d836d05d8698d85fd4253b0ecdca0c5f2bf21d06e3285368548",
      "operator_class": "reduction",
      "performance_sha256": "6ecf06134ae475b429f744e460f3726afdbf7c17d13649ac31ca916b93bd8e49",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "92b5e5480fe389209a39efb951c9c3dd19ec2ec1be74c26080d30e140d8dd82b",
      "verify_sha256": "5c850ee2e9ae998b706534166ed814cedf1f3464cdf745da8074fd05c6cfae4e"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "redundant-whole-tensor-rescan",
      "gm-read-amplification"
    ],
    "guard": [
      "split-completeness-host-guaranteed",
      "splitTensorId-sentinel"
    ],
    "pattern": "skip-redundant-whole-tensor-split-path",
    "structure": [
      "whole-tensor-plus-split-dual-path",
      "split-owner-final-writer",
      "listlen-1-plugin-launch"
    ]
  },
  "generality": "op_class",
  "id": "NORM-ELIMINATE-REDUNDANT-WHOLE-TENSOR-PASS",
  "implementation_steps": [
    "确认 host tiling 的 splitEnabled/splitTensorId 语义与 split 切片完整性（numPartials==blockDim、最后切片非空、切片铺满）",
    "在 Process 的 whole-tensor 循环体顶部加 if (t==splitTensorId_) { continue; } 并注释机制",
    "确认每块仍到达无条件 SyncAll，owner 的 post-SyncAll 写序与 workspace slot 索引不变",
    "重新跑 verify（5/5 目标 case）与 measure，确认 per-kernel 收敛到单遍 split 读带宽下限"
  ],
  "intent": "消除 split 张量的 whole-tensor 路径在每块上重复读取/计算整个张量（GM 读放大 blockDim 倍、anti-pattern A3）且结果被 split owner 覆盖丢弃的冗余工作",
  "mechanism": "在 ForeachNormKernel::Process 的 for(t=coreStartTensor_; t<coreEndTensor_; t++) 循环体顶部加 if (t==splitTensorId_) { continue; }。当前 host 保证每个 launch 都是 L=1（plugin 逐张量调用、tiling listLen=1）且 splitEnabled 恒真，核心 quota 使 coreStartTensor_==0/coreEndTensor_==1，因此守卫使 whole-tensor 循环整体为空，只跑 split 路径。无 split launch（totalElems<=tileLen）保持 splitTensorId_==listLen_ sentinel，守卫永不匹配（t<coreEndTensor_<=listLen_），whole-tensor 路径原样运行。守卫只跳过循环体、不跳过 SyncAll，owner 的 post-SyncAll 写序不变。",
  "name": "跳过被 cross-core split 覆盖时冗余执行的 whole-tensor 归约路径",
  "operator_class": "reduction",
  "operator_scope": "同时运行 whole-tensor 路径与 cross-core split 路径、且 split owner 在 SyncAll 后覆盖 y[splitTensorId] 的单张量归约 kernel（当前 plugin 结构 listLen=1、splitEnabled 对所有 totalElems>tileLen 的 launch 为真）",
  "principle": "若两条路径产生同一输出而最终写者确定是后者，则前者是可证明的死工作：跳过它不改变最终值或写序。正确性前提是 host 保证 split 切片完整覆盖张量（numPartials==blockDim、最后参与者切片非空、切片铺满整个张量）、split 路径自持 accumulator 与独立 workspace slots/partialsBuf、split owner（sliceStart==0）是 post-SyncAll 对 y[splitTensorId] 的唯一写者，且每块仍到达同一个无条件 SyncAll。",
  "related_anti_patterns": [
    "wrong-axis-per-core-rescan"
  ],
  "risks": [
    "守卫依赖 splitTensorId_ sentinel 语义：sentinel 值或含义被后续编辑改变而不同步会破坏正确性",
    "若未来 host tiling 开启不完整 split 覆盖（如空最后参与者切片），whole-tensor 路径不能再作为 fallback 写者——需 host 断言加固",
    "守卫跳过的只是循环体；任何未来把 SyncAll 或 owner merge 移入被跳过区域的编辑都会破坏可见性"
  ],
  "slug": "skip-redundant-whole-tensor-split-path",
  "summary": "当 host 保证 split 路径完整覆盖被切分张量且 split owner 是 y[splitTensorId] 的最终写者时，在 Process 的 whole-tensor 循环体顶部加 if (t==splitTensorId_) { continue; }，消除每块 32x 冗余的全张量 CopyIn/Compute/Write 与被丢弃结果（GM 读放大 blockDim 倍，即 anti-pattern A3）。per-kernel 时间收敛到单遍 split 读带宽下限；无 split launch 保持 splitTensorId_==listLen_ sentinel 使 whole-tensor 路径原样运行。实测 5/5 目标 case 提升 5.25-43.31x。",
  "verification": {
    "correctness": [
      "rounds/002 verify ok=true，5/5 目标 case（3,9,12,13,20）全部通过；kernel_hash 7cb1818193a15cf7 与 build.json kernel_after 一致",
      "final 全 20 case verify 通过（20/20，kernel_hash 7cb1818193a15cf7）；无 summation-order 或 tolerance 变化（split 结果本就是改动前的最终输出）"
    ],
    "performance": [
      "5/5 目标 case 实测 5.25-43.31x vs baseline：case 3 891.696->20.804us（42.86x）、case 9 2635.741->60.857us（43.31x）、case 12 35.49->6.763us（5.25x）、case 13 553.989->22.395us（24.74x）、case 20 597.103->23.224us（25.71x）",
      "selector 子集 total 35.1682x（4714.019->134.042us），5 improved / 0 regressed",
      "per-kernel 收敛到单遍 split 读带宽下限（case 3: 33.5MB 单遍读 20.8us ~= 1.6TB/s 聚合；此前为 32x 冗余 ~1GB 丢弃读）"
    ],
    "rollback_signals": [
      "任一目标 case 正确性失败（证伪 whole-path 结果被丢弃、split owner 是最终写者的论断）",
      "case 3/9 无 material per-launch 下降（证伪 32x 冗余 whole-tensor-path 假设）",
      "任一 case 回归超过 max_case_regression 0.95",
      "split owner/workspace slot/partials merge 路径回归（y 写零或两次、partialsBuf 溢出、IsSplitOwner/slot 索引被编辑破坏）"
    ]
  }
}
-->

# 性能优化策略：跳过被 cross-core split 覆盖时冗余执行的 whole-tensor 归约路径

单一优化点：当 host 保证 split 路径完整覆盖被切分张量且 split owner 是 y[splitTensorId] 的最终写者时，在 Process 的 whole-tensor 循环体顶部加 if (t==splitTensorId_) { continue; }，消除每块 32x 冗余的全张量 CopyIn/Compute/Write 与被丢弃结果（GM 读放大 blockDim 倍，即 anti-pattern A3）。per-kernel 时间收敛到单遍 split 读带宽下限；无 split launch 保持 splitTensorId_==listLen_ sentinel 使 whole-tensor 路径原样运行。实测 5/5 目标 case 提升 5.25-43.31x。

## 1. 原理

若两条路径产生同一输出而最终写者确定是后者，则前者是可证明的死工作：跳过它不改变最终值或写序。正确性前提是 host 保证 split 切片完整覆盖张量（numPartials==blockDim、最后参与者切片非空、切片铺满整个张量）、split 路径自持 accumulator 与独立 workspace slots/partialsBuf、split owner（sliceStart==0）是 post-SyncAll 对 y[splitTensorId] 的唯一写者，且每块仍到达同一个无条件 SyncAll。

实现机制：在 ForeachNormKernel::Process 的 for(t=coreStartTensor_; t<coreEndTensor_; t++) 循环体顶部加 if (t==splitTensorId_) { continue; }。当前 host 保证每个 launch 都是 L=1（plugin 逐张量调用、tiling listLen=1）且 splitEnabled 恒真，核心 quota 使 coreStartTensor_==0/coreEndTensor_==1，因此守卫使 whole-tensor 循环整体为空，只跑 split 路径。无 split launch（totalElems<=tileLen）保持 splitTensorId_==listLen_ sentinel，守卫永不匹配（t<coreEndTensor_<=listLen_），whole-tensor 路径原样运行。守卫只跳过循环体、不跳过 SyncAll，owner 的 post-SyncAll 写序不变。

## 2. 性能问题模式

- 优化目标：消除 split 张量的 whole-tensor 路径在每块上重复读取/计算整个张量（GM 读放大 blockDim 倍、anti-pattern A3）且结果被 split owner 覆盖丢弃的冗余工作
- 适用数据流：同时运行 whole-tensor 路径与 cross-core split 路径、且 split owner 在 SyncAll 后覆盖 y[splitTensorId] 的单张量归约 kernel（当前 plugin 结构 listLen=1、splitEnabled 对所有 totalElems>tileLen 的 launch 为真）
- Feature signature：`{"bottleneck": ["redundant-whole-tensor-rescan", "gm-read-amplification"], "guard": ["split-completeness-host-guaranteed", "splitTensorId-sentinel"], "pattern": "skip-redundant-whole-tensor-split-path", "structure": ["whole-tensor-plus-split-dual-path", "split-owner-final-writer", "listlen-1-plugin-launch"]}`

## 3. 正确性红线

- 守卫依赖 splitTensorId_ sentinel 语义：sentinel 值或含义被后续编辑改变而不同步会破坏正确性
- 若未来 host tiling 开启不完整 split 覆盖（如空最后参与者切片），whole-tensor 路径不能再作为 fallback 写者——需 host 断言加固
- 守卫跳过的只是循环体；任何未来把 SyncAll 或 owner merge 移入被跳过区域的编辑都会破坏可见性

资源与硬件约束：

- 守卫与 splitTensorId_==listLen_ sentinel 语义耦合：任何改变 sentinel 值或非参与者含义的后续编辑必须同步守卫
- 依赖 host 保证的 split 完整性：建议在 host 加防御性断言（最后参与者切片非空、切片铺满张量）作为加固
- splitStartElem_ = blockIdx * sliceLen 需保持 32B 对齐（sliceLen 为 32B 对齐倍数）

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- host 保证 split 路径产生 split 张量的完整范数：splitEnabled=(listLen<coreNum && totalElems>listLen*tileLen) 为真、numPartials==blockDim、切片铺满整个张量且最后参与者切片非空
- split owner（sliceStart==0）是 post-SyncAll 对 y[splitTensorId] 的唯一写者，且其 CopyOutSplit 在改动前就已覆盖 whole-tensor 结果
- split 路径自持 accumulator（InitAcc）与独立 workspace slots/partialsBuf，对 whole-tensor 路径无数据依赖
- 每块仍到达同一个无条件 AscendC::SyncAll()（守卫只跳过循环体，不跳过同步）

不适用：

- 无 split launch（totalElems<=tileLen）：splitTensorId_==listLen_ sentinel，守卫不得命中，whole-tensor 路径是唯一路径
- 未来 fused L>1 launch 的非 split 张量仍需 whole-tensor 路径（守卫只跳过 split 张量）
- split 切片覆盖不完整（如某参与者切片为空）时不得跳过 whole-tensor 路径

## 5. 实施步骤

1. 确认 host tiling 的 splitEnabled/splitTensorId 语义与 split 切片完整性（numPartials==blockDim、最后切片非空、切片铺满）
2. 在 Process 的 whole-tensor 循环体顶部加 if (t==splitTensorId_) { continue; } 并注释机制
3. 确认每块仍到达无条件 SyncAll，owner 的 post-SyncAll 写序与 workspace slot 索引不变
4. 重新跑 verify（5/5 目标 case）与 measure，确认 per-kernel 收敛到单遍 split 读带宽下限

## 6. LLM 前置问题

- 目标实现是否满足：host 保证 split 路径产生 split 张量的完整范数：splitEnabled=(listLen<coreNum && totalElems>listLen*tileLen) 为真、numPartials==blockDim、切片铺满整个张量且最后参与者切片非空？
- 目标实现是否满足：split owner（sliceStart==0）是 post-SyncAll 对 y[splitTensorId] 的唯一写者，且其 CopyOutSplit 在改动前就已覆盖 whole-tensor 结果？
- 目标实现是否满足：split 路径自持 accumulator（InitAcc）与独立 workspace slots/partialsBuf，对 whole-tensor 路径无数据依赖？
- 是否命中排除条件：无 split launch（totalElems<=tileLen）：splitTensorId_==listLen_ sentinel，守卫不得命中，whole-tensor 路径是唯一路径？

## 7. 验收标准

正确性：

- rounds/002 verify ok=true，5/5 目标 case（3,9,12,13,20）全部通过；kernel_hash 7cb1818193a15cf7 与 build.json kernel_after 一致
- final 全 20 case verify 通过（20/20，kernel_hash 7cb1818193a15cf7）；无 summation-order 或 tolerance 变化（split 结果本就是改动前的最终输出）

性能：

- 5/5 目标 case 实测 5.25-43.31x vs baseline：case 3 891.696->20.804us（42.86x）、case 9 2635.741->60.857us（43.31x）、case 12 35.49->6.763us（5.25x）、case 13 553.989->22.395us（24.74x）、case 20 597.103->23.224us（25.71x）
- selector 子集 total 35.1682x（4714.019->134.042us），5 improved / 0 regressed
- per-kernel 收敛到单遍 split 读带宽下限（case 3: 33.5MB 单遍读 20.8us ~= 1.6TB/s 聚合；此前为 32x 冗余 ~1GB 丢弃读）

回滚信号：

- 任一目标 case 正确性失败（证伪 whole-path 结果被丢弃、split owner 是最终写者的论断）
- case 3/9 无 material per-launch 下降（证伪 32x 冗余 whole-tensor-path 假设）
- 任一 case 回归超过 max_case_regression 0.95
- split owner/workspace slot/partials merge 路径回归（y 写零或两次、partialsBuf 溢出、IsSplitOwner/slot 索引被编辑破坏）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：wrong-axis-per-core-rescan

- foreach_norm-20260823_153850-f56b93（round=2, status=accepted）

## 检索卡（短卡）

动作：当 cross-core split 完整覆盖且最终写回同一输出时，跳过先执行后被覆盖的 whole-tensor 路径。
适用：whole-tensor 与 split 产生同一输出、split 为确定最终写者，且 host 保证切片完整覆盖。
限制：必须满足 numPartials==blockDim、末参与者切片非空并铺满张量；守卫须保持 sentinel 语义同步。
范围：normalization 的 split 张量 whole-tensor 路径
检索词：cross-core split、whole-tensor、splitTensorId sentinel、numPartials、split 切片、死
机会：每块重复读取、计算整个张量，而结果随后被 split owner 覆盖丢弃。
