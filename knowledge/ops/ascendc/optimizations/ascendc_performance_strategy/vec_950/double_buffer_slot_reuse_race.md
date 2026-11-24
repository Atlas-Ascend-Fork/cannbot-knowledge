---
type: Optimization
title: 双队列 freed 槽位复用竞态
description: 深度 ≥2 双队列复用 freed 槽位会与在途访问竞态；depth=1 串行化或显式槽位生命周期可保证安全。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/double-buffer-slot-reuse-race.md
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
      "队列槽位复用前必须证明没有在途的 V 读/写仍引用该槽位",
      "depth=1 或显式槽位生命周期管理可作为安全收尾"
    ],
    "excluded_conditions": [
      "编译器与硬件保证 freed 槽位与在途访问之间不存在重叠，或队列实现本身串行化时不需要",
      "单缓冲、无槽位复用或访问完全串行化时不适用"
    ],
    "required_conditions": [
      "kernel 使用深度 ≥2 的双队列（inQ/outQ）复用 freed 槽位",
      "异步流水（如 cast-copy）中写侧释放槽位与读侧在途访问可能重叠"
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
      "slot-reuse-race"
    ],
    "pattern": "double-buffer-slot-reuse-race",
    "structure": [
      "double-buffer",
      "queue",
      "cast-copy"
    ]
  },
  "generality": "common",
  "id": "L-DBUF-SLOT-RACE",
  "implementation_steps": [
    "识别双队列中 freed 槽位复用的所有路径，画出在途 V 读/写的存活区间",
    "确认新写入不会与仍在途的读取重叠，必要时退回 depth=1 串行化",
    "或用显式槽位生命周期（计数、屏障）保证复用安全",
    "用竞态用例（大 batch 异步 cast-copy）验证无数据腐坏"
  ],
  "intent": "避免 depth≥2 双队列复用 freed 槽位与在途 V 访问重叠导致的竞态数据腐坏。",
  "mechanism": "D/K-split 的 depth=2 inQ/outQ 复用 freed slot 时，新写可能与在途 V 读重叠；depth=1 串行化安全（该路径最终被 S1 取代，D/K-split 仍作 fallback）。",
  "name": "双队列 freed 槽位复用竞态",
  "op": "scatter",
  "operator_class": "",
  "operator_scope": "使用深度 ≥2 双队列并在异步流水之间复用 freed 槽位的 kernel 数据流",
  "principle": "队列 depth>1 时槽位在流水完成前被释放，复用同一槽位的新传输可能与在途读取重叠，产生无法通过静态检查发现的竞态；降低 depth 或显式管理槽位生命周期可把复用边界变为可证明安全。",
  "provenance": {
    "opt_md": "scatter_opt.md",
    "state_md": "STATE.md",
    "task_dir": "task_scatter_20260821_180115_5c6355f3"
  },
  "related_anti_patterns": [],
  "related_seed_ids": [],
  "risks": [
    "竞态表现为偶发数据腐坏，依赖确定性用例难以复现",
    "depth=1 会串行化传输，可能在批量场景引入吞吐回归"
  ],
  "schema_version": 2,
  "slug": "double-buffer-slot-reuse-race",
  "source": "task_dir",
  "status": "applied",
  "summary": "深度 ≥2 双队列复用 freed 槽位会与在途访问竞态；depth=1 串行化或显式槽位生命周期可保证安全。",
  "verification": {
    "correctness": [
      "在大 batch 异步 cast-copy 下反复运行，确认无偶发数据腐坏"
    ],
    "performance": [
      "对比 depth=1 串行化与显式槽位管理在批量场景的吞吐，避免回归"
    ],
    "rollback_signals": [
      "出现偶发腐坏、深度调整后吞吐明显下降或复用边界无法证明时回退"
    ]
  }
}
-->

# 性能优化策略：双队列 freed 槽位复用竞态

单一优化点：深度 ≥2 双队列复用 freed 槽位会与在途访问竞态；depth=1 串行化或显式槽位生命周期可保证安全。

## 1. 原理

队列 depth>1 时槽位在流水完成前被释放，复用同一槽位的新传输可能与在途读取重叠，产生无法通过静态检查发现的竞态；降低 depth 或显式管理槽位生命周期可把复用边界变为可证明安全。

实现机制：D/K-split 的 depth=2 inQ/outQ 复用 freed slot 时，新写可能与在途 V 读重叠；depth=1 串行化安全（该路径最终被 S1 取代，D/K-split 仍作 fallback）。

## 2. 性能问题模式

- 优化目标：避免 depth≥2 双队列复用 freed 槽位与在途 V 访问重叠导致的竞态数据腐坏。
- 适用数据流：使用深度 ≥2 双队列并在异步流水之间复用 freed 槽位的 kernel 数据流
- Feature signature：`{"bottleneck": ["slot-reuse-race"], "pattern": "double-buffer-slot-reuse-race", "structure": ["double-buffer", "queue", "cast-copy"]}`

## 3. 正确性红线

- 竞态表现为偶发数据腐坏，依赖确定性用例难以复现
- depth=1 会串行化传输，可能在批量场景引入吞吐回归

资源与硬件约束：

- 队列槽位复用前必须证明没有在途的 V 读/写仍引用该槽位
- depth=1 或显式槽位生命周期管理可作为安全收尾

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- kernel 使用深度 ≥2 的双队列（inQ/outQ）复用 freed 槽位
- 异步流水（如 cast-copy）中写侧释放槽位与读侧在途访问可能重叠

不适用：

- 编译器与硬件保证 freed 槽位与在途访问之间不存在重叠，或队列实现本身串行化时不需要
- 单缓冲、无槽位复用或访问完全串行化时不适用

## 5. 实施步骤

1. 识别双队列中 freed 槽位复用的所有路径，画出在途 V 读/写的存活区间
2. 确认新写入不会与仍在途的读取重叠，必要时退回 depth=1 串行化
3. 或用显式槽位生命周期（计数、屏障）保证复用安全
4. 用竞态用例（大 batch 异步 cast-copy）验证无数据腐坏

## 6. LLM 前置问题

- 目标实现是否满足：kernel 使用深度 ≥2 的双队列（inQ/outQ）复用 freed 槽位？
- 目标实现是否满足：异步流水（如 cast-copy）中写侧释放槽位与读侧在途访问可能重叠？
- 是否命中排除条件：编译器与硬件保证 freed 槽位与在途访问之间不存在重叠，或队列实现本身串行化时不需要？

## 7. 验收标准

正确性：

- 在大 batch 异步 cast-copy 下反复运行，确认无偶发数据腐坏

性能：

- 对比 depth=1 串行化与显式槽位管理在批量场景的吞吐，避免回归

回滚信号：

- 出现偶发腐坏、深度调整后吞吐明显下降或复用边界无法证明时回退

## 8. 分类与证据

- Classification：`lesson`
- Generality：`common`
- Related anti-patterns：无

- task_scatter_20260821_180115_5c6355f3（status=accepted, case=S1-GmAddWs 排障）

## 检索卡（短卡）

动作：降低队列 depth，或显式管理槽位生命周期，使复用边界可证明安全。
适用：内核使用深度≥2的 inQ/outQ，并跨异步流水复用 freed 槽位。
限制：复用槽位前必须证明没有在途 V 读写仍引用它。
范围：深度≥2双队列的异步槽位复用路径。
检索词：双队列、depth>1、freed槽位、在途V读写、cast-copy
机会：freed 槽位的新传输可能与仍在途的读取重叠。
代价：退回 depth=1 会串行化传输，批量场景可能吞吐回归。
