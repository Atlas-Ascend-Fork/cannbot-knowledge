---
type: Optimization
title: 8-bit narrow dtype LSD radix single-round reduction (roundNum 4->1)
description: 把 8-bit value domain 的 LSD radix keyBits 由 32 改为 8，使 roundNum 由 4 降到 1。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/unique-narrow-roundnum-reduction.md
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
      "host tiling 修改仅当运行时加载 run 的 tiling 生效（须正确 ASCEND_OPP_PATH/ASCEND_CUSTOM_OPP_PATH）",
      "并发 batch kernel-dir 抢占会使测量失效（host-only 改动对任何 kernel binary 稳健）",
      "int8 kernel 改动产生新 kernel_hash（fingerprint 一致性须满足）"
    ],
    "excluded_conditions": [
      "fp/int32/int64 及非 8-bit 宽度 dtype",
      "若 roundNum>1 恢复则 roundShift 不变式须重访",
      "kernel .o 与 host 契约不一致（fingerprint 校验失败）"
    ],
    "required_conditions": [
      "8-bit value domain 一轮可完全排序（uint8 0..255 / int8 -128..127）",
      "roundShift=0 不变式（roundNum=1）",
      "kernel key transform 在 A1/A3 路径都保持 bucket==value / monotonic",
      "int8 需 byte-0 monotonic key（^0x80）在 A3 scatter 与 A1 histogram 一致应用"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "operator_class": "sort-select",
      "precision": "8/8 PASS",
      "round": 2,
      "run_id": "<run-id>",
      "speedup": "incremental 1.577x; case6 uint8 2.2521x (778.3s->345.6s)",
      "status": "accepted"
    },
    {
      "operator_class": "sort-select",
      "precision": "20/20 PASS",
      "round": 3,
      "run_id": "<run-id>",
      "speedup": "incremental 1.0999x; case10 int8 2.26x (official); cumulative 1.7347",
      "status": "accepted"
    },
    {
      "comparison_sha256": "242c7c04b80e1197eec8466ef9f32284e9ecb80d7103671113a2b8c6963b1361",
      "decision_sha256": "92b28c916945732b11863a60e1e43f4cae203219cc7fdb2bcdbcef329e4dcce6",
      "operator_class": "sort-select",
      "performance_sha256": "51b0cbc02682694b4c1e6ef17662b3c63db7e6f6b1d37142448657f97a398baa",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "a2d03ead75ae8f25774720bab0bf306c5c3a79630c78141f526500767bdbd19a",
      "verify_sha256": "4182d6a8f8b71971439755e9a54aa9643e50d41dce2ca6d5e72f46dab2085084"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "store-drain-stall",
      "full-array-radix-rounds"
    ],
    "dtypes": [
      "uint8",
      "int8"
    ],
    "pattern": "narrow-dtype-lsd-radix-single-round",
    "structure": [
      "host-getkeybits",
      "kernel-monotonic-key",
      "roundnum-reduction"
    ]
  },
  "generality": "op_class",
  "id": "UNIQUE-NARROW-ROUNDNUM-REDUCTION",
  "implementation_steps": [
    "host GetKeyBits 增加 DT_UINT8->8U（roundNum=1）",
    "int8 时 kernel 增加 SortKeyBucketS monotonic key + HistogramU32ExtLoop mask 修正",
    "验证 roundNum=1 的 sortedDataOffset 契约（wsBufOffsetB）",
    "官方路径复验（elapsed + bit-exact 精度）"
  ],
  "intent": "消除窄（8-bit）value domain 上多余的全数组 LSD radix 轮（roundNum 4->1），削减最大 wall-clock case 的 store-drain 停顿与 scattered-write 流量。",
  "mechanism": "host 侧 GetKeyBits：DT_UINT8 返回 8U 而非 32U -> roundNum=CeilDiv(keyBits,8)=1。roundNum=1（odd）设 sortedDataOffset=wsBufOffsetB（round-0 A3 目标），保持最终 buffer 契约。kernel 侧对 int8 需单调 8-bit key 修正（SortKeyBucketS int8 branch key=uint8(bits&0xFF)^0x80；HistogramU32ExtLoop signMask 0x80000000->0x80），使单轮输出为升序 -128..127。uint8 版 kernel .o byte-identical。",
  "name": "8-bit narrow dtype LSD radix single-round reduction (roundNum 4->1)",
  "operator_class": "sort-select",
  "operator_scope": "sort-select 数据流中 8-bit value domain（uint8/int8）的 LSD radix 排序",
  "principle": "8-bit value domain 只需一轮 8-bit LSD radix；多余轮次以无排序收益地重做整个全数组 pipeline，故把 roundNum 4->1 移除 3/4 工作量，同时保持顺序（uint8 bucket==value）。",
  "related_anti_patterns": [],
  "risks": [
    "int8 key 修正不一致会产生 wrap 顺序 0..127,-128..-1",
    "host-only 改动依赖正确 OPP 环境加载",
    "并发 build 抢占使 fingerprint/测量失效"
  ],
  "slug": "unique-narrow-roundnum-reduction",
  "summary": "当 value domain 为 8-bit（uint8 0..255 或 int8 -128..127）时，LSD radix 只需一轮即可完全排序；host 把 uint8/int8 的 keyBits 从 32 改为 8，使 roundNum 从 4 降到 1，消除 3/4 的全数组 histogram/prefix/scatter/flush 往返，直接消灭最大 case 的 store-drain 停顿。int8 还需 kernel 单调 8-bit key 修正（^0x80）以输出升序 -128..127。",
  "verification": {
    "correctness": [
      "R2 8/8 validation cases；R3 20/20 verify；官方 spot-check bit-exact（y int8 mismatch 0, inverse int64 mismatch 0）"
    ],
    "performance": [
      "R2: incremental 1.577x, case6 uint8 2.2521x（778.3s->345.6s kernel_details）；R3: incremental 1.0999x, case10 int8 2.26x（官方 24.4s->10.8s）"
    ],
    "rollback_signals": [
      "int8 输出 wrap 顺序、case6/case10 store-drain 未降、fingerprint 不一致时回退"
    ]
  }
}
-->

# 性能优化策略：8-bit narrow dtype LSD radix single-round reduction (roundNum 4->1)

单一优化点：当 value domain 为 8-bit（uint8 0..255 或 int8 -128..127）时，LSD radix 只需一轮即可完全排序；host 把 uint8/int8 的 keyBits 从 32 改为 8，使 roundNum 从 4 降到 1，消除 3/4 的全数组 histogram/prefix/scatter/flush 往返，直接消灭最大 case 的 store-drain 停顿。int8 还需 kernel 单调 8-bit key 修正（^0x80）以输出升序 -128..127。

## 1. 原理

8-bit value domain 只需一轮 8-bit LSD radix；多余轮次以无排序收益地重做整个全数组 pipeline，故把 roundNum 4->1 移除 3/4 工作量，同时保持顺序（uint8 bucket==value）。

实现机制：host 侧 GetKeyBits：DT_UINT8 返回 8U 而非 32U -> roundNum=CeilDiv(keyBits,8)=1。roundNum=1（odd）设 sortedDataOffset=wsBufOffsetB（round-0 A3 目标），保持最终 buffer 契约。kernel 侧对 int8 需单调 8-bit key 修正（SortKeyBucketS int8 branch key=uint8(bits&0xFF)^0x80；HistogramU32ExtLoop signMask 0x80000000->0x80），使单轮输出为升序 -128..127。uint8 版 kernel .o byte-identical。

## 2. 性能问题模式

- 优化目标：消除窄（8-bit）value domain 上多余的全数组 LSD radix 轮（roundNum 4->1），削减最大 wall-clock case 的 store-drain 停顿与 scattered-write 流量。
- 适用数据流：sort-select 数据流中 8-bit value domain（uint8/int8）的 LSD radix 排序
- Feature signature：`{"bottleneck": ["store-drain-stall", "full-array-radix-rounds"], "dtypes": ["uint8", "int8"], "pattern": "narrow-dtype-lsd-radix-single-round", "structure": ["host-getkeybits", "kernel-monotonic-key", "roundnum-reduction"]}`

## 3. 正确性红线

- int8 key 修正不一致会产生 wrap 顺序 0..127,-128..-1
- host-only 改动依赖正确 OPP 环境加载
- 并发 build 抢占使 fingerprint/测量失效

资源与硬件约束：

- host tiling 修改仅当运行时加载 run 的 tiling 生效（须正确 ASCEND_OPP_PATH/ASCEND_CUSTOM_OPP_PATH）
- 并发 batch kernel-dir 抢占会使测量失效（host-only 改动对任何 kernel binary 稳健）
- int8 kernel 改动产生新 kernel_hash（fingerprint 一致性须满足）

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- 8-bit value domain 一轮可完全排序（uint8 0..255 / int8 -128..127）
- roundShift=0 不变式（roundNum=1）
- kernel key transform 在 A1/A3 路径都保持 bucket==value / monotonic
- int8 需 byte-0 monotonic key（^0x80）在 A3 scatter 与 A1 histogram 一致应用

不适用：

- fp/int32/int64 及非 8-bit 宽度 dtype
- 若 roundNum>1 恢复则 roundShift 不变式须重访
- kernel .o 与 host 契约不一致（fingerprint 校验失败）

## 5. 实施步骤

1. host GetKeyBits 增加 DT_UINT8->8U（roundNum=1）
2. int8 时 kernel 增加 SortKeyBucketS monotonic key + HistogramU32ExtLoop mask 修正
3. 验证 roundNum=1 的 sortedDataOffset 契约（wsBufOffsetB）
4. 官方路径复验（elapsed + bit-exact 精度）

## 6. LLM 前置问题

- 目标实现是否满足：8-bit value domain 一轮可完全排序（uint8 0..255 / int8 -128..127）？
- 目标实现是否满足：roundShift=0 不变式（roundNum=1）？
- 目标实现是否满足：kernel key transform 在 A1/A3 路径都保持 bucket==value / monotonic？
- 是否命中排除条件：fp/int32/int64 及非 8-bit 宽度 dtype？

## 7. 验收标准

正确性：

- R2 8/8 validation cases；R3 20/20 verify；官方 spot-check bit-exact（y int8 mismatch 0, inverse int64 mismatch 0）

性能：

- R2: incremental 1.577x, case6 uint8 2.2521x（778.3s->345.6s kernel_details）；R3: incremental 1.0999x, case10 int8 2.26x（官方 24.4s->10.8s）

回滚信号：

- int8 输出 wrap 顺序、case6/case10 store-drain 未降、fingerprint 不一致时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- unique-20260830_063304-5167c9（round=2, status=accepted, speedup=incremental 1.577x; case6 uint8 2.2521x (778.3s->345.6s)）
- unique-20260830_063304-5167c9（round=3, status=accepted, speedup=incremental 1.0999x; case10 int8 2.26x (official); cumulative 1.7347）
- unique-20260830_063304-5167c9（round=2, status=accepted）

## 检索卡（短卡）

动作：把 8-bit value domain 的 LSD radix keyBits 由 32 改为 8，使 roundNum 由 4 降到 1。
适用：8-bit value domain 一轮可完全排序（uint8 0..255 / int8 -128..127）。
限制：int8 须 byte-0 单调 key（^0x80）在 scatter 与 histogram 一致应用，否则输出 wrap 顺序。
范围：sort-select 的 8-bit value domain LSD radix 排序
检索词：GetKeyBits、roundNum、SortKeyBucketS、HistogramU32ExtLoop
机会：多余轮次无排序收益地重做全数组 pipeline，受 store-drain 支配
代价：int8 kernel 改动产生新 kernel_hash，须校验 fingerprint
