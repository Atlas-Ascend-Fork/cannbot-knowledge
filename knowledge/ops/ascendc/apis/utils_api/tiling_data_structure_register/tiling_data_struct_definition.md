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

- [Host 缺 SetDataSize 致 TilingData 截断](../../../runbooks/precision/host_setdatasize_tilingdata.md)（`exemplifies`）：The structure API defines serialization and data-length semantics for the custom TilingData whose complete byte count must be published with SetDataSize.
- [RmsNormTiling 与 CANN 内置类型冲突 — 改名隔离](../../../runbooks/compilation/tiling_type_name_does_not_shadow_cann_builtin.md)（`exemplifies`）：API 明确 tiling 结构体名是全局唯一标记、同名不同结构会产生未定义行为，直接支撑本卡用 op 前缀/Params 后缀避开 CANN 已导出 RmsNormTiling。
- [TILING_DATA_DEF 迁移 rebase 字段失配判别](../../../runbooks/compilation/tiling_data_def_rebase.md)（`exemplifies`）：API 定义了 TILING_DATA_FIELD_DEF 生成 set/get 字段和序列化长度的契约，解释为何旧 struct 新增字段必须同步声明到新 TilingData 类型。
- [TilingData 须 host 与 kernel 各定义一份](../../../runbooks/compilation/tilingdata_host_kernel.md)（`exemplifies`）：TilingData 须 host 与 kernel 各定义一份：本故障来自host不可见kernel侧struct；TilingData定义/注册/属性传递卡给出正式契约，struct.h include与手写头遮蔽、rebase字段失配卡覆盖同一双侧类型同步链的具体失败。 目标卡《TilingData结构定义》补充：定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。
- [通过TilingData传递属性信息](../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_data_attributes.md)（`explains`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“TilingData结构定义”明确定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [限制TilingData结构大小](../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/limit_tiling_data_size.md)（`explains`）：字段类型和排布在结构定义处决定总字节数，是优化落点。
- [GET_TILING_DATA_MEMBER](../../simd_api/basic_api/kernel_tiling/get_tiling_data_member.md)（`related`）：TilingData结构定义说明定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。
- [GET_TILING_DATA_PTR_WITH_STRUCT](../../simd_api/basic_api/kernel_tiling/get_tiling_data_ptr_with_struct.md)（`related`）：“GET_TILING_DATA_PTR_WITH_STRUCT”定义：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。；“TilingData结构定义”定义：定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。。实质衔接：宏按结构名返回带 __tiling_data_ptr__ 的指针，可再拷到栈；但直调工程没有生成宏、模板类型又会破坏字符串化，两张 runbook 精确界定停止边界。
- [TilingData结构注册](tiling_data_struct_register.md)（`same_topic`）：必须先用定义宏声明 TilingData 成员与布局，再由注册宏把该结构绑定到 op_type。
- [Tiling数据结构注册](tiling_data_structure_register.md)（`same_topic`）：Tiling数据结构注册 与《TilingData结构定义》的实质衔接是：TilingData 定义、注册、读取宏、尺寸限制与三张冲突/截断故障卡共同覆盖 host→kernel 数据契约。
<!-- cannbot:related:end -->
