---
type: API
title: GET_TILING_DATA_WITH_STRUCT
description: 使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/GET_TILING_DATA_WITH_STRUCT.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GET_TILING_DATA_WITH_STRUCT

使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。

用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构注册注册了多个TilingData结构体，使用该接口返回默认注册的结构体。

本接口组包含 GET_TILING_DATA, GET_TILING_DATA。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：本函数需在算子kernel代码处使用，并且传入的tiling_data参数不需要声明类型。；暂不支持kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GET_TILING_DATA 首参传类型名致变量遮蔽类型](../../../../runbooks/compilation/get_tiling_data.md)（`exemplifies`）：正式 WithStruct API 给出参数与限制，连接 runbook 和接口契约。
- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《GET_TILING_DATA_WITH_STRUCT》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [REGISTER_TILING_DEFAULT 取小档致 NaN](../../../../runbooks/compilation/register_tiling_default_nan.md)（`exemplifies`）：REGISTER_TILING_DEFAULT 取小档致 NaN 与《GET_TILING_DATA_WITH_STRUCT》的实质衔接是：REGISTER_TILING_DEFAULT 决定 opParaSize，必须覆盖最大 TilingData struct；注册宏、GET 宏、host/kernel 结构、SetDataSize 与追加越界卡描述同一 buffer 尺寸链。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：REGISTER_TILING_DEFAULT 多 struct 冲突 与《GET_TILING_DATA_WITH_STRUCT》的实质衔接是：一个算子只能有一个 REGISTER_TILING_DEFAULT struct；新分支须按 TilingKey 注册，GET 宏、Host/Kernel struct、SetDataSize 与冲突故障共同约束 buffer 和 key。
- [Stub tiling padding 不解 aclnn Segfault](../../../../runbooks/compilation/stub_tiling_padding_aclnn_segfault.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 决定 kernel 注册的 tiling 结构和 opParaSize，本卡用 host `sizeof(T)` 对照该容量并证明 padding 只修容量契约。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`exemplifies`）：API 正文明确写出 GET_TILING_DATA_WITH_STRUCT 暂不支持 kernel 直调工程，直接解释本卡为何必须在 <<<>>> 路径改为 typed __gm__ 指针逐字段读取。
- [算子属性默认值 stringstream 截断致 FP32 标量误差](../../../../runbooks/precision/stringstream_fp32.md)（`exemplifies`）：算子属性默认值 stringstream 截断致 FP32 标量误差 与《GET_TILING_DATA_WITH_STRUCT》的实质衔接是：OpDef Attr是默认 float 字面量进入 op_build 序列化的起点，GET_TILING_DATA_WITH_STRUCT是 device 读取终点；TilingData缓存与 numpy标量提升是相同稳定ULP现象的关键差分根因。
- [通过TilingData传递属性信息](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_data_attributes.md)（`explains`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“GET_TILING_DATA_WITH_STRUCT”明确使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [GET_TILING_DATA_MEMBER](get_tiling_data_member.md)（`related`）：GET_TILING_DATA_WITH_STRUCT说明使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。
- [InitV2](../../adv_api/hccl_communication/hccl_kernel/init_v2.md)（`related`）：InitV2 的 initTiling 不能是 GM 地址，推荐由该宏取得 TilingData 栈地址后传入。
- [Kernel Tiling](kernel_tiling.md)（`related`）：GET_TILING_DATA_WITH_STRUCT说明使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。
- [RegisterNoneTiling](register_none_tiling.md)（`related`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《GET_TILING_DATA_WITH_STRUCT》补充：使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。
- [COPY_TILING_WITH_STRUCT](copy_tiling_with_struct.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；GET_TILING_DATA_WITH_STRUCT正文说明“使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [GET_TILING_DATA](get_tiling_data.md)（`same_topic`）：WITH_STRUCT 显式指定结构体类型，适合多 TilingData 或需要栈地址的场景；普通宏返回默认注册结构。
- [GET_TILING_DATA_PTR_WITH_STRUCT](get_tiling_data_ptr_with_struct.md)（`same_topic`）：“GET_TILING_DATA_PTR_WITH_STRUCT”定义：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。；“GET_TILING_DATA_WITH_STRUCT”定义：使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。。实质衔接：宏按结构名返回带 __tiling_data_ptr__ 的指针，可再拷到栈；但直调工程没有生成宏、模板类型又会破坏字符串化，两张 runbook 精确界定停止边界。
<!-- cannbot:related:end -->
