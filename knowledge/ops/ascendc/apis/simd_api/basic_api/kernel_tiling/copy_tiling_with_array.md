---
type: API
title: COPY_TILING_WITH_ARRAY
description: 拷贝指定大小的数组内容到目标数组中，并返回指向拷贝后数组的指针。适用于拷贝一个结构体的数组成员变量的场景。该宏将指定数组拷贝至栈上，适用于频繁访问Tiling数据的场景，能够加快数据访问速度。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/COPY_TILING_WITH_ARRAY.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# COPY_TILING_WITH_ARRAY

拷贝指定大小的数组内容到目标数组中，并返回指向拷贝后数组的指针。适用于拷贝一个结构体的数组成员变量的场景。该宏将指定数组拷贝至栈上，适用于频繁访问Tiling数据的场景，能够加快数据访问速度。

在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。

本接口组包含 GET_TILING_DATA_PTR_WITH_STRUCT。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：该宏需在算子Kernel代码处使用，并且传入的dst_ptr参数无需声明类型。；动态Shape场景下，获取到的dst_ptr是指向Global Memory变量的指针；静态Shape场景下，获取到的dst_ptr是指向局部变量的指针，需确保在合理的作用域范围内使用。；暂不支持Kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [COPY_TILING_WITH_STRUCT](copy_tiling_with_struct.md)（`related`）：COPY_TILING_WITH_STRUCT说明拷贝Tiling结构体，并返回指向拷贝后的Tiling结构体的指针。该宏适用于嵌套结构体场景，可拷贝结构体的子结构体成员变量。该宏将指定结构体拷贝至栈上，适用于频繁访问Tiling数据的场景，能够加快数据访问速度；对COPY_TILING_WITH_ARRAY而言，数组 TilingData 的复制宏与结构体宏互为声明方案，Kernel 侧再按整对象或成员宏解析同一块 GM Tiling 数据。
- [GET_TILING_DATA](get_tiling_data.md)（`related`）：GET_TILING_DATA说明用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构注册注册了多个TilingData结构体，使用该接口返回默认注册的结构体；对COPY_TILING_WITH_ARRAY而言，数组 TilingData 的复制宏与结构体宏互为声明方案，Kernel 侧再按整对象或成员宏解析同一块 GM Tiling 数据。
- [GET_TILING_DATA_MEMBER](get_tiling_data_member.md)（`related`）：GET_TILING_DATA_MEMBER说明用于获取tiling结构体的成员变量；对COPY_TILING_WITH_ARRAY而言，数组 TilingData 的复制宏与结构体宏互为声明方案，Kernel 侧再按整对象或成员宏解析同一块 GM Tiling 数据。
<!-- cannbot:related:end -->
