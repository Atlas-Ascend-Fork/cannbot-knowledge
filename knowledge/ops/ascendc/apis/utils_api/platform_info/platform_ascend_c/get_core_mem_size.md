---
type: API
title: GetCoreMemSize
description: 获取硬件平台存储空间的内存大小，例如L1、L0_A、L0_B、L2等，支持的存储空间类型定义如下：
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreMemSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GetCoreMemSize

## 功能说明
获取硬件平台存储空间的内存大小，例如L1、L0_A、L0_B、L2等，支持的存储空间类型定义如下：
## 函数原型
## 参数说明
## 返回值说明
无
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [507035 — Host 按逻辑行宽预算导致 UB 溢出](../../../../runbooks/compilation/ub_budget_uses_aligned_physical_width_507035.md)（`exemplifies`）：GetCoreMemSize 与《507035 — Host 按逻辑行宽预算导致 UB 溢出》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR](../../../../runbooks/compilation/fp16_double_buffer_ub_budget_queue_vs_tbuf_multiplier.md)（`exemplifies`）：GetCoreMemSize 与《FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [Conv3DBackpropFilter Tiling构造函数](../../../simd_api/adv_api/convolution_compute/conv3_d_backprop_filter_tiling/conv3_d_backprop_filter_tiling_constructor.md)（`related`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《GetCoreMemSize》说明获取硬件平台存储空间的内存大小，例如L1、L0_A、L0_B、L2等，支持的存储空间类型定义如下：。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [GetCoreMemBw](get_core_mem_bw.md)（`related`）：GetCoreMemSize 与《GetCoreMemBw》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [MultiCoreMatmulGetTmpBufSize](../../../simd_api/adv_api/cube_compute/get_matmul_compute_space/multi_core_matmul_get_tmp_buf_size.md)（`related`）：GetCoreMemSize 与《MultiCoreMatmulGetTmpBufSize》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [MultiCoreMatmulGetTmpBufSizeV2](../../../simd_api/adv_api/cube_compute/get_matmul_compute_space/multi_core_matmul_get_tmp_buf_size_v2.md)（`related`）：GetCoreMemSize 与《MultiCoreMatmulGetTmpBufSizeV2》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [PlatformAscendC](platform_ascend_c.md)（`related`）：GetCoreMemSize 与《PlatformAscendC》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [PlatformAscendC简介](platform_ascend_c_intro.md)（`related`）：GetCoreMemSize 与《PlatformAscendC简介》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [ReserveLocalMemory](reserve_local_memory.md)（`related`）：GetCoreMemSize 与《ReserveLocalMemory》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [更多样例（数学计算）](../../../simd_api/adv_api/math_compute/more_examples.md)（`related`）：样例一、二都要在预留后查询实际可用 UB，再据此选择 tmpSize 或最大 Shape；GetCoreMemSize 是该预算步骤的直接输入。
- [构造及析构函数（PlatformAscendC）](constructor_and_destructor.md)（`related`）：GetCoreMemSize 与《构造及析构函数（PlatformAscendC）》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
<!-- cannbot:related:end -->
