---
type: Optimization
title: 固定轮逐 lane 迭代循环的分块全 lane 早退
description: 将固定轮逐 lane 迭代改为分块执行，并在全部活动 lane 完成后早退。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/fixed-round-vector-loop-early-exit.md
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
      "chunk 间 A/B 持久化占用 UB：需要 host tiling UB 预算预留持久化窗口，或复用已有窗口",
      "每 chunk 的 V->S 同步 + PipeBarrier 有流水开销，K（chunk 大小）与 done 检查频率需实测调参",
      "done 槽复用与归约 lane-0 假设依赖平台向量归约语义，需 reviewer verify 确认",
      "共享轮体改动会影响所有 BCT/dtype 模板，需对每个 route 做 no-regression 验证"
    ],
    "excluded_conditions": [
      "非 VEC-bound（MTE2/launch/scalar bound）时指令削减不预期转化为时延收益",
      "迭代轮数上界已被数据最坏情况占满（无早退空间），或轮体为数据无关的定长变换",
      "完成谓词无法向量化检测，或算法语义要求所有 lane 同步执行相同轮数（轮间存在跨 lane 通信）"
    ],
    "required_conditions": [
      "完整 msprof 显示 VEC 为唯一关键流水（aiv_vec_ratio >= ~99%），MTE2/MTE3/scalar 在其下重叠，无竞争次要流水",
      "热链是编译期固定轮数、无早退的逐 lane 迭代循环，且轮数上界远大于数据实际收敛轮数（存在数据相关早退空间）",
      "逐 lane 迭代有停止保护：完成 lane 的结果在后续额外轮中保持位精确不变（无跨 lane 依赖、无进位/状态污染）",
      "存在可编译的跨流水 done 通道（VF 归约 + V->S 同步 + aicore 读回），或允许在 aicore 层执行 chunk 循环"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-24",
  "evidence": [
    {
      "case": "T3(3,9,13,20) + T2 control(2,5,11,18)",
      "operator_class": "broadcast",
      "round": 1,
      "run_id": "<run-id>",
      "speedup": "T3 int64 4.47-5.64x; T2 int32 control 1.48-3.75x; total 4.428",
      "status": "accepted"
    },
    {
      "comparison_sha256": "6d2ebc560770dc390e925f4abb9eed331843acaa69c8a1cc9abf407389ee411b",
      "decision_sha256": "b012328fd4f91fb345b578b7bd5c4ee85294c8b39e9f35c1106128d44dd7bc3c",
      "operator_class": "broadcast",
      "performance_sha256": "b37e0b34faf84486e1dd8122c0659c475e6f86b6f5850e19a91ea88b76c6e401",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "b19c4299243893a31058613bbd5ea7919ac2f1fae6e6a80c96d54af61253f436",
      "verify_sha256": "42815192ec863938b180adfae8f64c6e904a1029ebcf88d590fd86ad53c59d93"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "fixed-round-loop",
      "per-lane-convergence"
    ],
    "dtypes": [
      "int16",
      "int32",
      "int64"
    ],
    "pattern": "chunked-all-lanes-early-exit",
    "structure": [
      "vec-iterative-loop",
      "streaming-elementwise",
      "ub-persistent-state",
      "cross-pipe-done-reduction"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-FIXED-ROUND-EARLY-EXIT",
  "implementation_steps": [
    "用 msprof 确认 VEC 为唯一临界流水，并定位固定轮迭代循环（编译期 MAX_ROUNDS、无早退）",
    "抽取单轮函数，保持与原始轮体逐字一致的指令序列与停止保护语义",
    "把循环重构成 K 轮 chunk：A/B 中间态持久化在 UB，每 chunk 跑固定 K 轮后统计未完成 lane 数",
    "建立跨流水 done 通道：VF 内 Reg::Reduce 归约未完成数 -> StoreAlign 写 UB done 槽 -> TQueSync<PIPE_V, PIPE_S> -> aicore GetValue 读回，为 0 即 break",
    "验证位精确性（收敛 lane 不变）与全 route no-regression，实测调参 chunk 大小 K"
  ],
  "intent": "消除固定轮迭代循环在数据已收敛后的多余 VEC 指令（固定轮数上界远大于数据实际收敛轮数），降低 VEC-bound 大 shape 的端到端时延。",
  "mechanism": "__simd_vf__ 内数据相关 while / 跨流水读回被 bisheng 硬性禁止（'Unsupported scalar instruction in AIV loop'），故把分块循环上提到 __aicore__ 层：A/B 经 UB（复用已有窗口）在 chunk 间持久化；每 chunk 的 VF 跑固定 K 轮（抽取的单轮函数与原始轮体逐字一致，保证位精确）后，用 Compares(EQ, B, 0) + Select + Reg::Reduce 统计本 block 未完成 lane 数并累加到 slice 级，StoreAlign 写 UB done 槽；TQueSync<PIPE_V, PIPE_S> 后 aicore GetValue 读回，为 0 即 break；未 break 则 PipeBarrier<PIPE_V> 保证 A/B 写对下个 chunk 可见。收敛 lane 的停止保护使超出精确轮数不超过 K-1 轮的冗余 chunk 仍是位精确 no-op。",
  "name": "固定轮逐 lane 迭代循环的分块全 lane 早退",
  "op": "gcd",
  "operator_class": "broadcast",
  "operator_scope": "VEC-bound 的流式 elementwise 迭代计算：热链是编译期固定 MAX_ROUNDS、无早退的逐 lane 迭代循环（GM->UB->VEC->UB->GM，无数据复用、无跨核流量），每 lane 有可检测的完成谓词（如欧几里得算法的 B==0），且完成 lane 的停止保护使后续额外轮在位精确语义下是 no-op",
  "principle": "VEC 为唯一临界流水（aiv_vec_ratio >= 99%）时，端到端时延近似正比于 VEC 指令发射量；固定轮循环为最坏数据支付恒定指令数。逐 lane 迭代若有停止保护（完成 lane 保持结果不变），则'全部活动 lane 已完成即终止'是位精确的。把循环切成 K 轮 chunk 并在 chunk 边界做向量宽 done 归约与跨流水读回，即可在数据相关轮次终止，按元素削减多余轮次的 VEC 指令。",
  "related_anti_patterns": [],
  "risks": [
    "VF 内数据相关 while / 跨流水读回可能被编译器拒绝，需要把循环上提到 aicore 层并增加 UB 往返同步",
    "chunk 间 A/B 读写竞争依赖 TQueSync/PipeBarrier 的硬件排序语义，若弱于预期存在 UB RAW 竞争",
    "done 槽复用与归约 lane-0 假设不成立时早退计数错误",
    "提升域（dtype promotion）中间态需 2x 原生宽度 UB，超出只改 kernel 的预算时必须协调 host tiling 预留"
  ],
  "slug": "fixed-round-vector-loop-early-exit",
  "summary": "把编译期固定轮数、无早退的逐 lane 迭代循环重构成 K 轮分块循环并上提到 __aicore__ 层：A/B 中间态在 UB 中跨 chunk 持久化，每 chunk 在 VF 内跑固定 K 轮后用向量宽归约统计未完成 lane 数并写 UB done 槽，aicore 经 V->S 同步读回，全部活动 lane 完成即 break，把每元素固定指令数降为数据相关指令数，VEC-bound 下直接转化为 wall-time。",
  "verification": {
    "correctness": [
      "全量 verify 位精确：早退终止后收敛 lane 的结果与固定轮路径逐位一致",
      "覆盖值域边界（提升域 abs-wrap 与全 dtype 域极值）"
    ],
    "performance": [
      "target route 中位时延按早退轮数比例下降，且 aiv_vec_time 同步下降",
      "control route 无超过 max_case_regression 的回归（共享轮体改动需逐 route 验证）"
    ],
    "rollback_signals": [
      "任一 verify 位精确失败（早退改变了收敛 lane 结果）",
      "target 无方向性收益（chunk 同步开销吞噬早退收益）或 control 回归超阈值",
      "VF 数据相关分支编译失败时回退，而不是弱化正确性"
    ]
  }
}
-->

# 性能优化策略：固定轮逐 lane 迭代循环的分块全 lane 早退

单一优化点：把编译期固定轮数、无早退的逐 lane 迭代循环重构成 K 轮分块循环并上提到 __aicore__ 层：A/B 中间态在 UB 中跨 chunk 持久化，每 chunk 在 VF 内跑固定 K 轮后用向量宽归约统计未完成 lane 数并写 UB done 槽，aicore 经 V->S 同步读回，全部活动 lane 完成即 break，把每元素固定指令数降为数据相关指令数，VEC-bound 下直接转化为 wall-time。

## 1. 原理

VEC 为唯一临界流水（aiv_vec_ratio >= 99%）时，端到端时延近似正比于 VEC 指令发射量；固定轮循环为最坏数据支付恒定指令数。逐 lane 迭代若有停止保护（完成 lane 保持结果不变），则'全部活动 lane 已完成即终止'是位精确的。把循环切成 K 轮 chunk 并在 chunk 边界做向量宽 done 归约与跨流水读回，即可在数据相关轮次终止，按元素削减多余轮次的 VEC 指令。

实现机制：__simd_vf__ 内数据相关 while / 跨流水读回被 bisheng 硬性禁止（'Unsupported scalar instruction in AIV loop'），故把分块循环上提到 __aicore__ 层：A/B 经 UB（复用已有窗口）在 chunk 间持久化；每 chunk 的 VF 跑固定 K 轮（抽取的单轮函数与原始轮体逐字一致，保证位精确）后，用 Compares(EQ, B, 0) + Select + Reg::Reduce 统计本 block 未完成 lane 数并累加到 slice 级，StoreAlign 写 UB done 槽；TQueSync<PIPE_V, PIPE_S> 后 aicore GetValue 读回，为 0 即 break；未 break 则 PipeBarrier<PIPE_V> 保证 A/B 写对下个 chunk 可见。收敛 lane 的停止保护使超出精确轮数不超过 K-1 轮的冗余 chunk 仍是位精确 no-op。

## 2. 性能问题模式

- 优化目标：消除固定轮迭代循环在数据已收敛后的多余 VEC 指令（固定轮数上界远大于数据实际收敛轮数），降低 VEC-bound 大 shape 的端到端时延。
- 适用数据流：VEC-bound 的流式 elementwise 迭代计算：热链是编译期固定 MAX_ROUNDS、无早退的逐 lane 迭代循环（GM->UB->VEC->UB->GM，无数据复用、无跨核流量），每 lane 有可检测的完成谓词（如欧几里得算法的 B==0），且完成 lane 的停止保护使后续额外轮在位精确语义下是 no-op
- Feature signature：`{"bottleneck": ["vec-bound", "fixed-round-loop", "per-lane-convergence"], "dtypes": ["int16", "int32", "int64"], "pattern": "chunked-all-lanes-early-exit", "structure": ["vec-iterative-loop", "streaming-elementwise", "ub-persistent-state", "cross-pipe-done-reduction"]}`

## 3. 正确性红线

- VF 内数据相关 while / 跨流水读回可能被编译器拒绝，需要把循环上提到 aicore 层并增加 UB 往返同步
- chunk 间 A/B 读写竞争依赖 TQueSync/PipeBarrier 的硬件排序语义，若弱于预期存在 UB RAW 竞争
- done 槽复用与归约 lane-0 假设不成立时早退计数错误
- 提升域（dtype promotion）中间态需 2x 原生宽度 UB，超出只改 kernel 的预算时必须协调 host tiling 预留

资源与硬件约束：

- chunk 间 A/B 持久化占用 UB：需要 host tiling UB 预算预留持久化窗口，或复用已有窗口
- 每 chunk 的 V->S 同步 + PipeBarrier 有流水开销，K（chunk 大小）与 done 检查频率需实测调参
- done 槽复用与归约 lane-0 假设依赖平台向量归约语义，需 reviewer verify 确认
- 共享轮体改动会影响所有 BCT/dtype 模板，需对每个 route 做 no-regression 验证

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- 完整 msprof 显示 VEC 为唯一关键流水（aiv_vec_ratio >= ~99%），MTE2/MTE3/scalar 在其下重叠，无竞争次要流水
- 热链是编译期固定轮数、无早退的逐 lane 迭代循环，且轮数上界远大于数据实际收敛轮数（存在数据相关早退空间）
- 逐 lane 迭代有停止保护：完成 lane 的结果在后续额外轮中保持位精确不变（无跨 lane 依赖、无进位/状态污染）
- 存在可编译的跨流水 done 通道（VF 归约 + V->S 同步 + aicore 读回），或允许在 aicore 层执行 chunk 循环

不适用：

- 非 VEC-bound（MTE2/launch/scalar bound）时指令削减不预期转化为时延收益
- 迭代轮数上界已被数据最坏情况占满（无早退空间），或轮体为数据无关的定长变换
- 完成谓词无法向量化检测，或算法语义要求所有 lane 同步执行相同轮数（轮间存在跨 lane 通信）

## 5. 实施步骤

1. 用 msprof 确认 VEC 为唯一临界流水，并定位固定轮迭代循环（编译期 MAX_ROUNDS、无早退）
2. 抽取单轮函数，保持与原始轮体逐字一致的指令序列与停止保护语义
3. 把循环重构成 K 轮 chunk：A/B 中间态持久化在 UB，每 chunk 跑固定 K 轮后统计未完成 lane 数
4. 建立跨流水 done 通道：VF 内 Reg::Reduce 归约未完成数 -> StoreAlign 写 UB done 槽 -> TQueSync<PIPE_V, PIPE_S> -> aicore GetValue 读回，为 0 即 break
5. 验证位精确性（收敛 lane 不变）与全 route no-regression，实测调参 chunk 大小 K

## 6. LLM 前置问题

- 目标实现是否满足：完整 msprof 显示 VEC 为唯一关键流水（aiv_vec_ratio >= ~99%），MTE2/MTE3/scalar 在其下重叠，无竞争次要流水？
- 目标实现是否满足：热链是编译期固定轮数、无早退的逐 lane 迭代循环，且轮数上界远大于数据实际收敛轮数（存在数据相关早退空间）？
- 目标实现是否满足：逐 lane 迭代有停止保护：完成 lane 的结果在后续额外轮中保持位精确不变（无跨 lane 依赖、无进位/状态污染）？
- 是否命中排除条件：非 VEC-bound（MTE2/launch/scalar bound）时指令削减不预期转化为时延收益？

## 7. 验收标准

正确性：

- 全量 verify 位精确：早退终止后收敛 lane 的结果与固定轮路径逐位一致
- 覆盖值域边界（提升域 abs-wrap 与全 dtype 域极值）

性能：

- target route 中位时延按早退轮数比例下降，且 aiv_vec_time 同步下降
- control route 无超过 max_case_regression 的回归（共享轮体改动需逐 route 验证）

回滚信号：

- 任一 verify 位精确失败（早退改变了收敛 lane 结果）
- target 无方向性收益（chunk 同步开销吞噬早退收益）或 control 回归超阈值
- VF 数据相关分支编译失败时回退，而不是弱化正确性

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260824_045521-4a1ef3（round=1, status=accepted, case=T3(3,9,13,20) + T2 control(2,5,11,18), speedup=T3 int64 4.47-5.64x; T2 int32 control 1.48-3.75x; total 4.428）
- gcd-20260824_045521-4a1ef3（round=1, status=accepted）

## 检索卡（短卡）

动作：将固定轮逐 lane 迭代改为分块执行，并在全部活动 lane 完成后早退。
适用：VEC 为唯一临界流水，且完成 lane 有保持结果不变的停止保护。
限制：若 VF 数据相关循环或跨流水读回被拒绝，须上提至 aicore 层并增加 UB 往返同步。
范围：elementwise-arithmetic 的逐 lane 固定轮循环。
检索词：VEC 临界流水、固定轮迭代、活动 lane 完成、MAX_ROUNDS。
机会：固定轮数上界远大于实际收敛轮数，且循环使用编译期 MAX_ROUNDS、无早退。
代价：chunk间A/B持久化占用UB，必须纳入host tiling容量预算。
