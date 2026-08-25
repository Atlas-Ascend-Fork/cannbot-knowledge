---
type: API
title: DumpTensor
description: 打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/onboard_print/DumpTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DumpTensor

打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。

该接口可以打印Tensor的内容，同时支持打印自定义的标签（仅支持uint32_t数据类型的信息），比如打印当前行号等。 在算子kernel侧实现代码中需要打印Tensor数据的地方，调用DumpTensor接口打印相关内容。样例如下： > [!CAUTION]注意 > 该接口主要用于调试分析，开启后会对算子性能产生一定影响，通常在调试阶段使用，生产环境建议关闭。 > 默认情况下，调用该接口就会打印相关内容，开发者可以参考关闭ASCENDC_DUMP说明，按需关闭该接口功能。 打印示例如下：

参数说明：T：需要dump的Tensor的数据类型。；tensor：输入 需要dump的Tensor。 •待dump的tensor位于Unified Buffer/L1 Buffer/L0C Buffer时使用LocalTensor类型的tensor参数输入。 •待dump的tensor位于Global Memory时使用GlobalTensor类型的tensor参数输入。；desc：输入 用户自定义附加信息（行号或其他自定义数字）。 在使用DumpTensor功能时，用户可通过desc参数附加自定义信息，以便在不同场景下区分Dump内容的来源。此功能有助于精准定位具体DumpTensor的输出，提升调试与分析效率。；dumpSize：输入 需要dump的元素个数。；shapeInfo：输入 传入Tensor的shape信息，可按照shape信息进行打印。 •当Shape尺寸大于dumpSize元素个数时，按照ShapeInfo打印元素，不足的Dump数据用"-"展示。 •当Shape尺寸小于等于dumpSize元素个数时，按照ShapeInfo打印元素，多出的Dump数据不展示。

约束：当前支持打印存储位置为Unified Buffer/L1 Buffer/L0C Buffer/Global Memory的Tensor信息。；在Ascend 950PR/Ascend 950DT下新增BiasTable Buffer和Fixpipe Buffer的Tensor数据打印。；针对Ascend 950PR/Ascend 950DT，使用该接口打印L1 Buffer、BiasTable Buffer或Fixpipe Buffer数据时，HDK版本需要至少升级到25.7.0以上。；针对Ascend 950PR/Ascend 950DT，打印Fixpipe Buffer中的Tensor信息场景：

<!-- cannbot:related:start -->
## 相关

- [双 VF 融合输出非预期 先排 CopyOut slot 勿用 PRINTF](../../../../../runbooks/precision/vf_fusion_output_unexpected_check_copyout_slot_not_printf.md)（`exemplifies`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《双 VF 融合输出非预期 先排 CopyOut slot 勿用 PRINTF》说明VF 融合(asc_vf_call/__simd_vf__)kernel 输出非预期(全零/错误)时，先排除 CopyOut buffer slot/参数顺序/buffer 映射等非 VF 因素，勿在 __simd_vf__ 函数内用 PRINTF(语义不兼容致观测假象)，用控制变量实验+参考实现交叉验证。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [稀疏反卷积精度误差源隔离配方](../../../../../runbooks/precision/cube_simt_fp32_precision_error_source_isolation.md)（`exemplifies`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《稀疏反卷积精度误差源隔离配方》说明用 K=1/inChannels=1/单核/SIMT 线程=1 退化测试与 kIdx=0 DumpTensor 对比，逐层隔离 Cube MatMul 与 SIMT ScatterAdd 的 FP32 误差贡献。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [NPU域上板调试（功能调试）](../../../../../guides/programming_guide/debug_and_tuning/functional_debug/npu_board_debug.md)（`explains`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《NPU域上板调试（功能调试）》说明NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [ShowKernelDebugData工具](../../../../../guides/programming_guide/appendix/show_kernel_debug_data_tool.md)（`explains`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《ShowKernelDebugData工具》说明提供Ascend C算子Kernel调测信息的离线解析能力，将导出的bin文件解析为可读格式。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [DumpAccChkPoint](dump_acc_chk_point.md)（`related`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《DumpAccChkPoint》说明打印指定Tensor内容并支持自定义标签，区别于DumpTensor，支持指定偏移位置开始打印Tensor数据。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [asc_dump](../../../../utils_api/tuning_interface/asc_dump.md)（`related`）：“asc_dump”定义：将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。使用该接口需要包含"utils/debug/asc_dump.h"头文件。该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。；“DumpTensor”定义：打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。。实质衔接：asc_dump 用于调试期查看任意内存并带附加信息；DumpTensor 是张量级替代，生产环境需通过 ASCENDC_DUMP 关闭以免影响性能。
- [上板打印](onboard_print.md)（`related`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《上板打印》说明上板打印接口集，包含 DumpTensor、DumpAccChkPoint、PrintTimeStamp 等调试输出接口。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [关闭ASCENDC_DUMP说明](../disable_ascendc_dump.md)（`related`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《关闭ASCENDC_DUMP说明》说明调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [调试接口](../debug_interface.md)（`related`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《调试接口》说明AscendC 调试接口总览，涵盖上板打印、异常检测、CPU 孪生调试、性能统计及 ASCENDC_DUMP 控制说明。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
<!-- cannbot:related:end -->
