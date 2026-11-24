---
type: Optimization
title: 组级在线归一化的连续访问预取与输出缓冲解耦
description: 用组级在线状态缩短slot驻留，将独立任务与组展平成连续访问流，计算前预取后继，并拆分输入输出缓冲。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/online-group-visit-prefetch-dealiased-epilogue.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "online-group-visit-prefetch-dealiased-epilogue",
  "slug": "online-group-visit-prefetch-dealiased-epilogue",
  "name": "组级在线归一化的连续访问预取与输出缓冲解耦",
  "classification": "validated_strategy",
  "generality": "dataflow_pattern",
  "validation_scope": "组合机制已有验证；迁移须核对目标架构、工具链、数值契约和资源预算并重新配对测量",
  "feature_signature": {
    "pattern": "online-group-visit-prefetch-dealiased-epilogue",
    "structure": [
      "online-group-normalization",
      "cross-task-visit-prefetch",
      "dealiased-epilogue-lifetime"
    ]
  },
  "verification": {
    "status": "validated_as_combination",
    "attribution": "组合内子动作未逐项独立消融，不承诺单项或跨场景收益",
    "migration_required": true
  }
}
-->

# 性能优化策略：组级在线归一化的连续访问预取与输出缓冲解耦

> 组合优化点：用组级在线状态缩短驻留周期，将独立外层任务与组展平成连续访问流，在当前组计算前预取后继，并按生命周期拆分输入输出缓冲。

## 1. 原理

对于可分组等价计算的归约，一组输入完成局部统计、状态更新和加权消费后即可释放驻留slot。稳定指数归一化的一种状态更新形式为：

`m_new=max(m,max(s_group))`

`scale=exp(m-m_new)`

`l_new=l*scale+sum(exp(s_group-m_new))`

`a_new=a*scale+sum(exp(s_group-m_new)*v_group)`

每个独立外层任务的首组重置状态，最后一组完成后由最终状态产生输出。其它归约必须先推导自己的等价状态，不能照搬上述公式。

将“外层任务、组”展平成连续visit流，当前slot ready后、计算之前发起下一visit搬运；当前任务最后一组的后继可以是下一独立任务的首组，避免在嵌套循环边界断流。slot的释放点由真实最后消费者决定，通常晚于局部统计阶段。

输入暂存与输出回写使用独立缓冲：下一输入写入只需等待当前计算读完输入，下一输出覆盖则等待旧输出搬运完成。需同时调整依赖边；仅增加TBuf不能证明发生了重叠。

## 2. 性能问题模式

- 完整归约集合长期驻留，后继搬运只能在晚阶段开始。
- 已有双缓冲，但外层循环边界或提前保留slot缩短了重叠窗口。
- 原地复用输入输出，使下一输入加载等待上一输出回写，形成额外WAR串行边。

## 3. 正确性红线

- 先证明分组状态更新等价，核对初始哨兵、首组和任务边界重置；浮点重排仍需原精度门。
- slot在真实最后消费者结束后释放，不能在统计结束但加权消费未结束时复用。
- MTE2→V ready、V→MTE2 free、V→MTE3输出及MTE3→V覆盖与实际流水一致。
- 所有Set/Wait首尾闭合；尾组、空任务及没有后继visit时不得发起伪预取，退出前drain剩余事件。
- 输入释放等待最后V读，输出覆盖等待最后MTE3读；不得提前覆盖任一活跃缓冲。
- 双slot、独立输入输出、状态、scratch、行guard、对齐和事件共同满足真实预算。

## 4. 泛化条件

适用：外层任务独立；归约可稳定分组等价计算；有合法双slot与后继visit；额外缓冲和事件满足目标资源限制。

不适用或需回退：跨任务有依赖、不能分组等价、资源不足、仅单visit且固定开销占优，或状态可见性尚未证明。分组更小可能增加状态更新、VF和同步；分组更大可能挤压寄存器与可重叠任务数，需联合评估。

## 5. 实施步骤

1. 画出各slot、输入和输出的最后消费者，冻结原数据流和精度对照。
2. 推导组级状态更新、首组重置及任务结束输出，先验证数值等价和精度。
3. 按实际UB与事件预算布置双slot，展平外层任务与组的访问顺序，在当前计算前发后继预取。
4. 按生命周期拆分输入输出缓冲，分别维护输入的V→MTE2和输出的MTE3→V释放边。
5. 核对启动、稳态、尾组、最后任务和drain，联合调整分组与寄存器工作块。
6. 覆盖单组、多组、单任务、多任务和非整除尾部，精度通过后配对测量各受影响域。

## 6. LLM 前置问题

- 归约如何分组等价更新，任务间状态怎样重置？
- 下一visit最早何时可搬运，当前slot真正的最后消费者是谁？
- 缓冲拆分移除了哪条依赖边，新增了多少UB与事件？
- 跨外层边界的后继和最后一次访问的drain是否闭合？
- 分组变化是在扩大重叠窗口，还是只增加状态更新与VF成本？

## 7. 验收标准

正确性：保持接口语义与原精度阈值，覆盖尾部、容量边界、空域及策略涉及的状态和数值边界。使用正确性对照验证所有受影响路径，不仅验证主路径。

性能：冻结前后源码与二进制，在同设备、同输入、同构建配置下按配对测量协议比较设备Task Duration；先对相同输入域内的多次结果取均值，再按约定跨域聚合，并检查域内回归。

决策：精度、越界、资源或同步检查失败时先修复或回退；没有可信性能收益时保留原路径。组合已有验证不等于其中任一子动作独立有效，单独迁移子动作需要独立验证。

## 检索卡（短卡）

动作：用组级在线状态缩短slot驻留，将独立任务与组展平成连续访问流，计算前预取后继，并拆分输入输出缓冲。
适用：外层任务独立，归约可稳定分组等价计算，存在后继visit，双slot和独立缓冲满足UB及事件预算。
限制：首组与任务边界重置状态；slot等最后消费者；输入等V读完、输出等MTE3读完；末尾drain；无后继不预取。
范围：分组归约、在线状态更新、融合计算的跨阶段流水。
检索词：在线归一化、visit流、双缓冲、TBuf、MTE2、MTE3、WAR、drain。
机会：完整集合长驻留，外层边界中断预取，原地输入输出使下一加载等待上一回写。
代价：额外缓冲与事件管理；分组过小增加状态更新和VF调用，过大挤压资源及重叠对象。
