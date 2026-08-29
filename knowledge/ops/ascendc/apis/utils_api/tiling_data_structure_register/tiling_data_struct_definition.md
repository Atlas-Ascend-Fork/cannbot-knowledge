---
type: API
title: TilingData结构定义
description: 定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_data_structure_register/TilingData_struct_definition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# TilingData结构定义

## 功能说明
定义一个TilingData的类，添加所需的成员变量（TilingData字段），用于保存所需TilingData参数。完成该TilingData类的定义后，该类通过继承TilingDef类（用来存放、处理用户自定义Tiling结构体成员变量的基类）提供以下接口：
-   set_\{field_name\}接口：用于设置TilingData类的字段值，field_name为定义TilingData类时添加的字段名。
-   get_\{field_name\}接口：用于获取字段名为field_name的字段值。
-   SaveToBuffer接口：完成TilingData的序列化和保存。
-   GetDataSize接口：获取TilingData的长度。
-   CheckAlignAndGenPlaceHolder：该接口是内部关联接口，用于框架侧检查Tiling结构体中成员变量是否满足字节对齐要求，并对不对齐的变量进行补齐，开发者无需关注。
-   SetDataPtr接口：该接口为预留接口，开发者无需关注。
## 函数原型
-   定义一个TilingData类
-   添加通用数据类型的TilingData字段
-   添加数组类型的TilingData字段，数组的元素数据类型为通用数据类型
-   添加结构体类型的TilingData字段
-   定义结束
## 参数说明
BEGIN_TILING_DATA_DEF参数说明
TILING_DATA_FIELD_DEF参数说明
TILING_DATA_FIELD_DEF_ARR参数说明
TILING_DATA_FIELD_DEF_STRUCT参数说明
## 约束说明
-   使用时需要包含头文件register/tilingdata_base.h。
-   TILING_DATA_FIELD_DEF和TILING_DATA_FIELD_DEF_ARR中定义的变量，仅支持int8_t, uint8_t, int16_t, uint16_t, int32_t, uint32_t, int64_t, uint64_t, float数据类型。
-   TILING_DATA_FIELD_DEF_STRUCT中struct_type仅支持用BEGIN_TILING_DATA_DEF等定义的tiling结构体，不支持直接使用c++语法定义的结构体类型。
-   用户在host侧设置参数值和使用tiling数据需要使用set_xxx和get_xxx接口（xxx请替换为字段名），具体使用方法见调用示例。
-   tiling数据成员需要满足字节对齐要求，即：当前数据成员dataVar位于结构体的偏移offset满足， offset % sizeof(dataVar) == 0。
-   tiling结构体是全局属性，需注意应通过结构体名作为全局唯一标记，不同算子若注册同名不同结构tiling结构体则会发生未定义行为。

<!-- cannbot:related:start -->
## 相关

- [Host 缺 SetDataSize 致 TilingData 截断](../../../runbooks/precision/host_setdatasize_tilingdata.md)（`exemplifies`）：“- GetDataSize接口：获取TilingData的长度。”；“- **API 路径**：`REGISTER_TILING_DEFAULT(<TilingData>)`（kernel 侧注册）→ host `rawTilingData->GetData()` 填字段 → `rawTilingData->SetDataSize(sizeof(<TilingData>))` → kernel `GET_TILING_DATA(<TilingData>, tiling)` 解析。”。目标 runbook 展示未声明完整结构长度会导致传输截断，并给出 Host 到 Device 的可执行修复顺序。
- [TILING_DATA_DEF 迁移 rebase 字段失配判别](../../../runbooks/compilation/tiling_data_def_rebase.md)（`exemplifies`）：焦点卡指出“任何 kernel 直读的字段都必须在 `TILING_DATA_FIELD_DEF` 中显式声明”，候选 API 说明“set_\{field_name\}接口：用于设置TilingData类的字段值”；API 的字段生成合同正是 rebase 后 host setter 与 kernel 字段集必须同步的依据。
- [TilingData 须 host 与 kernel 各定义一份](../../../runbooks/compilation/tilingdata_host_kernel.md)（`exemplifies`）：新增 TilingData struct 时，同步在 host 可见头与 kernel 可见头**各定义一份**，字段顺序/类型逐字一致；优先放在算子既有的 host struct 汇总头（若该头非跨算子共享、可改）。；定义一个TilingData的类，添加所需的成员变量（TilingData字段），用于保存所需TilingData参数。完成该TilingData类的定义后，该类通过继承TilingDef类（用来存放、处理用户自定义Tiling结构体成员变量的基类）提供以下接口：runbook 的双端字段一致性要求由结构定义 API 补齐字段、序列化和长度接口背景。
- [限制TilingData结构大小](../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/limit_tiling_data_size.md)（`explains`）：“- CheckAlignAndGenPlaceHolder：该接口是内部关联接口，用于框架侧检查Tiling结构体中成员变量是否满足字节对齐要求，并对不对齐的变量进行补齐，开发者无需关注。”；“调用GET_TILING_DATA宏后，会将Tiling信息从GM拷贝到AI处理器的栈空间上，期间会有拷贝开销，由于GM访问效率较低，同时考虑到栈空间限制，需要限制TilingData结构大小。”。指南把结构定义的对齐与长度直接转成字段精简、排布和 GM→栈开销优化决策。
- [GET_TILING_DATA](../../simd_api/basic_api/kernel_tiling/get_tiling_data.md)（`related`）：“- SaveToBuffer接口：完成TilingData的序列化和保存。”；“获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。”。Host 序列化的 TilingData 经 kernel 入参传递后由 GET_TILING_DATA 反序列化到同一注册结构。
- [TilingData结构注册](tiling_data_struct_register.md)（`related`）：“定义一个TilingData的类，添加所需的成员变量（TilingData字段），用于保存所需TilingData参数。”；“注册定义的TilingData结构体并和自定义算子绑定。具体使用说明请参考调用示例。”。结构定义先产生字段与序列化类型，注册步骤再把该类型绑定到算子。
<!-- cannbot:related:end -->
