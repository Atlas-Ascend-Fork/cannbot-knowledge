---
type: Optimization
title: 连续广播段的整体地址折叠
description: 由完整形状和步幅证明连续非平凡段，将整组广播坐标分解折叠并消去退化步骤。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/contiguous-broadcast-run-offset-collapse.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "CONTIGUOUS-BROADCAST-RUN-OFFSET-COLLAPSE",
  "slug": "contiguous-broadcast-run-offset-collapse",
  "name": "连续广播段的整体地址折叠",
  "classification": "validated_strategy",
  "generality": "op_class",
  "phase": [
    "design",
    "tuning"
  ],
  "revision": "2026-11-09-blind-feedback-v2",
  "evidence_policy": "具名来源与测量由独立证据台账保存，修订指导本身不宣称新增性能验证。"
}
-->

# 连续广播段的整体地址折叠

## 原理与适用条件

从两侧完整形状、物理步幅和广播映射证明地址关系。若一侧按输出连续访问，另一侧的非平凡维构成无孔洞的连续段，可将逐维坐标分解折叠为少量周期和段内位置运算。优化机会在于消除整组分解，只有逐维快除替换时仍是另一种机制。

例如对连续源形状 `[1, L, 1]` 广播到 `[O, L, R]`，以输出线性下标 `i` 计，源段内元素偏移是 `(i // R) % L`。在没有对应重复或下标已限制到段内时，可继续省掉无用运算。多个非平凡维能否合并，要以实际步幅和完整输出区间证明；同样的逻辑 shape 不能代替物理连续性检查。

## 正确性红线

- 对每个命中形状证明折叠地址与原映射逐元素一致，包含外层基址、维度交换、标量及长度为一的维。内部广播孔洞、非连续视图、双侧同时扩展未证明时走通用路径。
- 形状乘积、周期、段内下标、字节偏移和中间运算必须在实际计算类型中合法。只检查最终偏移不足以证明中间乘积不会溢出。
- 路由依据合法元数据，不依赖测试身份或默认布局猜测；尾块和向量访问不得越界。若与算术改写组合，仍保持接口的数值、类型、别名与输出契约。

## 实施与代价

先从通用映射推导折叠谓词、周期及段内公式，把连续、标量、可折叠广播和通用广播的地址状态分别列清。将证明后的简化移出每元素路径；必要时隔离初始化和入口实例，避免未命中域也携带无用的元数据与活跃状态。

对比实际少掉的地址运算和新增分派、元数据、代码体积。优化可与窄域计算或线程预算组合，但不能将整体收益拆给折叠。回测左右操作数交换、内部孔洞、双侧扩展、索引边界及尾块；未命中路径源码相同仍需检查生成资源和实际耗时。

## 检索卡（短卡）

动作：由完整形状和步幅证明连续非平凡段，将整组广播坐标分解折叠并消去退化步骤。
适用：一侧连续，另一侧非平凡维构成无孔洞连续段。
限制：孔洞、双侧扩展及宽索引另证；公共入口变化须回测未命中域。
范围：重复地址生成与广播路由。
检索词：连续段、地址折叠、广播、热路径隔离、域外回测
机会：消去整段分解；可与算术、窄域和线程优化组合。
代价：元数据、实例和入口资源可能引发域外退化。
