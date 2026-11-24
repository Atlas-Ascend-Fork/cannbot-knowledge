---
type: Optimization
title: 独立行逐lane映射与组级融合流水
description: 把逐行跨lane归约和多阶段VF调用改为一行一lane的组级计算，按列镜像衔接生产、处理与写回。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/independent-row-lane-fused-pipeline.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "independent-row-lane-fused-pipeline",
  "name": "独立行逐lane映射与组级融合流水",
  "classification": "validated_strategy",
  "slug": "independent-row-lane-fused-pipeline",
  "generality": "dataflow_pattern",
  "feature_signature": {
    "pattern": "independent-row-lane-fused-pipeline"
  },
  "verification": {
    "status": "validated_as_combination",
    "attribution": "行组布局与调用粒度作为组合验证，未拆分二者的独立贡献；迁移收益需重新测量。",
    "migration_required": true
  }
}
-->

# 性能优化策略：独立行逐lane映射与组级融合流水

> 组合优化点：把逐行跨lane归约和分阶段VF调用，改为一行一lane的组级计算，使有依赖的阶段在同一有界行组内衔接。

## 1. 原理

独立行沿同一列轴执行相同递推时，可令一个lane对应一行，每步Gather相同列的多行元素，按lane独立维护行状态。行内的标量结果不再依赖反复跨lane归约，向量指令同时推进多个独立状态。

把生产、中间处理和写回组织在同一个组级VF内，摊薄逐行调用、mask和指针准备成本。按列距对齐的片上镜像供后续阶段使用；生产者与消费者通过明确的LocalMemBar闭合依赖，不能把同一VF误认为天然没有同步需求。

布局映射、VF粒度、工作集和并行组数共同构成组合动作。行组不是越大越好：扩大行组会增加列缓冲、输出暂存和寄存器占用，并可能减少并行组数。

## 2. 性能问题模式

- 窄行不能充分利用向量lane，且独立行数量充足。
- 每行反复调用VF并执行跨lane归约、广播或中间量读写。
- 输入已经片上驻留，固定调度和指令发射仍占主要开销。

## 3. 正确性红线

- 先证明行之间无依赖、写入互不重叠，更新全部布局生产者与消费者。
- 列距按目标对齐粒度向上取整；以实际尾组行数设置mask。所有Gather索引均须满足宽度和地址范围，不能只依赖输出mask。
- 缓冲预算计入输入、列镜像、输出、索引、guard和所有并发驻留状态；空行域不发起计算。
- 跨行布局可能改变行内浮点结合顺序；只在精度契约允许时采用，严格位一致路径保留原归约组织。
- 分组数和每核组数采用向上取整，保证有效行恰好覆盖一次；启核数不得超过有效独立组数。

## 4. 泛化条件

适用：多行彼此独立、列向操作同构且逐行VF或水平归约开销明显；寄存器、片上空间和索引宽度允许成组处理。

不适用或需回退：行间依赖、组数不足、布局转换或列循环更贵、浮点重排不被允许，或者扩大工作集造成资源回退。

## 5. 实施步骤

1. 定位逐行调用和跨lane合并，记录原状态、输出布局与访问范围。
2. 依据目标lane数、缓冲预算及索引宽度选择有界行组，不照搬固定行数。
3. 构造逐lane行偏移，迁移阶段与全部消费者，补齐尾组、空域和RAW/WAR屏障。
4. 按实际组数分配独立任务；资源或工作量边界保留原路径。
5. 分别检查VF次数、向量利用、资源占用和总设备耗时，再决定是否采纳。

## 6. LLM 前置问题

- 各行的状态和写入是否真正独立？
- 布局变化是否改变浮点次序，精度契约是否许可？
- 尾lane即使被mask，实际索引和guard是否仍合法？
- 行组增加是否减少了可用并行组数？

## 7. 验收标准

正确性：保持原接口、精度阈值和输出布局，覆盖空域、尾部、容量边界、重复值和所有受影响分支。先验证语义与合法访问，再判断收益；不放宽阈值以迁就新路径。

性能：冻结前后源码和二进制，同设备、同输入、同工具链，依照配对测量协议比较设备Task Duration；每个输入域先取均值，再按约定跨域聚合，保留域内回归和剔除补测记录。迁移到新的资源、布局或数值域必须重新验证。

决策：资源、越界、同步或精度检查失败时修复或回退；没有可信收益时保留原路径。组合验证不能推出任何子动作独立有效。

## 8. 与相邻策略的边界

与[row-per-lane-packed-scan](row_per_lane_packed_scan.md)共享lane到行的映射思想，本策略增加多阶段消费者的组内衔接和资源约束；与[group-vf-shared-vector-compact-score-axis](group_vf_shared_vector_compact_score_axis.md)不同，不要求跨行共享只读向量，也不依赖下游结果轴紧凑化。

## 检索卡（短卡）

动作：把逐行跨lane归约和多阶段VF调用改为一行一lane的组级计算，按列镜像衔接生产、处理与写回。
适用：行独立且列向操作同构，逐行开销显著，片上容量和索引宽度允许成组。
限制：尾mask不能代替合法访问；列距对齐；浮点重排须获精度许可，组数不足时回退。
范围：独立行扫描、归约及其后续同构处理。
检索词：RegTensor、Gather、Scatter、VF、LocalMemBar、行组
机会：窄行lane闲置，逐行VF和跨lane合并反复支付固定成本。
代价：列缓冲与布局转换增加占用；行组扩大可能降低并行度。
