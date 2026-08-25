---
type: API
title: asc_dump
description: 将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。使用该接口需要包含"utils/debug/asc_dump.h"头文件。该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/asc_dump.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_dump

将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。

使用该接口需要包含"utils/debug/asc_dump.h"头文件。

> [!CAUTION]注意
>该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。
>默认情况下，该功能开启。

函数原型：template<typename T>；__aicore__ static __attribute__((noinline)) void asc_dump_gm(__gm__ T* input, uint32_t desc, uint32_t dump_size)；template<typename T> 等28种重载

参数：T（输入）：待dump的数据类型。；U（输入）：待dump的寄存器数据类型。；input（输入）：所需打印的内存块的起始地址。；desc（输入）：自定义信息。uint32_t类型，支持的数据范围是[0, 2^32 - 1]。；dump_size（输入）：所需要打印的元素数量。

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   针对Ascend 950PR/Ascend 950DT，在使用该接口打印L1 Buffer、BiasTable Buffer或Fixpipe Buffer数据时，HDK版本需要至少升级到25.7.0以上。

<!-- cannbot:related:start -->
## 相关

- [NPU域上板调试（功能调试）](../../../guides/programming_guide/debug_and_tuning/functional_debug/npu_board_debug.md)（`explains`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《asc_dump》提供“将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。使用该接口需要包含"utils/debug/asc_dump.h"头文件。该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [DumpAccChkPoint](../../simd_api/basic_api/debug_interface/onboard_print/dump_acc_chk_point.md)（`related`）：DumpAccChkPoint 与《asc_dump》的实质衔接是：DumpAccChkPoint 与 DumpTensor 都受 ASCENDC_DUMP 控制，前者额外支持 offset；上板打印与 NPU 域调试指南给出启用位置，asc_dump 是 C 接口层对应的内存打印能力。
- [DumpTensor](../../simd_api/basic_api/debug_interface/onboard_print/dump_tensor.md)（`related`）：“asc_dump”定义：将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。使用该接口需要包含"utils/debug/asc_dump.h"头文件。该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。；“DumpTensor”定义：打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。。实质衔接：asc_dump 用于调试期查看任意内存并带附加信息；DumpTensor 是张量级替代，生产环境需通过 ASCENDC_DUMP 关闭以免影响性能。
- [ToFile](../../simd_api/basic_api/data_structures/local_tensor/to_file.md)（`related`）：ToFile 与《asc_dump》的实质衔接是：ToFile 与 Print/asc_dump 都从 LocalTensor 导出调试数据，区别在文件、控制台和 dump 通道。
- [关闭ASCENDC_DUMP说明](../../simd_api/basic_api/debug_interface/disable_ascendc_dump.md)（`related`）：“asc_dump”定义：将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。使用该接口需要包含"utils/debug/asc_dump.h"头文件。该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。；“关闭ASCENDC_DUMP说明”定义：调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。。实质衔接：asc_dump 用于调试期查看任意内存并带附加信息；DumpTensor 是张量级替代，生产环境需通过 ASCENDC_DUMP 关闭以免影响性能。
- [调测接口](tuning_interface.md)（`related`）：“asc_dump”定义：将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。使用该接口需要包含"utils/debug/asc_dump.h"头文件。该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。；“调测接口”定义：提供printf、assert、__trap、asc_dump等调测接口。。实质衔接：asc_dump 用于调试期查看任意内存并带附加信息；DumpTensor 是张量级替代，生产环境需通过 ASCENDC_DUMP 关闭以免影响性能。
<!-- cannbot:related:end -->
