---
type: API
title: SetGlobalBuffer
description: 传入全局数据地址，初始化GlobalTensor。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetGlobalBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetGlobalBuffer

传入 GM 全局数据地址和大小，初始化 GlobalTensor。参数：buffer 为 GlobalTensor 源操作数（GM 地址），bufferSize 为元素个数。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [DataCopy 不自动按 tile 推进须显式元素 offset](../../../../../runbooks/precision/datacopy_setglobalbuffer_no_auto_advance_tileoffset.md)（`exemplifies`）：SetGlobalBuffer 只绑定 GM 基址和可选长度，不维护 Process 循环的 tile 游标，因此每轮必须显式使用 gm[tileOffset] 子视图。
- [DataCopyPad CopyIn 小输入 32B DMA 越界](../../../../../runbooks/compilation/datacopypad_copyin_32b_dma.md)（`exemplifies`）：《DataCopyPad CopyIn 小输入 32B DMA 越界》说明DataCopyPad CopyIn 不论 DataCopyExtParams.blockLen 写多少，底层 DMA 引擎按 32 字节（1 DataBlock）粒度读 GM；当 Host 仅按有效元素数分配 < 32B 输入、SetGlobalBuffer(ptr,N) 只声明逻辑可读范围不扩大物理分配时，DMA 实读 32B 越过已映射内存 → device error 507035 / segfault。判别：小输入（有效元素 × sizeof(T) < 32B）+ SetGlobalBuffer N < ceil(32/sizeof(T)) + Host 分配未对齐到 32B。；《SetGlobalBuffer》说明传入全局数据地址，初始化GlobalTensor。。二者在小输入越界由GM物理分配小于32B DMA粒度触发；GM到UB DataCopyPad接口和SetGlobalBuffer共同界定逻辑范围与物理读取的差异上存在可执行的直接衔接。
- [GM_ADDR 标量不可解引用为 tiling 结构体指针](../../../../../runbooks/compilation/gm_addr_tiling.md)（`exemplifies`）：GM_ADDR 标量不可解引用为 tiling 结构体指针 与《SetGlobalBuffer》的实质衔接是：GM_ADDR 在该入口是 __gm__ uint8_t 标量而非结构体指针；typed __gm__ tiling 指针、Kernel Tiling/GET_TILING_DATA 和地址空间案例给出正确入口与强转边界。
- [GetShapeInfo](get_shape_info.md)（`related`）：GetShapeInfo 与《SetGlobalBuffer》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [GlobalTensor简介](global_tensor_intro.md)（`related`）：《SetGlobalBuffer》明确“传入全局数据地址，初始化GlobalTensor。”；它与《GlobalTensor简介》的“GlobalTensor用来存放Global Memory（外部存储）的全局数据。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
