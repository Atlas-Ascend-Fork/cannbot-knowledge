---
type: Optimization
title: 组数/核数占用与 elementwise 替换 packed
description: 先算 G=B/64 与核数 C；G≥C/4 时减到 G 核（1 组/核）并实测 elementwise，禁止纸面排除。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/simt-group-occupancy-and-elementwise-replacement.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "schema_version": 2,
  "id": "F3",
  "slug": "simt-group-occupancy-and-elementwise-replacement",
  "name": "组数/核数占用与 elementwise 替换 packed",
  "summary": "先算 G=B/64 与核数 C；G≥C/4 时减到 G 核（1 组/核）并实测 elementwise，禁止纸面排除。",
  "intent": "去掉跨 lane 归约链，让发射单元不再等待",
  "mechanism": "矩阵元素数（n²）个位置寄存器、lane=batch，所有运算逐 lane elementwise，无跨 lane 归约。并行度=G=B/64 个组；G<C/4 才算严重不足，G≥C/4 时把核数减到 G（1 组/核），不要 2 组/核（实测更慢）。必须对 B=512/1024 实际跑 elementwise vs packed 的同 case A/B。",
  "principle": "packed 路径每 4 个矩阵一条跨 lane 归约链，发射单元在链上等待；elementwise 把 ops/矩阵降到 1.0，但需要 n² 个位置寄存器，且 lane 部分填充时指令数不变。",
  "operator_scope": "小矩阵多 batch、跨 lane 归约链成为瓶颈",
  "operator_class": "",
  "op": "seed",
  "applicability": {
    "required_conditions": [
      "n² 个位置寄存器可装下",
      "无跨 lane 归约需求",
      "G/C 可路由"
    ],
    "excluded_conditions": [
      "n 大、位置寄存器放不下",
      "必须跨 lane 归约",
      "G<C/4 且减核后仍不足"
    ],
    "constraints": [
      "lane 部分填充：指令仍按 64 lane 发射，有效吞吐 b/64",
      "优先 G 核（1 组/核）；2G（2 组/核）通常更慢",
      "必须实测 A/B，不能只纸面估算"
    ]
  },
  "applicability_boundary": "",
  "feature_signature": {
    "bottleneck": [
      "cross-lane-reduction-chain",
      "occupancy"
    ],
    "pattern": "batch-lane-elementwise",
    "reduce_mode": "elementwise",
    "structure": [
      "position-registers",
      "group-count",
      "mandatory-ab"
    ],
    "dtypes": []
  },
  "implementation_steps": [
    "算 G=B/64、C=核数；G<C/4 才算严重",
    "G≥C/4：把核数减到 G，每核 1 组",
    "把矩阵位置映射到寄存器、batch 映射到 lane",
    "对 B=512/1024 实测 elementwise vs packed（16/8/64 核三档）",
    "逐 n A/B，n 大回退 packed"
  ],
  "verification": {
    "correctness": [
      "全量 20/20",
      "每个 n 的模板实例数值穿刺",
      "组间/尾组正确"
    ],
    "performance": [
      "相对基线有可测提升；具体数值不在卡内给出",
      "关键 shape 不回归"
    ],
    "rollback_signals": [
      "实测更慢或寄存器不足时回退 packed；记录实测数据"
    ]
  },
  "risks": [
    "位置寄存器不足",
    "模板实例静默失效",
    "2 组/核更慢"
  ],
  "gain": "已验证：该机制在目标 A5 算子族上有效，精度 20/20。",
  "generality": "common",
  "classification": "validated_strategy",
  "created": "2026-11-11",
  "evidence": [
    {
      "run_id": "<run-id>",
      "operator_class": "small-matrix-iteration",
      "status": "accepted",
      "speedup": "validated",
      "precision": "20/20 PASS"
    }
  ],
  "related_anti_patterns": [
    "iterative-small-matrix-packed-layout",
    "micro-shape-half-core-two-tiles"
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

# 性能优化策略：组数/核数占用与 elementwise 替换 packed

单一优化点：先算 G=B/64 与核数 C；G≥C/4 时减到 G 核（1 组/核）并实测 elementwise，禁止纸面排除。

## 1. 原理

packed 路径每 4 个矩阵一条跨 lane 归约链，发射单元在链上等待；elementwise 把 ops/矩阵降到 1.0，但需要 n² 个位置寄存器，且 lane 部分填充时指令数不变。

实现机制：矩阵元素数（n²）个位置寄存器、lane=batch，所有运算逐 lane elementwise，无跨 lane 归约。并行度=G=B/64 个组；G<C/4 才算严重不足，G≥C/4 时把核数减到 G（1 组/核），不要 2 组/核（实测更慢）。必须对 B=512/1024 实际跑 elementwise vs packed 的同 case A/B。

## 2. 性能问题模式

- 优化目标：去掉跨 lane 归约链，让发射单元不再等待
- 适用数据流：小矩阵多 batch、跨 lane 归约链成为瓶颈
- Feature signature：`{"bottleneck": ["cross-lane-reduction-chain", "occupancy"], "pattern": "batch-lane-elementwise", "reduce_mode": "elementwise", "structure": ["position-registers", "group-count", "mandatory-ab"], "dtypes": []}`

## 3. 正确性红线

- 全量 20/20
- 每个 n 的模板实例数值穿刺
- 组间/尾组正确

资源与硬件约束：

- lane 部分填充：指令仍按 64 lane 发射，有效吞吐 b/64
- 优先 G 核（1 组/核）；2G（2 组/核）通常更慢
- 必须实测 A/B，不能只纸面估算

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- n² 个位置寄存器可装下
- 无跨 lane 归约需求
- G/C 可路由

不适用：

- n 大、位置寄存器放不下
- 必须跨 lane 归约
- G<C/4 且减核后仍不足

## 5. 实施步骤

1. 算 G=B/64、C=核数；G<C/4 才算严重
2. G≥C/4：把核数减到 G，每核 1 组
3. 把矩阵位置映射到寄存器、batch 映射到 lane
4. 对 B=512/1024 实测 elementwise vs packed（16/8/64 核三档）
5. 逐 n A/B，n 大回退 packed

## 6. LLM 前置问题

- 目标实现是否满足：n² 个位置寄存器可装下？
- 目标实现是否满足：无跨 lane 归约需求？
- 目标实现是否满足：G/C 可路由？
- 是否命中排除条件：n 大、位置寄存器放不下？
- 是否命中排除条件：必须跨 lane 归约？
- 是否命中排除条件：G<C/4 且减核后仍不足？

## 7. 验收标准

正确性：

- 全量 20/20
- 每个 n 的模板实例数值穿刺
- 组间/尾组正确

性能：

- 相对基线有可测提升；具体数值不在卡内给出
- 关键 shape 不回归

回滚信号：

- 实测更慢或寄存器不足时回退 packed；记录实测数据

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related strategies：iterative-small-matrix-packed-layout、micro-shape-half-core-two-tiles

- v4-cardonly-elementwise-20261111-01（status=accepted, operator_class=small-matrix-iteration, speedup=validated, precision=20/20 PASS）

## 检索卡（短卡）

动作：batch-per-lane先算G=B/64与核数C；G<C/4才算严重，G≥C/4减到G核（1组/核），不要2组/核；必须实测elementwise vs packed。
适用：小矩阵多batch，跨lane归约链成为发射瓶颈。
限制：lane部分填充时指令数不变、有效吞吐b/64；2组/核实测更慢；n²位置寄存器放不下则不可用。
范围：batch-per-lane的组数/核数选择与packed替换。
检索词：G=B/64、1组/核、lane部分填充、elementwise、跨lane链、强制A/B。
机会：elementwise在B=512/1024上实测有效；必须实测对照。
代价：寄存器预算；n大不可用；需逐shape实测。
