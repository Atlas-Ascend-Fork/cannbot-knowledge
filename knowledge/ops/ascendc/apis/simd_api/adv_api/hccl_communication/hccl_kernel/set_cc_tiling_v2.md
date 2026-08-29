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

<!-- cannbot:related:start -->
## 相关

- [GetTiling](../hccl_tiling/get_tiling.md)（`related`）：Host Tiling 接口“获取Mc2InitTiling参数和Mc2CcTiling参数。”；Device 接口说明“Mc2CcTiling在Host侧计算得出”，因此 GetTiling 产出的 Mc2CcTiling 正是 SetCcTilingV2 在 Kernel 侧消费的配置来源。
- [MatmulAllReduce 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_all_reduce_950.md)（`related`）：算子 POD 表注明“｜ 950 POD ｜ `mc2CcTiling` ｜ 外部结构 ｜ offset `sizeof(Mc2InitTiling)` ｜ 通信描述 ｜ AllReduce 或 AllToAll config ｜ `SetCcTilingV2` ｜ opType 随 topology ｜”；接口卡说明“用于设置HCCL客户端中某个通信算法配置的TilingData地址。”，闭合 topology 选择后的通信配置地址安装。
- [MatmulAlltoAll A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_allto_all.md)（`related`）：`mc2CcTiling` ｜ generated POD ｜ 同上 ｜ HCCL CC 配置 ｜ 同上 ｜ `SetCcTilingV2`；Mc2CcTiling在Host侧计算得出；连接 Host 产生的通信 Tiling 与 Kernel 地址设置。
- [ReduceScatter](reduce_scatter.md)（`related`）：调用本接口前确保已调用过InitV2和SetCcTilingV2接口。；用于设置HCCL客户端中某个通信算法配置的TilingData地址。ReduceScatter 明确要求前置调用，而 SetCcTilingV2 卡给出该前置步骤设置通信算法 TilingData 的参数和覆盖规则。
- [SetCcTiling（废弃）](set_cc_tiling_deprecated.md)（`same_topic`）：用于设置HCCL客户端通信算法的Tiling地址。；用于设置HCCL客户端中某个通信算法配置的TilingData地址。两卡核心对象与决策都是 HCCL 通信算法 Tiling 地址设置，旧接口传 GM 指针且已废弃，V2 改为相对 Mc2InitTiling 的 offset。
<!-- cannbot:related:end -->
