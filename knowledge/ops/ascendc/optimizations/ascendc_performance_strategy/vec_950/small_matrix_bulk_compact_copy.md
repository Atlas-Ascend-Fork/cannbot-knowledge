---
type: Optimization
title: 小方阵紧凑布局与整块搬运
description: 规则小方阵用紧凑连续布局 + 单条二维搬运；padded 槽位不适用；微 case 回退。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/small-matrix-bulk-compact-copy.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "schema_version": 2,
  "id": "F6",
  "slug": "small-matrix-bulk-compact-copy",
  "name": "小方阵紧凑布局与整块搬运",
  "summary": "规则小方阵用紧凑连续布局 + 单条二维搬运；padded 槽位不适用；微 case 回退。",
  "intent": "消除逐矩阵/逐行描述符与 padded lane 浪费",
  "mechanism": "UB 侧每矩阵 n×n 个 float 连续存放，一条二维 DataCopyPad 搬入整批行；VF 输入步长按紧凑步长派生；布局重排交给寄存器 Gather/Scatter。输出侧块间 stride 必须 32B 对齐。padded 槽位（32B/64B pitch > 行字节）下整块拷贝不可行；微 case 走回退。",
  "principle": "逐矩阵搬运的浪费是描述符随矩阵数线性增长和 padded 槽 lane 浪费；整块搬运把描述符数降为常数，但布局重排成本转移到寄存器。",
  "operator_scope": "固定小方阵、行距规则的 GM↔UB 搬运",
  "operator_class": "",
  "op": "seed",
  "applicability": {
    "required_conditions": [
      "矩阵行列固定、整块连续",
      "尾部 pad 可用掩码",
      "消费方能按实际落盘步幅计算"
    ],
    "excluded_conditions": [
      "padded 槽位（pitch > 行字节）",
      "输出块间 stride 非 32B 对齐",
      "索引驱动/非规则搬运",
      "微 case"
    ],
    "constraints": [
      "前置：紧凑布局；padded 槽位不可行",
      "输出块间 32B 对齐",
      "微 case 回退逐矩阵"
    ]
  },
  "applicability_boundary": "",
  "feature_signature": {
    "bottleneck": [
      "mte-descriptor-spray",
      "lane-waste"
    ],
    "pattern": "small-matrix-copy",
    "reduce_mode": "copy",
    "structure": [
      "bulk-copy",
      "compact-layout",
      "32b-align"
    ],
    "dtypes": []
  },
  "implementation_steps": [
    "把 UB 布局改为紧凑 n×n 连续",
    "用一条二维搬运搬入整批行",
    "VF 输入步长改紧凑步长，尾部加保护",
    "输出侧与打包布局一起改，核对 32B 对齐",
    "与逐矩阵路径逐 case A/B；微 case 回退"
  ],
  "verification": {
    "correctness": [
      "全量 20/20",
      "逐行核对 UB 布局/padding",
      "覆盖对齐/非对齐块长"
    ],
    "performance": [
      "相对基线有可测提升；具体数值不在卡内给出",
      "关键 shape 不回归"
    ],
    "rollback_signals": [
      "精度失败/行错位/微 case 回归时回退逐矩阵"
    ]
  },
  "risks": [
    "输出端单独合并易失败",
    "索引表/寄存器压力",
    "padded 槽位不适用"
  ],
  "gain": "已验证：该机制在目标 A5 算子族上有效，精度 20/20。",
  "generality": "common",
  "classification": "validated_strategy",
  "created": "2026-11-11",
  "evidence": [
    {
      "run_id": "<run-id>",
      "operator_class": "small-matrix-copy",
      "status": "accepted",
      "speedup": "validated",
      "precision": "20/20 PASS"
    }
  ],
  "related_anti_patterns": [
    "iterative-small-matrix-packed-layout"
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

# 性能优化策略：小方阵紧凑布局与整块搬运

单一优化点：规则小方阵用紧凑连续布局 + 单条二维搬运；padded 槽位不适用；微 case 回退。

## 1. 原理

逐矩阵搬运的浪费是描述符随矩阵数线性增长和 padded 槽 lane 浪费；整块搬运把描述符数降为常数，但布局重排成本转移到寄存器。

实现机制：UB 侧每矩阵 n×n 个 float 连续存放，一条二维 DataCopyPad 搬入整批行；VF 输入步长按紧凑步长派生；布局重排交给寄存器 Gather/Scatter。输出侧块间 stride 必须 32B 对齐。padded 槽位（32B/64B pitch > 行字节）下整块拷贝不可行；微 case 走回退。

## 2. 性能问题模式

- 优化目标：消除逐矩阵/逐行描述符与 padded lane 浪费
- 适用数据流：固定小方阵、行距规则的 GM↔UB 搬运
- Feature signature：`{"bottleneck": ["mte-descriptor-spray", "lane-waste"], "pattern": "small-matrix-copy", "reduce_mode": "copy", "structure": ["bulk-copy", "compact-layout", "32b-align"], "dtypes": []}`

## 3. 正确性红线

- 全量 20/20
- 逐行核对 UB 布局/padding
- 覆盖对齐/非对齐块长

资源与硬件约束：

- 前置：紧凑布局；padded 槽位不可行
- 输出块间 32B 对齐
- 微 case 回退逐矩阵

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 矩阵行列固定、整块连续
- 尾部 pad 可用掩码
- 消费方能按实际落盘步幅计算

不适用：

- padded 槽位（pitch > 行字节）
- 输出块间 stride 非 32B 对齐
- 索引驱动/非规则搬运
- 微 case

## 5. 实施步骤

1. 把 UB 布局改为紧凑 n×n 连续
2. 用一条二维搬运搬入整批行
3. VF 输入步长改紧凑步长，尾部加保护
4. 输出侧与打包布局一起改，核对 32B 对齐
5. 与逐矩阵路径逐 case A/B；微 case 回退

## 6. LLM 前置问题

- 目标实现是否满足：矩阵行列固定、整块连续？
- 目标实现是否满足：尾部 pad 可用掩码？
- 目标实现是否满足：消费方能按实际落盘步幅计算？
- 是否命中排除条件：padded 槽位（pitch > 行字节）？
- 是否命中排除条件：输出块间 stride 非 32B 对齐？
- 是否命中排除条件：索引驱动/非规则搬运？
- 是否命中排除条件：微 case？

## 7. 验收标准

正确性：

- 全量 20/20
- 逐行核对 UB 布局/padding
- 覆盖对齐/非对齐块长

性能：

- 相对基线有可测提升；具体数值不在卡内给出
- 关键 shape 不回归

回滚信号：

- 精度失败/行错位/微 case 回归时回退逐矩阵

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related strategies：iterative-small-matrix-packed-layout

- v3-cardonly-bulk-20261111-01（status=accepted, operator_class=small-matrix-copy, speedup=validated, precision=20/20 PASS）

## 检索卡（短卡）

动作：规则小矩阵用紧凑连续布局+单条二维DataCopyPad整块搬运，布局重排交给寄存器Gather/Scatter；padded槽位下不要用；微case回退。
适用：固定小方阵、行距规则、整块连续且尾部pad可掩码。
限制：padded槽位（pitch>行字节）不可行；输出块间stride必须32B对齐；微case可能回退。
范围：小矩阵GM↔UB的整块搬运。
检索词：整块Copy、紧凑布局、32B对齐、padded槽位、Gather/Scatter、微case回退。
机会：输入整块搬运在目标shape上有效。
代价：输出单独做易失败；索引表成本；小shape回退。
