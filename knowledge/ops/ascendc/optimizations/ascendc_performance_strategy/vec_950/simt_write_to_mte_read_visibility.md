---
type: Optimization
title: SIMT 写后 DMA 读的可见性保证
description: SIMT 写后必须 asc_threadfence 加核间同步，才能让后续 MTE 读观察到全部更新。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/simt-write-to-mte-read-visibility.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "anti_pattern_reasoning": {
    "simt-write-mte-read-visibility-gap": "实测确认缺少 threadfence 时，Pass2 的 SIMT 原子写滞留核内 cache，Pass3 的 MTE 读读到过期值，全部更新丢失（y==data）。"
  },
  "applicability": {
    "constraints": [
      "fence 与核间同步的插入位置必须覆盖所有 SIMT 写→MTE 读路径，不能只放在循环末尾",
      "跨核消费必须在写侧同步完成后进行，不能依赖同执行模型排序"
    ],
    "excluded_conditions": [
      "消费方与写方共享一致的原子/缓存语义，或平台文档保证 SIMT 写对 DMA 读立即可见时无需该步骤",
      "工作区只由 SIMT 侧消费、没有后续 MTE 读时不适用"
    ],
    "required_conditions": [
      "同一 kernel 中先由 SIMT/VF 流水产生 GM 写入，随后由 MTE/DMA 读同一地址",
      "写与读之间没有内存一致性或跨执行模型排序保证"
    ]
  },
  "applicability_boundary": "",
  "classification": "lesson",
  "created": "2026-08-23",
  "evidence": [
    {
      "case": "S1-GmAddWs 排障",
      "precision": "全 20 例过",
      "status": "accepted",
      "task_dir": "task_scatter_20260821_180115_5c6355f3"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "simt-cache-stale"
    ],
    "pattern": "simt-write-mte-read-visibility",
    "structure": [
      "simt-write",
      "mte-read",
      "workspace"
    ]
  },
  "generality": "common",
  "id": "L-SIMT-WRITE-VISIBILITY",
  "implementation_steps": [
    "识别所有 SIMT 流水 GM 写与后续 MTE/DMA 读之间的数据依赖边",
    "在 SIMT 写侧放置 asc_threadfence()，确保写离开核内 cache",
    "跨核消费前执行一次核间同步（如 SyncAll），再发起 MTE 读",
    "用覆盖更新丢失场景的用例验证每条写后读路径完整"
  ],
  "intent": "避免 SIMT 写滞留核内 cache 导致后续 DMA 读取过期值并静默覆盖已完成更新。",
  "mechanism": "SIMT __gm__ 写在 SyncAll 后仍可能滞留在核内 cache；须在 VF 内 asc_threadfence() 强制写离开 cache，并在 Pass2 写完成后 SyncAll 再启动 Pass3 的 MTE 读。",
  "name": "SIMT 写后 DMA 读的可见性保证",
  "op": "scatter",
  "operator_class": "",
  "operator_scope": "同一 kernel 中先由 SIMT/VF 流水写 GM、再由 MTE/DMA 读同一工作区的数据流",
  "principle": "SIMT 写与 DMA 读属于不同执行模型，缓存一致性由显式原语维持而不是隐式保证；缺少 fence 时本核 DMA 读可能读到陈旧值并把已完成更新覆盖回旧值。",
  "provenance": {
    "opt_md": "scatter_opt.md",
    "state_md": "STATE.md",
    "task_dir": "task_scatter_20260821_180115_5c6355f3"
  },
  "related_anti_patterns": [
    "simt-write-mte-read-visibility-gap"
  ],
  "related_seed_ids": [],
  "risks": [
    "fence 缺失导致静默更新丢失且难以从常规精度用例暴露",
    "同步位置错误或过度同步会引入额外流水排空并抵消收益"
  ],
  "schema_version": 2,
  "slug": "simt-write-to-mte-read-visibility",
  "source": "task_dir",
  "status": "applied",
  "summary": "SIMT 写后必须 asc_threadfence 加核间同步，才能让后续 MTE 读观察到全部更新。",
  "verification": {
    "correctness": [
      "构造含高冲突与全覆盖写后读用例，确认无更新丢失、无陈旧读覆盖已完成更新"
    ],
    "performance": [
      "对比加/不加 fence 与同步的耗时，确认同步次数与数据依赖边数成正比而不是逐更新"
    ],
    "rollback_signals": [
      "出现更新丢失、陈旧读或同步开销随更新数线性增长时回退并重构可见性边界"
    ]
  }
}
-->

# 性能优化策略：SIMT 写后 DMA 读的可见性保证

单一优化点：SIMT 写后必须 asc_threadfence 加核间同步，才能让后续 MTE 读观察到全部更新。

## 1. 原理

SIMT 写与 DMA 读属于不同执行模型，缓存一致性由显式原语维持而不是隐式保证；缺少 fence 时本核 DMA 读可能读到陈旧值并把已完成更新覆盖回旧值。

实现机制：SIMT __gm__ 写在 SyncAll 后仍可能滞留在核内 cache；须在 VF 内 asc_threadfence() 强制写离开 cache，并在 Pass2 写完成后 SyncAll 再启动 Pass3 的 MTE 读。

## 2. 性能问题模式

- 优化目标：避免 SIMT 写滞留核内 cache 导致后续 DMA 读取过期值并静默覆盖已完成更新。
- 适用数据流：同一 kernel 中先由 SIMT/VF 流水写 GM、再由 MTE/DMA 读同一工作区的数据流
- Feature signature：`{"bottleneck": ["simt-cache-stale"], "pattern": "simt-write-mte-read-visibility", "structure": ["simt-write", "mte-read", "workspace"]}`

## 3. 正确性红线

- fence 缺失导致静默更新丢失且难以从常规精度用例暴露
- 同步位置错误或过度同步会引入额外流水排空并抵消收益

资源与硬件约束：

- fence 与核间同步的插入位置必须覆盖所有 SIMT 写→MTE 读路径，不能只放在循环末尾
- 跨核消费必须在写侧同步完成后进行，不能依赖同执行模型排序

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 同一 kernel 中先由 SIMT/VF 流水产生 GM 写入，随后由 MTE/DMA 读同一地址
- 写与读之间没有内存一致性或跨执行模型排序保证

不适用：

- 消费方与写方共享一致的原子/缓存语义，或平台文档保证 SIMT 写对 DMA 读立即可见时无需该步骤
- 工作区只由 SIMT 侧消费、没有后续 MTE 读时不适用

## 5. 实施步骤

1. 识别所有 SIMT 流水 GM 写与后续 MTE/DMA 读之间的数据依赖边
2. 在 SIMT 写侧放置 asc_threadfence()，确保写离开核内 cache
3. 跨核消费前执行一次核间同步（如 SyncAll），再发起 MTE 读
4. 用覆盖更新丢失场景的用例验证每条写后读路径完整

## 6. LLM 前置问题

- 目标实现是否满足：同一 kernel 中先由 SIMT/VF 流水产生 GM 写入，随后由 MTE/DMA 读同一地址？
- 目标实现是否满足：写与读之间没有内存一致性或跨执行模型排序保证？
- 是否命中排除条件：消费方与写方共享一致的原子/缓存语义，或平台文档保证 SIMT 写对 DMA 读立即可见时无需该步骤？

## 7. 验收标准

正确性：

- 构造含高冲突与全覆盖写后读用例，确认无更新丢失、无陈旧读覆盖已完成更新

性能：

- 对比加/不加 fence 与同步的耗时，确认同步次数与数据依赖边数成正比而不是逐更新

回滚信号：

- 出现更新丢失、陈旧读或同步开销随更新数线性增长时回退并重构可见性边界

## 8. 分类与证据

- Classification：`lesson`
- Generality：`common`
- Related anti-patterns：simt-write-mte-read-visibility-gap

- task_scatter_20260821_180115_5c6355f3（status=accepted, case=S1-GmAddWs 排障）

## 检索卡（短卡）

动作：在 SIMT GM 写侧、后续 MTE/DMA 读取依赖之前放置 asc_threadfence()，使写对 DMA 可见。
适用：同一 kernel 内 SIMT/VF 先写 GM、MTE/DMA 后读同址，且二者之间缺少一致性或排序。
限制：SIMT写侧fence使写离开cache；跨核消费前须核间同步，保持后续MTE读取可见性
范围：同一 kernel 的 SIMT/VF 写 GM→MTE/DMA 读路径
检索词：SIMT/VF、GM、MTE/DMA、asc_threadfence、cache 可见性、fence 顺序
机会：SIMT 写后紧接 DMA 同址读取，缺少跨执行模型排序，可能读取陈旧值并覆盖更新。
代价：同步位置错误或过度同步会增加流水排空。
