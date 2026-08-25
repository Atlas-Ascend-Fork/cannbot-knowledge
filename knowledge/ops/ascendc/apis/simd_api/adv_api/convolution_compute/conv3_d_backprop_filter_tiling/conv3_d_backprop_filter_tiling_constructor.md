---
type: API
title: Conv3DBackpropFilter Tiling构造函数
description: 用于创建一个Conv3DBackpropFilter单核Tiling对象。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/Conv3DBackpropFilter_Tiling_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# Conv3DBackpropFilter Tiling构造函数

用于创建一个Conv3DBackpropFilter单核Tiling对象。

参数：
- ascendcPlatform（输入）：传入硬件平台的信息，PlatformAscendC定义请参见构造及析构函数。
- platform（输入）：传入硬件版本以及AI Core中各个硬件单元提供的内存大小。PlatformInfo构造时通过构造及析构函数获取。 PlatformInfo结构定义如下代码所示，socVersion通过GetSocVersion获取并透传，各类硬件存储空间大小通过GetCoreMemSize获取并透传。

<!-- cannbot:related:start -->
## 相关

- [GetCoreMemSize](../../../../utils_api/platform_info/platform_ascend_c/get_core_mem_size.md)（`related`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《GetCoreMemSize》说明获取硬件平台存储空间的内存大小，例如L1、L0_A、L0_B、L2等，支持的存储空间类型定义如下：。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [GetSocVersion](../../../../utils_api/platform_info/platform_ascend_c/get_soc_version.md)（`related`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《GetSocVersion》说明获取当前硬件平台版本型号。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [GetTiling](get_tiling.md)（`related`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《GetTiling》说明获取Tiling参数。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [PlatformInfo](../../../../utils_api/tiling_tuning/context_builder/platform_info.md)（`related`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [TConv3DBpFilterTiling结构体](t_conv3_d_bp_filter_tiling_struct.md)（`related`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《TConv3DBpFilterTiling结构体》说明TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [构造及析构函数（PlatformAscendC）](../../../../utils_api/platform_info/platform_ascend_c/constructor_and_destructor.md)（`related`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《构造及析构函数（PlatformAscendC）》说明在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [Conv3DBackpropFilter Tiling侧接口](conv3_d_backprop_filter_tiling.md)（`same_topic`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《Conv3DBackpropFilter Tiling侧接口》说明提供Conv3D反向卷积滤波器梯度的Host侧Tiling接口，包含TConv3DBpFilterTiling结构体、GetTiling及形状与类型设置方法。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [Conv3DBackpropFilterTiling](conv3_d_backprop_filter_tiling_usage.md)（`same_topic`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《Conv3DBackpropFilterTiling》说明提供获取Conv3DBackpropFilter Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
<!-- cannbot:related:end -->
