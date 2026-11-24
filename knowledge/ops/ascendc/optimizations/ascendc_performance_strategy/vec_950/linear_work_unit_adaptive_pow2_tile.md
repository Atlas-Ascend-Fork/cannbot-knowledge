---
type: Optimization
title: 线性工作单元与自适应二次幂 tile（规避跨步 2D 写约束）
description: 输出按连续地址切线性工作单元并用一维连续搬运；tile 按 UB 预算取最大二次幂自适应，避免跨步 2D 写约束导致的逐行小 DMA。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/linear-work-unit-adaptive-pow2-tile.md
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
      "保持原数值路径与索引顺序；非对齐单元须预留 32B guard"
    ],
    "excluded_conditions": [
      "输出本已连续且天然对齐，一维连续搬运即等价"
    ],
    "required_conditions": [
      "输出存在跨步写，或行字节数非 32B 对齐，2D 搬运描述符约束易触发退化"
    ]
  },
  "applicability_boundary": "",
  "classification": "lesson",
  "created": "2026-10-12",
  "evidence": [],
  "generality": "op_class",
  "id": "VEC-LINEAR-UNIT-ADAPTIVE-POW2-TILE",
  "implementation_steps": [
    "枚举输出为连续（线性）工作单元",
    "按 UB 预算取最大二次幂 tile 并随形状自适应",
    "对齐段用纯 DataCopy、非对齐段用元素级 DataCopyPad 并留 32B guard",
    "核验数值路径、索引顺序与原容差不变"
  ],
  "instance_ids": [],
  "intent": "避免按 2D 形状跨步写出、受 2D 搬运描述符硬约束而退化为逐行小粒度 DMA。",
  "mechanism": "2D DataCopyPad 的 dstStride 须 32B 对齐、blockCount<=32；行字节非 32B 对齐时跨步 2D 写会退化为逐行 1D 双写（tiny DMA）。改为线性工作单元 + 自适应二次幂 tile：对齐段走纯 DataCopy，非对齐段走元素级 DataCopyPad 并预留 32B guard，从而不依赖跨步 2D 写。",
  "name": "线性工作单元与自适应二次幂 tile（规避跨步 2D 写约束）",
  "op": "seed",
  "operator_class": "",
  "operator_scope": "按 2D 形状跨步写出的规则切片/搬运类设备代码",
  "principle": "把输出按连续（线性）地址切成工作单元，单元内是连续内存，用一维 DataCopy/DataCopyPad 搬运；tile 按 UB 预算取最大二次幂并随形状自适应。",
  "provenance": {
    "skill": "由 AOA_vs_BASE 8 算子根因分析（0017_cat_maximum）提炼"
  },
  "related_anti_patterns": [],
  "related_seed_ids": [],
  "risks": [
    "若对齐分支未经实测可能引入额外开销而无收益"
  ],
  "schema_version": 2,
  "slug": "linear-work-unit-adaptive-pow2-tile",
  "source": "skill",
  "status": "seed",
  "summary": "输出按连续地址切线性工作单元并用一维连续搬运；tile 按 UB 预算取最大二次幂自适应，避免跨步 2D 写约束导致的逐行小 DMA。",
  "verification": {
    "correctness": [
      "覆盖非 32B 对齐、质数/尾部 shape 与 buffer 紧邻布局，逐位或原容差通过"
    ],
    "performance": [
      "与跨步 2D 写路径同轮对照，确认事务数与耗时下降"
    ],
    "rollback_signals": [
      "对齐分支无收益或改变数值路径时回退原 2D 写路径"
    ]
  }
}
-->

# 性能优化策略：线性工作单元与自适应二次幂 tile（规避跨步 2D 写约束）

单一优化点：输出按连续地址切线性工作单元并用一维连续搬运；tile 按 UB 预算取最大二次幂自适应，避免跨步 2D 写约束导致的逐行小 DMA。

## 1. 原理

把输出按连续（线性）地址切成工作单元，单元内是连续内存，用一维 DataCopy/DataCopyPad 搬运；tile 按 UB 预算取最大二次幂并随形状自适应。

2D DataCopyPad 的 dstStride 须 32B 对齐、blockCount<=32；行字节非 32B 对齐时跨步 2D 写会退化为逐行 1D 双写（tiny DMA）。改为线性工作单元 + 自适应二次幂 tile：对齐段走纯 DataCopy，非对齐段走元素级 DataCopyPad 并预留 32B guard，从而不依赖跨步 2D 写。

## 2. 性能问题模式

- 优化目标：避免按 2D 形状跨步写出、受 2D 搬运描述符硬约束而退化为逐行小粒度 DMA。
- 适用数据流：按 2D 形状跨步写出的规则切片/搬运类设备代码
- Feature signature：`{}`

## 3. 正确性红线

- 若对齐分支未经实测可能引入额外开销而无收益

资源与硬件约束：

- 保持原数值路径与索引顺序；非对齐单元须预留 32B guard

## 4. 泛化条件

- 策略作用域：op_class

适用：

- 输出存在跨步写，或行字节数非 32B 对齐，2D 搬运描述符约束易触发退化

不适用：

- 输出本已连续且天然对齐，一维连续搬运即等价

## 5. 实施步骤

1. 枚举输出为连续（线性）工作单元
2. 按 UB 预算取最大二次幂 tile 并随形状自适应
3. 对齐段用纯 DataCopy、非对齐段用元素级 DataCopyPad 并留 32B guard
4. 核验数值路径、索引顺序与原容差不变

## 6. LLM 前置问题

- 目标实现是否满足：输出存在跨步写，或行字节数非 32B 对齐，2D 搬运描述符约束易触发退化？
- 是否命中排除条件：输出本已连续且天然对齐，一维连续搬运即等价？

## 7. 验收标准

正确性：

- 覆盖非 32B 对齐、质数/尾部 shape 与 buffer 紧邻布局，逐位或原容差通过

性能：

- 与跨步 2D 写路径同轮对照，确认事务数与耗时下降

回滚信号：

- 对齐分支无收益或改变数值路径时回退原 2D 写路径

## 8. 分类与证据

- Classification：`lesson`
- Generality：`op_class`
- Related anti-patterns：无

- 尚无归档证据（provenance：由 AOA_vs_BASE 8 算子根因分析（0017_cat_maximum）提炼）。

## 检索卡（短卡）

动作：把输出按连续地址切成线性工作单元，用一维连续 DataCopy/DataCopyPad 搬运；tile 按 UB 预算取最大二次幂并随形状自适应
适用：输出跨步写或行字节非 32B 对齐，2D 搬运描述符约束易致逐行小粒度退化
限制：保持原数值路径与索引顺序；非对齐单元走元素级 DataCopyPad 并预留 32B guard
范围：跨 operator class 的 GM 规则切片写入或搬出
检索词：线性工作单元、自适应二次幂 tile、DataCopyPad、blockCount、dstStride、跨步 2D 写
机会：按 2D 形状跨步写出非对齐时退化为逐行 tiny DMA，连续单元可规避该约束
代价：需额外 tile 尺寸推导与对齐分支，须核验不改变数值路径
