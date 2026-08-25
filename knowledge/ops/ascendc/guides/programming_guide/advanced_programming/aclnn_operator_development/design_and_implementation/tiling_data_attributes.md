---
type: Guide
title: 通过TilingData传递属性信息
description: 本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_data_attributes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 通过TilingData传递属性信息

本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。
本文以LeakyReluCustom的negative_slope属性为例，介绍如何通过TilingData将属性从Host侧传递至Kernel侧，包括在算子原型中声明属性、在Host侧读取属性并写入TilingData，以及在Kernel侧从TilingData中读取并使用该属性。TilingData的基础定义和写入方法见基本流程。
## 属性传递流程
属性传递流程如下：
只有Kernel运行时需要使用的结果才写入TilingData。如果属性只影响Host侧的切分、Block数量或TilingKey，Host侧完成计算后传递最终运行参数即可，不需要原样传递属性。
## 在算子原型中声明属性
LeakyReluCustom的计算语义为：当x>=0时y=x，当x<0时y=negative_slope*x。Host侧通过GetAttrs()返回本次调用的属性列表。GetAttrPointer(index)通过属性在列表中的位置读取对应的值，index按照原型中Attr的声明顺序从0开始编号。本例只声明了negative_slope一个属性，因此将它的索引定义为0。
negative_slope的取值在不同调用之间可能变化，因此TilingFunc需要读取本次调用的属性值，不能在Tiling实现中将其写成固定常量。
即使属性在原型中定义了默认值，读取后仍建议判空，避免索引、类型或工程版本不匹配时直接解引用无效指针。
### 属性类型对应关系
GetAttrPointer的模板参数需要与原型声明的属性类型一致。
原型属性接口：Host侧读取类型：适合写入TilingData的类型
.Bool(...)：bool：bool或明确宽度的整数
.Float(...)：float：float
.Int(...)：与接口约定一致的整数类型：按Kernel需求检查范围后转换
属性读取类型不匹配会导致数据解析错误。整数属性转换成uint32_t等更窄类型前，需要检查负数和溢出范围。
### 多属性场景
假设原型按以下顺序声明两个属性：
Host侧对应使用索引0和1：
新增、删除或调整属性顺序时，需要同步检查所有GetAttrPointer(index)调用。建议为索引定义具名常量，避免在Tiling函数中散落数字。
## Kernel侧使用属性
Kernel入口解析TilingData后，将属性字段传给Kernel实现类：
Init把negativeSlope保存为Kernel类成员。配套样例使用Maxs、Mins、Muls和Add组合实现LeakyRelu。
计算完成后再按Kernel基本流程把yLocal写回Global Memory。
