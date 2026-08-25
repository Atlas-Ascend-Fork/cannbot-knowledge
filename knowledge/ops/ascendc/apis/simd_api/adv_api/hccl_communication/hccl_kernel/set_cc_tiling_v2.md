---
type: API
title: SetCcTilingV2
description: 用于设置HCCL客户端中某个通信算法配置的TilingData地址。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/SetCcTilingV2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetCcTilingV2

用于设置HCCL客户端中某个通信算法配置的TilingData地址。

函数原型：__aicore__ inline int32_t SetCcTilingV2(uint64_t offset)

参数：
- offset（输入）：通信算法配置Mc2CcTiling参数地址相对于Mc2InitTiling起始地址的偏移。Mc2CcTiling在Host侧计算得出，具体请参考表2 Mc2CcTiling参数说明，由框架传递到Kernel函数中使用。

返回值：- HCCL_SUCCESS，表示成功。

约束：
- 若调用本接口，必须保证InitV2在本接口前被调用。
- Tiling参数相同的同一种通信算法在调用Prepare接口前，只需要调用一次本接口，请参考调用示例：类型不同、Tiling参数不同的通信。
- 对于同一种通信算法，如果Tiling参数不同，重复调用本接口会覆盖之前的Tiling参数地址，因此需要在调用Prepare接口后再调用本接口设置新的Tiling参数。请参考调用示例：类型相同、Tiling参数不同的通信。
- 若调用本接口，必须使用标准C++语法定义TilingData结构体的开发方式。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。
