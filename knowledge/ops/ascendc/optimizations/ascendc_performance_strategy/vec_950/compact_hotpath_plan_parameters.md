---
type: Optimization
title: 裁剪设备热路径参数对象以减少线程栈物化
description: 把设备热路径传递的大型按值 Plan 改为必要标量参数，保留通用对象路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/compact-hotpath-plan-parameters.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "excluded_conditions": [
      "整对象确有必要或编译器已完成标量替换",
      "只存在核入口元数据装载成本"
    ],
    "required_conditions": [
      "设备热路径携带大型按值对象但只消费少数字段",
      "专用路径能完整判定布局与地址条件"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "thread-private-object-materialization",
      "by-value-plan-copy"
    ],
    "pattern": "compact-hotpath-plan-parameters",
    "structure": [
      "SIMT",
      "device-helper",
      "compact-scalar-parameters"
    ]
  },
  "generality": "pattern",
  "id": "COMPACT-HOTPATH-PLAN-PARAMETERS",
  "implementation_steps": [
    "按设备调用链列出实际消费字段，核对栈帧、复制指令和参数存活范围。",
    "建立专用入口或 helper，以必要标量替换完整 Plan；保持计算和同步顺序。",
    "用合法元数据分派专用路径，未覆盖布局继续使用通用对象路径。",
    "对照编译资源和生成代码确认对象及私有访存是否收缩，再测完整调用。"
  ],
  "intent": "细粒度 SIMT 循环反复携带完整 Plan；编译资源报告出现线程栈，生成代码包含对象复制或私有装载，而实际地址计算只用少数字段。",
  "mechanism": "对只消费少数字段的设备热路径，将大型按值参数对象替换为必要标量，减少线程私有对象与栈复制。",
  "name": "裁剪设备热路径参数对象以减少线程栈物化",
  "operator_scope": "设备热路径存在大对象物化或栈复制，且合法元数据可划出只需少数字段的专用路径。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "大型参数对象包含维度、步长与模式等字段，设备函数即便仅用其中少量字段，也可能受 ABI、取址和调用边界影响而物化线程私有副本。把热路径改为显式传递长度、基址与必要步长，可缩小对象存活范围并减少栈复制及私有访存。作用位置是设备函数和线程执行路径，区别于削减核入口的 GM 元数据读取。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "必要字段不能遗漏，标量的整数宽度、有符号性、溢出边界及地址单位必须与原路径一致",
    "布局、对齐、数据类型与范围不满足专用条件时回退",
    "不能仅凭 inline、强制内联或改成引用就认定对象消失；引用还受设备地址空间和调用约定约束"
  ],
  "schema_version": 2,
  "slug": "compact-hotpath-plan-parameters",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "把设备热路径传递的大型按值 Plan 改为必要标量参数，保留通用对象路径。",
  "verification": {
    "correctness": [
      "覆盖布局、步长、尾部与整数边界，专用和通用路径满足同一语义",
      "编译产物显示目标对象复制或线程私有访问减少，且完整调用耗时改善"
    ],
    "performance": [
      "栈大小变化本身不能替代性能验收；出现寄存器压力增大、越界或路径回退劣化时调整分派或恢复通用路径"
    ],
    "rollback_signals": [
      "全部字段都必要、对象已经被编译器标量替换，或瓶颈仅是核入口元数据装载",
      "新增入口和模板会增加代码体积与维护成本；标量过多也可能增加寄存器压力"
    ]
  }
}
-->

# 性能优化策略：裁剪设备热路径参数对象以减少线程栈物化

单一优化点：把设备热路径传递的大型按值 Plan 改为必要标量参数，保留通用对象路径。

## 1. 原理

大型参数对象包含维度、步长与模式等字段，设备函数即便仅用其中少量字段，也可能受 ABI、取址和调用边界影响而物化线程私有副本。把热路径改为显式传递长度、基址与必要步长，可缩小对象存活范围并减少栈复制及私有访存。作用位置是设备函数和线程执行路径，区别于削减核入口的 GM 元数据读取。

## 2. 性能问题模式

细粒度 SIMT 循环反复携带完整 Plan；编译资源报告出现线程栈，生成代码包含对象复制或私有装载，而实际地址计算只用少数字段。问题在对象传递成本时，增加并行线程可能同时放大私有存储流量。

## 3. 正确性红线

必要字段不能遗漏，标量的整数宽度、有符号性、溢出边界及地址单位必须与原路径一致。布局、对齐、数据类型与范围不满足专用条件时回退。不能仅凭 inline、强制内联或改成引用就认定对象消失；引用还受设备地址空间和调用约定约束。

## 4. 泛化条件

适用：设备热路径存在大对象物化或栈复制，且合法元数据可划出只需少数字段的专用路径。

不适用：全部字段都必要、对象已经被编译器标量替换，或瓶颈仅是核入口元数据装载。新增入口和模板会增加代码体积与维护成本；标量过多也可能增加寄存器压力。

## 5. 实施步骤

1. 按设备调用链列出实际消费字段，核对栈帧、复制指令和参数存活范围。
2. 建立专用入口或 helper，以必要标量替换完整 Plan；保持计算和同步顺序。
3. 用合法元数据分派专用路径，未覆盖布局继续使用通用对象路径。
4. 对照编译资源和生成代码确认对象及私有访存是否收缩，再测完整调用。

## 6. LLM 前置问题

- 成本位于线程热路径，还是每核入口装载？
- 哪些字段确实参与地址和边界计算，哪些可删除？
- 当前编译产物是否已消除对象？新参数是否增加寄存器或代码压力？

## 7. 验收标准

覆盖布局、步长、尾部与整数边界，专用和通用路径满足同一语义。编译产物显示目标对象复制或线程私有访问减少，且完整调用耗时改善。栈大小变化本身不能替代性能验收；出现寄存器压力增大、越界或路径回退劣化时调整分派或恢复通用路径。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：把设备热路径的大型按值Plan改为必要标量参数，保留通用对象路径。
适用：设备热路径存在大对象物化或栈复制，且合法元数据可划出仅需少数字段的专用路径。
限制：保留地址单位、整数宽度与溢出边界；不满足布局条件须回退；不能凭inline或引用断定消栈。
范围：SIMT设备函数及线程热路径参数传递。
检索词：Plan、ABI、SIMT、标量替换、线程栈、私有访存
机会：热循环反复携带完整对象，实际只用少数字段，却产生私有副本和栈复制。
代价：新增入口与模板增加维护和代码体积；过多标量可能增加寄存器压力。
