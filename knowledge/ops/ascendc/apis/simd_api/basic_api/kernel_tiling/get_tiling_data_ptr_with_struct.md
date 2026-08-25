---
type: API
title: GET_TILING_DATA_PTR_WITH_STRUCT
description: 在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/GET_TILING_DATA_PTR_WITH_STRUCT.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GET_TILING_DATA_PTR_WITH_STRUCT

在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。

在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：该宏需在算子Kernel代码处使用，并且传入的dst_ptr参数无需声明类型。；动态Shape场景下，获取到的dst_ptr是指向Global Memory变量的指针；静态Shape场景下，获取到的dst_ptr是指向局部变量的指针，需确保在合理的作用域范围内使用。；暂不支持Kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：“GET_TILING_DATA_PTR_WITH_STRUCT”定义：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。；“GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型”定义：GET_TILING_DATA_WITH_STRUCT 宏内部对 tiling_struct 做 # 字符串化拼进 section 名，传入带 <> 的模板类型（如 MaskedFillTilingData<RANK>）会触发 C++ 解析错；用 if constexpr 或 trait 绕开 <> 又会破坏节级 tiling 注册，报 do not registe tiling struct。。实质衔接：宏按结构名返回带 __tiling_data_ptr__ 的指针，可再拷到栈；但直调工程没有生成宏、模板类型又会破坏字符串化，两张 runbook 精确界定停止边界。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`exemplifies`）：“GET_TILING_DATA_PTR_WITH_STRUCT”定义：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。；“直调不可用 GET_TILING_DATA_WITH_STRUCT 宏”定义：`<<<>>>` 直调工程无法使用自定义算子编译期生成的 GET_TILING_DATA_WITH_STRUCT/REGISTER_TILING_DEFAULT 宏，需逐字段从 __gm__ 拷贝 tiling 到 local；其它 void*→GM_ADDR、std::string、goto 限制为次要附带项，见对应卡。。实质衔接：宏按结构名返回带 __tiling_data_ptr__ 的指针，可再拷到栈；但直调工程没有生成宏、模板类型又会破坏字符串化，两张 runbook 精确界定停止边界。
- [COPY_TILING_WITH_STRUCT](copy_tiling_with_struct.md)（`related`）：“GET_TILING_DATA_PTR_WITH_STRUCT”定义：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。；“COPY_TILING_WITH_STRUCT”定义：拷贝Tiling结构体，并返回指向拷贝后的Tiling结构体的指针。该宏适用于嵌套结构体场景，可拷贝结构体的子结构体成员变量。该宏将指定结构体拷贝至栈上，适用于频繁访问Tiling数据的场景，能够加快数据访问速度。。实质衔接：宏按结构名返回带 __tiling_data_ptr__ 的指针，可再拷到栈；但直调工程没有生成宏、模板类型又会破坏字符串化，两张 runbook 精确界定停止边界。
- [GET_TILING_DATA_MEMBER](get_tiling_data_member.md)（`related`）：GET_TILING_DATA_PTR_WITH_STRUCT说明在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。
- [GetTiling](../../adv_api/convolution_compute/conv3_d_backprop_filter_tiling/get_tiling.md)（`related`）：GetTiling 与《GET_TILING_DATA_PTR_WITH_STRUCT》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [RegisterNoneTiling](register_none_tiling.md)（`related`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《GET_TILING_DATA_PTR_WITH_STRUCT》补充：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。
- [TilingData结构定义](../../../utils_api/tiling_data_structure_register/tiling_data_struct_definition.md)（`related`）：“GET_TILING_DATA_PTR_WITH_STRUCT”定义：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。；“TilingData结构定义”定义：定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。。实质衔接：宏按结构名返回带 __tiling_data_ptr__ 的指针，可再拷到栈；但直调工程没有生成宏、模板类型又会破坏字符串化，两张 runbook 精确界定停止边界。
- [GET_TILING_DATA_WITH_STRUCT](get_tiling_data_with_struct.md)（`same_topic`）：“GET_TILING_DATA_PTR_WITH_STRUCT”定义：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。；“GET_TILING_DATA_WITH_STRUCT”定义：使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。。实质衔接：宏按结构名返回带 __tiling_data_ptr__ 的指针，可再拷到栈；但直调工程没有生成宏、模板类型又会破坏字符串化，两张 runbook 精确界定停止边界。
<!-- cannbot:related:end -->
