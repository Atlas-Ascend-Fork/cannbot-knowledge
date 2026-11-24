---
type: Optimization
title: 规则二维切片的批量数据搬运
description: 用一条二维 DMA 描述符表达多个等长切片，替代循环内逐切片发射搬运。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/2d-bulk-data-copy.md
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
      "区分 DataCopyParams 与 DataCopyExtParams，以及 DataCopyExtParams 在不同搬运方向上的 stride 单位：GM 侧按字节、UB 侧按 dataBlock（32B）；blockLen 始终为字节",
      "使用 DataCopyPad 时必须计入每块独立补齐产生的 UB 行距，并核对左右 padding 上限"
    ],
    "excluded_conditions": [
      "每行长度或地址间距不规则、索引驱动的随机搬运不能强行合并为二维描述符",
      "合并后超出单条命令字段上限时必须分批，而不是截断参数"
    ],
    "required_conditions": [
      "各切片块长一致，源地址间距和目标地址间距可以用固定 stride 表达",
      "二维搬运的 blockCount、blockLen 和 stride 均落在目标接口的合法范围",
      "消费方能够按 DMA 实际落盘规则计算 UB 中每行的真实步幅"
    ]
  },
  "applicability_boundary": "",
  "classification": "validated_strategy",
  "created": "2026-08-21",
  "evidence": [
    {
      "case": "combined-path",
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/strategies/unsorted_segment_sum_opt_20260820.md",
      "speedup": "1.0-1.3",
      "status": "accepted"
    },
    {
      "comparison_sha256": "f3cd36ab4b3d9315fe7414bd9e7264196f2d447a35b42a605beb609e05cb1c73",
      "decision_sha256": "a27f97e142d6c49d0b9bcab92974a84296a95e03301ae8d70c7bc1bf470e99ae",
      "operator_class": "layout-transform",
      "performance_sha256": "7e3f444b2b304b65f1c79954cfd86194ac118a88d0d47a68869a7b6c494987b3",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "92165e8570f04673ee276573296c62de7e125503df6f544125df63a32b221ea3",
      "verify_sha256": "95b8ea7e5ef1b36eea8f07ee653c0f13d67658f0fdb48b956084fbbf8d82ffc4"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "mte-descriptor-spray"
    ],
    "dtypes": [],
    "pattern": "2d-bulk-copy",
    "reduce_mode": "copy",
    "structure": [
      "2d-copy",
      "bulk-mte"
    ]
  },
  "gain": "UnsortedSegmentSum 单项/组合路径约 1.0–1.3x（中等强度证据）。",
  "generality": "common",
  "id": "S4",
  "implementation_steps": [
    "从逻辑布局推导块数、有效块长、源行距、目标行距以及尾部 padding",
    "选择与对齐条件匹配的二维 DataCopy 或 DataCopyPad 接口，并检查所有字段上限",
    "按接口规定的单位填写 blockLen 和 stride，禁止混用元素、字节和 datablock",
    "让后续计算使用 DMA 实际生成的 UB 行距，而不是直接复用 GM 行距",
    "对超字段上限、非规则布局和尾块提供分批或逐行回退"
  ],
  "instance_ids": [],
  "intent": "消除逐行/逐元素 MTE 描述符",
  "mechanism": "2D 批量搬运（行切片读）：单条 DataCopyExtParams{blockCount=nLen, blockLen=fLen*s, srcStride=(F-fLen)*s, dstStride=0}；dstStride=0 时 UB 每块按 Normal 模式补齐至 32B，消费方按本 tile fLen 派生行步幅。注意 stride 单位按搬运方向区分：GM→UB 时 srcStride 为字节、dstStride 为 dataBlock（32B）；UB→GM 时 srcStride 为 dataBlock、dstStride 为字节；blockLen 始终为字节。不可把 UB 侧 stride 当字节直接填，也不可把 GM 侧 stride 当 dataBlock 填。",
  "name": "规则二维切片的批量数据搬运",
  "op": "seed",
  "operator_class": "",
  "operator_scope": "GM 中由固定块长和固定行距描述、需要搬入或写回多个规则切片的数据布局",
  "principle": "逐行 DataCopy 的主要浪费是重复构造和发射描述符；二维搬运把块数、块长和跨步编码进一次命令，在总字节数不变时减少标量控制与 MTE 发射开销。",
  "provenance": {
    "skill": "SKILL.md §7 S4"
  },
  "related_anti_patterns": [
    "per-element-mte-descriptor-spray"
  ],
  "related_seed_ids": [],
  "risks": [
    "stride 单位混淆会产生跨行错位，padding 行距误判会让后续向量计算读取错误数据",
    "只减少描述符而未减少等待或队列往返时，收益可能被其他固定开销限制"
  ],
  "schema_version": 2,
  "slug": "2d-bulk-data-copy",
  "source": "skill",
  "status": "applied",
  "summary": "用一条二维 DMA 描述符表达多个等长切片，替代循环内逐切片发射搬运。",
  "verification": {
    "correctness": [
      "覆盖连续与带 stride 的布局、非对齐块长、最大字段边界和尾批，并逐行核对 UB 布局；补充 UB 侧非零 stride 用例（GM→UB 的 dstStride、UB→GM 的 srcStride）"
    ],
    "performance": [
      "确认 MTE 描述符数量按批次下降，并在小块多行与大块少行两类形状上检查收益边界"
    ],
    "rollback_signals": [
      "出现行错位、padding 污染、描述符字段溢出或大块路径回归时回退"
    ]
  }
}
-->

# 性能优化策略：规则二维切片的批量数据搬运

单一优化点：用一条二维 DMA 描述符表达多个等长切片，替代循环内逐切片发射搬运。

## 1. 原理

逐行 DataCopy 的主要浪费是重复构造和发射描述符；二维搬运把块数、块长和跨步编码进一次命令，在总字节数不变时减少标量控制与 MTE 发射开销。

实现机制：2D 批量搬运（行切片读）：单条 DataCopyExtParams{blockCount=nLen, blockLen=fLen*s, srcStride=(F-fLen)*s, dstStride=0}；dstStride=0 时 UB 每块按 Normal 模式补齐至 32B，消费方按本 tile fLen 派生行步幅。注意 stride 单位按搬运方向区分：GM→UB 时 srcStride 为字节、dstStride 为 dataBlock（32B）；UB→GM 时 srcStride 为 dataBlock、dstStride 为字节；blockLen 始终为字节。不可把 UB 侧 stride 当字节直接填，也不可把 GM 侧 stride 当 dataBlock 填。

## 2. 性能问题模式

- 优化目标：消除逐行/逐元素 MTE 描述符
- 适用数据流：GM 中由固定块长和固定行距描述、需要搬入或写回多个规则切片的数据布局
- Feature signature：`{"bottleneck": ["mte-descriptor-spray"], "dtypes": [], "pattern": "2d-bulk-copy", "reduce_mode": "copy", "structure": ["2d-copy", "bulk-mte"]}`

## 3. 正确性红线

- stride 单位混淆会产生跨行错位，padding 行距误判会让后续向量计算读取错误数据
- 只减少描述符而未减少等待或队列往返时，收益可能被其他固定开销限制

资源与硬件约束：

- 区分 DataCopyParams 与 DataCopyExtParams，以及 DataCopyExtParams 在不同搬运方向上的 stride 单位：GM 侧按字节、UB 侧按 dataBlock（32B）；使用 DataCopyPad 时必须计入每块独立补齐产生的 UB 行距，并核对左右 padding 上限

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 各切片块长一致，源地址间距和目标地址间距可以用固定 stride 表达
- 二维搬运的 blockCount、blockLen 和 stride 均落在目标接口的合法范围
- 消费方能够按 DMA 实际落盘规则计算 UB 中每行的真实步幅

不适用：

- 每行长度或地址间距不规则、索引驱动的随机搬运不能强行合并为二维描述符
- 合并后超出单条命令字段上限时必须分批，而不是截断参数

## 5. 实施步骤

1. 从逻辑布局推导块数、有效块长、源行距、目标行距以及尾部 padding
2. 选择与对齐条件匹配的二维 DataCopy 或 DataCopyPad 接口，并检查所有字段上限
3. 按搬运方向填写 stride：GM→UB 的 srcStride 用字节、dstStride 用 dataBlock；UB→GM 的 srcStride 用 dataBlock、dstStride 用字节；blockLen 始终用字节。禁止混用元素、字节和 datablock
4. 让后续计算使用 DMA 实际生成的 UB 行距，而不是直接复用 GM 行距
5. 对超字段上限、非规则布局和尾块提供分批或逐行回退

## 6. LLM 前置问题

- 目标实现是否满足：各切片块长一致，源地址间距和目标地址间距可以用固定 stride 表达？
- 目标实现是否满足：二维搬运的 blockCount、blockLen 和 stride 均落在目标接口的合法范围？
- 目标实现是否满足：消费方能够按 DMA 实际落盘规则计算 UB 中每行的真实步幅？
- 是否命中排除条件：每行长度或地址间距不规则、索引驱动的随机搬运不能强行合并为二维描述符？

## 7. 验收标准

正确性：

- 覆盖连续与带 stride 的布局、非对齐块长、最大字段边界和尾批，并逐行核对 UB 布局；补充 UB 侧非零 stride 用例（GM→UB 的 dstStride、UB→GM 的 srcStride）

性能：

- 确认 MTE 描述符数量按批次下降，并在小块多行与大块少行两类形状上检查收益边界

回滚信号：

- 出现行错位、padding 污染、描述符字段溢出或大块路径回归时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related anti-patterns：per-element-mte-descriptor-spray

- strategy-unsorted-segment-sum-20260820-uss-003（status=accepted, case=combined-path, speedup=1.0-1.3）
- moe_re_routing（run-id 已脱敏；round=1, status=accepted）

## 检索卡（短卡）

动作：将规则切片的逐行DataCopy改为单次二维搬运，在总字节数不变时编码块数、块长与跨步
适用：各切片块长一致，源与目标地址间距均可用固定stride表达
限制：stride 单位按搬运方向区分（GM 侧字节、UB 侧 dataBlock）；blockLen 用字节；字段合法且 padding/stride 行距一致
范围：跨operator class的GM规则二维切片搬入或写回
检索词：二维DataCopy、DataCopyExtParams、blockCount、blockLen、stride、DataCopyPad
机会：GM中多个规则切片具有固定块长和行距，却逐行重复构造并发射DataCopy描述符
