---
type: API
title: TilingData结构注册
description: 注册定义的TilingData结构体并和自定义算子绑定。具体使用说明请参考调用示例。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_data_structure_register/TilingData_struct_register.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# TilingData结构注册

## 功能说明
注册定义的TilingData结构体并和自定义算子绑定。具体使用说明请参考调用示例。
## 函数原型
## 参数说明
参数说明
## 约束说明
-   使用时需要包含头文件register/tilingdata_base.h。
-   中间结构体和定制tilingkey结构体需注意op_type命名规则，具体见调用示例。
-   算子定制tilingkey结构体需保证必须注册op_type默认结构体。
-   tiling结构体是全局属性，需注意应通过结构体名作为全局唯一标记，不同算子若注册同名不同结构tiling结构体则会发生未定义行为。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《TilingData结构注册》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《TilingData结构注册》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [REGISTER_TILING_DEFAULT 取小档致 NaN](../../../runbooks/compilation/register_tiling_default_nan.md)（`exemplifies`）：REGISTER_TILING_DEFAULT 取小档致 NaN 与《TilingData结构注册》的实质衔接是：REGISTER_TILING_DEFAULT 决定 opParaSize，必须覆盖最大 TilingData struct；注册宏、GET 宏、host/kernel 结构、SetDataSize 与追加越界卡描述同一 buffer 尺寸链。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：REGISTER_TILING_DEFAULT 多 struct 冲突 与《TilingData结构注册》的实质衔接是：一个算子只能有一个 REGISTER_TILING_DEFAULT struct；新分支须按 TilingKey 注册，GET 宏、Host/Kernel struct、SetDataSize 与冲突故障共同约束 buffer 和 key。
- [TilingData 须 host 与 kernel 各定义一份](../../../runbooks/compilation/tilingdata_host_kernel.md)（`exemplifies`）：TilingData 须 host 与 kernel 各定义一份：本故障来自host不可见kernel侧struct；TilingData定义/注册/属性传递卡给出正式契约，struct.h include与手写头遮蔽、rebase字段失配卡覆盖同一双侧类型同步链的具体失败。 目标卡《TilingData结构注册》补充：注册定义的TilingData结构体并和自定义算子绑定。具体使用说明请参考调用示例。
- [通过TilingData传递属性信息](../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_data_attributes.md)（`explains`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“TilingData结构注册”明确注册定义的TilingData结构体并和自定义算子绑定。具体使用说明请参考调用示例。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [TilingData结构定义](tiling_data_struct_definition.md)（`same_topic`）：必须先用定义宏声明 TilingData 成员与布局，再由注册宏把该结构绑定到 op_type。
- [Tiling数据结构注册](tiling_data_structure_register.md)（`same_topic`）：Tiling数据结构注册 与《TilingData结构注册》的实质衔接是：TilingData 定义、注册、读取宏、尺寸限制与三张冲突/截断故障卡共同覆盖 host→kernel 数据契约。
<!-- cannbot:related:end -->
