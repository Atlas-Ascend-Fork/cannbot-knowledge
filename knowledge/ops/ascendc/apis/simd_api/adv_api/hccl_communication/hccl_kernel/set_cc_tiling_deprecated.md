---
type: API
title: SetCcTiling（废弃）
description: 用于设置HCCL客户端通信算法的Tiling地址。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/SetCcTiling_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetCcTiling（废弃）

用于设置HCCL客户端通信算法的Tiling地址。

函数原型：__aicore__ inline int32_t SetCcTiling(__gm__ void* ccOpTilingData)

参数：
- ccOpTilingData（输入）：通信算法的Mc2CcTiling参数的地址。Mc2CcTiling在Host侧计算得出，具体请参考表2 Mc2CcTiling参数说明，由框架传递到Kernel函数中使用。

返回值：- HCCL_SUCCESS，表示成功。

约束：
- 参数相同的同一种通信算法在调用Prepare接口前只需要调用一次本接口，否则需要多次调用本接口。
- 同一种通信算法只支持设置一个ccOpTilingData地址；对于同一种通信算法，重复调用本接口会覆盖该通信算法的ccOpTilingData地址。
- 若调用本接口，必须与传initTiling地址的Init接口配合使用，且Init接口在本接口前被调用。
- 若调用本接口，必须使用标准C++语法定义TilingData结构体的开发方式。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [v1版本TilingData（废弃）](../hccl_tiling/v1_tiling_data_deprecated.md)（`related`）：旧 Kernel SetCcTiling 消费 V1/V2 数据，迁移时 Host 与 Kernel 两端需同时替换。
- [Init（废弃）](init_deprecated.md)（`same_topic`）：焦点处理废弃 HCCL Init 向 InitV2/SetCcTilingV2 迁移的生命周期；SetCcTiling（废弃）正文说明“用于设置HCCL客户端通信算法的Tiling地址”。候选给出旧接口的一一替代、通信配置迁移或最终资源回收步骤。
- [SetCcTilingV2](set_cc_tiling_v2.md)（`same_topic`）：废弃接口与 V2 都向 HCCL 客户端设置通信算法 TilingData 地址；V2 是正文给出的迁移目标。
- [v2版本TilingData（废弃）](../hccl_tiling/v2_tiling_data_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《SetCcTiling（废弃）》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
<!-- cannbot:related:end -->
