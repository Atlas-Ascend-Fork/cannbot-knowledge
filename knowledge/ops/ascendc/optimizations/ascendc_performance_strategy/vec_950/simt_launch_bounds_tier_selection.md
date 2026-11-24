---
type: Optimization
title: SIMT 线程档选择与按 shape 双档路由
description: 按每线程寄存器预算选 launch_bounds 档；至少测 1024/2048，并允许双实例按 shape 路由。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/simt-launch-bounds-tier-selection.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "schema_version": 2,
  "id": "F5",
  "slug": "simt-launch-bounds-tier-selection",
  "name": "SIMT 线程档选择与按 shape 双档路由",
  "summary": "按每线程寄存器预算选 launch_bounds 档；至少测 1024/2048，并允许双实例按 shape 路由。",
  "intent": "避免把线程数当环境常量，错过延迟隐藏档位",
  "mechanism": "官方 __launch_bounds__ 档位：257–512→64 寄存器、513–1024→32、1025–2048→16。先估算主路径局部变量/累加器/地址索引，再选候选档；同一 kernel 编译 1024/2048 双实例，按 tail 路由：tail<1024 或 >8192 用 2048，1024≤tail≤8192 用 1024。改档同步 warp 数/scratch/步长；2048 档的跨 warp 扫描要支持 32–64 warp。",
  "principle": "SIMT 寄存器文件按线程数均分；线程多延迟隐藏好但每线程寄存器少。线程档是 tiling 旋钮，不是环境常量。",
  "operator_scope": "SIMT/__simt_vf__ 核函数，瓶颈为依赖链或访存延迟",
  "operator_class": "",
  "op": "seed",
  "applicability": {
    "required_conditions": [
      "kernel 为 SIMT",
      "线程局部变量能装进目标档位",
      "可按 mode/shape 路由"
    ],
    "excluded_conditions": [
      "复杂模式已确认 32 寄存器会 spill",
      "改档破坏 warp/scratch/步长且未同步",
      "纯原子吞吐受限"
    ],
    "constraints": [
      "至少测 1024/2048 两档",
      "双实例按 shape 路由",
      "2048 档支持 32–64 warp 扫描",
      "小 case 可能微降"
    ]
  },
  "applicability_boundary": "",
  "feature_signature": {
    "bottleneck": [
      "latency-bound",
      "low-occupancy"
    ],
    "pattern": "simt-kernel",
    "reduce_mode": "mixed",
    "structure": [
      "launch-bounds",
      "dual-tier",
      "shape-route"
    ],
    "dtypes": []
  },
  "implementation_steps": [
    "估算主路径寄存器需求",
    "编译 1024/2048 双实例",
    "按 tail 分组做同 case A/B",
    "路由：tail<1024 或 >8192→2048，否则 1024",
    "检查 spill 与精度 20/20"
  ],
  "verification": {
    "correctness": [
      "全量 20/20",
      "确认无 spill"
    ],
    "performance": [
      "相对基线有可测提升；具体数值不在卡内给出",
      "关键 shape 不回归"
    ],
    "rollback_signals": [
      "spill/精度失败/小 case 回归时按 mode 回退"
    ]
  },
  "risks": [
    "线程多导致寄存器压力",
    "双实例增加代码体积",
    "小 case 可能微降"
  ],
  "gain": "已验证：该机制在目标 A5 算子族上有效，精度 20/20。",
  "generality": "common",
  "classification": "validated_strategy",
  "created": "2026-11-11",
  "evidence": [
    {
      "run_id": "<run-id>",
      "operator_class": "simt-kernel",
      "status": "accepted",
      "speedup": "validated",
      "precision": "20/20 PASS"
    }
  ],
  "related_anti_patterns": [
    "simt-group-occupancy-and-elementwise-replacement"
  ],
  "related_seed_ids": [],
  "instance_ids": [],
  "source": "benchmark-extraction",
  "status": "validated",
  "provenance": {
    "skill": "validated-optimization-extraction-20261111"
  }
}
-->

# 性能优化策略：SIMT 线程档选择与按 shape 双档路由

单一优化点：按每线程寄存器预算选 launch_bounds 档；至少测 1024/2048，并允许双实例按 shape 路由。

## 1. 原理

SIMT 寄存器文件按线程数均分；线程多延迟隐藏好但每线程寄存器少。线程档是 tiling 旋钮，不是环境常量。

实现机制：官方 __launch_bounds__ 档位：257–512→64 寄存器、513–1024→32、1025–2048→16。先估算主路径局部变量/累加器/地址索引，再选候选档；同一 kernel 编译 1024/2048 双实例，按 tail 路由：tail<1024 或 >8192 用 2048，1024≤tail≤8192 用 1024。改档同步 warp 数/scratch/步长；2048 档的跨 warp 扫描要支持 32–64 warp。

## 2. 性能问题模式

- 优化目标：避免把线程数当环境常量，错过延迟隐藏档位
- 适用数据流：SIMT/__simt_vf__ 核函数，瓶颈为依赖链或访存延迟
- Feature signature：`{"bottleneck": ["latency-bound", "low-occupancy"], "pattern": "simt-kernel", "reduce_mode": "mixed", "structure": ["launch-bounds", "dual-tier", "shape-route"], "dtypes": []}`

## 3. 正确性红线

- 全量 20/20
- 确认无 spill

资源与硬件约束：

- 至少测 1024/2048 两档
- 双实例按 shape 路由
- 2048 档支持 32–64 warp 扫描
- 小 case 可能微降

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- kernel 为 SIMT
- 线程局部变量能装进目标档位
- 可按 mode/shape 路由

不适用：

- 复杂模式已确认 32 寄存器会 spill
- 改档破坏 warp/scratch/步长且未同步
- 纯原子吞吐受限

## 5. 实施步骤

1. 估算主路径寄存器需求
2. 编译 1024/2048 双实例
3. 按 tail 分组做同 case A/B
4. 路由：tail<1024 或 >8192→2048，否则 1024
5. 检查 spill 与精度 20/20

## 6. LLM 前置问题

- 目标实现是否满足：kernel 为 SIMT？
- 目标实现是否满足：线程局部变量能装进目标档位？
- 目标实现是否满足：可按 mode/shape 路由？
- 是否命中排除条件：复杂模式已确认 32 寄存器会 spill？
- 是否命中排除条件：改档破坏 warp/scratch/步长且未同步？
- 是否命中排除条件：纯原子吞吐受限？

## 7. 验收标准

正确性：

- 全量 20/20
- 确认无 spill

性能：

- 相对基线有可测提升；具体数值不在卡内给出
- 关键 shape 不回归

回滚信号：

- spill/精度失败/小 case 回归时按 mode 回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related strategies：simt-group-occupancy-and-elementwise-replacement

- v1-blind-thread-tier-20261111-01（status=accepted, operator_class=simt-kernel, speedup=validated, precision=20/20 PASS）

## 检索卡（短卡）

动作：按每线程寄存器预算选__launch_bounds__档位（512/1024/2048），至少测1024/2048；同kernel双实例按shape路由；2048档支持32–64 warp扫描。
适用：SIMT核函数，瓶颈为依赖链/访存延迟。
限制：复杂模式可能spill；小case可能微降；双实例增加代码体积。
范围：SIMT核的线程档选择。
检索词：launch_bounds、1024/2048、双实例、按shape路由、32–64 warp、spill。
机会：512→1024与1024/2048双档路由在目标shape上有效。
代价：寄存器压力；需按模式/形状校准。
