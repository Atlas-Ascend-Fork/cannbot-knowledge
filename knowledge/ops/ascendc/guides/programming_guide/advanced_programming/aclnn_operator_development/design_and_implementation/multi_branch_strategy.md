---
type: Guide
title: 多分支策略
description: 本文属于扩展内容，介绍同一个算子需要根据dtype、shape或属性执行不同计算流程时，如何使用TilingKey或Kernel模板组织多个Kernel分支。TilingKey使用数字标识分支，适合分支数量较少、含义稳定的场景；Kernel模板使用具名参数描述分支，适合由多个维度共同决定分支的场景。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/multi_branch_strategy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 多分支策略

本文属于扩展内容，介绍同一个算子需要根据dtype、shape或属性执行不同计算流程时，如何使用TilingKey或Kernel模板组织多个Kernel分支。TilingKey使用数字标识分支，适合分支数量较少、含义稳定的场景；Kernel模板使用具名参数描述分支，适合由多个维度共同决定分支的场景。
本文分别说明两种方式的使用原因、Host与Kernel侧的对应关系以及接入步骤。
## 为什么需要多分支
普通的运行时分支会将所有处理逻辑保留在同一个Kernel中：
单次执行虽然只会进入其中一个分支，但两个分支的代码都属于同一个Kernel。分支代码较大时，会增加指令缓存压力和Scalar侧的控制开销。
使用TilingKey后，可以将分支条件变为编译期常量：
编译时框架会自动识别TilingKey并编译多个Kernel入口函数，将条件判断进行常量折叠，消除运行时的分支判断开销。
增加分支前，还需要判断差异是否确实需要独立Kernel实现：
分支维度：Host侧判断依据：典型差异
dtype：context->GetInputDesc()、context->GetOutputDesc()：计算类型、搬运粒度、精度策略
shape：context->GetInputShape()：小shape直算、大shape分块、尾块处理
属性：context->GetAttrs()：算法模式、维度、开关
format：输入输出描述：数据组织和搬运方式
如果不同场景只影响Tile大小、Block数量等运行参数，而Kernel计算流程不变，只需要在TilingData中传递不同参数，不必增加Kernel分支。只有计算流程、数据类型实例或代码体积确实不同，才需要使用TilingKey或Kernel模板。
## 使用TilingKey选择分支
TilingKey使用非负整数标识Kernel分支。Host侧通过SetTilingKey选择本次执行的key，Kernel侧通过TILING_KEY_IS(key)声明与该key对应的分支。
### Host侧设置TilingKey
TilingKey只负责选择Kernel计算分支，并不要求每个分支使用不同的TilingData。多个分支需要的运行参数结构相同时，可以共用一个TilingData。下面根据输入数据量选择不同分支，并通过同一个TilingData传递参数：
### Kernel侧声明分支
在核函数中通过TILING_KEY_IS选择计算分支：
### 为特定分支使用不同TilingData
只有某个分支的字段集合或布局与默认结构体不同时，才需要为该TilingKey注册单独的TilingData类型。例如，key 1使用默认的TilingData，key 2使用TilingData1：
使用REGISTER_TILING_FOR_TILINGKEY时，必须同时通过REGISTER_TILING_DEFAULT注册默认结构体。Host侧也需要在key 2分支中调用GetTilingData()写入数据，保证两侧类型和字段布局一致。
