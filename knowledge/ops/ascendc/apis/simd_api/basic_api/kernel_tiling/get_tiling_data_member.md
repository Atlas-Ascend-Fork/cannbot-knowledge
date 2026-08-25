---
type: API
title: GET_TILING_DATA_MEMBER
description: 用于获取tiling结构体的成员变量。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/GET_TILING_DATA_MEMBER.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GET_TILING_DATA_MEMBER

用于获取tiling结构体的成员变量。

用于获取tiling结构体的成员变量。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：本函数需在算子kernel代码处使用，并且传入的tiling_data参数不需要声明类型。；暂不支持Kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [GET_TILING_DATA 首参传类型名致变量遮蔽类型](../../../../runbooks/compilation/get_tiling_data.md)（`exemplifies`）：Member 版本读取 TilingData 单字段，适合避免复制整个结构；与普通宏按访问粒度选型。
- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《GET_TILING_DATA_MEMBER》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [COPY_TILING_WITH_ARRAY](copy_tiling_with_array.md)（`related`）：GET_TILING_DATA_MEMBER说明用于获取tiling结构体的成员变量；对COPY_TILING_WITH_ARRAY而言，数组 TilingData 的复制宏与结构体宏互为声明方案，Kernel 侧再按整对象或成员宏解析同一块 GM Tiling 数据。
- [GET_TILING_DATA_PTR_WITH_STRUCT](get_tiling_data_ptr_with_struct.md)（`related`）：GET_TILING_DATA_PTR_WITH_STRUCT说明在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。
- [GET_TILING_DATA_WITH_STRUCT](get_tiling_data_with_struct.md)（`related`）：GET_TILING_DATA_WITH_STRUCT说明使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。
- [GetTiling](../../adv_api/convolution_compute/conv3_d_backprop_filter_tiling/get_tiling.md)（`related`）：GetTiling 与《GET_TILING_DATA_MEMBER》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [RegisterNoneTiling](register_none_tiling.md)（`related`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《GET_TILING_DATA_MEMBER》补充：用于获取tiling结构体的成员变量。
- [TilingData结构定义](../../../utils_api/tiling_data_structure_register/tiling_data_struct_definition.md)（`related`）：TilingData结构定义说明定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。
- [COPY_TILING_WITH_STRUCT](copy_tiling_with_struct.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；GET_TILING_DATA_MEMBER正文说明“用于获取tiling结构体的成员变量”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [GET_TILING_DATA](get_tiling_data.md)（`same_topic`）：MEMBER 只读取指定 tiling 字段，避免无须复制完整结构，是同一传递契约的细粒度变体。
<!-- cannbot:related:end -->
