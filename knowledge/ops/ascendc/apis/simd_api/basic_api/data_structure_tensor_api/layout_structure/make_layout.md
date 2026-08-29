---
type: API
title: MakeLayout
description: 根据Shape和Stride构造Layout对象，描述数据张量在逻辑维度上的形状及各维步长信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/MakeLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MakeLayout

根据Shape和Stride构造Layout对象，描述数据张量在逻辑维度上的形状及各维步长信息。

构造Shape对象，用于描述数据的逻辑形状。支持传入多个维度值，也支持传入嵌套的Shape子结构以构造层次化Shape。

本接口组包含 MakeShape, MakeStride, MakePatternLayout，辅助接口包括 GetLayoutPattern。

返回值：返回Shape 对象。

约束：输入参数不可为空；输入的参数为正整数。；支持的数据类型包括：size_t、int等整数类型或者Std::Int类型。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [MakePatternLayout](make_pattern_layout.md)（`same_topic`）：“根据Shape和Stride构造Layout对象，描述数据张量在逻辑维度上的形状及各维步长信息。”与“根据 Shape、Stride、LayoutPattern 和 TraitType 构造带布局模式信息的 Layout 对象。”是双方正文中的具体合同。两端都由 Shape 与 Stride 构造 Layout，Pattern 版本额外携带 LayoutPattern 与 TraitType，互读可完成基础布局和模式布局的选型。
<!-- cannbot:related:end -->
